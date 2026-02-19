import logging
import time
import json
import struct

from pydoover.docker import Application

from .app_config import ModbusChannelRelayConfig, ModbusRegisterType, ModbusDataType

log = logging.getLogger()


class ModbusChannelRelayApplication(Application):
    config: ModbusChannelRelayConfig
    last_fetched: float

    async def setup(self):
        self.last_fetched = 0.0

        self.modbus_iface.timeout = 15 ## Set GRPC timeout to 15 seconds for modbus iface

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
                registers = await self.modbus_iface.read_registers_async(
                    start_address=mb_map.start_address.value,
                    num_registers=mb_map.number_of_registers.value,
                    modbus_id=mb_map.modbus_id.value,
                    register_type=ModbusRegisterType.choice_to_number(mb_map.register_type.value),
                    bus_id=self.config.modbus_config.name.value,
                )
            except Exception as e:
                error = e
            
            if registers is None or error is not None:
                log.error(f"Failed to read registers for modbus map {mb_map.modbus_id.value}, start address {mb_map.start_address.value}, number of registers {mb_map.number_of_registers.value}: {error}")
                ## Null out FLOAT32_CD_AB keys so the aggregate sheds stale values
                for register_map in mb_map.register_maps.elements:
                    if register_map.data_type.value != ModbusDataType.FLOAT32_CD_AB:
                        continue
                    j_keys = register_map.json_key.value.split(".")
                    j_keys.reverse()
                    j_obj = {j_keys[0]: "none"}
                    for j_key in j_keys[1:]:
                        j_obj = {j_key: j_obj}
                    map_msg.update(j_obj)
            else:
                ## Convert the registers to a dictionary with the register number as the key
                if isinstance(registers, int) or isinstance(registers, float):
                    registers = [registers]
                registers = dict(enumerate(registers, start=mb_map.start_address.value))

                for register_map in mb_map.register_maps.elements:
                    ## Create the nested object structure
                    j_keys = register_map.json_key.value.split(".")
                    j_keys.reverse()
                    if register_map.data_type.value == ModbusDataType.INTEGER16:
                        j_obj = {j_keys[0]: registers.pop(register_map.register_number.value)}
                        for j_key in j_keys[1:]:
                            j_obj = {j_key: j_obj}
                        map_msg.update(j_obj)
                    elif register_map.data_type.value == ModbusDataType.FLOAT32_CD_AB:
                        reg_low = registers.pop(register_map.register_number.value)
                        reg_high = registers.pop(register_map.register_number.value + 1)
                        j_obj = {j_keys[0]: struct.unpack(">f", struct.pack(">HH", reg_high, reg_low))[0]}
                        for j_key in j_keys[1:]:
                            j_obj = {j_key: j_obj}
                        map_msg.update(j_obj)
                ## For remaining registers, add them to the map msg
                for k,v in registers.items():
                    map_msg[k] = v
            if mb_map.channel_namespace.value not in [None, "", "null", "None", "none", "NONE"]:
                map_msg = {mb_map.channel_namespace.value: map_msg}
            
            channel_msg.update(map_msg)
            log.info(f"Channel msg: {channel_msg}")

        await self.device_agent.publish_to_channel_async(self.config.channel_name.value, json.dumps(channel_msg))

        self.last_fetched = time.time()
