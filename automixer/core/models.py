"""
Core data models for the Automixer system.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import uuid


class EquipmentStatus(str, Enum):
    """Equipment status enumeration."""
    IDLE = "idle"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class BatchStatus(str, Enum):
    """Batch processing status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QualityStatus(str, Enum):
    """Quality control status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    REQUIRES_ADJUSTMENT = "requires_adjustment"


class Ingredient(BaseModel):
    """Model for skincare ingredients."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    supplier: str
    batch_number: str
    expiration_date: datetime
    concentration_range: Dict[str, float] = Field(description="Min/max concentration percentages")
    properties: Dict[str, Any] = Field(default_factory=dict)
    safety_data: Dict[str, Any] = Field(default_factory=dict)
    cost_per_gram: float


class Recipe(BaseModel):
    """Model for skincare formulation recipes."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    version: str
    description: Optional[str] = None
    ingredients: List[Dict[str, Any]] = Field(description="List of ingredients with quantities")
    target_batch_size: float = Field(description="Target batch size in grams")
    mixing_parameters: Dict[str, Any] = Field(default_factory=dict)
    processing_steps: List[Dict[str, Any]] = Field(default_factory=list)
    quality_targets: Dict[str, float] = Field(default_factory=dict)
    optimization_score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Equipment(BaseModel):
    """Model for manufacturing equipment."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str
    capacity: float
    status: EquipmentStatus = EquipmentStatus.IDLE
    current_batch_id: Optional[str] = None
    last_maintenance: datetime
    next_maintenance: datetime
    calibration_data: Dict[str, Any] = Field(default_factory=dict)
    sensors: List[Dict[str, Any]] = Field(default_factory=list)
    location: str


class Batch(BaseModel):
    """Model for production batches."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    recipe_id: str
    batch_number: str
    status: BatchStatus = BatchStatus.PENDING
    target_quantity: float
    actual_quantity: Optional[float] = None
    assigned_equipment: List[str] = Field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    quality_results: Dict[str, Any] = Field(default_factory=dict)
    processing_log: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QualityCheck(BaseModel):
    """Model for quality control checks."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    batch_id: str
    test_type: str
    status: QualityStatus = QualityStatus.PENDING
    target_values: Dict[str, float]
    measured_values: Dict[str, float] = Field(default_factory=dict)
    tolerance: Dict[str, float] = Field(default_factory=dict)
    test_method: str
    operator: Optional[str] = None
    equipment_used: Optional[str] = None
    test_date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class DigitalTwinState(BaseModel):
    """Model for digital twin state representation."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    equipment_states: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    process_parameters: Dict[str, Any] = Field(default_factory=dict)
    environmental_conditions: Dict[str, float] = Field(default_factory=dict)
    active_batches: List[str] = Field(default_factory=list)
    alerts: List[Dict[str, Any]] = Field(default_factory=list)


class OptimizationResult(BaseModel):
    """Model for recipe optimization results."""
    recipe_id: str
    optimization_type: str
    original_score: float
    optimized_score: float
    parameter_changes: Dict[str, Any]
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    validation_required: bool = True