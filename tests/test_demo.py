import asyncio
import contextlib
import logging
from typing import Optional

import pytest
from pydoover.docker import ModbusInterface, MockDeviceAgentInterface

from modbus_channel_relay.application import ModbusChannelRelayApplication

logging.basicConfig(level=logging.INFO)

SAMPLE_CONFIG = {
    "period": 0.01,
    "channel_name": "modbus_output",
    "modbus_config": {
        "name": "default",
    },
    "modbus_maps": [
        {
            "modbus_id": 1,
            "start_address": 0,
            "number_of_registers": 2,
            "register_type": "Holding Register",
            "channel_namespace": None,
            "register_maps": [
                {
                    "register_number": 0,
                    "json_key": "output",
                    "data_type": "16-bit Integer",
                }
            ],
        }
    ],
}


class MockModbusInterface(ModbusInterface):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.registers = []

    async def read_registers(
        self,
        bus_id: str = "default",
        modbus_id: int = 1,
        start_address: int = 0,
        num_registers: int = 1,
        register_type: int = 4,
        **kwargs,
    ) -> Optional[int | list[int]]:
        try:
            return self.registers[start_address : start_address + num_registers]
        except IndexError:
            return None


class MockDeviceAgent(MockDeviceAgentInterface):
    """Records published messages so a test can assert on the payload.

    The mock in pydoover accepts ``create_message`` and drops it on the floor,
    which is all a normal app needs from it -- but this app's whole output is
    that message.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.messages = {}

    async def create_message(self, channel_name, data, **kwargs):
        self.messages[channel_name] = data
        return 0


async def runner(app):
    async with app:
        await app._run()


# Generous: this bounds "the runner is never coming back", not loop latency.
STEP_TIMEOUT = 30


async def step(app, task):
    """Run one main-loop iteration, failing rather than hanging if it can't.

    ``app.next()`` waits on an event the runner only sets at the *end* of a loop
    iteration. A runner that has stopped -- setup raised, or the loop caught an
    exception and broke out -- never sets it again, so the wait is forever: in
    CI that is a job that hangs until the six-hour limit instead of a failed
    test. Bound the wait, and if the runner died, re-raise what killed it rather
    than reporting a timeout that says nothing about the cause.
    """
    try:
        await asyncio.wait_for(app.next(), STEP_TIMEOUT)
    except asyncio.TimeoutError:
        if task.done():
            task.result()  # re-raises the runner's exception, if it had one
            raise AssertionError("app runner exited before the loop could run")
        raise AssertionError(
            f"main loop did not complete an iteration within {STEP_TIMEOUT}s"
        )


@pytest.fixture(scope="module")
def mock_modbus():
    return MockModbusInterface("app_key")


@pytest.fixture(scope="module")
def mock_device_agent():
    return MockDeviceAgent("app_key")


@pytest.fixture(scope="module")
def app(mock_modbus, mock_device_agent):
    app = ModbusChannelRelayApplication(
        device_agent=mock_device_agent,
        modbus_iface=mock_modbus,
        test_mode=True,
    )
    # The app builds its own config from ``config_cls``; a test supplies the
    # deployment values the device agent would otherwise inject.
    app.config._inject_deployment_config(SAMPLE_CONFIG)
    return app


@pytest.fixture(scope="module")
def config(app):
    return app.config


@pytest.mark.asyncio
async def test_modbus_channel_relay(app, config, mock_modbus, mock_device_agent):
    t = asyncio.create_task(runner(app))
    try:
        # Wait on the app's own readiness rather than a fixed sleep: startup is
        # slower on a loaded CI runner than on a laptop, and a sleep that is too
        # short here used to land in the deadlock described on `step`.
        await asyncio.wait_for(app.wait_until_ready(), STEP_TIMEOUT)

        mock_modbus.registers = [10, 20]  # initial values
        # Wait for the first period
        await asyncio.sleep(config.period.value * 60 * 2)

        # Update the mock registers
        mock_modbus.registers = [30, 40]

        # go to next iteration of app and assert output is OK
        await step(app, t)
        output = mock_device_agent.messages.get(config.channel_name.value)
        assert output == {"output": 30, "1": 40}

        # Wait for the next period
        await asyncio.sleep(config.period.value * 60 * 2)

        # Update the mock registers
        mock_modbus.registers = [50, 60]

        # go to next iteration of app and assert output is OK
        await step(app, t)
        output = mock_device_agent.messages.get(config.channel_name.value)
        assert output == {"output": 50, "1": 60}

        # update the mock registers
        mock_modbus.registers = [70, 80]
        # without sleeping, go to next iteration and make sure it doesn't update
        await step(app, t)
        output = mock_device_agent.messages.get(config.channel_name.value)
        assert output == {"output": 50, "1": 60}
    finally:
        # Awaited, not just cancelled: an un-awaited cancellation leaves the
        # runner's teardown racing pytest's loop shutdown.
        t.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await t
