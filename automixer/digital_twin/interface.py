"""
Digital Twin Interface for connecting to physical equipment and real-time monitoring.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import numpy as np

from ..core.models import Equipment, EquipmentStatus, DigitalTwinState


class ConnectionStatus(str, Enum):
    """Connection status for equipment."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


@dataclass
class SensorReading:
    """Sensor reading data structure."""
    sensor_id: str
    equipment_id: str
    parameter: str
    value: float
    unit: str
    timestamp: datetime
    quality: str = "good"  # good, uncertain, bad


@dataclass
class ControlCommand:
    """Control command data structure."""
    command_id: str
    equipment_id: str
    parameter: str
    target_value: float
    timestamp: datetime
    executed: bool = False
    result: Optional[str] = None


class DigitalTwinInterface:
    """
    Digital Twin Interface for physical equipment integration.
    
    Features:
    - Real-time equipment monitoring
    - Bidirectional communication with physical systems
    - Predictive maintenance alerts
    - Process optimization through ML
    - Virtual equipment simulation
    - Data synchronization between digital and physical twins
    """
    
    def __init__(self):
        self.connected_equipment: Dict[str, Dict] = {}
        self.sensor_data: Dict[str, List[SensorReading]] = {}
        self.control_commands: Dict[str, ControlCommand] = {}
        self.twin_state: DigitalTwinState = DigitalTwinState()
        self.event_callbacks: Dict[str, List[Callable]] = {}
        self.simulation_mode = False
        self.data_retention_days = 30
    
    async def connect_equipment(self, equipment_id: str, connection_config: Dict[str, Any]) -> bool:
        """Connect to physical equipment."""
        
        try:
            # Simulate connection process
            connection_info = {
                'equipment_id': equipment_id,
                'connection_type': connection_config.get('type', 'modbus'),
                'address': connection_config.get('address'),
                'port': connection_config.get('port'),
                'status': ConnectionStatus.CONNECTED,
                'connected_at': datetime.utcnow(),
                'last_heartbeat': datetime.utcnow(),
                'sensors': connection_config.get('sensors', []),
                'actuators': connection_config.get('actuators', [])
            }
            
            self.connected_equipment[equipment_id] = connection_info
            
            # Initialize sensor data storage
            self.sensor_data[equipment_id] = []
            
            # Start monitoring this equipment
            await self._start_equipment_monitoring(equipment_id)
            
            return True
            
        except Exception as e:
            print(f"Failed to connect to equipment {equipment_id}: {e}")
            return False
    
    async def disconnect_equipment(self, equipment_id: str) -> bool:
        """Disconnect from physical equipment."""
        
        if equipment_id in self.connected_equipment:
            self.connected_equipment[equipment_id]['status'] = ConnectionStatus.DISCONNECTED
            self.connected_equipment[equipment_id]['disconnected_at'] = datetime.utcnow()
            
            # Stop monitoring
            await self._stop_equipment_monitoring(equipment_id)
            
            return True
        
        return False
    
    async def _start_equipment_monitoring(self, equipment_id: str) -> None:
        """Start continuous monitoring of equipment."""
        
        # This would typically start a background task for real monitoring
        # For simulation, we'll generate synthetic data
        if self.simulation_mode:
            asyncio.create_task(self._simulate_equipment_data(equipment_id))
    
    async def _stop_equipment_monitoring(self, equipment_id: str) -> None:
        """Stop monitoring equipment."""
        
        # In real implementation, this would stop monitoring tasks
        pass
    
    async def _simulate_equipment_data(self, equipment_id: str) -> None:
        """Simulate equipment sensor data for testing."""
        
        equipment_info = self.connected_equipment.get(equipment_id)
        if not equipment_info:
            return
        
        sensors = equipment_info.get('sensors', [])
        
        while equipment_info.get('status') == ConnectionStatus.CONNECTED:
            for sensor_config in sensors:
                sensor_id = sensor_config['id']
                parameter = sensor_config['parameter']
                base_value = sensor_config.get('base_value', 50.0)
                noise_level = sensor_config.get('noise_level', 5.0)
                
                # Generate realistic sensor reading with noise
                noise = np.random.normal(0, noise_level)
                value = base_value + noise
                
                reading = SensorReading(
                    sensor_id=sensor_id,
                    equipment_id=equipment_id,
                    parameter=parameter,
                    value=value,
                    unit=sensor_config.get('unit', ''),
                    timestamp=datetime.utcnow()
                )
                
                await self._process_sensor_reading(reading)
            
            # Wait before next reading cycle
            await asyncio.sleep(sensor_config.get('read_interval', 5))
    
    async def _process_sensor_reading(self, reading: SensorReading) -> None:
        """Process incoming sensor reading."""
        
        # Store sensor data
        if reading.equipment_id not in self.sensor_data:
            self.sensor_data[reading.equipment_id] = []
        
        self.sensor_data[reading.equipment_id].append(reading)
        
        # Update digital twin state
        if reading.equipment_id not in self.twin_state.equipment_states:
            self.twin_state.equipment_states[reading.equipment_id] = {}
        
        self.twin_state.equipment_states[reading.equipment_id][reading.parameter] = {
            'value': reading.value,
            'unit': reading.unit,
            'timestamp': reading.timestamp.isoformat(),
            'quality': reading.quality
        }
        
        # Check for alerts
        await self._check_sensor_alerts(reading)
        
        # Trigger callbacks
        await self._trigger_callbacks('sensor_reading', reading)
        
        # Clean old data
        await self._cleanup_old_data(reading.equipment_id)
    
    async def _check_sensor_alerts(self, reading: SensorReading) -> None:
        """Check sensor reading for alert conditions."""
        
        # Define alert thresholds (would typically come from configuration)
        alert_thresholds = {
            'temperature': {'min': 15, 'max': 30, 'critical_max': 35},
            'pressure': {'min': 0.5, 'max': 5.0, 'critical_max': 6.0},
            'ph': {'min': 5.0, 'max': 7.5},
            'vibration': {'max': 10.0, 'critical_max': 15.0}
        }
        
        parameter = reading.parameter.lower()
        if parameter in alert_thresholds:
            thresholds = alert_thresholds[parameter]
            
            alert_level = None
            message = ""
            
            if 'critical_max' in thresholds and reading.value >= thresholds['critical_max']:
                alert_level = "critical"
                message = f"{reading.parameter} critical high: {reading.value} >= {thresholds['critical_max']}"
            elif 'critical_min' in thresholds and reading.value <= thresholds['critical_min']:
                alert_level = "critical" 
                message = f"{reading.parameter} critical low: {reading.value} <= {thresholds['critical_min']}"
            elif 'max' in thresholds and reading.value > thresholds['max']:
                alert_level = "warning"
                message = f"{reading.parameter} high: {reading.value} > {thresholds['max']}"
            elif 'min' in thresholds and reading.value < thresholds['min']:
                alert_level = "warning"
                message = f"{reading.parameter} low: {reading.value} < {thresholds['min']}"
            
            if alert_level:
                alert = {
                    'timestamp': reading.timestamp.isoformat(),
                    'equipment_id': reading.equipment_id,
                    'sensor_id': reading.sensor_id,
                    'parameter': reading.parameter,
                    'value': reading.value,
                    'level': alert_level,
                    'message': message
                }
                
                self.twin_state.alerts.append(alert)
                await self._trigger_callbacks('alert', alert)
    
    async def _cleanup_old_data(self, equipment_id: str) -> None:
        """Clean up old sensor data beyond retention period."""
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.data_retention_days)
        
        if equipment_id in self.sensor_data:
            self.sensor_data[equipment_id] = [
                reading for reading in self.sensor_data[equipment_id]
                if reading.timestamp > cutoff_date
            ]
    
    async def send_control_command(self, equipment_id: str, parameter: str,
                                 target_value: float, command_type: str = "setpoint") -> str:
        """Send control command to physical equipment."""
        
        if equipment_id not in self.connected_equipment:
            raise ValueError(f"Equipment {equipment_id} not connected")
        
        command = ControlCommand(
            command_id=f"cmd_{equipment_id}_{datetime.utcnow().timestamp()}",
            equipment_id=equipment_id,
            parameter=parameter,
            target_value=target_value,
            timestamp=datetime.utcnow()
        )
        
        self.control_commands[command.command_id] = command
        
        # Simulate command execution
        success = await self._execute_control_command(command)
        
        command.executed = True
        command.result = "success" if success else "failed"
        
        return command.command_id
    
    async def _execute_control_command(self, command: ControlCommand) -> bool:
        """Execute control command on physical equipment."""
        
        try:
            # Simulate command execution
            equipment_info = self.connected_equipment[command.equipment_id]
            
            print(f"Executing command on {command.equipment_id}: "
                  f"Set {command.parameter} to {command.target_value}")
            
            # Update equipment state to reflect command
            if command.equipment_id not in self.twin_state.equipment_states:
                self.twin_state.equipment_states[command.equipment_id] = {}
            
            self.twin_state.equipment_states[command.equipment_id][f"{command.parameter}_setpoint"] = {
                'value': command.target_value,
                'timestamp': command.timestamp.isoformat(),
                'command_id': command.command_id
            }
            
            await self._trigger_callbacks('command_executed', command)
            
            return True
            
        except Exception as e:
            print(f"Failed to execute command {command.command_id}: {e}")
            return False
    
    def get_equipment_status(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of connected equipment."""
        
        if equipment_id not in self.connected_equipment:
            return None
        
        equipment_info = self.connected_equipment[equipment_id]
        recent_data = self._get_recent_sensor_data(equipment_id, minutes=5)
        
        return {
            'equipment_id': equipment_id,
            'connection_status': equipment_info['status'].value,
            'connected_at': equipment_info['connected_at'].isoformat(),
            'last_heartbeat': equipment_info['last_heartbeat'].isoformat(),
            'sensor_count': len(equipment_info.get('sensors', [])),
            'recent_readings': len(recent_data),
            'current_state': self.twin_state.equipment_states.get(equipment_id, {}),
            'active_alerts': self._get_equipment_alerts(equipment_id)
        }
    
    def _get_recent_sensor_data(self, equipment_id: str, minutes: int = 10) -> List[SensorReading]:
        """Get recent sensor data for equipment."""
        
        if equipment_id not in self.sensor_data:
            return []
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        return [
            reading for reading in self.sensor_data[equipment_id]
            if reading.timestamp > cutoff_time
        ]
    
    def _get_equipment_alerts(self, equipment_id: str) -> List[Dict]:
        """Get active alerts for equipment."""
        
        return [
            alert for alert in self.twin_state.alerts
            if alert.get('equipment_id') == equipment_id
        ]
    
    def get_digital_twin_state(self) -> Dict[str, Any]:
        """Get current digital twin state."""
        
        return {
            'timestamp': self.twin_state.timestamp.isoformat(),
            'connected_equipment_count': len(self.connected_equipment),
            'equipment_states': self.twin_state.equipment_states,
            'process_parameters': self.twin_state.process_parameters,
            'environmental_conditions': self.twin_state.environmental_conditions,
            'active_batches': self.twin_state.active_batches,
            'total_alerts': len(self.twin_state.alerts),
            'active_alerts': len([a for a in self.twin_state.alerts if 'resolved' not in a]),
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def register_callback(self, event_type: str, callback: Callable) -> None:
        """Register callback for specific events."""
        
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        
        self.event_callbacks[event_type].append(callback)
    
    async def _trigger_callbacks(self, event_type: str, data: Any) -> None:
        """Trigger registered callbacks for event type."""
        
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    print(f"Error in callback for {event_type}: {e}")
    
    def start_simulation_mode(self) -> None:
        """Enable simulation mode for testing without physical equipment."""
        
        self.simulation_mode = True
        
        # Add some simulated equipment
        asyncio.create_task(self._setup_simulated_equipment())
    
    async def _setup_simulated_equipment(self) -> None:
        """Set up simulated equipment for testing."""
        
        # Simulate mixer
        await self.connect_equipment("mixer_001", {
            'type': 'modbus',
            'address': '192.168.1.100',
            'port': 502,
            'sensors': [
                {
                    'id': 'temp_001',
                    'parameter': 'temperature',
                    'unit': '°C',
                    'base_value': 22.0,
                    'noise_level': 1.0,
                    'read_interval': 2
                },
                {
                    'id': 'speed_001',
                    'parameter': 'mixing_speed',
                    'unit': 'RPM',
                    'base_value': 150.0,
                    'noise_level': 5.0,
                    'read_interval': 3
                },
                {
                    'id': 'torque_001',
                    'parameter': 'torque',
                    'unit': 'Nm',
                    'base_value': 25.0,
                    'noise_level': 2.0,
                    'read_interval': 2
                }
            ],
            'actuators': [
                {'id': 'speed_control', 'parameter': 'mixing_speed'},
                {'id': 'temp_control', 'parameter': 'temperature'}
            ]
        })
        
        # Simulate homogenizer
        await self.connect_equipment("homogenizer_001", {
            'type': 'ethernet_ip',
            'address': '192.168.1.101',
            'sensors': [
                {
                    'id': 'pressure_001',
                    'parameter': 'pressure',
                    'unit': 'bar',
                    'base_value': 2.5,
                    'noise_level': 0.2,
                    'read_interval': 1
                },
                {
                    'id': 'flow_001',
                    'parameter': 'flow_rate',
                    'unit': 'L/min',
                    'base_value': 5.0,
                    'noise_level': 0.5,
                    'read_interval': 2
                }
            ]
        })
    
    def get_process_analytics(self, equipment_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get process analytics for equipment over specified time period."""
        
        if equipment_id not in self.sensor_data:
            return {}
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        relevant_data = [
            reading for reading in self.sensor_data[equipment_id]
            if reading.timestamp > cutoff_time
        ]
        
        # Group by parameter
        parameter_data = {}
        for reading in relevant_data:
            if reading.parameter not in parameter_data:
                parameter_data[reading.parameter] = []
            parameter_data[reading.parameter].append(reading.value)
        
        # Calculate statistics
        analytics = {}
        for parameter, values in parameter_data.items():
            if values:
                analytics[parameter] = {
                    'count': len(values),
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'latest': values[-1],
                    'trend': self._calculate_trend(values)
                }
        
        return {
            'equipment_id': equipment_id,
            'analysis_period_hours': hours,
            'total_readings': len(relevant_data),
            'parameter_analytics': analytics,
            'uptime_percentage': self._calculate_uptime(equipment_id, hours),
            'alert_count': len(self._get_equipment_alerts(equipment_id))
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for a series of values."""
        
        if len(values) < 2:
            return "insufficient_data"
        
        # Simple trend calculation using first and last quartile
        quartile_size = len(values) // 4
        if quartile_size < 1:
            return "stable"
        
        first_quartile = np.mean(values[:quartile_size])
        last_quartile = np.mean(values[-quartile_size:])
        
        change_percent = ((last_quartile - first_quartile) / first_quartile) * 100
        
        if abs(change_percent) < 5:
            return "stable"
        elif change_percent > 0:
            return "increasing"
        else:
            return "decreasing"
    
    def _calculate_uptime(self, equipment_id: str, hours: int) -> float:
        """Calculate equipment uptime percentage."""
        
        # Simplified uptime calculation based on connection status
        equipment_info = self.connected_equipment.get(equipment_id)
        if not equipment_info:
            return 0.0
        
        if equipment_info['status'] == ConnectionStatus.CONNECTED:
            return 100.0
        else:
            # In real implementation, this would track actual uptime
            return 85.0  # Simulated uptime