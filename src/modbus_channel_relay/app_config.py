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


class ModbusChannelRelayConfig(config.Schema):
    def __init__(self):

        register_map_element = config.Object("Register Map")
        register_map_element.add_elements(
            config.Integer("Register Number", description="Register number to read from"),
            config.String("JSON Key", description="Flat JSON key to store the register value. (. separated)"),
        )

        mb_map_element = config.Object("Modbus Map")
        mb_map_element.add_elements(
            config.String("Modbus ID", description="Modbus ID for this map. Sometimes known as slave ID."),
            config.String("Channel Namespace", description="Optional JSON namespace to wrap around the register values.", default=None),
            config.Integer("Start Address", description="Register address to start reading from"),
            config.Integer("Number of Registers", description="Number of registers to read"),
            config.Enum("Register Type", description="Register type to read from", choices=ModbusRegisterType.get_choices(), default=ModbusRegisterType.HOLDING_REGISTER),
            config.Array("Register Maps", element=register_map_element),
        )
        self.modbus_maps = config.Array(
            "Modbus Maps",
            element=mb_map_element
        )
        
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

        self.modbus_config = ModbusConfig()

    @property
    def register_type_num(self):
        return ModbusRegisterType.choice_to_number(self.register_type.value)

def export():
    """Export the config to the doover_config.json file."""

    c = ModbusChannelRelayConfig()
    c.export(Path(__file__).parents[2] / "doover_config.json", "modbus_channel_relay")