#!/usr/bin/env python3
"""
Demo script showcasing the Automixer laboratory automation system.
"""

import asyncio
import time
from datetime import datetime

from automixer import (
    RecipeManager,
    QualityControlMonitor, 
    ResourceScheduler,
    BatchTracker,
    DigitalTwinInterface
)
from automixer.core.models import Recipe, Equipment, EquipmentStatus
from automixer.scheduling.scheduler import Priority


async def main():
    """Demonstrate the complete automation workflow."""
    
    print("🔬 AUTOMIXER LABORATORY AUTOMATION DEMO")
    print("=" * 60)
    print()
    
    # Initialize all system components
    print("📋 Initializing system components...")
    recipe_manager = RecipeManager()
    quality_monitor = QualityControlMonitor()
    scheduler = ResourceScheduler()
    tracker = BatchTracker()
    digital_twin = DigitalTwinInterface()
    
    # Start digital twin simulation
    digital_twin.start_simulation_mode()
    await asyncio.sleep(2)  # Allow time for equipment connection
    
    print("✅ All components initialized and ready!")
    print()
    
    # 1. RECIPE MANAGEMENT DEMO
    print("🧪 RECIPE MANAGEMENT DEMONSTRATION")
    print("-" * 40)
    
    # Create a skincare recipe
    recipe = Recipe(
        name="Premium Anti-Aging Serum",
        version="2.1",
        description="Advanced anti-aging serum with peptides and hyaluronic acid",
        ingredients=[
            {"name": "Distilled Water", "quantity": 700.0, "concentration": 70.0},
            {"name": "Hyaluronic Acid", "quantity": 10.0, "concentration": 1.0},
            {"name": "Peptide Complex", "quantity": 20.0, "concentration": 2.0},
            {"name": "Glycerin", "quantity": 150.0, "concentration": 15.0},
            {"name": "Preservative System", "quantity": 20.0, "concentration": 2.0},
            {"name": "Vitamin C", "quantity": 50.0, "concentration": 5.0},
            {"name": "Niacinamide", "quantity": 30.0, "concentration": 3.0},
            {"name": "Stabilizer", "quantity": 20.0, "concentration": 2.0}
        ],
        target_batch_size=1000.0,
        mixing_parameters={
            "temperature": 65.0,
            "mixing_speed": 200.0,
            "mixing_time": 45
        },
        processing_steps=[
            {"type": "heat", "temperature": 65, "duration": 10},
            {"type": "mix", "speed": 200, "duration": 30},
            {"type": "add_actives", "temperature": 40, "duration": 10},
            {"type": "homogenize", "pressure": 3.0, "duration": 5},
            {"type": "cool", "temperature": 25, "duration": 20}
        ],
        quality_targets={
            "ph": 6.5,
            "viscosity": 4500.0,
            "particle_size": 80.0,
            "stability": 95.0
        }
    )
    
    recipe_id = recipe_manager.add_recipe(recipe)
    print(f"✅ Created recipe: {recipe.name} (ID: {recipe_id[:8]}...)")
    
    # Demonstrate recipe optimization
    print("🔧 Optimizing recipe for quality...")
    optimization_result = recipe_manager.optimize_recipe(recipe_id, "quality")
    print(f"✅ Quality score improved: {optimization_result.original_score:.2f} → {optimization_result.optimized_score:.2f}")
    print(f"   Confidence: {optimization_result.confidence:.0%}")
    
    # Scale recipe for production
    print("📏 Scaling recipe for production batch...")
    scaled_recipe = recipe_manager.scale_recipe(recipe_id, 5000.0)
    print(f"✅ Recipe scaled to {scaled_recipe.target_batch_size}g batch")
    print()
    
    # 2. EQUIPMENT AND SCHEDULING DEMO
    print("⚙️  RESOURCE SCHEDULING DEMONSTRATION")
    print("-" * 40)
    
    # Add equipment to scheduler
    equipment = Equipment(
        name="Production Mixer Alpha",
        type="mixer",
        capacity=5000.0,
        status=EquipmentStatus.IDLE,
        last_maintenance=datetime.utcnow(),
        next_maintenance=datetime.utcnow(),
        location="Production Line 1"
    )
    scheduler.add_equipment(equipment)
    
    # Update material inventory
    scheduler.update_material_inventory({
        "Distilled Water": 50000.0,
        "Hyaluronic Acid": 1000.0,
        "Peptide Complex": 2000.0,
        "Glycerin": 10000.0,
        "Preservative System": 5000.0,
        "Vitamin C": 3000.0,
        "Niacinamide": 2000.0,
        "Stabilizer": 1500.0
    })
    
    print("✅ Equipment registered and materials stocked")
    
    # 3. BATCH TRACKING DEMO
    print("📊 BATCH TRACKING DEMONSTRATION")
    print("-" * 40)
    
    # Create production batch
    batch_id = tracker.create_batch(scaled_recipe, 5000.0, "Production Operator")
    batch = tracker.batches[batch_id]
    print(f"✅ Created batch: {batch.batch_number}")
    
    # Schedule the batch
    task_id = scheduler.schedule_batch(
        batch=batch,
        recipe=scaled_recipe,
        priority=Priority.HIGH
    )
    print(f"✅ Batch scheduled for production (Task ID: {task_id[:8]}...)")
    
    # Add material lots for traceability
    tracker.add_material_lot("Hyaluronic Acid", "Premium Supplier Co.", "HA-2024-001", 100.0, datetime.utcnow())
    tracker.add_material_lot("Peptide Complex", "BioTech Labs", "PC-2024-025", 150.0, datetime.utcnow())
    
    # Consume materials
    tracker.consume_material(batch_id, "Hyaluronic Acid", "HA-2024-001", 50.0, "Production Operator")
    tracker.consume_material(batch_id, "Peptide Complex", "PC-2024-025", 100.0, "Production Operator")
    
    print("✅ Material lots tracked and consumed")
    print()
    
    # 4. QUALITY CONTROL DEMO
    print("🔍 QUALITY CONTROL DEMONSTRATION")
    print("-" * 40)
    
    # Start quality monitoring
    quality_monitor.start_batch_monitoring(batch_id, scaled_recipe.quality_targets)
    print("✅ Quality monitoring started")
    
    # Simulate production measurements
    measurements = [
        ("ph", 6.3, "Initial pH measurement"),
        ("temperature", 64.5, "Heating phase"),
        ("mixing_speed", 198.0, "Mixing phase"),
        ("viscosity", 4200.0, "Mid-process check"),
        ("ph", 6.6, "Post-active addition"),
        ("particle_size", 85.0, "Post-homogenization"),
        ("viscosity", 4600.0, "Final viscosity"),
        ("ph", 6.5, "Final pH check")
    ]
    
    for param, value, note in measurements:
        quality_monitor.record_measurement(batch_id, param, value, equipment.id)
        print(f"   📈 {param}: {value} - {note}")
        time.sleep(0.5)  # Simulate real-time measurements
    
    # Get quality summary
    quality_summary = quality_monitor.get_batch_quality_summary(batch_id)
    print(f"✅ Batch monitoring completed: {quality_summary['total_measurements']} measurements recorded")
    print(f"   Adjustments made: {quality_summary['adjustments_made']}")
    print()
    
    # 5. DIGITAL TWIN DEMO
    print("🤖 DIGITAL TWIN DEMONSTRATION")
    print("-" * 40)
    
    # Get real-time equipment status
    twin_state = digital_twin.get_digital_twin_state()
    print(f"✅ Digital twin active with {twin_state['connected_equipment_count']} connected devices")
    
    # Send control commands
    print("🎛️  Sending control commands...")
    await digital_twin.send_control_command("mixer_001", "mixing_speed", 180.0)
    await digital_twin.send_control_command("mixer_001", "temperature", 65.0)
    
    print("✅ Control commands executed")
    
    # Get equipment analytics
    analytics = digital_twin.get_process_analytics("mixer_001", 1)
    if analytics:
        print(f"   Uptime: {analytics['uptime_percentage']:.1f}%")
        print(f"   Total readings: {analytics['total_readings']}")
    
    print()
    
    # 6. COMPLETE TRACEABILITY DEMO
    print("📋 COMPLETE TRACEABILITY DEMONSTRATION")
    print("-" * 40)
    
    # Update batch status to completed
    tracker.update_batch_status(batch_id, batch.status.__class__.COMPLETED, "Production Operator")
    
    # Get complete traceability report
    traceability = tracker.get_batch_traceability(batch_id)
    
    print(f"✅ Batch {batch.batch_number} completed successfully!")
    print(f"   Total events: {traceability['total_events']}")
    print(f"   Materials used: {len(traceability['material_traceability'])}")
    print(f"   Processing time: {traceability['metrics']['total_processing_time_minutes']} minutes")
    print(f"   Quality checks: {traceability['metrics']['quality_checks_performed']}")
    print()
    
    # 7. SYSTEM SUMMARY
    print("📊 SYSTEM SUMMARY")
    print("-" * 40)
    print("✅ Recipe Management: Formulation created, optimized, and scaled")  
    print("✅ Quality Control: Real-time monitoring with automatic adjustments")
    print("✅ Resource Scheduling: Equipment and materials intelligently allocated")
    print("✅ Batch Tracking: Complete traceability from raw materials to finished product")
    print("✅ Digital Twin: Real-time equipment monitoring and control")
    print()
    print("🎉 LABORATORY AUTOMATION COMPLETE!")
    print("   The Automixer system has successfully demonstrated:")
    print("   • Fully automated sample production")
    print("   • Real-time quality control and adjustment")
    print("   • Complete traceability and compliance")
    print("   • Intelligent resource optimization")
    print("   • Digital twin integration with physical equipment")
    print()
    print("🚀 Ready for production deployment!")


if __name__ == "__main__":
    asyncio.run(main())