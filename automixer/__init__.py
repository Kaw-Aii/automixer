"""
Automixer - AI-Driven Digital Twin for Skincare Manufacturing Optimization
Enhanced with advanced simulation, AI optimization, and hardware integration
"""

# Core models and functionality
from .core.models import (
    Recipe, Ingredient, Equipment, Batch, QualityCheck,
    DigitalTwinState, OptimizationResult
)

# Recipe management
from .recipe.manager import RecipeManager

# Quality control
from .quality.monitor import QualityControlMonitor

# Resource scheduling
from .scheduling.scheduler import ResourceScheduler

# Batch tracking
from .tracking.tracker import BatchTracker

# Enhanced digital twin interface
from .digital_twin.interface import DigitalTwinInterface, EnhancedDigitalTwinInterface

# Advanced simulation engine
from .simulation import (
    SkincareSimulationEngine, VesselSimulation, 
    MolecularInteractionEngine, ProcessOptimizer
)

# AI chemist system
from .ai_chemist import (
    MasterCoordinatorAgent, FormulationOptimizerAgent,
    QualityPredictorAgent, AIChemistSystem
)

# Hardware communication
from .hardware import (
    HardwareDeviceManager, ModbusProtocol, OPCUAProtocol,
    SerialProtocol, HTTPProtocol
)

# Safety systems
from .safety import (
    SafetySystemManager, EmergencyShutdownSystem,
    ProcessControlSystem, AlarmManager, PredictiveSafetyAnalytics
)

# Automated workflows
from .workflows import (
    WorkflowEngine, RecipeExecutor, QualityController,
    ResourceOptimizer, BatchProcessor
)

__version__ = "2.0.0"
__author__ = "Automixer Development Team"

__all__ = [
    # Core models
    "Recipe", "Ingredient", "Equipment", "Batch", "QualityCheck",
    "DigitalTwinState", "OptimizationResult",
    
    # Core functionality
    "RecipeManager", "QualityControlMonitor", "ResourceScheduler", 
    "BatchTracker", "DigitalTwinInterface", "EnhancedDigitalTwinInterface",
    
    # Advanced simulation
    "SkincareSimulationEngine", "VesselSimulation", 
    "MolecularInteractionEngine", "ProcessOptimizer",
    
    # AI chemist
    "MasterCoordinatorAgent", "FormulationOptimizerAgent",
    "QualityPredictorAgent", "AIChemistSystem",
    
    # Hardware communication
    "HardwareDeviceManager", "ModbusProtocol", "OPCUAProtocol",
    "SerialProtocol", "HTTPProtocol",
    
    # Safety systems
    "SafetySystemManager", "EmergencyShutdownSystem",
    "ProcessControlSystem", "AlarmManager", "PredictiveSafetyAnalytics",
    
    # Automated workflows
    "WorkflowEngine", "RecipeExecutor", "QualityController",
    "ResourceOptimizer", "BatchProcessor"
]
