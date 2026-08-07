import enum

from pathlib import Path

from pydoover import config
from pydoover.docker.modbus import ModbusConfig


class ModbusRegisterType(enum.Enum):
    """The register types a map can read from.

    The member *values* are what a stored deployment config carries, so they
    must not change: an existing install holds e.g. ``"Holding Register"``.
    """

    COIL = "Coil"
    DISCRETE_INPUT = "Discrete Input"
    INPUT_REGISTER = "Input Register"
    HOLDING_REGISTER = "Holding Register"

    @property
    def code(self) -> int:
        """The register type number the modbus interface expects."""
        return _REGISTER_TYPE_CODES[self]


_REGISTER_TYPE_CODES = {
    ModbusRegisterType.COIL: 1,
    ModbusRegisterType.DISCRETE_INPUT: 2,
    ModbusRegisterType.INPUT_REGISTER: 3,
    ModbusRegisterType.HOLDING_REGISTER: 4,
}


class ModbusDataType(enum.Enum):
    """How to interpret the register(s) at a given address.

    As above, the values are the stored config representation.
    """

    INTEGER16 = "16-bit Integer"
    FLOAT32_CD_AB = "32-bit Float CD-AB"


# The defaults live here rather than inline in the elements below because the
# fallback in ``as_enum`` needs the same value: an element that took a null
# cannot report its own default (see below).
DEFAULT_REGISTER_TYPE = ModbusRegisterType.HOLDING_REGISTER
DEFAULT_DATA_TYPE = ModbusDataType.INTEGER16


def as_enum(element, default):
    """The enum member a ``config.Enum`` element holds, falling back to `default`.

    An element declared from an ``EnumType`` yields a member, but a value
    arriving from an injected deployment config can still be the raw string, so
    normalise rather than assuming either.

    The fallback is for an explicit null. pydoover types every optional element
    as ``[<type>, "null"]``, so a stored config can carry a null where the
    previous schema could not -- and loading one makes pydoover swallow the
    failed enum lookup and replace the declared element with an untyped one, so
    by the time it is read it no longer knows its own default. A relay that
    stops reading registers over a blank drop-down is worse than one that reads
    the default.
    """
    enum_cls = type(default)
    value = element.value
    if isinstance(value, enum_cls):
        return value
    if value is None:
        return default
    return enum_cls(value)


class RegisterMap(config.Object):
    register_number = config.Integer(
        "Register Number", description="Register number to read from"
    )
    json_key = config.String(
        "JSON Key",
        description="Flat JSON key to store the register value. (. separated)",
    )
    data_type = config.Enum(
        "Data Type",
        description="Data type to store the register value in",
        choices=ModbusDataType,
        default=DEFAULT_DATA_TYPE,
    )

    def __init__(self, display_name: str = "Register Map"):
        super().__init__(display_name)


class ModbusMap(config.Object):
    modbus_id = config.Integer(
        "Modbus ID",
        description="Modbus ID for this map. Sometimes known as slave ID.",
        minimum=0,
        default=1,
    )
    channel_namespace = config.String(
        "Channel Namespace",
        description="Optional JSON namespace to wrap around the register values.",
        default=None,
    )
    start_address = config.Integer(
        "Start Address", description="Register address to start reading from"
    )
    number_of_registers = config.Integer(
        "Number of Registers", description="Number of registers to read"
    )
    register_type = config.Enum(
        "Register Type",
        description="Register type to read from",
        choices=ModbusRegisterType,
        default=DEFAULT_REGISTER_TYPE,
    )
    register_maps = config.Array("Register Maps", element=RegisterMap())

    def __init__(self, display_name: str = "Modbus Map"):
        super().__init__(display_name)


class ModbusChannelRelayConfig(config.Schema):
    modbus_maps = config.Array("Modbus Maps", element=ModbusMap())
    period = config.Number(
        "Period",
        default=60.0,
        description="Period between upload in minutes.",
        minimum=0,
    )
    channel_name = config.String(
        "Channel Name",
        description="Name of the channel",
        default="ModbusChannelRelay",
    )
    modbus_config = ModbusConfig()


def export():
    """Export the config to the doover_config.json file."""

    ModbusChannelRelayConfig.export(
        Path(__file__).parents[2] / "doover_config.json", "modbus_channel_relay"
    )
