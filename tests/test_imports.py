"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""


def test_import_app():
    from modbus_channel_relay.application import ModbusChannelRelayApplication

    assert ModbusChannelRelayApplication


def test_config():
    from modbus_channel_relay.app_config import ModbusChannelRelayConfig

    assert isinstance(ModbusChannelRelayConfig.to_schema(), dict)


def test_enum_elements_fall_back_to_default_when_null():
    """Optional elements are typed ``[<type>, "null"]``, so a stored config can
    carry an explicit null where the previous schema could not."""
    from modbus_channel_relay.app_config import (
        DEFAULT_DATA_TYPE,
        DEFAULT_REGISTER_TYPE,
        ModbusChannelRelayConfig,
        ModbusDataType,
        ModbusRegisterType,
        as_enum,
    )

    config = ModbusChannelRelayConfig()
    config._inject_deployment_config(
        {
            "channel_name": "c",
            "modbus_config": {"name": "default"},
            "modbus_maps": [
                {
                    "modbus_id": 1,
                    "start_address": 0,
                    "number_of_registers": 1,
                    "register_type": None,
                    "channel_namespace": None,
                    "register_maps": [
                        {"register_number": 0, "json_key": "o", "data_type": None}
                    ],
                }
            ],
        }
    )

    mb_map = config.modbus_maps.elements[0]
    assert (
        as_enum(mb_map.register_type, DEFAULT_REGISTER_TYPE)
        is ModbusRegisterType.HOLDING_REGISTER
    )
    assert (
        as_enum(mb_map.register_maps.elements[0].data_type, DEFAULT_DATA_TYPE)
        is ModbusDataType.INTEGER16
    )
