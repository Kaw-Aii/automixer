"""
Basic functionality tests for the Automixer system.
"""

from datetime import datetime

from automixer.core.models import Recipe, Batch, Equipment, EquipmentStatus
from automixer.recipe.manager import RecipeManager
from automixer.quality.monitor import QualityControlMonitor
from automixer.scheduling.scheduler import ResourceScheduler, Priority
from automixer.tracking.tracker import BatchTracker, TraceabilityEvent


def test_recipe_manager_basic():
    """Test basic recipe manager functionality."""
    manager = RecipeManager()
    
    # Create a test recipe
    recipe = Recipe(
        name="Test Cream",
        version="1.0",
        ingredients=[
            {"name": "Water", "quantity": 700.0, "concentration": 70.0},
            {"name": "Glycerin", "quantity": 100.0, "concentration": 10.0}
        ],
        target_batch_size=1000.0,
        quality_targets={"ph": 6.0}
    )
    
    # Add recipe
    recipe_id = manager.add_recipe(recipe)
    assert recipe_id is not None
    
    # Retrieve recipe
    retrieved = manager.get_recipe(recipe_id)
    assert retrieved is not None
    assert retrieved.name == "Test Cream"
    
    # Scale recipe
    scaled = manager.scale_recipe(recipe_id, 2000.0)
    assert scaled is not None
    assert scaled.target_batch_size == 2000.0
    
    print("✅ Recipe Manager tests passed")


def test_quality_monitor_basic():
    """Test basic quality monitoring functionality."""
    monitor = QualityControlMonitor()
    
    # Start monitoring
    batch_id = "test_batch_001"
    targets = {"ph": 6.0, "viscosity": 5000.0}
    
    result = monitor.start_batch_monitoring(batch_id, targets)
    assert result is True
    
    # Record measurements
    result = monitor.record_measurement(batch_id, "ph", 6.1)
    assert result is True
    
    result = monitor.record_measurement(batch_id, "viscosity", 5200.0)
    assert result is True
    
    # Get summary
    summary = monitor.get_batch_quality_summary(batch_id)
    assert summary is not None
    assert summary["batch_id"] == batch_id
    
    print("✅ Quality Monitor tests passed")


def test_resource_scheduler_basic():
    """Test basic resource scheduling functionality."""
    scheduler = ResourceScheduler()
    
    # Add equipment
    equipment = Equipment(
        name="Test Mixer",
        type="mixer",
        capacity=100.0,
        status=EquipmentStatus.IDLE,
        last_maintenance=datetime.utcnow(),
        next_maintenance=datetime.utcnow(),
        location="Test Lab"
    )
    
    equipment_id = scheduler.add_equipment(equipment)
    assert equipment_id is not None
    
    # Update inventory
    scheduler.update_material_inventory({"Water": 1000.0, "Glycerin": 200.0})
    
    # Test scheduling functionality exists
    schedule = scheduler.get_schedule(7)
    assert isinstance(schedule, dict)
    
    utilization = scheduler.get_equipment_utilization(7)
    assert isinstance(utilization, dict)
    
    print("✅ Resource Scheduler tests passed")


def test_batch_tracker_basic():
    """Test basic batch tracking functionality."""
    tracker = BatchTracker()
    
    # Create a test recipe
    recipe = Recipe(
        name="Test Recipe",
        version="1.0",
        ingredients=[{"name": "Water", "quantity": 500.0}],
        target_batch_size=500.0
    )
    
    # Create batch
    batch_id = tracker.create_batch(recipe, 500.0, "test_operator")
    assert batch_id is not None
    
    # Record event
    event_id = tracker.record_event(
        batch_id=batch_id,
        event_type=TraceabilityEvent.PROCESSING_STEP,
        operator="test_operator",
        details={"step": "mixing"}
    )
    assert event_id is not None
    
    # Get traceability
    traceability = tracker.get_batch_traceability(batch_id)
    assert traceability is not None
    assert traceability["batch_info"]["id"] == batch_id
    
    print("✅ Batch Tracker tests passed")


def test_system_integration():
    """Test basic system integration."""
    # Initialize all components
    recipe_manager = RecipeManager()
    quality_monitor = QualityControlMonitor()
    scheduler = ResourceScheduler()
    tracker = BatchTracker()
    
    # Create recipe
    recipe = Recipe(
        name="Integration Test Cream",
        version="1.0",
        ingredients=[
            {"name": "Water", "quantity": 600.0, "concentration": 60.0},
            {"name": "Oil", "quantity": 200.0, "concentration": 20.0}
        ],
        target_batch_size=1000.0,
        quality_targets={"ph": 6.0, "viscosity": 4000.0}
    )
    
    recipe_id = recipe_manager.add_recipe(recipe)
    
    # Create batch
    batch_id = tracker.create_batch(recipe, 1000.0, "integration_test")
    
    # Start quality monitoring
    quality_monitor.start_batch_monitoring(batch_id, recipe.quality_targets)
    
    # Record some measurements
    quality_monitor.record_measurement(batch_id, "ph", 5.9)
    quality_monitor.record_measurement(batch_id, "viscosity", 4100.0)
    
    # Verify integration
    traceability = tracker.get_batch_traceability(batch_id)
    quality_summary = quality_monitor.get_batch_quality_summary(batch_id)
    
    assert traceability is not None
    assert quality_summary is not None
    
    print("✅ System Integration tests passed")


if __name__ == "__main__":
    test_recipe_manager_basic()
    test_quality_monitor_basic()
    test_resource_scheduler_basic()
    test_batch_tracker_basic()
    test_system_integration()
    
    print("")
    print("🎉 All basic tests completed successfully!")
    print("🔬 Automixer Laboratory Automation System validated!")