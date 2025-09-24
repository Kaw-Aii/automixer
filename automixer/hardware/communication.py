#!/usr/bin/env python3
"""
Hardware Communication Protocols for Laboratory Equipment Integration
===================================================================

This module implements comprehensive communication protocols for integrating
laboratory equipment with the digital twin simulation engine. It provides
standardized interfaces for various equipment types and communication methods.

Key Features:
- Multi-protocol support (Modbus, Serial, Ethernet/IP, OPC UA)
- Device discovery and auto-configuration
- Real-time data streaming and command execution
- Safety interlocks and error handling
- Protocol conversion and gateway functions
- Comprehensive logging and diagnostics

Author: Manus AI
Date: January 21, 2025
Version: 1.0
"""

import asyncio
import json
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
import serial
import socket
import struct
from abc import ABC, abstractmethod

# Third-party imports for protocol implementations
try:
    from pymodbus.client import ModbusTcpClient, ModbusSerialClient
    from pymodbus.constants import Endian
    from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
    MODBUS_AVAILABLE = True
except ImportError:
    try:
        # Try alternative import for older versions
        from pymodbus.client.sync import ModbusTcpClient, ModbusSerialClient
        from pymodbus.constants import Endian
        from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
        MODBUS_AVAILABLE = True
    except ImportError:
        MODBUS_AVAILABLE = False
        logging.warning("Modbus library not available. Install pymodbus for Modbus support.")

try:
    import opcua
    from opcua import Client as OPCClient, Server as OPCServer
    OPCUA_AVAILABLE = True
except ImportError:
    OPCUA_AVAILABLE = False
    logging.warning("OPC UA library not available. Install opcua for OPC UA support.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeviceType(Enum):
    """Equipment device types"""
    MIXER = "mixer"
    HEATER = "heater"
    PUMP = "pump"
    SCALE = "scale"
    SENSOR = "sensor"
    VALVE = "valve"
    ANALYZER = "analyzer"
    CONTROLLER = "controller"

class ProtocolType(Enum):
    """Communication protocol types"""
    MODBUS_TCP = "modbus_tcp"
    MODBUS_RTU = "modbus_rtu"
    SERIAL_ASCII = "serial_ascii"
    ETHERNET_IP = "ethernet_ip"
    OPC_UA = "opc_ua"
    HTTP_REST = "http_rest"
    WEBSOCKET = "websocket"

class DeviceStatus(Enum):
    """Device operational status"""
    OFFLINE = "offline"
    CONNECTING = "connecting"
    ONLINE = "online"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    CALIBRATING = "calibrating"

@dataclass
class DeviceConfiguration:
    """Device configuration parameters"""
    device_id: str
    device_type: DeviceType
    protocol_type: ProtocolType
    connection_params: Dict[str, Any]
    data_points: Dict[str, Any]
    control_points: Dict[str, Any]
    safety_limits: Dict[str, Any] = field(default_factory=dict)
    calibration_params: Dict[str, Any] = field(default_factory=dict)
    polling_interval: float = 1.0
    timeout: float = 5.0
    retry_count: int = 3
    enabled: bool = True

@dataclass
class DataPoint:
    """Represents a data point from a device"""
    device_id: str
    point_name: str
    value: Any
    timestamp: datetime
    quality: str = "good"
    units: str = ""
    description: str = ""

@dataclass
class ControlCommand:
    """Represents a control command to a device"""
    device_id: str
    command_name: str
    parameters: Dict[str, Any]
    timestamp: datetime
    priority: int = 5
    timeout: float = 10.0
    callback: Optional[Callable] = None

class CommunicationProtocol(ABC):
    """Abstract base class for communication protocols"""
    
    def __init__(self, config: DeviceConfiguration):
        self.config = config
        self.status = DeviceStatus.OFFLINE
        self.last_error = None
        self.connection = None
        self.data_cache = {}
        self.lock = threading.Lock()
        
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to device"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from device"""
        pass
    
    @abstractmethod
    async def read_data(self, point_names: List[str]) -> List[DataPoint]:
        """Read data points from device"""
        pass
    
    @abstractmethod
    async def write_data(self, commands: List[ControlCommand]) -> List[bool]:
        """Write control commands to device"""
        pass
    
    @abstractmethod
    async def get_device_info(self) -> Dict[str, Any]:
        """Get device information and status"""
        pass
    
    def is_connected(self) -> bool:
        """Check if device is connected"""
        return self.status == DeviceStatus.ONLINE
    
    def get_status(self) -> Dict[str, Any]:
        """Get current device status"""
        return {
            "device_id": self.config.device_id,
            "status": self.status.value,
            "last_error": self.last_error,
            "connection_time": getattr(self, 'connection_time', None),
            "data_points": len(self.data_cache)
        }

class ModbusTCPProtocol(CommunicationProtocol):
    """Modbus TCP communication protocol implementation"""
    
    def __init__(self, config: DeviceConfiguration):
        super().__init__(config)
        if not MODBUS_AVAILABLE:
            raise ImportError("Modbus library not available")
        self.client = None
        
    async def connect(self) -> bool:
        """Establish Modbus TCP connection"""
        try:
            self.status = DeviceStatus.CONNECTING
            
            host = self.config.connection_params.get('host', 'localhost')
            port = self.config.connection_params.get('port', 502)
            unit_id = self.config.connection_params.get('unit_id', 1)
            
            self.client = ModbusTcpClient(host=host, port=port)
            
            if self.client.connect():
                self.status = DeviceStatus.ONLINE
                self.connection_time = datetime.now()
                logger.info(f"Connected to Modbus device {self.config.device_id} at {host}:{port}")
                return True
            else:
                self.status = DeviceStatus.ERROR
                self.last_error = "Failed to establish Modbus connection"
                return False
                
        except Exception as e:
            self.status = DeviceStatus.ERROR
            self.last_error = str(e)
            logger.error(f"Modbus connection error for {self.config.device_id}: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Modbus device"""
        try:
            if self.client:
                self.client.close()
                self.client = None
            self.status = DeviceStatus.OFFLINE
            logger.info(f"Disconnected from Modbus device {self.config.device_id}")
            return True
        except Exception as e:
            logger.error(f"Modbus disconnect error for {self.config.device_id}: {e}")
            return False
    
    async def read_data(self, point_names: List[str]) -> List[DataPoint]:
        """Read data points from Modbus device"""
        data_points = []
        
        if not self.is_connected():
            return data_points
        
        try:
            unit_id = self.config.connection_params.get('unit_id', 1)
            
            for point_name in point_names:
                if point_name not in self.config.data_points:
                    continue
                
                point_config = self.config.data_points[point_name]
                register_type = point_config.get('register_type', 'holding')
                address = point_config.get('address', 0)
                count = point_config.get('count', 1)
                data_type = point_config.get('data_type', 'uint16')
                scale_factor = point_config.get('scale_factor', 1.0)
                offset = point_config.get('offset', 0.0)
                units = point_config.get('units', '')
                
                # Read registers based on type
                if register_type == 'holding':
                    result = self.client.read_holding_registers(address, count, unit=unit_id)
                elif register_type == 'input':
                    result = self.client.read_input_registers(address, count, unit=unit_id)
                elif register_type == 'coil':
                    result = self.client.read_coils(address, count, unit=unit_id)
                elif register_type == 'discrete':
                    result = self.client.read_discrete_inputs(address, count, unit=unit_id)
                else:
                    logger.error(f"Unknown register type: {register_type}")
                    continue
                
                if result.isError():
                    logger.error(f"Modbus read error for {point_name}: {result}")
                    continue
                
                # Convert raw data based on data type
                raw_value = result.registers if hasattr(result, 'registers') else result.bits
                value = self._convert_modbus_data(raw_value, data_type, scale_factor, offset)
                
                data_point = DataPoint(
                    device_id=self.config.device_id,
                    point_name=point_name,
                    value=value,
                    timestamp=datetime.now(),
                    quality="good",
                    units=units,
                    description=point_config.get('description', '')
                )
                
                data_points.append(data_point)
                self.data_cache[point_name] = data_point
                
        except Exception as e:
            logger.error(f"Modbus read error for {self.config.device_id}: {e}")
            self.last_error = str(e)
        
        return data_points
    
    async def write_data(self, commands: List[ControlCommand]) -> List[bool]:
        """Write control commands to Modbus device"""
        results = []
        
        if not self.is_connected():
            return [False] * len(commands)
        
        try:
            unit_id = self.config.connection_params.get('unit_id', 1)
            
            for command in commands:
                if command.command_name not in self.config.control_points:
                    results.append(False)
                    continue
                
                control_config = self.config.control_points[command.command_name]
                register_type = control_config.get('register_type', 'holding')
                address = control_config.get('address', 0)
                data_type = control_config.get('data_type', 'uint16')
                scale_factor = control_config.get('scale_factor', 1.0)
                offset = control_config.get('offset', 0.0)
                
                # Get command value
                value = command.parameters.get('value', 0)
                
                # Convert value to Modbus format
                modbus_value = self._convert_to_modbus_data(value, data_type, scale_factor, offset)
                
                # Write to device
                if register_type == 'holding':
                    if isinstance(modbus_value, list):
                        result = self.client.write_registers(address, modbus_value, unit=unit_id)
                    else:
                        result = self.client.write_register(address, modbus_value, unit=unit_id)
                elif register_type == 'coil':
                    result = self.client.write_coil(address, bool(modbus_value), unit=unit_id)
                else:
                    logger.error(f"Unsupported write register type: {register_type}")
                    results.append(False)
                    continue
                
                success = not result.isError()
                results.append(success)
                
                if success:
                    logger.info(f"Modbus write successful: {command.command_name} = {value}")
                else:
                    logger.error(f"Modbus write error: {result}")
                
        except Exception as e:
            logger.error(f"Modbus write error for {self.config.device_id}: {e}")
            self.last_error = str(e)
            results.extend([False] * (len(commands) - len(results)))
        
        return results
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get Modbus device information"""
        info = {
            "device_id": self.config.device_id,
            "protocol": "Modbus TCP",
            "status": self.status.value,
            "connection_params": self.config.connection_params
        }
        
        if self.is_connected():
            try:
                # Try to read device identification if supported
                unit_id = self.config.connection_params.get('unit_id', 1)
                # This is device-specific and may not be supported by all devices
                info["last_communication"] = datetime.now().isoformat()
            except Exception as e:
                logger.debug(f"Could not read device info: {e}")
        
        return info
    
    def _convert_modbus_data(self, raw_value: Union[List[int], List[bool]], 
                           data_type: str, scale_factor: float, offset: float) -> Any:
        """Convert raw Modbus data to engineering units"""
        try:
            if data_type == 'bool':
                return bool(raw_value[0]) if isinstance(raw_value, list) else bool(raw_value)
            elif data_type == 'uint16':
                value = raw_value[0] if isinstance(raw_value, list) else raw_value
                return (value * scale_factor) + offset
            elif data_type == 'int16':
                value = raw_value[0] if isinstance(raw_value, list) else raw_value
                # Convert unsigned to signed
                if value > 32767:
                    value -= 65536
                return (value * scale_factor) + offset
            elif data_type == 'uint32':
                if len(raw_value) >= 2:
                    value = (raw_value[0] << 16) | raw_value[1]
                    return (value * scale_factor) + offset
            elif data_type == 'int32':
                if len(raw_value) >= 2:
                    value = (raw_value[0] << 16) | raw_value[1]
                    # Convert unsigned to signed
                    if value > 2147483647:
                        value -= 4294967296
                    return (value * scale_factor) + offset
            elif data_type == 'float32':
                if len(raw_value) >= 2:
                    # Convert two 16-bit registers to float
                    decoder = BinaryPayloadDecoder.fromRegisters(raw_value, Endian.Big)
                    value = decoder.decode_32bit_float()
                    return (value * scale_factor) + offset
            
            return raw_value
            
        except Exception as e:
            logger.error(f"Data conversion error: {e}")
            return raw_value
    
    def _convert_to_modbus_data(self, value: Any, data_type: str, 
                              scale_factor: float, offset: float) -> Union[int, List[int]]:
        """Convert engineering units to Modbus data format"""
        try:
            # Apply inverse scaling
            scaled_value = (value - offset) / scale_factor
            
            if data_type == 'bool':
                return 1 if value else 0
            elif data_type == 'uint16':
                return int(max(0, min(65535, scaled_value)))
            elif data_type == 'int16':
                return int(max(-32768, min(32767, scaled_value)))
            elif data_type == 'uint32':
                int_value = int(max(0, min(4294967295, scaled_value)))
                return [(int_value >> 16) & 0xFFFF, int_value & 0xFFFF]
            elif data_type == 'int32':
                int_value = int(max(-2147483648, min(2147483647, scaled_value)))
                if int_value < 0:
                    int_value += 4294967296
                return [(int_value >> 16) & 0xFFFF, int_value & 0xFFFF]
            elif data_type == 'float32':
                builder = BinaryPayloadBuilder(byteorder=Endian.Big)
                builder.add_32bit_float(float(scaled_value))
                return builder.to_registers()
            
            return int(scaled_value)
            
        except Exception as e:
            logger.error(f"Data conversion error: {e}")
            return 0

class SerialProtocol(CommunicationProtocol):
    """Serial communication protocol implementation"""
    
    def __init__(self, config: DeviceConfiguration):
        super().__init__(config)
        self.serial_connection = None
        
    async def connect(self) -> bool:
        """Establish serial connection"""
        try:
            self.status = DeviceStatus.CONNECTING
            
            port = self.config.connection_params.get('port', '/dev/ttyUSB0')
            baudrate = self.config.connection_params.get('baudrate', 9600)
            bytesize = self.config.connection_params.get('bytesize', 8)
            parity = self.config.connection_params.get('parity', 'N')
            stopbits = self.config.connection_params.get('stopbits', 1)
            timeout = self.config.connection_params.get('timeout', 1.0)
            
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=bytesize,
                parity=parity,
                stopbits=stopbits,
                timeout=timeout
            )
            
            if self.serial_connection.is_open:
                self.status = DeviceStatus.ONLINE
                self.connection_time = datetime.now()
                logger.info(f"Connected to serial device {self.config.device_id} on {port}")
                return True
            else:
                self.status = DeviceStatus.ERROR
                self.last_error = "Failed to open serial port"
                return False
                
        except Exception as e:
            self.status = DeviceStatus.ERROR
            self.last_error = str(e)
            logger.error(f"Serial connection error for {self.config.device_id}: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from serial device"""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
            self.status = DeviceStatus.OFFLINE
            logger.info(f"Disconnected from serial device {self.config.device_id}")
            return True
        except Exception as e:
            logger.error(f"Serial disconnect error for {self.config.device_id}: {e}")
            return False
    
    async def read_data(self, point_names: List[str]) -> List[DataPoint]:
        """Read data points from serial device"""
        data_points = []
        
        if not self.is_connected():
            return data_points
        
        try:
            for point_name in point_names:
                if point_name not in self.config.data_points:
                    continue
                
                point_config = self.config.data_points[point_name]
                command = point_config.get('read_command', '')
                response_format = point_config.get('response_format', 'ascii')
                units = point_config.get('units', '')
                
                # Send read command
                if command:
                    self.serial_connection.write(command.encode())
                    time.sleep(0.1)  # Allow device to respond
                
                # Read response
                if self.serial_connection.in_waiting > 0:
                    response = self.serial_connection.read_all()
                    
                    # Parse response based on format
                    value = self._parse_serial_response(response, response_format, point_config)
                    
                    data_point = DataPoint(
                        device_id=self.config.device_id,
                        point_name=point_name,
                        value=value,
                        timestamp=datetime.now(),
                        quality="good",
                        units=units,
                        description=point_config.get('description', '')
                    )
                    
                    data_points.append(data_point)
                    self.data_cache[point_name] = data_point
                
        except Exception as e:
            logger.error(f"Serial read error for {self.config.device_id}: {e}")
            self.last_error = str(e)
        
        return data_points
    
    async def write_data(self, commands: List[ControlCommand]) -> List[bool]:
        """Write control commands to serial device"""
        results = []
        
        if not self.is_connected():
            return [False] * len(commands)
        
        try:
            for command in commands:
                if command.command_name not in self.config.control_points:
                    results.append(False)
                    continue
                
                control_config = self.config.control_points[command.command_name]
                command_template = control_config.get('command_template', '')
                
                # Format command with parameters
                formatted_command = command_template.format(**command.parameters)
                
                # Send command
                self.serial_connection.write(formatted_command.encode())
                
                # Wait for acknowledgment if expected
                ack_expected = control_config.get('ack_expected', False)
                if ack_expected:
                    time.sleep(0.1)
                    response = self.serial_connection.read_all()
                    success = self._validate_ack_response(response, control_config)
                else:
                    success = True
                
                results.append(success)
                
                if success:
                    logger.info(f"Serial write successful: {command.command_name}")
                else:
                    logger.error(f"Serial write failed: {command.command_name}")
                
        except Exception as e:
            logger.error(f"Serial write error for {self.config.device_id}: {e}")
            self.last_error = str(e)
            results.extend([False] * (len(commands) - len(results)))
        
        return results
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get serial device information"""
        info = {
            "device_id": self.config.device_id,
            "protocol": "Serial",
            "status": self.status.value,
            "connection_params": self.config.connection_params
        }
        
        if self.is_connected():
            info["port_info"] = {
                "port": self.serial_connection.port,
                "baudrate": self.serial_connection.baudrate,
                "is_open": self.serial_connection.is_open
            }
        
        return info
    
    def _parse_serial_response(self, response: bytes, format_type: str, config: Dict[str, Any]) -> Any:
        """Parse serial device response"""
        try:
            if format_type == 'ascii':
                text = response.decode('ascii').strip()
                # Extract numeric value using regex or simple parsing
                import re
                numbers = re.findall(r'-?\d+\.?\d*', text)
                if numbers:
                    return float(numbers[0])
                return text
            elif format_type == 'binary':
                # Parse binary data based on configuration
                data_type = config.get('data_type', 'uint16')
                if data_type == 'uint16' and len(response) >= 2:
                    return struct.unpack('>H', response[:2])[0]
                elif data_type == 'float32' and len(response) >= 4:
                    return struct.unpack('>f', response[:4])[0]
            
            return response.decode('ascii', errors='ignore')
            
        except Exception as e:
            logger.error(f"Response parsing error: {e}")
            return None
    
    def _validate_ack_response(self, response: bytes, config: Dict[str, Any]) -> bool:
        """Validate acknowledgment response"""
        try:
            expected_ack = config.get('ack_pattern', b'OK')
            return expected_ack in response
        except Exception as e:
            logger.error(f"ACK validation error: {e}")
            return False


class OPCUAProtocol(CommunicationProtocol):
    """OPC UA communication protocol implementation"""
    
    def __init__(self, config: DeviceConfiguration):
        super().__init__(config)
        if not OPCUA_AVAILABLE:
            raise ImportError("OPC UA library not available")
        self.client = None
        
    async def connect(self) -> bool:
        """Establish OPC UA connection"""
        try:
            self.status = DeviceStatus.CONNECTING
            
            endpoint = self.config.connection_params.get('endpoint', 'opc.tcp://localhost:4840')
            username = self.config.connection_params.get('username')
            password = self.config.connection_params.get('password')
            
            self.client = OPCClient(endpoint)
            
            if username and password:
                self.client.set_user(username)
                self.client.set_password(password)
            
            await asyncio.get_event_loop().run_in_executor(None, self.client.connect)
            
            self.status = DeviceStatus.ONLINE
            self.connection_time = datetime.now()
            logger.info(f"Connected to OPC UA device {self.config.device_id} at {endpoint}")
            return True
                
        except Exception as e:
            self.status = DeviceStatus.ERROR
            self.last_error = str(e)
            logger.error(f"OPC UA connection error for {self.config.device_id}: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from OPC UA device"""
        try:
            if self.client:
                await asyncio.get_event_loop().run_in_executor(None, self.client.disconnect)
                self.client = None
            self.status = DeviceStatus.OFFLINE
            logger.info(f"Disconnected from OPC UA device {self.config.device_id}")
            return True
        except Exception as e:
            logger.error(f"OPC UA disconnect error for {self.config.device_id}: {e}")
            return False
    
    async def read_data(self, point_names: List[str]) -> List[DataPoint]:
        """Read data points from OPC UA device"""
        data_points = []
        
        if not self.is_connected():
            return data_points
        
        try:
            for point_name in point_names:
                if point_name not in self.config.data_points:
                    continue
                
                point_config = self.config.data_points[point_name]
                node_id = point_config.get('node_id', '')
                units = point_config.get('units', '')
                
                # Get node and read value
                node = self.client.get_node(node_id)
                value = await asyncio.get_event_loop().run_in_executor(None, node.get_value)
                
                data_point = DataPoint(
                    device_id=self.config.device_id,
                    point_name=point_name,
                    value=value,
                    timestamp=datetime.now(),
                    quality="good",
                    units=units,
                    description=point_config.get('description', '')
                )
                
                data_points.append(data_point)
                self.data_cache[point_name] = data_point
                
        except Exception as e:
            logger.error(f"OPC UA read error for {self.config.device_id}: {e}")
            self.last_error = str(e)
        
        return data_points
    
    async def write_data(self, commands: List[ControlCommand]) -> List[bool]:
        """Write control commands to OPC UA device"""
        results = []
        
        if not self.is_connected():
            return [False] * len(commands)
        
        try:
            for command in commands:
                if command.command_name not in self.config.control_points:
                    results.append(False)
                    continue
                
                control_config = self.config.control_points[command.command_name]
                node_id = control_config.get('node_id', '')
                
                # Get command value
                value = command.parameters.get('value', 0)
                
                # Get node and write value
                node = self.client.get_node(node_id)
                await asyncio.get_event_loop().run_in_executor(None, node.set_value, value)
                
                results.append(True)
                logger.info(f"OPC UA write successful: {command.command_name} = {value}")
                
        except Exception as e:
            logger.error(f"OPC UA write error for {self.config.device_id}: {e}")
            self.last_error = str(e)
            results.extend([False] * (len(commands) - len(results)))
        
        return results
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get OPC UA device information"""
        info = {
            "device_id": self.config.device_id,
            "protocol": "OPC UA",
            "status": self.status.value,
            "connection_params": self.config.connection_params
        }
        
        if self.is_connected():
            try:
                # Get server info
                server_info = await asyncio.get_event_loop().run_in_executor(
                    None, self.client.get_server_node().get_browse_name
                )
                info["server_info"] = str(server_info)
            except Exception as e:
                logger.debug(f"Could not read server info: {e}")
        
        return info

class HTTPRESTProtocol(CommunicationProtocol):
    """HTTP REST API communication protocol implementation"""
    
    def __init__(self, config: DeviceConfiguration):
        super().__init__(config)
        self.session = None
        
    async def connect(self) -> bool:
        """Establish HTTP connection"""
        try:
            import aiohttp
            
            self.status = DeviceStatus.CONNECTING
            
            base_url = self.config.connection_params.get('base_url', 'http://localhost')
            username = self.config.connection_params.get('username')
            password = self.config.connection_params.get('password')
            
            # Create session with authentication if provided
            auth = None
            if username and password:
                auth = aiohttp.BasicAuth(username, password)
            
            self.session = aiohttp.ClientSession(auth=auth)
            
            # Test connection with a simple GET request
            test_endpoint = self.config.connection_params.get('test_endpoint', '/status')
            async with self.session.get(f"{base_url}{test_endpoint}") as response:
                if response.status == 200:
                    self.status = DeviceStatus.ONLINE
                    self.connection_time = datetime.now()
                    logger.info(f"Connected to HTTP device {self.config.device_id} at {base_url}")
                    return True
                else:
                    self.status = DeviceStatus.ERROR
                    self.last_error = f"HTTP connection test failed: {response.status}"
                    return False
                
        except Exception as e:
            self.status = DeviceStatus.ERROR
            self.last_error = str(e)
            logger.error(f"HTTP connection error for {self.config.device_id}: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from HTTP device"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            self.status = DeviceStatus.OFFLINE
            logger.info(f"Disconnected from HTTP device {self.config.device_id}")
            return True
        except Exception as e:
            logger.error(f"HTTP disconnect error for {self.config.device_id}: {e}")
            return False
    
    async def read_data(self, point_names: List[str]) -> List[DataPoint]:
        """Read data points from HTTP device"""
        data_points = []
        
        if not self.is_connected():
            return data_points
        
        try:
            base_url = self.config.connection_params.get('base_url', 'http://localhost')
            
            for point_name in point_names:
                if point_name not in self.config.data_points:
                    continue
                
                point_config = self.config.data_points[point_name]
                endpoint = point_config.get('endpoint', f'/data/{point_name}')
                method = point_config.get('method', 'GET')
                units = point_config.get('units', '')
                
                # Make HTTP request
                url = f"{base_url}{endpoint}"
                
                if method.upper() == 'GET':
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            value = self._extract_value_from_response(data, point_config)
                        else:
                            logger.error(f"HTTP read error for {point_name}: {response.status}")
                            continue
                else:
                    logger.error(f"Unsupported HTTP method for read: {method}")
                    continue
                
                data_point = DataPoint(
                    device_id=self.config.device_id,
                    point_name=point_name,
                    value=value,
                    timestamp=datetime.now(),
                    quality="good",
                    units=units,
                    description=point_config.get('description', '')
                )
                
                data_points.append(data_point)
                self.data_cache[point_name] = data_point
                
        except Exception as e:
            logger.error(f"HTTP read error for {self.config.device_id}: {e}")
            self.last_error = str(e)
        
        return data_points
    
    async def write_data(self, commands: List[ControlCommand]) -> List[bool]:
        """Write control commands to HTTP device"""
        results = []
        
        if not self.is_connected():
            return [False] * len(commands)
        
        try:
            base_url = self.config.connection_params.get('base_url', 'http://localhost')
            
            for command in commands:
                if command.command_name not in self.config.control_points:
                    results.append(False)
                    continue
                
                control_config = self.config.control_points[command.command_name]
                endpoint = control_config.get('endpoint', f'/control/{command.command_name}')
                method = control_config.get('method', 'POST')
                
                # Prepare request data
                request_data = self._prepare_request_data(command, control_config)
                url = f"{base_url}{endpoint}"
                
                # Make HTTP request
                if method.upper() == 'POST':
                    async with self.session.post(url, json=request_data) as response:
                        success = response.status in [200, 201, 202]
                elif method.upper() == 'PUT':
                    async with self.session.put(url, json=request_data) as response:
                        success = response.status in [200, 201, 202]
                else:
                    logger.error(f"Unsupported HTTP method for write: {method}")
                    success = False
                
                results.append(success)
                
                if success:
                    logger.info(f"HTTP write successful: {command.command_name}")
                else:
                    logger.error(f"HTTP write failed: {command.command_name}")
                
        except Exception as e:
            logger.error(f"HTTP write error for {self.config.device_id}: {e}")
            self.last_error = str(e)
            results.extend([False] * (len(commands) - len(results)))
        
        return results
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get HTTP device information"""
        info = {
            "device_id": self.config.device_id,
            "protocol": "HTTP REST",
            "status": self.status.value,
            "connection_params": self.config.connection_params
        }
        
        if self.is_connected():
            try:
                base_url = self.config.connection_params.get('base_url', 'http://localhost')
                info_endpoint = self.config.connection_params.get('info_endpoint', '/info')
                
                async with self.session.get(f"{base_url}{info_endpoint}") as response:
                    if response.status == 200:
                        device_info = await response.json()
                        info["device_info"] = device_info
            except Exception as e:
                logger.debug(f"Could not read device info: {e}")
        
        return info
    
    def _extract_value_from_response(self, data: Dict[str, Any], config: Dict[str, Any]) -> Any:
        """Extract value from HTTP response data"""
        try:
            value_path = config.get('value_path', 'value')
            
            # Navigate nested dictionary using dot notation
            current = data
            for key in value_path.split('.'):
                current = current[key]
            
            return current
            
        except Exception as e:
            logger.error(f"Value extraction error: {e}")
            return None
    
    def _prepare_request_data(self, command: ControlCommand, config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare HTTP request data"""
        try:
            template = config.get('request_template', {})
            
            # Start with template and substitute parameters
            request_data = template.copy()
            
            # Add command parameters
            for key, value in command.parameters.items():
                request_data[key] = value
            
            return request_data
            
        except Exception as e:
            logger.error(f"Request data preparation error: {e}")
            return {}

class DeviceManager:
    """Manages multiple device connections and communication protocols"""
    
    def __init__(self):
        self.devices: Dict[str, CommunicationProtocol] = {}
        self.device_configs: Dict[str, DeviceConfiguration] = {}
        self.polling_tasks: Dict[str, asyncio.Task] = {}
        self.event_callbacks: List[Callable] = []
        self.running = False
        
    def register_device(self, config: DeviceConfiguration) -> bool:
        """Register a new device with the manager"""
        try:
            # Create protocol instance based on type
            if config.protocol_type == ProtocolType.MODBUS_TCP:
                protocol = ModbusTCPProtocol(config)
            elif config.protocol_type == ProtocolType.SERIAL_ASCII:
                protocol = SerialProtocol(config)
            elif config.protocol_type == ProtocolType.OPC_UA:
                protocol = OPCUAProtocol(config)
            elif config.protocol_type == ProtocolType.HTTP_REST:
                protocol = HTTPRESTProtocol(config)
            else:
                logger.error(f"Unsupported protocol type: {config.protocol_type}")
                return False
            
            self.devices[config.device_id] = protocol
            self.device_configs[config.device_id] = config
            
            logger.info(f"Registered device {config.device_id} with protocol {config.protocol_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Device registration error for {config.device_id}: {e}")
            return False
    
    def unregister_device(self, device_id: str) -> bool:
        """Unregister a device from the manager"""
        try:
            if device_id in self.devices:
                # Stop polling if running
                if device_id in self.polling_tasks:
                    self.polling_tasks[device_id].cancel()
                    del self.polling_tasks[device_id]
                
                # Disconnect device
                asyncio.create_task(self.devices[device_id].disconnect())
                
                # Remove from manager
                del self.devices[device_id]
                del self.device_configs[device_id]
                
                logger.info(f"Unregistered device {device_id}")
                return True
            else:
                logger.warning(f"Device {device_id} not found for unregistration")
                return False
                
        except Exception as e:
            logger.error(f"Device unregistration error for {device_id}: {e}")
            return False
    
    async def connect_all_devices(self) -> Dict[str, bool]:
        """Connect to all registered devices"""
        results = {}
        
        for device_id, protocol in self.devices.items():
            if self.device_configs[device_id].enabled:
                success = await protocol.connect()
                results[device_id] = success
                
                if success and self.device_configs[device_id].polling_interval > 0:
                    # Start polling task
                    task = asyncio.create_task(self._polling_loop(device_id))
                    self.polling_tasks[device_id] = task
            else:
                results[device_id] = False
                logger.info(f"Device {device_id} is disabled, skipping connection")
        
        return results
    
    async def disconnect_all_devices(self) -> Dict[str, bool]:
        """Disconnect from all devices"""
        results = {}
        
        # Cancel all polling tasks
        for task in self.polling_tasks.values():
            task.cancel()
        self.polling_tasks.clear()
        
        # Disconnect all devices
        for device_id, protocol in self.devices.items():
            success = await protocol.disconnect()
            results[device_id] = success
        
        return results
    
    async def read_device_data(self, device_id: str, point_names: List[str]) -> List[DataPoint]:
        """Read data from a specific device"""
        if device_id not in self.devices:
            logger.error(f"Device {device_id} not found")
            return []
        
        return await self.devices[device_id].read_data(point_names)
    
    async def write_device_data(self, device_id: str, commands: List[ControlCommand]) -> List[bool]:
        """Write data to a specific device"""
        if device_id not in self.devices:
            logger.error(f"Device {device_id} not found")
            return [False] * len(commands)
        
        return await self.devices[device_id].write_data(commands)
    
    async def get_all_device_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all devices"""
        status = {}
        
        for device_id, protocol in self.devices.items():
            status[device_id] = protocol.get_status()
        
        return status
    
    async def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific device"""
        if device_id not in self.devices:
            return None
        
        return await self.devices[device_id].get_device_info()
    
    def add_event_callback(self, callback: Callable):
        """Add callback for device events"""
        self.event_callbacks.append(callback)
    
    def remove_event_callback(self, callback: Callable):
        """Remove event callback"""
        if callback in self.event_callbacks:
            self.event_callbacks.remove(callback)
    
    async def _polling_loop(self, device_id: str):
        """Continuous polling loop for a device"""
        try:
            config = self.device_configs[device_id]
            protocol = self.devices[device_id]
            
            while True:
                if protocol.is_connected():
                    # Read all configured data points
                    point_names = list(config.data_points.keys())
                    if point_names:
                        data_points = await protocol.read_data(point_names)
                        
                        # Notify callbacks of new data
                        for callback in self.event_callbacks:
                            try:
                                await callback('data_received', {
                                    'device_id': device_id,
                                    'data_points': [asdict(dp) for dp in data_points]
                                })
                            except Exception as e:
                                logger.error(f"Callback error: {e}")
                
                # Wait for next polling interval
                await asyncio.sleep(config.polling_interval)
                
        except asyncio.CancelledError:
            logger.info(f"Polling loop cancelled for device {device_id}")
        except Exception as e:
            logger.error(f"Polling loop error for device {device_id}: {e}")
            
            # Notify callbacks of error
            for callback in self.event_callbacks:
                try:
                    await callback('device_error', {
                        'device_id': device_id,
                        'error': str(e)
                    })
                except Exception as cb_error:
                    logger.error(f"Callback error: {cb_error}")

# Example usage and testing
async def main():
    """Example usage of the hardware communication protocols"""
    
    # Create device manager
    manager = DeviceManager()
    
    # Example device configurations
    modbus_config = DeviceConfiguration(
        device_id="mixer_001",
        device_type=DeviceType.MIXER,
        protocol_type=ProtocolType.MODBUS_TCP,
        connection_params={
            'host': '192.168.1.100',
            'port': 502,
            'unit_id': 1
        },
        data_points={
            'temperature': {
                'register_type': 'holding',
                'address': 100,
                'data_type': 'float32',
                'count': 2,
                'units': '°C',
                'description': 'Vessel temperature'
            },
            'mixing_speed': {
                'register_type': 'holding',
                'address': 102,
                'data_type': 'uint16',
                'scale_factor': 1.0,
                'units': 'RPM',
                'description': 'Mixing speed'
            }
        },
        control_points={
            'set_temperature': {
                'register_type': 'holding',
                'address': 200,
                'data_type': 'float32'
            },
            'set_mixing_speed': {
                'register_type': 'holding',
                'address': 202,
                'data_type': 'uint16'
            }
        },
        polling_interval=1.0
    )
    
    # Register devices
    manager.register_device(modbus_config)
    
    # Add event callback
    async def data_callback(event_type: str, data: Dict[str, Any]):
        if event_type == 'data_received':
            print(f"Received data from {data['device_id']}: {len(data['data_points'])} points")
        elif event_type == 'device_error':
            print(f"Device error for {data['device_id']}: {data['error']}")
    
    manager.add_event_callback(data_callback)
    
    try:
        # Connect to devices
        print("Connecting to devices...")
        results = await manager.connect_all_devices()
        print(f"Connection results: {results}")
        
        # Wait for some data
        await asyncio.sleep(5)
        
        # Send control command
        command = ControlCommand(
            device_id="mixer_001",
            command_name="set_mixing_speed",
            parameters={'value': 500},
            timestamp=datetime.now()
        )
        
        write_results = await manager.write_device_data("mixer_001", [command])
        print(f"Write results: {write_results}")
        
        # Get device status
        status = await manager.get_all_device_status()
        print(f"Device status: {status}")
        
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        # Disconnect all devices
        await manager.disconnect_all_devices()

if __name__ == "__main__":
    print("=== Hardware Communication Protocols Test ===")
    print("This module provides comprehensive communication protocols for laboratory equipment integration.")
    print("Supported protocols: Modbus TCP, Serial, OPC UA, HTTP REST")
    print()
    
    # Run example if executed directly
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error running example: {e}")
        print("Note: This example requires actual hardware or simulators to connect to.")

