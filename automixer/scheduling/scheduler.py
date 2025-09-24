"""
Resource Scheduling system for intelligent equipment and material allocation.
"""

import heapq
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from ..core.models import Equipment, EquipmentStatus, Batch, BatchStatus, Recipe


class Priority(Enum):
    """Priority levels for batch scheduling."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class ScheduledTask:
    """Represents a scheduled manufacturing task."""
    id: str
    batch_id: str
    recipe_id: str
    priority: Priority
    estimated_duration: int  # minutes
    required_equipment: List[str]
    required_materials: Dict[str, float]
    earliest_start: datetime
    deadline: Optional[datetime] = None
    assigned_equipment: List[str] = field(default_factory=list)
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"


class ResourceScheduler:
    """
    Intelligent resource scheduling system for manufacturing operations.
    
    Features:
    - Equipment allocation optimization
    - Material availability tracking
    - Priority-based scheduling
    - Dependency management
    - Real-time rescheduling
    - Capacity planning
    """
    
    def __init__(self):
        self.equipment: Dict[str, Equipment] = {}
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.material_inventory: Dict[str, float] = {}
        self.equipment_calendar: Dict[str, List[Dict]] = {}
        self.task_queue: List[Tuple[int, str]] = []  # Priority queue
        self.scheduling_horizon_days = 14
    
    def add_equipment(self, equipment: Equipment) -> str:
        """Add equipment to the scheduling system."""
        self.equipment[equipment.id] = equipment
        self.equipment_calendar[equipment.id] = []
        return equipment.id
    
    def update_equipment_status(self, equipment_id: str, status: EquipmentStatus,
                              current_batch_id: Optional[str] = None) -> bool:
        """Update equipment status."""
        if equipment_id not in self.equipment:
            return False
        
        equipment = self.equipment[equipment_id]
        equipment.status = status
        equipment.current_batch_id = current_batch_id
        
        # If equipment becomes available, trigger rescheduling
        if status == EquipmentStatus.IDLE:
            self._trigger_rescheduling()
        
        return True
    
    def update_material_inventory(self, materials: Dict[str, float]) -> None:
        """Update material inventory levels."""
        for material, quantity in materials.items():
            self.material_inventory[material] = quantity
    
    def add_material_stock(self, material: str, quantity: float) -> None:
        """Add material stock."""
        if material in self.material_inventory:
            self.material_inventory[material] += quantity
        else:
            self.material_inventory[material] = quantity
    
    def consume_materials(self, materials: Dict[str, float]) -> bool:
        """Consume materials from inventory."""
        # Check availability first
        for material, required in materials.items():
            available = self.material_inventory.get(material, 0)
            if available < required:
                return False
        
        # Consume materials
        for material, required in materials.items():
            self.material_inventory[material] -= required
        
        return True
    
    def schedule_batch(self, batch: Batch, recipe: Recipe, priority: Priority = Priority.NORMAL,
                      deadline: Optional[datetime] = None) -> str:
        """Schedule a batch for production."""
        
        # Create scheduled task
        task = ScheduledTask(
            id=f"task_{batch.id}",
            batch_id=batch.id,
            recipe_id=recipe.id,
            priority=priority,
            estimated_duration=self._estimate_batch_duration(recipe),
            required_equipment=self._determine_required_equipment(recipe),
            required_materials=self._extract_material_requirements(recipe),
            earliest_start=datetime.utcnow(),
            deadline=deadline
        )
        
        self.scheduled_tasks[task.id] = task
        
        # Add to priority queue
        # Use negative priority value for max heap behavior
        heapq.heappush(self.task_queue, (-priority.value, task.id))
        
        # Attempt immediate scheduling
        self._schedule_task(task.id)
        
        return task.id
    
    def _estimate_batch_duration(self, recipe: Recipe) -> int:
        """Estimate batch processing duration in minutes."""
        base_duration = 60  # Base 1 hour
        
        # Add time based on recipe complexity
        ingredient_time = len(recipe.ingredients) * 5  # 5 min per ingredient
        processing_time = len(recipe.processing_steps) * 15  # 15 min per step
        
        # Scale based on batch size (larger batches take longer)
        size_factor = max(1.0, recipe.target_batch_size / 1000)  # Base on 1kg batches
        
        total_duration = int((base_duration + ingredient_time + processing_time) * size_factor)
        
        return total_duration
    
    def _determine_required_equipment(self, recipe: Recipe) -> List[str]:
        """Determine required equipment types for a recipe."""
        required = ["mixer"]  # All recipes need mixing
        
        # Analyze recipe requirements
        for step in recipe.processing_steps:
            step_type = step.get('type', '').lower()
            if 'heat' in step_type:
                required.append("heater")
            elif 'cool' in step_type:
                required.append("cooler")
            elif 'homogenize' in step_type:
                required.append("homogenizer")
            elif 'filter' in step_type:
                required.append("filter")
        
        return list(set(required))  # Remove duplicates
    
    def _extract_material_requirements(self, recipe: Recipe) -> Dict[str, float]:
        """Extract material requirements from recipe."""
        materials = {}
        
        for ingredient in recipe.ingredients:
            name = ingredient.get('name', '')
            quantity = ingredient.get('quantity', 0)
            materials[name] = quantity
        
        return materials
    
    def _schedule_task(self, task_id: str) -> bool:
        """Attempt to schedule a specific task."""
        if task_id not in self.scheduled_tasks:
            return False
        
        task = self.scheduled_tasks[task_id]
        
        # Check material availability
        if not self._check_material_availability(task.required_materials):
            return False
        
        # Find available equipment
        equipment_assignment = self._find_equipment_assignment(task)
        if not equipment_assignment:
            return False
        
        # Find optimal time slot
        time_slot = self._find_optimal_time_slot(task, equipment_assignment)
        if not time_slot:
            return False
        
        # Make the assignment
        task.assigned_equipment = equipment_assignment
        task.scheduled_start = time_slot['start']
        task.scheduled_end = time_slot['end']
        task.status = "scheduled"
        
        # Reserve equipment
        self._reserve_equipment(equipment_assignment, time_slot)
        
        # Reserve materials
        self._reserve_materials(task.required_materials)
        
        return True
    
    def _check_material_availability(self, required_materials: Dict[str, float]) -> bool:
        """Check if required materials are available."""
        for material, required in required_materials.items():
            available = self.material_inventory.get(material, 0)
            if available < required:
                return False
        return True
    
    def _find_equipment_assignment(self, task: ScheduledTask) -> List[str]:
        """Find suitable equipment assignment for a task."""
        assignment = []
        
        for required_type in task.required_equipment:
            suitable_equipment = [
                eq_id for eq_id, eq in self.equipment.items()
                if eq.type == required_type and eq.status == EquipmentStatus.IDLE
            ]
            
            if not suitable_equipment:
                return []  # Cannot fulfill requirement
            
            # Select best equipment (could be optimized with more criteria)
            selected = suitable_equipment[0]
            assignment.append(selected)
        
        return assignment
    
    def _find_optimal_time_slot(self, task: ScheduledTask, equipment_list: List[str]) -> Optional[Dict]:
        """Find optimal time slot for task execution."""
        start_time = max(task.earliest_start, datetime.utcnow())
        duration = timedelta(minutes=task.estimated_duration)
        
        # Simple scheduling: find next available slot for all equipment
        for days_offset in range(self.scheduling_horizon_days):
            candidate_start = start_time + timedelta(days=days_offset)
            candidate_end = candidate_start + duration
            
            # Check if all equipment is available during this slot
            if self._is_time_slot_available(equipment_list, candidate_start, candidate_end):
                return {
                    'start': candidate_start,
                    'end': candidate_end
                }
        
        return None
    
    def _is_time_slot_available(self, equipment_list: List[str], start: datetime, end: datetime) -> bool:
        """Check if time slot is available for all equipment."""
        for equipment_id in equipment_list:
            calendar = self.equipment_calendar.get(equipment_id, [])
            
            for booking in calendar:
                booking_start = booking['start']
                booking_end = booking['end']
                
                # Check for overlap
                if not (end <= booking_start or start >= booking_end):
                    return False
        
        return True
    
    def _reserve_equipment(self, equipment_list: List[str], time_slot: Dict) -> None:
        """Reserve equipment for the time slot."""
        for equipment_id in equipment_list:
            self.equipment_calendar[equipment_id].append({
                'start': time_slot['start'],
                'end': time_slot['end'],
                'type': 'production',
                'task_id': equipment_id
            })
    
    def _reserve_materials(self, materials: Dict[str, float]) -> None:
        """Reserve materials (reduce available inventory)."""
        for material, quantity in materials.items():
            if material in self.material_inventory:
                self.material_inventory[material] -= quantity
    
    def _trigger_rescheduling(self) -> None:
        """Trigger rescheduling of pending tasks."""
        # Find unscheduled tasks
        unscheduled_tasks = [
            task for task in self.scheduled_tasks.values()
            if task.status == "pending"
        ]
        
        # Attempt to schedule them
        for task in unscheduled_tasks:
            self._schedule_task(task.id)
    
    def get_schedule(self, days_ahead: int = 7) -> Dict[str, List]:
        """Get production schedule for next N days."""
        end_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        schedule = {}
        
        for task in self.scheduled_tasks.values():
            if (task.scheduled_start and 
                task.scheduled_start <= end_date and
                task.status == "scheduled"):
                
                date_key = task.scheduled_start.date().isoformat()
                
                if date_key not in schedule:
                    schedule[date_key] = []
                
                schedule[date_key].append({
                    'task_id': task.id,
                    'batch_id': task.batch_id,
                    'start_time': task.scheduled_start.time().isoformat(),
                    'end_time': task.scheduled_end.time().isoformat(),
                    'duration_minutes': task.estimated_duration,
                    'equipment': task.assigned_equipment,
                    'priority': task.priority.name
                })
        
        return schedule
    
    def get_equipment_utilization(self, days_ahead: int = 7) -> Dict[str, Dict]:
        """Calculate equipment utilization metrics."""
        end_date = datetime.utcnow() + timedelta(days=days_ahead)
        total_minutes = days_ahead * 24 * 60
        
        utilization = {}
        
        for equipment_id, calendar in self.equipment_calendar.items():
            busy_minutes = 0
            
            for booking in calendar:
                if booking['start'] <= end_date:
                    duration = (booking['end'] - booking['start']).total_seconds() / 60
                    busy_minutes += duration
            
            utilization_rate = (busy_minutes / total_minutes) * 100 if total_minutes > 0 else 0
            
            utilization[equipment_id] = {
                'busy_minutes': busy_minutes,
                'total_minutes': total_minutes,
                'utilization_percentage': utilization_rate,
                'equipment_type': self.equipment[equipment_id].type,
                'status': self.equipment[equipment_id].status.value
            }
        
        return utilization
    
    def reschedule_task(self, task_id: str, new_priority: Optional[Priority] = None,
                       new_deadline: Optional[datetime] = None) -> bool:
        """Reschedule an existing task."""
        if task_id not in self.scheduled_tasks:
            return False
        
        task = self.scheduled_tasks[task_id]
        
        # Update task parameters
        if new_priority:
            task.priority = new_priority
        if new_deadline:
            task.deadline = new_deadline
        
        # If task was already scheduled, free up resources
        if task.status == "scheduled":
            self._free_resources(task)
            task.status = "pending"
        
        # Attempt to reschedule
        return self._schedule_task(task_id)
    
    def _free_resources(self, task: ScheduledTask) -> None:
        """Free up resources for a task."""
        # Free equipment reservations
        for equipment_id in task.assigned_equipment:
            calendar = self.equipment_calendar[equipment_id]
            self.equipment_calendar[equipment_id] = [
                booking for booking in calendar
                if booking.get('task_id') != task.id
            ]
        
        # Return materials to inventory
        for material, quantity in task.required_materials.items():
            if material in self.material_inventory:
                self.material_inventory[material] += quantity
    
    def get_resource_constraints(self) -> Dict[str, Any]:
        """Analyze current resource constraints."""
        constraints = {
            'equipment_bottlenecks': [],
            'material_shortages': [],
            'scheduling_conflicts': [],
            'utilization_warnings': []
        }
        
        # Check equipment utilization
        utilization = self.get_equipment_utilization()
        for equipment_id, util_data in utilization.items():
            if util_data['utilization_percentage'] > 90:
                constraints['equipment_bottlenecks'].append({
                    'equipment_id': equipment_id,
                    'utilization': util_data['utilization_percentage'],
                    'type': util_data['equipment_type']
                })
        
        # Check material shortages
        for task in self.scheduled_tasks.values():
            if task.status == "pending":
                for material, required in task.required_materials.items():
                    available = self.material_inventory.get(material, 0)
                    if available < required:
                        constraints['material_shortages'].append({
                            'material': material,
                            'required': required,
                            'available': available,
                            'task_id': task.id
                        })
        
        return constraints