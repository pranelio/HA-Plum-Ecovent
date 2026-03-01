"""Constants for the Plum Ecovent integration."""

DOMAIN = "plum_ecovent"
DEFAULT_NAME = "Plum Ecovent"

# Config keys
CONF_MODBUS_TYPE = "modbus_type"
MODBUS_TYPE_TCP = "tcp"
MODBUS_TYPE_RTU = "rtu"

CONF_SERIAL_PORT = "serial_port"
CONF_BAUDRATE = "baudrate"
CONF_HOST = "host"
CONF_PORT = "port"

# Example register addresses used by built-in entities
REG_SENSOR = 0
REG_BINARY = 1
REG_SWITCH = 2
REG_NUMBER = 3

# Modbus slave address/unit identifier (1–255)
CONF_UNIT = "unit"
DEFAULT_UNIT = 1
