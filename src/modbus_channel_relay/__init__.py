from pydoover.docker import run_app

from .app_config import ModbusChannelRelayConfig
from .application import ModbusChannelRelayApplication

def main():
    run_app(ModbusChannelRelayApplication(config=ModbusChannelRelayConfig()))
