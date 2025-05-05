FROM python:3.11-slim
RUN pip install pymodbus[simulator]==3.9.2
ENTRYPOINT ["pymodbus.simulator", "--modbus_device", "device_try", "--modbus_server", "server"]
