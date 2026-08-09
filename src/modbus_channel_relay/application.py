import logging
import time
import struct

from pydoover.docker import Application

from .app_config import (
    DEFAULT_DATA_TYPE,
    DEFAULT_REGISTER_TYPE,
    ModbusChannelRelayConfig,
    ModbusDataType,
    as_enum,
)

log = logging.getLogger()


class ModbusChannelRelayApplication(Application):
    config: ModbusChannelRelayConfig
    last_fetched: float

    config_cls = ModbusChannelRelayConfig

    async def setup(self):
        self.last_fetched = 0.0

        self.modbus_iface.timeout = (
            15  ## Set GRPC timeout to 15 seconds for modbus iface
        )

    async def main_loop(self):
        if time.time() - self.last_fetched < self.config.period.value * 60:
            log.info("Looping, time not yet reached...")
            return

        channel_msg = {}
        for mb_map in self.config.modbus_maps.elements:
            map_msg = {}

            registers = None
            error = None
            try:
                registers = await self.modbus_iface.read_registers(
                    start_address=mb_map.start_address.value,
                    num_registers=mb_map.number_of_registers.value,
                    modbus_id=mb_map.modbus_id.value,
                    register_type=as_enum(
                        mb_map.register_type, DEFAULT_REGISTER_TYPE
                    ).code,
                )
            except Exception as e:
                error = e

            if registers is None or error is not None:
                log.error(
                    f"Failed to read registers for modbus map {mb_map.modbus_id.value}, start address {mb_map.start_address.value}, number of registers {mb_map.number_of_registers.value}: {error}"
                )
                continue

            ## Convert the registers to a dictionary with the register number as the key
            if isinstance(registers, int) or isinstance(registers, float):
                registers = [registers]
            registers = dict(enumerate(registers, start=mb_map.start_address.value))

            for register_map in mb_map.register_maps.elements:
                ## Create the nested object structure
                j_keys = register_map.json_key.value.split(".")
                j_keys.reverse()
                data_type = as_enum(register_map.data_type, DEFAULT_DATA_TYPE)
                if data_type == ModbusDataType.INTEGER16:
                    j_obj = {
                        j_keys[0]: registers.pop(register_map.register_number.value)
                    }
                    for j_key in j_keys[1:]:
                        j_obj = {j_key: j_obj}
                    map_msg.update(j_obj)
                elif data_type == ModbusDataType.FLOAT32_CD_AB:
                    reg_low = registers.pop(register_map.register_number.value)
                    reg_high = registers.pop(register_map.register_number.value + 1)
                    j_obj = {
                        j_keys[0]: struct.unpack(
                            ">f", struct.pack(">HH", reg_high, reg_low)
                        )[0]
                    }
                    for j_key in j_keys[1:]:
                        j_obj = {j_key: j_obj}
                    map_msg.update(j_obj)
            ## For remaining registers, add them to the map msg. Channel data keys
            ## must be strings, so the register number is stringified here rather
            ## than relying on a JSON encoder to do it on the way out.
            for k, v in registers.items():
                map_msg[str(k)] = v
            if mb_map.channel_namespace.value not in [
                None,
                "",
                "null",
                "None",
                "none",
                "NONE",
            ]:
                map_msg = {mb_map.channel_namespace.value: map_msg}

            channel_msg.update(map_msg)
            log.info(f"Channel msg: {channel_msg}")

        ## Two writes, because the one call this replaced did both. The old
        ## `publish_to_channel_async` issued the DDA's `WriteToChannel` with
        ## `record_log=True`, which updates the channel *aggregate* and records a
        ## log entry alongside it. `create_message` alone is only the second
        ## half, and leaves the aggregate empty -- which is what everything
        ## reading this channel actually looks at.
        ##
        ## The aggregate goes first: it is the state consumers read, so if the
        ## log write fails it is better to have a current aggregate and a gap in
        ## history than the reverse. Merge (rather than replace) semantics are
        ## kept from `WriteToChannel`, so a key this cycle didn't produce keeps
        ## its previous value instead of disappearing.
        ##
        ## `save_log` exists on `UpdateAggregateRequest` and would collapse this
        ## back into one call, but pydoover does not surface it on
        ## `update_channel_aggregate`, so the message stays a separate call.
        channel_name = self.config.channel_name.value
        await self.device_agent.update_channel_aggregate(channel_name, channel_msg)
        await self.device_agent.create_message(channel_name, channel_msg)

        self.last_fetched = time.time()
