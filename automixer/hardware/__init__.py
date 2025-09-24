"""
Hardware Communication Module for Automixer
Provides universal equipment connectivity and control
"""

from .communication import (
    HardwareDeviceManager,
    ModbusProtocol,
    OPCUAProtocol,
    SerialProtocol,
    HTTPProtocol
)

__all__ = [
    "HardwareDeviceManager",
    "ModbusProtocol",
    "OPCUAProtocol",
    "SerialProtocol",
    "HTTPProtocol"
]
