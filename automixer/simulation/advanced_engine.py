"""
Skincare Manufacturing Simulation Engine
Comprehensive digital twin for laboratory-scale skincare manufacturing with AI-chemist optimization
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import uuid
from datetime import datetime, timedelta
import logging
from abc import ABC, abstractmethod
import threading
import queue
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessState(Enum):
    """Process state enumeration"""
    IDLE = "idle"
    PREPARING = "preparing"
    MIXING = "mixing"
    HEATING = "heating"
    COOLING = "cooling"
    TRANSFERRING = "transferring"
    MONITORING = "monitoring"
    COMPLETE = "complete"
    ERROR = "error"
    EMERGENCY_STOP = "emergency_stop"

class IngredientPhase(Enum):
    """Ingredient phase enumeration"""
    AQUEOUS = "aqueous"
    OIL = "oil"
    POWDER = "powder"
    EMULSION = "emulsion"
    SUSPENSION = "suspension"
    GEL = "gel"

@dataclass
class Ingredient:
    """Represents a cosmetic ingredient with molecular properties"""
    id: str
    name: str
    molecular_weight: float
    polarity_score: float  # 0-1 scale
    solubility_profile: Dict[str, float]  # water, oil, alcohol solubility
    functional_groups: List[str]
    concentration_range: Tuple[float, float]  # min, max percentage
    skin_penetration_score: float  # 0-1 scale
    safety_profile: Dict[str, Any]
    regulatory_status: Dict[str, str]  # market -> status
    cost_per_kg: float
    supplier: str
    batch_number: str = ""
    expiry_date: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.batch_number:
            self.batch_number = f"BATCH_{uuid.uuid4().hex[:8].upper()}"
        if not self.expiry_date:
            self.expiry_date = datetime.now() + timedelta(days=365)

@dataclass
class FormulationComponent:
    """Represents an ingredient in a specific formulation"""
    ingredient: Ingredient
    concentration: float  # percentage
    phase: IngredientPhase
    addition_order: int
    addition_temperature: float  # Celsius
    mixing_time: float  # minutes
    special_instructions: str = ""

@dataclass
class Formulation:
    """Represents a complete skincare formulation"""
    id: str
    name: str
    components: List[FormulationComponent]
    target_properties: Dict[str, float]
    manufacturing_parameters: Dict[str, Any]
    quality_specifications: Dict[str, Tuple[float, float]]  # parameter -> (min, max)
    batch_size: float  # liters
    created_date: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    
    def get_total_concentration(self) -> float:
        """Calculate total concentration of all components"""
        return sum(comp.concentration for comp in self.components)
    
    def get_phase_components(self, phase: IngredientPhase) -> List[FormulationComponent]:
        """Get all components in a specific phase"""
        return [comp for comp in self.components if comp.phase == phase]
    
    def validate_formulation(self) -> List[str]:
        """Validate formulation and return list of issues"""
        issues = []
        
        total_conc = self.get_total_concentration()
        if abs(total_conc - 100.0) > 0.1:
            issues.append(f"Total concentration {total_conc:.2f}% != 100%")
        
        # Check for duplicate ingredients
        ingredient_ids = [comp.ingredient.id for comp in self.components]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            issues.append("Duplicate ingredients found")
        
        # Check concentration ranges
        for comp in self.components:
            min_conc, max_conc = comp.ingredient.concentration_range
            if not (min_conc <= comp.concentration <= max_conc):
                issues.append(f"{comp.ingredient.name} concentration {comp.concentration}% outside range [{min_conc}-{max_conc}%]")
        
        return issues

class VesselSimulation:
    """Simulates a manufacturing vessel with thermal and mixing capabilities"""
    
    def __init__(self, vessel_id: str, capacity: float, vessel_type: str = "jacketed_reactor"):
        self.vessel_id = vessel_id
        self.capacity = capacity  # liters
        self.vessel_type = vessel_type
        self.current_volume = 0.0
        self.current_temperature = 20.0  # Celsius
        self.target_temperature = 20.0
        self.mixing_speed = 0.0  # RPM
        self.contents: List[FormulationComponent] = []
        self.state = ProcessState.IDLE
        
        # Physical properties
        self.thermal_mass = capacity * 2.5  # kg (vessel + contents)
        self.heat_transfer_coefficient = 150.0  # W/m²K
        self.surface_area = 0.5 * (capacity ** 0.67)  # m² (approximation)
        self.max_heating_power = 5000.0  # Watts
        self.max_cooling_power = 3000.0  # Watts
        
        # Mixing properties
        self.max_mixing_speed = 1000.0  # RPM
        self.mixing_efficiency = 0.85
        self.shear_rate_factor = 0.1  # RPM to shear rate conversion
        
        # Safety limits
        self.max_temperature = 85.0  # Celsius
        self.min_temperature = 5.0   # Celsius
        self.max_pressure = 2.0      # bar gauge
        
        # Monitoring data
        self.temperature_history = deque(maxlen=1000)
        self.mixing_history = deque(maxlen=1000)
        self.last_update = datetime.now()
    
    def add_ingredient(self, component: FormulationComponent, batch_size: float) -> bool:
        """Add an ingredient to the vessel"""
        try:
            # Calculate actual volume to add
            volume_to_add = (component.concentration / 100.0) * batch_size
            
            if self.current_volume + volume_to_add > self.capacity:
                logger.error(f"Cannot add {component.ingredient.name}: would exceed vessel capacity")
                return False
            
            # Check temperature compatibility
            if abs(self.current_temperature - component.addition_temperature) > 5.0:
                logger.warning(f"Temperature mismatch for {component.ingredient.name}: vessel={self.current_temperature}°C, required={component.addition_temperature}°C")
            
            self.contents.append(component)
            self.current_volume += volume_to_add
            self.state = ProcessState.PREPARING
            
            logger.info(f"Added {component.ingredient.name} ({component.concentration}%) to vessel {self.vessel_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding ingredient: {e}")
            return False
    
    def set_temperature(self, target_temp: float) -> bool:
        """Set target temperature for the vessel"""
        if not (self.min_temperature <= target_temp <= self.max_temperature):
            logger.error(f"Target temperature {target_temp}°C outside safe range [{self.min_temperature}-{self.max_temperature}°C]")
            return False
        
        self.target_temperature = target_temp
        if target_temp > self.current_temperature:
            self.state = ProcessState.HEATING
        elif target_temp < self.current_temperature:
            self.state = ProcessState.COOLING
        
        return True
    
    def set_mixing_speed(self, speed: float) -> bool:
        """Set mixing speed in RPM"""
        if not (0 <= speed <= self.max_mixing_speed):
            logger.error(f"Mixing speed {speed} RPM outside range [0-{self.max_mixing_speed}] RPM")
            return False
        
        self.mixing_speed = speed
        if speed > 0:
            self.state = ProcessState.MIXING
        
        return True
    
    def update_thermal_dynamics(self, dt: float) -> None:
        """Update vessel temperature based on thermal dynamics"""
        if abs(self.current_temperature - self.target_temperature) < 0.1:
            return
        
        # Calculate heating/cooling power
        temp_diff = self.target_temperature - self.current_temperature
        
        if temp_diff > 0:  # Heating
            power = min(self.max_heating_power, abs(temp_diff) * 100)
        else:  # Cooling
            power = -min(self.max_cooling_power, abs(temp_diff) * 100)
        
        # Heat transfer equation: Q = mcΔT
        # Power = Q/t, so ΔT = (Power * dt) / (m * c)
        specific_heat = 4186  # J/kg·K (water approximation)
        mass = self.thermal_mass + (self.current_volume * 1.0)  # kg
        
        temp_change = (power * dt) / (mass * specific_heat)
        self.current_temperature += temp_change
        
        # Add some thermal lag and noise
        self.current_temperature += np.random.normal(0, 0.1)
        
        # Record temperature history
        self.temperature_history.append({
            'timestamp': datetime.now(),
            'temperature': self.current_temperature,
            'target': self.target_temperature,
            'power': power
        })
    
    def calculate_mixing_effectiveness(self) -> float:
        """Calculate current mixing effectiveness based on speed and contents"""
        if self.mixing_speed == 0:
            return 0.0
        
        # Base effectiveness from mixing speed
        speed_factor = min(self.mixing_speed / 500.0, 1.0)  # Optimal around 500 RPM
        
        # Adjust for viscosity (estimated from contents)
        viscosity_factor = 1.0
        if self.contents:
            # Estimate viscosity from ingredient types
            oil_content = sum(comp.concentration for comp in self.contents 
                            if comp.phase == IngredientPhase.OIL)
            powder_content = sum(comp.concentration for comp in self.contents 
                               if comp.phase == IngredientPhase.POWDER)
            
            viscosity_factor = 1.0 / (1.0 + oil_content/50.0 + powder_content/20.0)
        
        effectiveness = speed_factor * viscosity_factor * self.mixing_efficiency
        return min(effectiveness, 1.0)
    
    def get_shear_rate(self) -> float:
        """Calculate current shear rate in the vessel"""
        return self.mixing_speed * self.shear_rate_factor
    
    def simulate_step(self, dt: float = 1.0) -> Dict[str, Any]:
        """Simulate one time step of vessel operation"""
        self.update_thermal_dynamics(dt)
        
        mixing_effectiveness = self.calculate_mixing_effectiveness()
        shear_rate = self.get_shear_rate()
        
        # Update mixing history
        self.mixing_history.append({
            'timestamp': datetime.now(),
            'mixing_speed': self.mixing_speed,
            'effectiveness': mixing_effectiveness,
            'shear_rate': shear_rate
        })
        
        self.last_update = datetime.now()
        
        return {
            'vessel_id': self.vessel_id,
            'state': self.state.value,
            'temperature': self.current_temperature,
            'target_temperature': self.target_temperature,
            'volume': self.current_volume,
            'mixing_speed': self.mixing_speed,
            'mixing_effectiveness': mixing_effectiveness,
            'shear_rate': shear_rate,
            'contents_count': len(self.contents)
        }
    
    def empty_vessel(self) -> bool:
        """Empty the vessel and reset to idle state"""
        try:
            self.contents.clear()
            self.current_volume = 0.0
            self.mixing_speed = 0.0
            self.target_temperature = 20.0
            self.state = ProcessState.IDLE
            
            logger.info(f"Vessel {self.vessel_id} emptied and reset")
            return True
            
        except Exception as e:
            logger.error(f"Error emptying vessel: {e}")
            return False

class MolecularInteractionEngine:
    """Simulates molecular interactions between ingredients"""
    
    def __init__(self):
        self.compatibility_matrix = {}
        self.interaction_rules = []
        self.stability_models = {}
        
    def calculate_molecular_similarity(self, ing1: Ingredient, ing2: Ingredient) -> float:
        """Calculate molecular similarity between two ingredients"""
        # Molecular weight similarity
        mw_diff = abs(ing1.molecular_weight - ing2.molecular_weight)
        mw_similarity = 1.0 / (1.0 + mw_diff / 500.0)
        
        # Polarity similarity
        polarity_similarity = 1.0 - abs(ing1.polarity_score - ing2.polarity_score)
        
        # Functional group overlap
        groups1 = set(ing1.functional_groups)
        groups2 = set(ing2.functional_groups)
        if groups1 or groups2:
            group_similarity = len(groups1 & groups2) / len(groups1 | groups2)
        else:
            group_similarity = 1.0
        
        # Solubility profile similarity
        sol_similarity = 0.0
        for solvent in ['water', 'oil', 'alcohol']:
            sol1 = ing1.solubility_profile.get(solvent, 0.0)
            sol2 = ing2.solubility_profile.get(solvent, 0.0)
            sol_similarity += 1.0 - abs(sol1 - sol2)
        sol_similarity /= 3.0
        
        # Weighted average
        overall_similarity = (
            mw_similarity * 0.25 +
            polarity_similarity * 0.25 +
            group_similarity * 0.25 +
            sol_similarity * 0.25
        )
        
        return overall_similarity
    
    def predict_compatibility(self, ing1: Ingredient, ing2: Ingredient) -> float:
        """Predict compatibility between two ingredients"""
        similarity = self.calculate_molecular_similarity(ing1, ing2)
        
        # Check for known incompatibilities
        incompatible_pairs = [
            (['carboxyl'], ['amine']),  # Acid-base reactions
            (['phenol'], ['iron']),     # Metal complexation
            (['vitamin_c'], ['niacinamide'])  # pH incompatibility
        ]
        
        for groups1, groups2 in incompatible_pairs:
            if (any(g in ing1.functional_groups for g in groups1) and
                any(g in ing2.functional_groups for g in groups2)):
                similarity *= 0.5  # Reduce compatibility
        
        # Boost compatibility for synergistic combinations
        synergistic_pairs = [
            (['hydroxyl'], ['humectant']),
            (['antioxidant'], ['vitamin_e']),
            (['peptide'], ['hyaluronic_acid'])
        ]
        
        for groups1, groups2 in synergistic_pairs:
            if (any(g in ing1.functional_groups for g in groups1) and
                any(g in ing2.functional_groups for g in groups2)):
                similarity = min(1.0, similarity * 1.2)  # Boost compatibility
        
        return similarity
    
    def predict_stability(self, formulation: Formulation, conditions: Dict[str, float]) -> Dict[str, float]:
        """Predict formulation stability under given conditions"""
        temperature = conditions.get('temperature', 25.0)
        humidity = conditions.get('humidity', 50.0)
        light_exposure = conditions.get('light_exposure', 0.0)
        
        stability_scores = {}
        
        # Chemical stability
        chemical_stability = 1.0
        for i, comp1 in enumerate(formulation.components):
            for comp2 in formulation.components[i+1:]:
                compatibility = self.predict_compatibility(comp1.ingredient, comp2.ingredient)
                chemical_stability *= compatibility
        
        # Temperature stability
        temp_factor = 1.0
        if temperature > 30:
            temp_factor = 1.0 - (temperature - 30) / 100.0
        elif temperature < 5:
            temp_factor = 1.0 - (5 - temperature) / 50.0
        
        # Humidity stability
        humidity_factor = 1.0 - abs(humidity - 50) / 200.0
        
        # Light stability
        light_factor = 1.0 - light_exposure / 100.0
        
        stability_scores['chemical'] = max(0.0, chemical_stability)
        stability_scores['thermal'] = max(0.0, temp_factor)
        stability_scores['humidity'] = max(0.0, humidity_factor)
        stability_scores['light'] = max(0.0, light_factor)
        stability_scores['overall'] = (
            stability_scores['chemical'] * 0.4 +
            stability_scores['thermal'] * 0.3 +
            stability_scores['humidity'] * 0.2 +
            stability_scores['light'] * 0.1
        )
        
        return stability_scores
    
    def simulate_phase_behavior(self, formulation: Formulation) -> Dict[str, Any]:
        """Simulate phase behavior of formulation"""
        phases = {
            'aqueous': [],
            'oil': [],
            'emulsion': [],
            'suspension': []
        }
        
        total_water = 0.0
        total_oil = 0.0
        
        for comp in formulation.components:
            if comp.phase == IngredientPhase.AQUEOUS:
                phases['aqueous'].append(comp)
                total_water += comp.concentration
            elif comp.phase == IngredientPhase.OIL:
                phases['oil'].append(comp)
                total_oil += comp.concentration
            elif comp.phase == IngredientPhase.EMULSION:
                phases['emulsion'].append(comp)
            elif comp.phase == IngredientPhase.SUSPENSION:
                phases['suspension'].append(comp)
        
        # Determine emulsion type
        emulsion_type = "none"
        if total_water > 0 and total_oil > 0:
            if total_water > total_oil:
                emulsion_type = "oil_in_water"
            else:
                emulsion_type = "water_in_oil"
        
        # Estimate droplet size (simplified model)
        droplet_size = 1.0  # micrometers
        if emulsion_type != "none":
            # Smaller droplets with higher shear and emulsifiers
            emulsifier_content = sum(comp.concentration for comp in phases['emulsion'])
            droplet_size = max(0.1, 5.0 - emulsifier_content / 2.0)
        
        return {
            'phases': phases,
            'emulsion_type': emulsion_type,
            'water_content': total_water,
            'oil_content': total_oil,
            'estimated_droplet_size': droplet_size,
            'phase_stability': self.predict_stability(formulation, {'temperature': 25.0})['overall']
        }

if __name__ == "__main__":
    # Example usage and testing
    print("=== Skincare Manufacturing Simulation Engine ===")
    
    # Create test ingredients
    hyaluronic_acid = Ingredient(
        id="ha_001",
        name="Hyaluronic Acid",
        molecular_weight=379.32,
        polarity_score=0.9,
        solubility_profile={'water': 1.0, 'oil': 0.0, 'alcohol': 0.3},
        functional_groups=['hydroxyl', 'carboxyl', 'amine'],
        concentration_range=(0.1, 2.0),
        skin_penetration_score=0.7,
        safety_profile={'irritation_potential': 'low', 'sensitization': 'none'},
        regulatory_status={'US': 'approved', 'EU': 'approved'},
        cost_per_kg=2500.0,
        supplier="Premium Ingredients Ltd"
    )
    
    niacinamide = Ingredient(
        id="nia_001",
        name="Niacinamide",
        molecular_weight=122.12,
        polarity_score=0.6,
        solubility_profile={'water': 1.0, 'oil': 0.1, 'alcohol': 0.8},
        functional_groups=['pyridine_ring', 'amide'],
        concentration_range=(2.0, 10.0),
        skin_penetration_score=0.8,
        safety_profile={'irritation_potential': 'low', 'sensitization': 'rare'},
        regulatory_status={'US': 'approved', 'EU': 'approved'},
        cost_per_kg=150.0,
        supplier="Active Cosmetics Inc"
    )
    
    # Create formulation components
    ha_component = FormulationComponent(
        ingredient=hyaluronic_acid,
        concentration=1.0,
        phase=IngredientPhase.AQUEOUS,
        addition_order=1,
        addition_temperature=25.0,
        mixing_time=10.0
    )
    
    nia_component = FormulationComponent(
        ingredient=niacinamide,
        concentration=5.0,
        phase=IngredientPhase.AQUEOUS,
        addition_order=2,
        addition_temperature=25.0,
        mixing_time=15.0
    )
    
    # Create water component
    water = Ingredient(
        id="water_001",
        name="Purified Water",
        molecular_weight=18.02,
        polarity_score=1.0,
        solubility_profile={'water': 1.0, 'oil': 0.0, 'alcohol': 1.0},
        functional_groups=['hydroxyl'],
        concentration_range=(50.0, 95.0),
        skin_penetration_score=1.0,
        safety_profile={'irritation_potential': 'none', 'sensitization': 'none'},
        regulatory_status={'US': 'approved', 'EU': 'approved'},
        cost_per_kg=0.5,
        supplier="Local Water Treatment"
    )
    
    water_component = FormulationComponent(
        ingredient=water,
        concentration=94.0,
        phase=IngredientPhase.AQUEOUS,
        addition_order=0,
        addition_temperature=25.0,
        mixing_time=5.0
    )
    
    # Create test formulation
    test_formulation = Formulation(
        id="FORM_001",
        name="Hydrating Serum",
        components=[water_component, ha_component, nia_component],
        target_properties={
            'viscosity': 50.0,  # cP
            'pH': 6.5,
            'stability': 0.9
        },
        manufacturing_parameters={
            'mixing_speed': 300,  # RPM
            'temperature': 25.0,  # Celsius
            'mixing_time': 30.0   # minutes
        },
        quality_specifications={
            'pH': (6.0, 7.0),
            'viscosity': (40.0, 60.0),
            'appearance': (8.0, 10.0)
        },
        batch_size=10.0  # liters
    )
    
    # Validate formulation
    issues = test_formulation.validate_formulation()
    if issues:
        print(f"Formulation issues: {issues}")
    else:
        print("✅ Formulation validation passed")
    
    # Create vessel simulation
    vessel = VesselSimulation("VESSEL_001", capacity=20.0)
    print(f"Created vessel: {vessel.vessel_id} (capacity: {vessel.capacity}L)")
    
    # Simulate adding ingredients
    print("\n🧪 Simulating ingredient addition:")
    for component in sorted(test_formulation.components, key=lambda x: x.addition_order):
        success = vessel.add_ingredient(component, test_formulation.batch_size)
        if success:
            print(f"  ✅ Added {component.ingredient.name} ({component.concentration}%)")
        else:
            print(f"  ❌ Failed to add {component.ingredient.name}")
    
    # Set mixing parameters
    vessel.set_mixing_speed(test_formulation.manufacturing_parameters['mixing_speed'])
    vessel.set_temperature(test_formulation.manufacturing_parameters['temperature'])
    
    # Run simulation steps
    print(f"\n⚙️ Running simulation steps:")
    for step in range(5):
        status = vessel.simulate_step(dt=1.0)
        print(f"  Step {step+1}: T={status['temperature']:.1f}°C, Mix={status['mixing_speed']} RPM, Eff={status['mixing_effectiveness']:.2f}")
        time.sleep(0.1)  # Brief pause for demonstration
    
    # Test molecular interactions
    print(f"\n🔬 Molecular interaction analysis:")
    interaction_engine = MolecularInteractionEngine()
    
    # Test compatibility
    compatibility = interaction_engine.predict_compatibility(hyaluronic_acid, niacinamide)
    print(f"  HA-Niacinamide compatibility: {compatibility:.3f}")
    
    # Test stability prediction
    stability = interaction_engine.predict_stability(test_formulation, {
        'temperature': 25.0,
        'humidity': 50.0,
        'light_exposure': 10.0
    })
    print(f"  Formulation stability: {stability['overall']:.3f}")
    
    # Test phase behavior
    phase_behavior = interaction_engine.simulate_phase_behavior(test_formulation)
    print(f"  Phase behavior: {phase_behavior['emulsion_type']}")
    print(f"  Water content: {phase_behavior['water_content']:.1f}%")
    
    print(f"\n✅ Simulation engine demonstration complete!")
    print(f"   - Vessel simulation: operational")
    print(f"   - Molecular interactions: functional")
    print(f"   - Formulation validation: working")
    print(f"   - Ready for AI-chemist integration!")



class SkincareSimulationEngine:
    """Main simulation engine that orchestrates all simulation components"""
    
    def __init__(self):
        self.vessels: Dict[str, VesselSimulation] = {}
        self.ingredients: Dict[str, Ingredient] = {}
        self.formulations: Dict[str, Formulation] = {}
        self.molecular_engine = MolecularInteractionEngine()
        self.running = False
        
        logger.info("Skincare Simulation Engine initialized")
    
    def add_vessel(self, vessel: VesselSimulation):
        """Add a vessel to the simulation"""
        self.vessels[vessel.vessel_id] = vessel
        logger.info(f"Added vessel: {vessel.vessel_id}")
    
    def add_ingredient(self, ingredient: Ingredient):
        """Add an ingredient to the simulation"""
        self.ingredients[ingredient.id] = ingredient
        logger.info(f"Added ingredient: {ingredient.name}")
    
    def add_formulation(self, formulation: Formulation):
        """Add a formulation to the simulation"""
        self.formulations[formulation.id] = formulation
        logger.info(f"Added formulation: {formulation.name}")
    
    def get_vessel(self, vessel_id: str) -> Optional[VesselSimulation]:
        """Get a vessel by ID"""
        return self.vessels.get(vessel_id)
    
    def get_ingredient(self, ingredient_id: str) -> Optional[Ingredient]:
        """Get an ingredient by ID"""
        return self.ingredients.get(ingredient_id)
    
    def get_formulation(self, formulation_id: str) -> Optional[Formulation]:
        """Get a formulation by ID"""
        return self.formulations.get(formulation_id)
    
    def start_simulation(self):
        """Start the simulation engine"""
        self.running = True
        logger.info("Simulation engine started")
    
    def stop_simulation(self):
        """Stop the simulation engine"""
        self.running = False
        logger.info("Simulation engine stopped")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "running": self.running,
            "vessels_count": len(self.vessels),
            "ingredients_count": len(self.ingredients),
            "formulations_count": len(self.formulations),
            "vessels": [
                {
                    "id": vessel.vessel_id,
                    "name": vessel.vessel_id,
                    "capacity": vessel.capacity,
                    "current_volume": vessel.current_volume,
                    "temperature": vessel.temperature,
                    "mixing_speed": vessel.mixing_speed,
                    "state": vessel.state.value
                }
                for vessel in self.vessels.values()
            ]
        }

# Create a Vessel class that wraps VesselSimulation for compatibility
class Vessel:
    """Vessel wrapper for compatibility with integration system"""
    
    def __init__(self, id: str, name: str, capacity: float, current_volume: float = 0.0,
                 temperature: float = 20.0, mixing_speed: int = 0, 
                 heating_cooling_rate: float = 1.0, max_temperature: float = 80.0,
                 min_temperature: float = 5.0):
        self.id = id
        self.name = name
        self.capacity = capacity
        self.current_volume = current_volume
        self.temperature = temperature
        self.mixing_speed = mixing_speed
        self.heating_cooling_rate = heating_cooling_rate
        self.max_temperature = max_temperature
        self.min_temperature = min_temperature
        
        # Create underlying VesselSimulation
        self._vessel_sim = VesselSimulation(
            vessel_id=id,
            capacity=capacity,
            vessel_type="jacketed_reactor"
        )
        
        # Set initial conditions
        self._vessel_sim.current_temperature = temperature
        self._vessel_sim.mixing_speed = mixing_speed
    
    @property
    def vessel_id(self) -> str:
        """Get the vessel ID"""
        return self.id
    
    @property
    def vessel_simulation(self) -> VesselSimulation:
        """Get the underlying vessel simulation"""
        return self._vessel_sim

# Create ProcessStep class for compatibility
@dataclass
class ProcessStep:
    """Represents a manufacturing process step"""
    step_id: str
    step_type: str
    parameters: Dict[str, Any]
    duration: float
    temperature: Optional[float] = None
    mixing_speed: Optional[int] = None
    description: str = ""

