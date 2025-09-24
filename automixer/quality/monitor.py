"""
Quality Control Integration with real-time monitoring and adjustment.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from ..core.models import QualityCheck, QualityStatus, Batch


@dataclass
class QualityAlert:
    """Alert for quality control issues."""
    id: str
    batch_id: str
    severity: str  # "low", "medium", "high", "critical"
    message: str
    timestamp: datetime
    resolved: bool = False


class QualityControlMonitor:
    """
    Real-time quality control monitoring and adjustment system.
    
    Features:
    - Continuous monitoring of production parameters
    - Automated quality checks
    - Real-time adjustments
    - Statistical process control
    - Trend analysis and prediction
    """
    
    def __init__(self):
        self.quality_checks: Dict[str, QualityCheck] = {}
        self.active_monitors: Dict[str, Dict] = {}
        self.alerts: List[QualityAlert] = []
        self.historical_data: Dict[str, List] = {}
        self.control_limits: Dict[str, Dict] = self._initialize_control_limits()
    
    def _initialize_control_limits(self) -> Dict[str, Dict]:
        """Initialize statistical control limits for key parameters."""
        return {
            'ph': {'lower': 5.0, 'upper': 7.5, 'target': 6.2},
            'viscosity': {'lower': 2000, 'upper': 8000, 'target': 5000},
            'temperature': {'lower': 18, 'upper': 25, 'target': 22},
            'moisture_content': {'lower': 45, 'upper': 65, 'target': 55},
            'particle_size': {'lower': 50, 'upper': 200, 'target': 100},
            'color_consistency': {'lower': 0.8, 'upper': 1.0, 'target': 0.95}
        }
    
    def start_batch_monitoring(self, batch_id: str, recipe_targets: Dict[str, float]) -> bool:
        """Start real-time monitoring for a production batch."""
        self.active_monitors[batch_id] = {
            'start_time': datetime.utcnow(),
            'targets': recipe_targets,
            'measurements': [],
            'adjustments_made': [],
            'status': 'active'
        }
        
        # Initialize historical data tracking
        if batch_id not in self.historical_data:
            self.historical_data[batch_id] = []
        
        return True
    
    def record_measurement(self, batch_id: str, parameter: str, value: float, 
                          equipment_id: Optional[str] = None) -> bool:
        """Record a quality measurement."""
        if batch_id not in self.active_monitors:
            return False
        
        measurement = {
            'timestamp': datetime.utcnow(),
            'parameter': parameter,
            'value': value,
            'equipment_id': equipment_id
        }
        
        self.active_monitors[batch_id]['measurements'].append(measurement)
        
        # Check if measurement is within control limits
        alert = self._check_control_limits(batch_id, parameter, value)
        if alert:
            self.alerts.append(alert)
        
        # Check if automatic adjustment is needed
        adjustment = self._evaluate_adjustment_need(batch_id, parameter, value)
        if adjustment:
            self._make_automatic_adjustment(batch_id, adjustment)
        
        return True
    
    def _check_control_limits(self, batch_id: str, parameter: str, value: float) -> Optional[QualityAlert]:
        """Check if a measurement violates control limits."""
        if parameter not in self.control_limits:
            return None
        
        limits = self.control_limits[parameter]
        alert_id = f"alert_{batch_id}_{parameter}_{datetime.utcnow().isoformat()}"
        
        if value < limits['lower']:
            return QualityAlert(
                id=alert_id,
                batch_id=batch_id,
                severity="high",
                message=f"{parameter} below lower limit: {value} < {limits['lower']}",
                timestamp=datetime.utcnow()
            )
        elif value > limits['upper']:
            return QualityAlert(
                id=alert_id,
                batch_id=batch_id,
                severity="high", 
                message=f"{parameter} above upper limit: {value} > {limits['upper']}",
                timestamp=datetime.utcnow()
            )
        
        # Check for trend warnings (approaching limits)
        target = limits['target']
        range_size = limits['upper'] - limits['lower']
        
        if abs(value - target) > 0.7 * range_size / 2:
            return QualityAlert(
                id=alert_id,
                batch_id=batch_id,
                severity="medium",
                message=f"{parameter} approaching control limits: {value}",
                timestamp=datetime.utcnow()
            )
        
        return None
    
    def _evaluate_adjustment_need(self, batch_id: str, parameter: str, value: float) -> Optional[Dict]:
        """Evaluate if automatic adjustment is needed."""
        if parameter not in self.control_limits:
            return None
        
        limits = self.control_limits[parameter]
        target = limits['target']
        deviation = abs(value - target)
        threshold = (limits['upper'] - limits['lower']) * 0.3  # 30% of range
        
        if deviation > threshold:
            return {
                'parameter': parameter,
                'current_value': value,
                'target_value': target,
                'adjustment_type': 'automatic',
                'severity': 'medium' if deviation < threshold * 1.5 else 'high'
            }
        
        return None
    
    def _make_automatic_adjustment(self, batch_id: str, adjustment: Dict) -> bool:
        """Make automatic process adjustments."""
        parameter = adjustment['parameter']
        current = adjustment['current_value']
        target = adjustment['target_value']
        
        adjustment_actions = {
            'ph': self._adjust_ph,
            'temperature': self._adjust_temperature,
            'viscosity': self._adjust_viscosity,
            'mixing_speed': self._adjust_mixing_speed
        }
        
        if parameter in adjustment_actions:
            success = adjustment_actions[parameter](batch_id, current, target)
            
            if success:
                self.active_monitors[batch_id]['adjustments_made'].append({
                    'timestamp': datetime.utcnow(),
                    'parameter': parameter,
                    'from_value': current,
                    'to_value': target,
                    'action': f"Automatic adjustment for {parameter}"
                })
            
            return success
        
        return False
    
    def _adjust_ph(self, batch_id: str, current: float, target: float) -> bool:
        """Adjust pH by recommending acid/base addition."""
        if current < target:
            # Need to increase pH
            adjustment_amount = (target - current) * 0.1  # Conservative adjustment
            action = f"Add {adjustment_amount:.2f}ml of base solution"
        else:
            # Need to decrease pH
            adjustment_amount = (current - target) * 0.1
            action = f"Add {adjustment_amount:.2f}ml of acid solution"
        
        # In real implementation, this would interface with dosing pumps
        print(f"pH Adjustment for batch {batch_id}: {action}")
        return True
    
    def _adjust_temperature(self, batch_id: str, current: float, target: float) -> bool:
        """Adjust temperature through heating/cooling systems."""
        if current < target:
            action = f"Increase heating to reach {target}°C"
        else:
            action = f"Increase cooling to reach {target}°C"
        
        print(f"Temperature Adjustment for batch {batch_id}: {action}")
        return True
    
    def _adjust_viscosity(self, batch_id: str, current: float, target: float) -> bool:
        """Adjust viscosity through thickening/thinning agents."""
        if current < target:
            action = "Add thickening agent"
        else:
            action = "Add thinning agent"
        
        print(f"Viscosity Adjustment for batch {batch_id}: {action}")
        return True
    
    def _adjust_mixing_speed(self, batch_id: str, current: float, target: float) -> bool:
        """Adjust mixing speed."""
        action = f"Adjust mixing speed to {target} RPM"
        print(f"Mixing Speed Adjustment for batch {batch_id}: {action}")
        return True
    
    def create_quality_check(self, batch_id: str, test_type: str, 
                           target_values: Dict[str, float]) -> str:
        """Create a new quality check for a batch."""
        check = QualityCheck(
            batch_id=batch_id,
            test_type=test_type,
            target_values=target_values,
            tolerance={key: value * 0.05 for key, value in target_values.items()}  # 5% tolerance
        )
        
        self.quality_checks[check.id] = check
        return check.id
    
    def update_quality_check(self, check_id: str, measured_values: Dict[str, float],
                           operator: Optional[str] = None) -> bool:
        """Update quality check with measured values."""
        if check_id not in self.quality_checks:
            return False
        
        check = self.quality_checks[check_id]
        check.measured_values = measured_values
        check.operator = operator
        check.status = self._evaluate_quality_status(check)
        
        return True
    
    def _evaluate_quality_status(self, check: QualityCheck) -> QualityStatus:
        """Evaluate quality status based on measurements vs targets."""
        if not check.measured_values:
            return QualityStatus.PENDING
        
        all_within_tolerance = True
        requires_adjustment = False
        
        for parameter, target in check.target_values.items():
            if parameter not in check.measured_values:
                continue
            
            measured = check.measured_values[parameter]
            tolerance = check.tolerance.get(parameter, target * 0.05)
            
            deviation = abs(measured - target)
            
            if deviation > tolerance:
                all_within_tolerance = False
                if deviation > tolerance * 2:  # Major deviation
                    return QualityStatus.FAILED
                else:
                    requires_adjustment = True
        
        if all_within_tolerance:
            return QualityStatus.PASSED
        elif requires_adjustment:
            return QualityStatus.REQUIRES_ADJUSTMENT
        else:
            return QualityStatus.FAILED
    
    def get_batch_quality_summary(self, batch_id: str) -> Dict[str, Any]:
        """Get comprehensive quality summary for a batch."""
        if batch_id not in self.active_monitors:
            return {}
        
        monitor_data = self.active_monitors[batch_id]
        
        # Calculate statistics for each parameter
        parameter_stats = {}
        for measurement in monitor_data['measurements']:
            param = measurement['parameter']
            value = measurement['value']
            
            if param not in parameter_stats:
                parameter_stats[param] = []
            parameter_stats[param].append(value)
        
        # Calculate statistics
        stats_summary = {}
        for param, values in parameter_stats.items():
            if values:
                stats_summary[param] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'count': len(values),
                    'latest': values[-1] if values else None
                }
        
        # Get alerts for this batch
        batch_alerts = [alert for alert in self.alerts if alert.batch_id == batch_id]
        
        return {
            'batch_id': batch_id,
            'monitoring_duration': (datetime.utcnow() - monitor_data['start_time']).total_seconds() / 60,
            'parameter_statistics': stats_summary,
            'total_measurements': len(monitor_data['measurements']),
            'adjustments_made': len(monitor_data['adjustments_made']),
            'alerts_count': len(batch_alerts),
            'active_alerts': len([a for a in batch_alerts if not a.resolved]),
            'status': monitor_data['status']
        }
    
    def get_trend_analysis(self, parameter: str, days: int = 7) -> Dict[str, Any]:
        """Analyze trends for a parameter across recent batches."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        recent_data = []
        for batch_id, monitor_data in self.active_monitors.items():
            if monitor_data['start_time'] > cutoff_date:
                for measurement in monitor_data['measurements']:
                    if measurement['parameter'] == parameter:
                        recent_data.append({
                            'timestamp': measurement['timestamp'],
                            'value': measurement['value'],
                            'batch_id': batch_id
                        })
        
        if not recent_data:
            return {'parameter': parameter, 'no_data': True}
        
        values = [d['value'] for d in recent_data]
        
        # Calculate trend statistics
        trend_analysis = {
            'parameter': parameter,
            'data_points': len(values),
            'mean': np.mean(values),
            'std': np.std(values),
            'trend_slope': self._calculate_trend_slope(recent_data),
            'control_limits': self.control_limits.get(parameter, {}),
            'out_of_control_points': self._count_out_of_control(parameter, values),
            'capability_index': self._calculate_capability_index(parameter, values)
        }
        
        return trend_analysis
    
    def _calculate_trend_slope(self, data: List[Dict]) -> float:
        """Calculate trend slope using linear regression."""
        if len(data) < 2:
            return 0.0
        
        # Sort by timestamp
        sorted_data = sorted(data, key=lambda x: x['timestamp'])
        
        # Convert timestamps to hours since first measurement
        start_time = sorted_data[0]['timestamp']
        x_values = [(d['timestamp'] - start_time).total_seconds() / 3600 for d in sorted_data]
        y_values = [d['value'] for d in sorted_data]
        
        # Simple linear regression
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope
    
    def _count_out_of_control(self, parameter: str, values: List[float]) -> int:
        """Count measurements outside control limits."""
        if parameter not in self.control_limits:
            return 0
        
        limits = self.control_limits[parameter]
        count = 0
        
        for value in values:
            if value < limits['lower'] or value > limits['upper']:
                count += 1
        
        return count
    
    def _calculate_capability_index(self, parameter: str, values: List[float]) -> float:
        """Calculate process capability index (Cpk)."""
        if parameter not in self.control_limits or len(values) < 2:
            return 0.0
        
        limits = self.control_limits[parameter]
        mean_value = np.mean(values)
        std_value = np.std(values)
        
        if std_value == 0:
            return 0.0
        
        # Calculate Cpk
        cpu = (limits['upper'] - mean_value) / (3 * std_value)
        cpl = (mean_value - limits['lower']) / (3 * std_value)
        
        return min(cpu, cpl)