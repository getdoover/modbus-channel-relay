# Modbus Channel Relay

A simple application that relays values from a Modbus server (TCP or Serial) to a Doover channel.

## Features

- **Modbus Communication**: Supports both TCP and Serial communication protocols.
- **Configurable Registers**: Reads from configurable Modbus registers (Coil, Discrete Input, Input Register, Holding Register).
- **Periodic Updates**: Relays data to the configured channel at a user-defined interval.

## Configuration

The application uses a configuration schema defined in `doover_config.json`. Below are the key configuration options:

- **period_between_uploads**: Time interval (in minutes) between data uploads to the channel.
- **channel_name**: Name of the Doover channel to which data is relayed.
- **device_id**: Modbus device ID (previously known as slave ID).
- **start_address**: Starting register address to read from.
- **number_of_registers**: Number of registers to read.
- **register_type**: Type of Modbus register to read (e.g., Coil, Holding Register).
- **modbus_config**: Configuration for the Modbus connection, including:
  - `bus_type`: Communication type (`serial` or `tcp`).
  - `serial_port`, `serial_baud`, `serial_method`, etc., for Serial communication.
  - `tcp_uri`, `tcp_timeout` for TCP communication.

## Usage

Install the application to your device through the Doover portal. A sample configuration is below:

```json
{
    "period_between_uploads": 1,
    "channel_name": "modbus_test",
    "device_id": 1,
    "start_address": 0,
    "number_of_registers": 10,
    "register_type": "Holding Register",
    "modbus_config": {
        "bus_type": "serial",
        "serial_port": "/dev/ttyAMA0",
        "serial_baud": 9600,
        "serial_method": "rtu"
    }
}
```
