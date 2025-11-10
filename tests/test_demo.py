import asyncio
import json
import logging
from typing import Optional

import pytest
from pydoover.docker import ModbusInterface, DeviceAgentInterface
from pydoover.docker.device_agent.grpc_stubs import device_agent_pb2

from modbus_channel_relay.app_config import ModbusChannelRelayConfig
from modbus_channel_relay.application import ModbusChannelRelayApplication

logging.basicConfig(level=logging.INFO)

SAMPLE_CONFIG = {
    "period_between_uploads": 0.01,
    "start_address": 0,
    "number_of_registers": 2,
    "register_type": "Holding Register",
    "device_id": 1,
    "channel_name": "modbus_output",
    "modbus_config": {
        "name": "default",
    },
}


class MockModbusInterface(ModbusInterface):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.registers = []

    def read_registers(
        self,
        bus_id: str = "default",
        modbus_id: int = 1,
        start_address: int = 0,
        num_registers: int = 1,
        register_type: int = 4,
        configure_bus: bool = True,
    ) -> Optional[int | list[int]]:
        try:
            return self.registers[start_address : start_address + num_registers]
        except IndexError:
            return None


class MockDeviceAgentInterface(DeviceAgentInterface):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channels = {}

        self.is_dda_online = True
        self.is_dda_available = True
        self.has_dda_been_online = True

    async def wait_for_channels_sync_async(
        self, channel_names: list[str], timeout: int = 5, inter_wait: float = 0.2
    ):
        for channel in channel_names:
            await self.recv_update_callback(
                channel,
                device_agent_pb2.ChannelSubscriptionResponse(
                    channel=device_agent_pb2.ChannelDetails(
                        channel_name=channel,
                        aggregate=json.dumps(self.channels.get(channel, {})),
                    )
                ),
            )
        return True

    async def start_subscription_listener(self, channel_name):
        return

    def get_channel_aggregate(self, channel_name):
        try:
            return self.channels[channel_name]
        except KeyError:
            pass

    def publish_to_channel(
        self,
        channel_name: str,
        message: dict | str,
        record_log: bool = True,
        max_age: int = None,
    ):
        self.channels[channel_name] = message


async def runner(app):
    async with app:
        await app._run()


@pytest.fixture(scope="module")
def mock_modbus():
    return MockModbusInterface("app_key")


@pytest.fixture(scope="module")
def mock_device_agent():
    return MockDeviceAgentInterface("app_key")


@pytest.fixture(scope="module")
def config():
    config = ModbusChannelRelayConfig()
    config._inject_deployment_config(SAMPLE_CONFIG)
    return config


@pytest.fixture(scope="module")
def app(config, mock_modbus, mock_device_agent):
    # Patch the ModbusInterface in the application
    return ModbusChannelRelayApplication(
        config=config,
        device_agent=mock_device_agent,
        modbus_iface=mock_modbus,
        test_mode=True,
    )


@pytest.mark.asyncio
async def test_modbus_channel_relay(app, config, mock_modbus, mock_device_agent):
    t = asyncio.create_task(runner(app))
    # Mock Modbus interface
    await asyncio.sleep(2)

    mock_modbus.registers = [10, 20]  # initial values
    # Wait for the first period
    await asyncio.sleep(config.period.value * 60 * 2)

    # Update the mock registers
    mock_modbus.registers = [30, 40]

    # go to next iteration of app and assert output is OK
    await app.next()
    output = mock_device_agent.channels.get(config.channel_name.value)
    assert output == "[30, 40]"

    # Wait for the next period
    await asyncio.sleep(config.period.value * 60 * 2)

    # Update the mock registers
    mock_modbus.registers = [50, 60]

    # go to next iteration of app and assert output is OK
    await app.next()
    output = mock_device_agent.channels.get(config.channel_name.value)
    assert output == "[50, 60]"

    # update the mock registers
    mock_modbus.registers = [70, 80]
    # without sleeping, go to next iteration and make sure it doesn't update
    await app.next()
    output = mock_device_agent.channels.get(config.channel_name.value)
    assert output == "[50, 60]"

    # Cancel the task to clean up
    t.cancel()
