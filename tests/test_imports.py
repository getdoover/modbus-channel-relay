"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""


def test_import_app():
    from modbus_channel_relay.application import ModbusChannelRelayApplication

    assert ModbusChannelRelayApplication


def test_config():
    from modbus_channel_relay.app_config import ModbusChannelRelayConfig

    config = ModbusChannelRelayConfig()
    assert isinstance(config.to_dict(), dict)