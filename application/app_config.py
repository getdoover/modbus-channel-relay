from pathlib import Path

from pydoover import config
from pydoover.docker.modbus import ModbusConfig

class ModbusRegisterType:
    COIL = "Coil"
    DISCRETE_INPUT = "Discrete Input"
    INPUT_REGISTER = "Input Register"
    HOLDING_REGISTER = "Holding Register"

    @staticmethod
    def get_choices():
        return [
            ModbusRegisterType.COIL,
            ModbusRegisterType.DISCRETE_INPUT,
            ModbusRegisterType.INPUT_REGISTER,
            ModbusRegisterType.HOLDING_REGISTER,
        ]

    @staticmethod
    def choice_to_number(choice: str):
        return {
            ModbusRegisterType.COIL: 1,
            ModbusRegisterType.DISCRETE_INPUT: 2,
            ModbusRegisterType.INPUT_REGISTER: 3,
            ModbusRegisterType.HOLDING_REGISTER: 4,
        }[choice]


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
            choices=ModbusRegisterType.get_choices(),
            default="Holding Register",
        )

        self.modbus_config = ModbusConfig()

    @property
    def register_type_num(self):
        return ModbusRegisterType.choice_to_number(self.register_type.value)


if __name__ == "__main__":
    c = SampleConfig()
    c.export(Path("../doover_config.json"), "modbus_channel_relay")
