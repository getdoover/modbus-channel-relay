from pydoover.docker import run_app

from .application import ModbusChannelRelayApplication


def main():
    run_app(ModbusChannelRelayApplication())
