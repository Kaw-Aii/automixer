"""
Configuration settings for the Automixer system.
"""

from pydantic_settings import BaseSettings
from typing import Dict, Any


class AutomixerSettings(BaseSettings):
    """Application settings."""
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    
    # Database Settings
    database_url: str = "sqlite:///./automixer.db"
    
    # Digital Twin Settings
    digital_twin_simulation_mode: bool = True
    digital_twin_data_retention_days: int = 30
    digital_twin_update_interval_seconds: int = 5
    
    # Quality Control Settings
    quality_control_limits: Dict[str, Dict[str, float]] = {
        'ph': {'lower': 5.0, 'upper': 7.5, 'target': 6.2},
        'viscosity': {'lower': 2000, 'upper': 8000, 'target': 5000},
        'temperature': {'lower': 18, 'upper': 25, 'target': 22},
        'moisture_content': {'lower': 45, 'upper': 65, 'target': 55},
        'particle_size': {'lower': 50, 'upper': 200, 'target': 100},
        'color_consistency': {'lower': 0.8, 'upper': 1.0, 'target': 0.95}
    }
    
    # Scheduling Settings
    scheduling_horizon_days: int = 14
    default_batch_duration_minutes: int = 120
    equipment_maintenance_interval_days: int = 30
    
    # Recipe Settings
    recipe_optimization_models_enabled: bool = True
    recipe_cost_optimization_enabled: bool = True
    recipe_validation_strict: bool = True
    
    # Tracking Settings  
    batch_tracking_enabled: bool = True
    material_traceability_enabled: bool = True
    regulatory_reporting_enabled: bool = True
    
    # Security Settings
    api_key_required: bool = False
    encryption_enabled: bool = False
    
    # Logging Settings
    log_level: str = "INFO"
    log_file: str = "automixer.log"
    
    class Config:
        env_file = ".env"
        env_prefix = "AUTOMIXER_"


# Global settings instance
settings = AutomixerSettings()