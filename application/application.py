import logging
import time

from pydoover.docker import Application

from .app_config import SampleConfig

log = logging.getLogger()

class SampleApplication(Application):
    config: SampleConfig
    last_fetched: float

    def setup(self):
        self.last_fetched = 0.0

    def main_loop(self):
        if time.time() - self.last_fetched < self.config.period.value * 60:
            log.info("Looping, time not yet reached...")
            return

        log.info("Fetching modbus registers")
        registers = self.read_modbus_registers(
            self.config.start_address.value,
            self.config.num_registers.value,
            modbus_id=self.config.modbus_id.value,
            register_type=self.config.register_type.value.lower().replace(" ", "_"),
            bus_id=self.config.modbus_config.name.value
        )

        if registers is None:
            log.error("Failed to read registers")
            return

        self.publish_to_channel(
            self.config.channel_name.value,
            registers
        )
        self.last_fetched = time.time()
