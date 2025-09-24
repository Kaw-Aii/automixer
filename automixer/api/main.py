"""
FastAPI application for the Automixer system.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..core.models import Recipe, Ingredient, Batch, Equipment, EquipmentStatus
from ..recipe.manager import RecipeManager
from ..quality.monitor import QualityControlMonitor
from ..scheduling.scheduler import ResourceScheduler, Priority
from ..tracking.tracker import BatchTracker
from ..digital_twin.interface import DigitalTwinInterface


# Pydantic models for API requests/responses
class RecipeCreate(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    ingredients: List[Dict[str, Any]]
    target_batch_size: float
    mixing_parameters: Dict[str, Any] = {}
    processing_steps: List[Dict[str, Any]] = []
    quality_targets: Dict[str, float] = {}


class BatchCreate(BaseModel):
    recipe_id: str
    target_quantity: float
    priority: str = "normal"
    deadline: Optional[datetime] = None


class QualityMeasurement(BaseModel):
    batch_id: str
    parameter: str
    value: float
    equipment_id: Optional[str] = None


# Initialize FastAPI app
app = FastAPI(
    title="Automixer API",
    description="AI-Driven Digital Twin for Skincare Manufacturing Optimization",
    version="0.1.0"
)

# Initialize system components
recipe_manager = RecipeManager()
quality_monitor = QualityControlMonitor()
resource_scheduler = ResourceScheduler()
batch_tracker = BatchTracker()
digital_twin = DigitalTwinInterface()


@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup."""
    # Start digital twin in simulation mode for demo
    digital_twin.start_simulation_mode()
    
    # Add some sample equipment
    sample_equipment = [
        Equipment(
            name="Industrial Mixer 1",
            type="mixer",
            capacity=100.0,
            status=EquipmentStatus.IDLE,
            last_maintenance=datetime.utcnow(),
            next_maintenance=datetime.utcnow(),
            location="Production Line A"
        ),
        Equipment(
            name="Homogenizer 1", 
            type="homogenizer",
            capacity=50.0,
            status=EquipmentStatus.IDLE,
            last_maintenance=datetime.utcnow(),
            next_maintenance=datetime.utcnow(),
            location="Production Line A"
        )
    ]
    
    for equipment in sample_equipment:
        resource_scheduler.add_equipment(equipment)


# Recipe Management Endpoints
@app.post("/recipes", response_model=Dict[str, str])
async def create_recipe(recipe_data: RecipeCreate):
    """Create a new recipe."""
    recipe = Recipe(**recipe_data.dict())
    recipe_id = recipe_manager.add_recipe(recipe)
    return {"recipe_id": recipe_id, "status": "created"}


@app.get("/recipes/{recipe_id}")
async def get_recipe(recipe_id: str):
    """Get a recipe by ID."""
    recipe = recipe_manager.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@app.get("/recipes/{recipe_id}/analytics")
async def get_recipe_analytics(recipe_id: str):
    """Get comprehensive analytics for a recipe."""
    analytics = recipe_manager.get_recipe_analytics(recipe_id)
    if not analytics:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return analytics


@app.post("/recipes/{recipe_id}/optimize")
async def optimize_recipe(recipe_id: str, optimization_target: str = "quality"):
    """Optimize a recipe."""
    try:
        result = recipe_manager.optimize_recipe(recipe_id, optimization_target)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/recipes/{recipe_id}/scale")
async def scale_recipe(recipe_id: str, target_batch_size: float):
    """Scale a recipe to target batch size."""
    scaled_recipe = recipe_manager.scale_recipe(recipe_id, target_batch_size)
    if not scaled_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return scaled_recipe


# Batch Management Endpoints
@app.post("/batches", response_model=Dict[str, str])
async def create_batch(batch_data: BatchCreate):
    """Create a new production batch."""
    recipe = recipe_manager.get_recipe(batch_data.recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Create batch tracking
    batch_id = batch_tracker.create_batch(
        recipe=recipe,
        target_quantity=batch_data.target_quantity,
        operator="api_user"
    )
    
    # Schedule batch
    batch = batch_tracker.batches[batch_id]
    priority_map = {"low": Priority.LOW, "normal": Priority.NORMAL, 
                   "high": Priority.HIGH, "urgent": Priority.URGENT}
    priority = priority_map.get(batch_data.priority.lower(), Priority.NORMAL)
    
    task_id = resource_scheduler.schedule_batch(
        batch=batch,
        recipe=recipe,
        priority=priority,
        deadline=batch_data.deadline
    )
    
    return {"batch_id": batch_id, "task_id": task_id, "status": "created"}


@app.get("/batches/{batch_id}/traceability")
async def get_batch_traceability(batch_id: str):
    """Get complete traceability information for a batch."""
    traceability = batch_tracker.get_batch_traceability(batch_id)
    if not traceability:
        raise HTTPException(status_code=404, detail="Batch not found")
    return traceability


@app.post("/batches/{batch_id}/start")
async def start_batch(batch_id: str):
    """Start batch production."""
    success = batch_tracker.update_batch_status(
        batch_id=batch_id,
        new_status=batch_tracker.batches[batch_id].status.__class__.IN_PROGRESS,
        operator="api_user"
    )
    
    if success:
        # Start quality monitoring
        recipe = recipe_manager.get_recipe(batch_tracker.batches[batch_id].recipe_id)
        quality_monitor.start_batch_monitoring(batch_id, recipe.quality_targets)
        
        return {"status": "started", "batch_id": batch_id}
    else:
        raise HTTPException(status_code=404, detail="Batch not found")


# Quality Control Endpoints
@app.post("/quality/measurements")
async def record_measurement(measurement: QualityMeasurement):
    """Record a quality measurement."""
    success = quality_monitor.record_measurement(
        batch_id=measurement.batch_id,
        parameter=measurement.parameter,
        value=measurement.value,
        equipment_id=measurement.equipment_id
    )
    
    if success:
        return {"status": "recorded", "timestamp": datetime.utcnow().isoformat()}
    else:
        raise HTTPException(status_code=400, detail="Failed to record measurement")


@app.get("/quality/batches/{batch_id}/summary")
async def get_quality_summary(batch_id: str):
    """Get quality summary for a batch."""
    summary = quality_monitor.get_batch_quality_summary(batch_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Batch monitoring not found")
    return summary


@app.get("/quality/trends/{parameter}")
async def get_quality_trends(parameter: str, days: int = 7):
    """Get quality trends for a parameter."""
    trends = quality_monitor.get_trend_analysis(parameter, days)
    return trends


# Scheduling Endpoints
@app.get("/schedule")
async def get_production_schedule(days_ahead: int = 7):
    """Get production schedule."""
    schedule = resource_scheduler.get_schedule(days_ahead)
    return {"schedule": schedule, "days_ahead": days_ahead}


@app.get("/resources/utilization")
async def get_resource_utilization(days_ahead: int = 7):
    """Get equipment utilization metrics."""
    utilization = resource_scheduler.get_equipment_utilization(days_ahead)
    return {"utilization": utilization, "analysis_period_days": days_ahead}


@app.get("/resources/constraints")
async def get_resource_constraints():
    """Get current resource constraints and bottlenecks."""
    constraints = resource_scheduler.get_resource_constraints()
    return constraints


# Digital Twin Endpoints
@app.get("/digital-twin/state")
async def get_digital_twin_state():
    """Get current digital twin state."""
    state = digital_twin.get_digital_twin_state()
    return state


@app.get("/equipment/{equipment_id}/status")
async def get_equipment_status(equipment_id: str):
    """Get equipment status."""
    status = digital_twin.get_equipment_status(equipment_id)
    if not status:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return status


@app.post("/equipment/{equipment_id}/control")
async def send_control_command(equipment_id: str, parameter: str, target_value: float):
    """Send control command to equipment."""
    try:
        command_id = await digital_twin.send_control_command(
            equipment_id=equipment_id,
            parameter=parameter,
            target_value=target_value
        )
        return {"command_id": command_id, "status": "sent"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/equipment/{equipment_id}/analytics")
async def get_equipment_analytics(equipment_id: str, hours: int = 24):
    """Get process analytics for equipment."""
    analytics = digital_twin.get_process_analytics(equipment_id, hours)
    if not analytics:
        raise HTTPException(status_code=404, detail="Equipment not found or no data")
    return analytics


# System Status Endpoints
@app.get("/system/status")
async def get_system_status():
    """Get overall system status."""
    return {
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "recipe_manager": "active",
            "quality_monitor": "active", 
            "resource_scheduler": "active",
            "batch_tracker": "active",
            "digital_twin": "active"
        },
        "statistics": {
            "total_recipes": len(recipe_manager.recipes),
            "active_batches": len([b for b in batch_tracker.batches.values() 
                                 if b.status.name == "IN_PROGRESS"]),
            "connected_equipment": len(digital_twin.connected_equipment),
            "pending_tasks": len(resource_scheduler.task_queue)
        }
    }


@app.get("/system/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Demo/Test Endpoints
@app.post("/demo/create-sample-recipe")
async def create_sample_recipe():
    """Create a sample skincare recipe for testing."""
    sample_recipe = Recipe(
        name="Hydrating Face Cream",
        version="1.0",
        description="A moisturizing face cream with hyaluronic acid",
        ingredients=[
            {"name": "Water", "quantity": 650.0, "concentration": 65.0},
            {"name": "Glycerin", "quantity": 100.0, "concentration": 10.0},
            {"name": "Hyaluronic Acid", "quantity": 5.0, "concentration": 0.5},
            {"name": "Cetyl Alcohol", "quantity": 50.0, "concentration": 5.0},
            {"name": "Stearic Acid", "quantity": 30.0, "concentration": 3.0},
            {"name": "Preservative", "quantity": 10.0, "concentration": 1.0}
        ],
        target_batch_size=1000.0,
        mixing_parameters={
            "temperature": 70.0,
            "mixing_speed": 150.0,
            "mixing_time": 30
        },
        processing_steps=[
            {"type": "heat", "temperature": 70, "duration": 10},
            {"type": "mix", "speed": 150, "duration": 20},
            {"type": "homogenize", "pressure": 2.5, "duration": 5},
            {"type": "cool", "temperature": 25, "duration": 15}
        ],
        quality_targets={
            "ph": 6.0,
            "viscosity": 5000.0,
            "particle_size": 100.0
        }
    )
    
    recipe_id = recipe_manager.add_recipe(sample_recipe)
    return {"recipe_id": recipe_id, "message": "Sample recipe created"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)