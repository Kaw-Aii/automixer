"""
Automixer: AI-Driven Digital Twin for Skincare Manufacturing Optimization

Complete Laboratory Automation Solution for Skincare Manufacturing
Connecting Digital Twin to Physical Equipment for Fully Automated Sample Production

Features:
✅ Recipe Management: Scalable formulations with automatic optimization
✅ Quality Control Integration: Real-time monitoring and adjustment
✅ Resource Scheduling: Intelligent equipment and material allocation
✅ Batch Tracking: Complete traceability from raw materials to finished products
✅ Digital Twin Interface: Real-time connection to physical equipment
"""

__version__ = "0.1.0"
__author__ = "Automixer Team"
__license__ = "AGPL-3.0"

# Import core modules
from .core.models import *
from .recipe.manager import RecipeManager
from .quality.monitor import QualityControlMonitor
from .scheduling.scheduler import ResourceScheduler
from .tracking.tracker import BatchTracker
from .digital_twin.interface import DigitalTwinInterface
from .config.settings import settings

__all__ = [
    "RecipeManager",
    "QualityControlMonitor", 
    "ResourceScheduler",
    "BatchTracker",
    "DigitalTwinInterface",
    "settings",
]