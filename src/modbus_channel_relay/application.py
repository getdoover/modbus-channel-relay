import logging
import time
import json

from pydoover.docker import Application

from .app_config import ModbusChannelRelayConfig, ModbusRegisterType

log = logging.getLogger()


class ModbusChannelRelayApplication(Application):
    config: ModbusChannelRelayConfig
    last_fetched: float

    def setup(self):
        self.last_fetched = 0.0

    def main_loop(self):
        if time.time() - self.last_fetched < self.config.period.value * 60:
            log.info("Looping, time not yet reached...")
            return

        channel_msg = {}
        for mb_map in self.config.modbus_maps.elements:
            map_msg = {}

            registers = None
            try:
                registers = self.read_modbus_registers(
                    mb_map.start_address.value,
                    mb_map.number_of_registers.value,
                    modbus_id=mb_map.modbus_id.value,
                    register_type=ModbusRegisterType.choice_to_number(mb_map.register_type.value),
                    bus_id=self.config.modbus_config.name.value,
                )
            except Exception as e:
                log.error(f"Failed to read registers for modbus map {mb_map.modbus_id.value}, start address {mb_map.start_address.value}, number of registers {mb_map.number_of_registers.value}: {e}")
                continue

            ## Convert the registers to a dictionary with the register number as the key
            registers = dict(enumerate(registers, start=mb_map.start_address.value))

            for register_map in mb_map.register_maps.elements:
                ## Create the nested object structure
                j_keys = register_map.json_key.value.split(".")
                j_keys.reverse()
                j_obj = {j_keys[0]: registers.pop(register_map.register_number.value)}
                for j_key in j_keys[1:]:
                    j_obj = {j_key: j_obj}
                map_msg.update(j_obj)

            ## For remaining registers, add them to the map msg
            for k,v in registers.items():
                map_msg[k] = v
            if mb_map.channel_namespace.value is not None:
                map_msg = {mb_map.channel_namespace.value: map_msg}
            
            channel_msg.update(map_msg)

        self.publish_to_channel(self.config.channel_name.value, json.dumps(channel_msg))

        self.last_fetched = time.time()
