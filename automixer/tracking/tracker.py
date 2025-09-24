"""
Batch Tracking system for complete traceability from raw materials to finished products.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..core.models import Batch, BatchStatus, Ingredient, Recipe, Equipment


class TraceabilityEvent(str, Enum):
    """Types of traceability events."""
    MATERIAL_RECEIVED = "material_received"
    MATERIAL_TESTED = "material_tested"
    BATCH_CREATED = "batch_created"
    INGREDIENT_ADDED = "ingredient_added"
    PROCESSING_STEP = "processing_step"
    QUALITY_CHECK = "quality_check"
    BATCH_COMPLETED = "batch_completed"
    PACKAGING = "packaging"
    SHIPMENT = "shipment"
    RECALL_INITIATED = "recall_initiated"


@dataclass
class TraceabilityRecord:
    """Individual traceability record."""
    id: str
    batch_id: str
    event_type: TraceabilityEvent
    timestamp: datetime
    operator: Optional[str] = None
    equipment_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    environmental_conditions: Dict[str, float] = field(default_factory=dict)
    parent_batch_ids: List[str] = field(default_factory=list)
    child_batch_ids: List[str] = field(default_factory=list)


@dataclass
class MaterialLot:
    """Material lot tracking information."""
    lot_id: str
    material_name: str
    supplier: str
    received_date: datetime
    expiration_date: datetime
    quantity_received: float
    quantity_remaining: float
    certificates: List[str] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    storage_conditions: Dict[str, Any] = field(default_factory=dict)
    blocked: bool = False
    block_reason: Optional[str] = None


class BatchTracker:
    """
    Complete batch tracking system for manufacturing traceability.
    
    Features:
    - End-to-end traceability from raw materials to finished products
    - Real-time tracking of processing steps
    - Material genealogy tracking
    - Quality event correlation
    - Regulatory compliance reporting
    - Recall management
    """
    
    def __init__(self):
        self.batches: Dict[str, Batch] = {}
        self.traceability_records: Dict[str, List[TraceabilityRecord]] = {}
        self.material_lots: Dict[str, MaterialLot] = {}
        self.batch_genealogy: Dict[str, Dict] = {}  # Parent-child relationships
        self.location_tracking: Dict[str, str] = {}  # batch_id -> current location
    
    def create_batch(self, recipe: Recipe, target_quantity: float,
                    operator: str, batch_number: Optional[str] = None) -> str:
        """Create a new batch and initialize tracking."""
        
        if not batch_number:
            batch_number = self._generate_batch_number()
        
        batch = Batch(
            recipe_id=recipe.id,
            batch_number=batch_number,
            target_quantity=target_quantity,
            status=BatchStatus.PENDING
        )
        
        self.batches[batch.id] = batch
        self.traceability_records[batch.id] = []
        
        # Record batch creation event
        self.record_event(
            batch_id=batch.id,
            event_type=TraceabilityEvent.BATCH_CREATED,
            operator=operator,
            details={
                'recipe_id': recipe.id,
                'recipe_name': recipe.name,
                'recipe_version': recipe.version,
                'target_quantity': target_quantity,
                'batch_number': batch_number
            }
        )
        
        # Initialize batch genealogy
        self.batch_genealogy[batch.id] = {
            'parents': [],
            'children': [],
            'raw_materials': []
        }
        
        return batch.id
    
    def _generate_batch_number(self) -> str:
        """Generate a unique batch number."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        sequence = len(self.batches) + 1
        return f"BT{timestamp}{sequence:04d}"
    
    def record_event(self, batch_id: str, event_type: TraceabilityEvent,
                    operator: Optional[str] = None, equipment_id: Optional[str] = None,
                    details: Optional[Dict[str, Any]] = None,
                    environmental_conditions: Optional[Dict[str, float]] = None) -> str:
        """Record a traceability event."""
        
        if batch_id not in self.traceability_records:
            self.traceability_records[batch_id] = []
        
        record = TraceabilityRecord(
            id=f"trace_{batch_id}_{len(self.traceability_records[batch_id]) + 1}",
            batch_id=batch_id,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            operator=operator,
            equipment_id=equipment_id,
            details=details or {},
            environmental_conditions=environmental_conditions or {}
        )
        
        self.traceability_records[batch_id].append(record)
        
        # Update batch processing log
        if batch_id in self.batches:
            self.batches[batch_id].processing_log.append({
                'timestamp': record.timestamp.isoformat(),
                'event': event_type.value,
                'details': record.details
            })
        
        return record.id
    
    def add_material_lot(self, material_name: str, supplier: str, lot_id: str,
                        quantity: float, expiration_date: datetime,
                        certificates: Optional[List[str]] = None) -> str:
        """Add a new material lot to tracking."""
        
        lot = MaterialLot(
            lot_id=lot_id,
            material_name=material_name,
            supplier=supplier,
            received_date=datetime.utcnow(),
            expiration_date=expiration_date,
            quantity_received=quantity,
            quantity_remaining=quantity,
            certificates=certificates or []
        )
        
        self.material_lots[lot_id] = lot
        return lot_id
    
    def consume_material(self, batch_id: str, material_name: str, lot_id: str,
                        quantity: float, operator: str,
                        equipment_id: Optional[str] = None) -> bool:
        """Record material consumption for a batch."""
        
        if lot_id not in self.material_lots:
            return False
        
        lot = self.material_lots[lot_id]
        
        if lot.quantity_remaining < quantity:
            return False
        
        if lot.blocked:
            return False
        
        # Consume material
        lot.quantity_remaining -= quantity
        
        # Record traceability event
        self.record_event(
            batch_id=batch_id,
            event_type=TraceabilityEvent.INGREDIENT_ADDED,
            operator=operator,
            equipment_id=equipment_id,
            details={
                'material_name': material_name,
                'lot_id': lot_id,
                'supplier': lot.supplier,
                'quantity_used': quantity,
                'remaining_quantity': lot.quantity_remaining,
                'expiration_date': lot.expiration_date.isoformat()
            }
        )
        
        # Update batch genealogy
        if batch_id in self.batch_genealogy:
            self.batch_genealogy[batch_id]['raw_materials'].append({
                'lot_id': lot_id,
                'material_name': material_name,
                'supplier': lot.supplier,
                'quantity_used': quantity
            })
        
        return True
    
    def record_processing_step(self, batch_id: str, step_name: str, 
                             parameters: Dict[str, Any], operator: str,
                             equipment_id: str, duration_minutes: int) -> str:
        """Record a processing step."""
        
        return self.record_event(
            batch_id=batch_id,
            event_type=TraceabilityEvent.PROCESSING_STEP,
            operator=operator,
            equipment_id=equipment_id,
            details={
                'step_name': step_name,
                'parameters': parameters,
                'duration_minutes': duration_minutes,
                'step_start': (datetime.utcnow().timestamp() - duration_minutes * 60),
                'step_end': datetime.utcnow().timestamp()
            }
        )
    
    def update_batch_status(self, batch_id: str, new_status: BatchStatus,
                          operator: str, notes: Optional[str] = None) -> bool:
        """Update batch status with traceability."""
        
        if batch_id not in self.batches:
            return False
        
        old_status = self.batches[batch_id].status
        self.batches[batch_id].status = new_status
        
        # Record status change
        self.record_event(
            batch_id=batch_id,
            event_type=TraceabilityEvent.PROCESSING_STEP,
            operator=operator,
            details={
                'status_change': {
                    'from': old_status.value,
                    'to': new_status.value
                },
                'notes': notes
            }
        )
        
        # Update timestamps
        if new_status == BatchStatus.IN_PROGRESS and not self.batches[batch_id].start_time:
            self.batches[batch_id].start_time = datetime.utcnow()
        elif new_status == BatchStatus.COMPLETED:
            self.batches[batch_id].end_time = datetime.utcnow()
            
            # Record completion event
            self.record_event(
                batch_id=batch_id,
                event_type=TraceabilityEvent.BATCH_COMPLETED,
                operator=operator,
                details={
                    'completion_time': datetime.utcnow().isoformat(),
                    'total_duration_minutes': self._calculate_batch_duration(batch_id)
                }
            )
        
        return True
    
    def _calculate_batch_duration(self, batch_id: str) -> Optional[int]:
        """Calculate total batch processing duration."""
        batch = self.batches.get(batch_id)
        if not batch or not batch.start_time or not batch.end_time:
            return None
        
        duration = batch.end_time - batch.start_time
        return int(duration.total_seconds() / 60)
    
    def track_location(self, batch_id: str, location: str, operator: str) -> bool:
        """Track batch location movement."""
        
        self.location_tracking[batch_id] = location
        
        self.record_event(
            batch_id=batch_id,
            event_type=TraceabilityEvent.PROCESSING_STEP,
            operator=operator,
            details={
                'location_change': location,
                'previous_location': self.location_tracking.get(batch_id, 'Unknown')
            }
        )
        
        return True
    
    def get_batch_traceability(self, batch_id: str) -> Dict[str, Any]:
        """Get complete traceability information for a batch."""
        
        if batch_id not in self.batches:
            return {}
        
        batch = self.batches[batch_id]
        records = self.traceability_records.get(batch_id, [])
        genealogy = self.batch_genealogy.get(batch_id, {})
        
        # Organize records by event type
        events_by_type = {}
        for record in records:
            event_type = record.event_type.value
            if event_type not in events_by_type:
                events_by_type[event_type] = []
            
            events_by_type[event_type].append({
                'timestamp': record.timestamp.isoformat(),
                'operator': record.operator,
                'equipment_id': record.equipment_id,
                'details': record.details,
                'environmental_conditions': record.environmental_conditions
            })
        
        # Get material traceability
        material_traceability = self._get_material_traceability(batch_id)
        
        # Calculate batch metrics
        metrics = self._calculate_batch_metrics(batch_id)
        
        return {
            'batch_info': {
                'id': batch.id,
                'batch_number': batch.batch_number,
                'recipe_id': batch.recipe_id,
                'status': batch.status.value,
                'target_quantity': batch.target_quantity,
                'actual_quantity': batch.actual_quantity,
                'start_time': batch.start_time.isoformat() if batch.start_time else None,
                'end_time': batch.end_time.isoformat() if batch.end_time else None,
                'current_location': self.location_tracking.get(batch_id, 'Unknown')
            },
            'events_by_type': events_by_type,
            'material_traceability': material_traceability,
            'genealogy': genealogy,
            'metrics': metrics,
            'total_events': len(records)
        }
    
    def _get_material_traceability(self, batch_id: str) -> List[Dict]:
        """Get material traceability for a batch."""
        genealogy = self.batch_genealogy.get(batch_id, {})
        material_info = []
        
        for material in genealogy.get('raw_materials', []):
            lot_id = material['lot_id']
            lot = self.material_lots.get(lot_id)
            
            if lot:
                material_info.append({
                    'lot_id': lot_id,
                    'material_name': material['material_name'],
                    'supplier': material['supplier'],
                    'quantity_used': material['quantity_used'],
                    'received_date': lot.received_date.isoformat(),
                    'expiration_date': lot.expiration_date.isoformat(),
                    'certificates': lot.certificates,
                    'test_results': lot.test_results,
                    'blocked': lot.blocked
                })
        
        return material_info
    
    def _calculate_batch_metrics(self, batch_id: str) -> Dict[str, Any]:
        """Calculate batch processing metrics."""
        batch = self.batches.get(batch_id)
        if not batch:
            return {}
        
        records = self.traceability_records.get(batch_id, [])
        
        metrics = {
            'total_processing_time_minutes': self._calculate_batch_duration(batch_id),
            'number_of_processing_steps': len([r for r in records if r.event_type == TraceabilityEvent.PROCESSING_STEP]),
            'quality_checks_performed': len([r for r in records if r.event_type == TraceabilityEvent.QUALITY_CHECK]),
            'operators_involved': len(set(r.operator for r in records if r.operator)),
            'equipment_used': len(set(r.equipment_id for r in records if r.equipment_id)),
            'yield_percentage': (batch.actual_quantity / batch.target_quantity * 100) if batch.actual_quantity and batch.target_quantity else None
        }
        
        return metrics
    
    def search_batches_by_material(self, material_name: str, lot_id: Optional[str] = None) -> List[str]:
        """Find all batches that used a specific material or lot."""
        matching_batches = []
        
        for batch_id, genealogy in self.batch_genealogy.items():
            for material in genealogy.get('raw_materials', []):
                if material['material_name'] == material_name:
                    if lot_id is None or material['lot_id'] == lot_id:
                        matching_batches.append(batch_id)
                        break
        
        return matching_batches
    
    def search_batches_by_equipment(self, equipment_id: str) -> List[str]:
        """Find all batches that used specific equipment."""
        matching_batches = []
        
        for batch_id, records in self.traceability_records.items():
            for record in records:
                if record.equipment_id == equipment_id:
                    matching_batches.append(batch_id)
                    break
        
        return matching_batches
    
    def initiate_recall(self, criteria: Dict[str, Any], reason: str,
                       operator: str) -> Dict[str, Any]:
        """Initiate a product recall based on criteria."""
        
        affected_batches = []
        
        # Search based on different criteria
        if 'material_lot' in criteria:
            lot_id = criteria['material_lot']
            affected_batches.extend(self.search_batches_by_material(None, lot_id))
        
        if 'material_name' in criteria:
            material_name = criteria['material_name']
            affected_batches.extend(self.search_batches_by_material(material_name))
        
        if 'equipment_id' in criteria:
            equipment_id = criteria['equipment_id']
            affected_batches.extend(self.search_batches_by_equipment(equipment_id))
        
        if 'date_range' in criteria:
            start_date = datetime.fromisoformat(criteria['date_range']['start'])
            end_date = datetime.fromisoformat(criteria['date_range']['end'])
            
            for batch_id, batch in self.batches.items():
                if batch.start_time and start_date <= batch.start_time <= end_date:
                    affected_batches.append(batch_id)
        
        # Remove duplicates
        affected_batches = list(set(affected_batches))
        
        # Record recall events
        recall_id = f"recall_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        for batch_id in affected_batches:
            self.record_event(
                batch_id=batch_id,
                event_type=TraceabilityEvent.RECALL_INITIATED,
                operator=operator,
                details={
                    'recall_id': recall_id,
                    'reason': reason,
                    'criteria': criteria,
                    'initiated_by': operator
                }
            )
        
        recall_info = {
            'recall_id': recall_id,
            'initiated_at': datetime.utcnow().isoformat(),
            'reason': reason,
            'criteria': criteria,
            'affected_batches': affected_batches,
            'batch_count': len(affected_batches),
            'initiated_by': operator
        }
        
        return recall_info
    
    def generate_regulatory_report(self, batch_id: str, report_type: str = "complete") -> Dict[str, Any]:
        """Generate regulatory compliance report for a batch."""
        
        traceability_data = self.get_batch_traceability(batch_id)
        
        if report_type == "materials":
            return {
                'batch_id': batch_id,
                'report_type': 'Material Traceability Report',
                'generated_at': datetime.utcnow().isoformat(),
                'material_traceability': traceability_data.get('material_traceability', [])
            }
        
        elif report_type == "processing":
            return {
                'batch_id': batch_id,
                'report_type': 'Processing History Report',
                'generated_at': datetime.utcnow().isoformat(),
                'processing_steps': traceability_data.get('events_by_type', {}).get('processing_step', []),
                'quality_checks': traceability_data.get('events_by_type', {}).get('quality_check', [])
            }
        
        else:  # complete report
            return {
                'batch_id': batch_id,
                'report_type': 'Complete Traceability Report',
                'generated_at': datetime.utcnow().isoformat(),
                'complete_traceability': traceability_data
            }