"""
Enhanced Digital Twin Interface for Automixer
Integrates with advanced simulation engine and hardware communication
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from ..simulation.advanced_engine import SkincareSimulationEngine
from ..hardware.communication import HardwareDeviceManager
from ..ai_chemist.optimization_system import AIChemistSystem
from ..safety.control_systems import SafetySystemManager
from ..workflows.production import WorkflowEngine


class EnhancedDigitalTwinInterface:
    """
    Enhanced Digital Twin Interface with full automation capabilities
    """
    
    def __init__(self):
        self.simulation_engine = SkincareSimulationEngine()
        self.hardware_manager = HardwareDeviceManager()
        self.ai_chemist = AIChemistSystem()
        self.safety_manager = SafetySystemManager()
        self.workflow_engine = WorkflowEngine()
        self.is_running = False
        self.sync_interval = 1.0  # seconds
        
    async def start_enhanced_mode(self):
        """Start enhanced digital twin with full automation"""
        self.is_running = True
        
        # Initialize all subsystems
        await self.simulation_engine.initialize()
        await self.hardware_manager.initialize()
        await self.ai_chemist.initialize()
        await self.safety_manager.initialize()
        await self.workflow_engine.initialize()
        
        # Start synchronization loop
        asyncio.create_task(self._sync_loop())
        
        print("Enhanced Digital Twin Interface started successfully")
    
    async def _sync_loop(self):
        """Continuous synchronization between digital and physical systems"""
        while self.is_running:
            try:
                # Get physical system state
                physical_state = await self.hardware_manager.get_system_state()
                
                # Update digital twin simulation
                await self.simulation_engine.update_state(physical_state)
                
                # Run AI optimization
                optimization_results = await self.ai_chemist.optimize_processes()
                
                # Apply optimizations if safe
                if await self.safety_manager.validate_changes(optimization_results):
                    await self.hardware_manager.apply_optimizations(optimization_results)
                
                # Execute scheduled workflows
                await self.workflow_engine.execute_pending_workflows()
                
                await asyncio.sleep(self.sync_interval)
                
            except Exception as e:
                print(f"Error in sync loop: {e}")
                await asyncio.sleep(self.sync_interval)
    
    async def execute_recipe(self, recipe_id: str, batch_size: float) -> str:
        """Execute a recipe with full automation"""
        try:
            # Create workflow for recipe execution
            workflow_id = await self.workflow_engine.create_recipe_workflow(
                recipe_id, batch_size
            )
            
            # Start execution
            batch_id = await self.workflow_engine.execute_workflow(workflow_id)
            
            return batch_id
            
        except Exception as e:
            print(f"Error executing recipe: {e}")
            raise
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "simulation_engine": await self.simulation_engine.get_status(),
            "hardware_manager": await self.hardware_manager.get_status(),
            "ai_chemist": await self.ai_chemist.get_status(),
            "safety_manager": await self.safety_manager.get_status(),
            "workflow_engine": await self.workflow_engine.get_status(),
            "is_running": self.is_running
        }
    
    async def emergency_stop(self, reason: str = "Manual emergency stop"):
        """Trigger emergency stop across all systems"""
        await self.safety_manager.emergency_stop(reason)
        await self.hardware_manager.emergency_stop()
        await self.workflow_engine.emergency_stop()
        
        print(f"Emergency stop triggered: {reason}")
    
    async def stop(self):
        """Gracefully stop the enhanced digital twin"""
        self.is_running = False
        
        await self.workflow_engine.shutdown()
        await self.safety_manager.shutdown()
        await self.ai_chemist.shutdown()
        await self.hardware_manager.shutdown()
        await self.simulation_engine.shutdown()
        
        print("Enhanced Digital Twin Interface stopped")


# Maintain backward compatibility
class DigitalTwinInterface(EnhancedDigitalTwinInterface):
    """Backward compatible digital twin interface"""
    
    def __init__(self):
        super().__init__()
        self.simulation_mode = True
    
    def start_simulation_mode(self):
        """Start in simulation mode for backward compatibility"""
        self.simulation_mode = True
        asyncio.create_task(self.start_enhanced_mode())
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state (synchronous for backward compatibility)"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.get_system_status())


# Export both interfaces
__all__ = ["DigitalTwinInterface", "EnhancedDigitalTwinInterface"]
