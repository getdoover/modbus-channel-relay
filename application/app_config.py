from pathlib import Path

from pydoover import config
from pydoover.docker.modbus import ModbusConfig


class SampleConfig(config.Schema):
    def __init__(self):
        self.period = config.Number(
            "Period between uploads",
            default=60.0,
            description="Value in minutes.",
            minimum=0,
        )
        self.channel_name = config.String(
            "Channel Name",
            description="Name of the channel",
            default="ModbusChannelRelay",
        )

        self.modbus_id = config.Integer(
            "Device ID",
            description="Device ID to read from. This was previously known as slave ID.",
        )
        self.start_address = config.Integer(
            "Start Address",
            description="Register address to start reading from",
        )
        self.num_registers = config.Integer(
            "Number of Registers",
            description="Number of registers to read",
        )
        self.register_type = config.Enum(
            "Register Type",
            description="Register type to read from",
            choices=[
                "Coil",
                "Discrete Input",
                "Input Register",
                "Holding Register",
            ],
            default="Holding Register",
        )

        self.modbus_config = ModbusConfig()


if __name__ == "__main__":
    c = SampleConfig()
    c.export(Path("../doover_config.json"), "modbus_channel_relay")
