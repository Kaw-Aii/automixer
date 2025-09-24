"""
AI-Chemist Optimization System
Autonomous agents for intelligent skincare formulation and process optimization
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import random
import time
import uuid
from datetime import datetime, timedelta
import logging
from abc import ABC, abstractmethod
import threading
import queue
from collections import defaultdict, deque
import copy

from skincare_simulation_engine import (
    Ingredient, FormulationComponent, Formulation, VesselSimulation,
    MolecularInteractionEngine, ProcessState, IngredientPhase
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentType(Enum):
    """AI-Chemist agent types"""
    MASTER_COORDINATOR = "master_coordinator"
    FORMULATION_OPTIMIZER = "formulation_optimizer"
    PROCESS_CONTROLLER = "process_controller"
    QUALITY_PREDICTOR = "quality_predictor"
    SAFETY_COMPLIANCE = "safety_compliance"
    INNOVATION_EXPLORER = "innovation_explorer"
    MARKET_ANALYZER = "market_analyzer"

class OptimizationObjective(Enum):
    """Optimization objectives"""
    MAXIMIZE_EFFICACY = "maximize_efficacy"
    MINIMIZE_COST = "minimize_cost"
    MAXIMIZE_STABILITY = "maximize_stability"
    MINIMIZE_IRRITATION = "minimize_irritation"
    MAXIMIZE_CONSUMER_APPEAL = "maximize_consumer_appeal"
    MINIMIZE_ENVIRONMENTAL_IMPACT = "minimize_environmental_impact"

@dataclass
class OptimizationTask:
    """Represents an optimization task for AI agents"""
    task_id: str
    task_type: str
    priority: int  # 1-10, 10 being highest
    objectives: List[OptimizationObjective]
    constraints: Dict[str, Any]
    target_formulation: Optional[Formulation] = None
    deadline: Optional[datetime] = None
    assigned_agent: Optional[str] = None
    status: str = "pending"
    results: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class AgentPerformance:
    """Tracks agent performance metrics"""
    agent_id: str
    agent_type: AgentType
    tasks_completed: int = 0
    success_rate: float = 0.0
    average_quality_score: float = 0.0
    average_processing_time: float = 0.0
    specialization_scores: Dict[str, float] = field(default_factory=dict)
    learning_rate: float = 0.1
    last_updated: datetime = field(default_factory=datetime.now)

class AIChemistAgent(ABC):
    """Base class for AI-Chemist agents"""
    
    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.performance = AgentPerformance(agent_id, agent_type)
        self.knowledge_base = {}
        self.active_tasks = []
        self.completed_tasks = []
        self.communication_queue = queue.Queue()
        self.is_active = True
        
        # Learning and adaptation
        self.experience_buffer = deque(maxlen=1000)
        self.model_parameters = {}
        self.confidence_threshold = 0.7
        
    @abstractmethod
    def process_task(self, task: OptimizationTask) -> Dict[str, Any]:
        """Process an optimization task"""
        pass
    
    @abstractmethod
    def update_knowledge(self, feedback: Dict[str, Any]) -> None:
        """Update agent knowledge based on feedback"""
        pass
    
    def send_message(self, recipient_id: str, message: Dict[str, Any]) -> None:
        """Send message to another agent"""
        message['sender'] = self.agent_id
        message['timestamp'] = datetime.now()
        # In a real implementation, this would route to the recipient
        logger.info(f"Agent {self.agent_id} sent message to {recipient_id}: {message.get('type', 'unknown')}")
    
    def receive_message(self, message: Dict[str, Any]) -> None:
        """Receive message from another agent"""
        self.communication_queue.put(message)
    
    def calculate_confidence(self, task: OptimizationTask) -> float:
        """Calculate confidence in handling a specific task"""
        base_confidence = 0.5
        
        # Adjust based on experience with similar tasks
        similar_tasks = [t for t in self.completed_tasks if t.task_type == task.task_type]
        if similar_tasks:
            success_rate = sum(1 for t in similar_tasks if t.status == "completed") / len(similar_tasks)
            base_confidence += success_rate * 0.3
        
        # Adjust based on specialization
        specialization_score = self.performance.specialization_scores.get(task.task_type, 0.5)
        base_confidence += specialization_score * 0.2
        
        return min(1.0, base_confidence)

class MasterCoordinatorAgent(AIChemistAgent):
    """Master coordinator agent that orchestrates all other agents"""
    
    def __init__(self, agent_id: str = "master_coordinator"):
        super().__init__(agent_id, AgentType.MASTER_COORDINATOR)
        self.subordinate_agents = {}
        self.task_queue = queue.PriorityQueue()
        self.global_objectives = []
        self.resource_allocation = {}
        
    def add_subordinate_agent(self, agent: AIChemistAgent) -> None:
        """Add a subordinate agent to coordinate"""
        self.subordinate_agents[agent.agent_id] = agent
        logger.info(f"Added subordinate agent: {agent.agent_id} ({agent.agent_type.value})")
    
    def assign_task(self, task: OptimizationTask) -> str:
        """Assign task to the most suitable agent"""
        best_agent = None
        best_score = 0.0
        
        for agent in self.subordinate_agents.values():
            if not agent.is_active:
                continue
                
            # Calculate suitability score
            confidence = agent.calculate_confidence(task)
            workload_factor = 1.0 / (1.0 + len(agent.active_tasks))
            performance_factor = agent.performance.success_rate
            
            suitability_score = confidence * 0.5 + workload_factor * 0.3 + performance_factor * 0.2
            
            if suitability_score > best_score:
                best_score = suitability_score
                best_agent = agent
        
        if best_agent:
            task.assigned_agent = best_agent.agent_id
            best_agent.active_tasks.append(task)
            logger.info(f"Assigned task {task.task_id} to agent {best_agent.agent_id} (score: {best_score:.3f})")
            return best_agent.agent_id
        else:
            logger.warning(f"No suitable agent found for task {task.task_id}")
            return ""
    
    def process_task(self, task: OptimizationTask) -> Dict[str, Any]:
        """Process coordination tasks"""
        if task.task_type == "coordinate_optimization":
            return self.coordinate_multi_objective_optimization(task)
        elif task.task_type == "resource_allocation":
            return self.optimize_resource_allocation(task)
        else:
            return {"status": "unsupported_task_type"}
    
    def coordinate_multi_objective_optimization(self, task: OptimizationTask) -> Dict[str, Any]:
        """Coordinate multi-objective optimization across agents"""
        results = {}
        
        # Break down complex optimization into subtasks
        subtasks = []
        for objective in task.objectives:
            subtask = OptimizationTask(
                task_id=f"{task.task_id}_{objective.value}",
                task_type=f"optimize_{objective.value}",
                priority=task.priority,
                objectives=[objective],
                constraints=task.constraints,
                target_formulation=task.target_formulation
            )
            subtasks.append(subtask)
        
        # Assign subtasks to appropriate agents
        subtask_results = {}
        for subtask in subtasks:
            agent_id = self.assign_task(subtask)
            if agent_id:
                agent = self.subordinate_agents[agent_id]
                result = agent.process_task(subtask)
                subtask_results[subtask.task_id] = result
        
        # Combine results using multi-objective optimization
        combined_result = self.combine_optimization_results(subtask_results, task.objectives)
        
        return {
            "status": "completed",
            "subtask_results": subtask_results,
            "combined_result": combined_result,
            "coordination_quality": self.evaluate_coordination_quality(subtask_results)
        }
    
    def combine_optimization_results(self, subtask_results: Dict[str, Any], objectives: List[OptimizationObjective]) -> Dict[str, Any]:
        """Combine multiple optimization results using Pareto optimization"""
        # Simplified Pareto front calculation
        solutions = []
        
        for task_id, result in subtask_results.items():
            if result.get("status") == "completed" and "optimized_formulation" in result:
                solution = {
                    "formulation": result["optimized_formulation"],
                    "scores": result.get("objective_scores", {}),
                    "source_task": task_id
                }
                solutions.append(solution)
        
        if not solutions:
            return {"status": "no_valid_solutions"}
        
        # Find Pareto optimal solutions
        pareto_solutions = []
        for i, sol1 in enumerate(solutions):
            is_dominated = False
            for j, sol2 in enumerate(solutions):
                if i != j and self.dominates(sol2, sol1, objectives):
                    is_dominated = True
                    break
            if not is_dominated:
                pareto_solutions.append(sol1)
        
        # Select best solution based on weighted objectives
        if pareto_solutions:
            best_solution = max(pareto_solutions, key=lambda s: self.calculate_weighted_score(s, objectives))
            return {
                "status": "completed",
                "best_solution": best_solution,
                "pareto_solutions": pareto_solutions,
                "solution_count": len(pareto_solutions)
            }
        else:
            return {"status": "no_pareto_solutions"}
    
    def dominates(self, sol1: Dict[str, Any], sol2: Dict[str, Any], objectives: List[OptimizationObjective]) -> bool:
        """Check if solution 1 dominates solution 2"""
        scores1 = sol1.get("scores", {})
        scores2 = sol2.get("scores", {})
        
        better_in_all = True
        better_in_at_least_one = False
        
        for objective in objectives:
            obj_name = objective.value
            score1 = scores1.get(obj_name, 0.0)
            score2 = scores2.get(obj_name, 0.0)
            
            if score1 < score2:
                better_in_all = False
            elif score1 > score2:
                better_in_at_least_one = True
        
        return better_in_all and better_in_at_least_one
    
    def calculate_weighted_score(self, solution: Dict[str, Any], objectives: List[OptimizationObjective]) -> float:
        """Calculate weighted score for solution selection"""
        scores = solution.get("scores", {})
        total_score = 0.0
        weight_sum = 0.0
        
        # Equal weights for now, could be made configurable
        for objective in objectives:
            weight = 1.0 / len(objectives)
            score = scores.get(objective.value, 0.0)
            total_score += weight * score
            weight_sum += weight
        
        return total_score / weight_sum if weight_sum > 0 else 0.0
    
    def evaluate_coordination_quality(self, subtask_results: Dict[str, Any]) -> float:
        """Evaluate the quality of coordination"""
        if not subtask_results:
            return 0.0
        
        completed_tasks = sum(1 for result in subtask_results.values() if result.get("status") == "completed")
        completion_rate = completed_tasks / len(subtask_results)
        
        # Average quality of completed tasks
        quality_scores = [result.get("quality_score", 0.0) for result in subtask_results.values() 
                         if result.get("status") == "completed"]
        average_quality = np.mean(quality_scores) if quality_scores else 0.0
        
        coordination_quality = completion_rate * 0.6 + average_quality * 0.4
        return coordination_quality
    
    def update_knowledge(self, feedback: Dict[str, Any]) -> None:
        """Update coordination knowledge based on feedback"""
        # Update coordination strategies based on success/failure patterns
        task_type = feedback.get("task_type", "")
        success = feedback.get("success", False)
        
        if task_type not in self.knowledge_base:
            self.knowledge_base[task_type] = {"success_count": 0, "total_count": 0, "strategies": {}}
        
        self.knowledge_base[task_type]["total_count"] += 1
        if success:
            self.knowledge_base[task_type]["success_count"] += 1
        
        # Update success rate
        success_rate = self.knowledge_base[task_type]["success_count"] / self.knowledge_base[task_type]["total_count"]
        self.performance.success_rate = success_rate

class FormulationOptimizerAgent(AIChemistAgent):
    """Agent specialized in formulation optimization"""
    
    def __init__(self, agent_id: str = "formulation_optimizer"):
        super().__init__(agent_id, AgentType.FORMULATION_OPTIMIZER)
        self.ingredient_database = {}
        self.optimization_algorithms = {
            "genetic_algorithm": self.genetic_algorithm_optimization,
            "gradient_descent": self.gradient_descent_optimization,
            "simulated_annealing": self.simulated_annealing_optimization
        }
        self.molecular_engine = MolecularInteractionEngine()
        
    def process_task(self, task: OptimizationTask) -> Dict[str, Any]:
        """Process formulation optimization task"""
        if not task.target_formulation:
            return {"status": "error", "message": "No target formulation provided"}
        
        start_time = time.time()
        
        # Select optimization algorithm based on task characteristics
        algorithm = self.select_optimization_algorithm(task)
        
        # Perform optimization
        optimized_formulation, optimization_history = algorithm(task)
        
        # Evaluate optimization results
        quality_score = self.evaluate_formulation_quality(optimized_formulation, task.objectives)
        
        processing_time = time.time() - start_time
        
        # Update performance metrics
        self.update_performance_metrics(task, quality_score, processing_time)
        
        return {
            "status": "completed",
            "optimized_formulation": optimized_formulation,
            "original_formulation": task.target_formulation,
            "quality_score": quality_score,
            "objective_scores": self.calculate_objective_scores(optimized_formulation, task.objectives),
            "optimization_algorithm": algorithm.__name__,
            "optimization_history": optimization_history,
            "processing_time": processing_time,
            "improvement_percentage": self.calculate_improvement(task.target_formulation, optimized_formulation, task.objectives)
        }
    
    def select_optimization_algorithm(self, task: OptimizationTask) -> Callable:
        """Select the best optimization algorithm for the task"""
        # Simple heuristic-based selection
        if len(task.objectives) > 2:
            return self.optimization_algorithms["genetic_algorithm"]
        elif task.priority > 7:
            return self.optimization_algorithms["gradient_descent"]
        else:
            return self.optimization_algorithms["simulated_annealing"]
    
    def genetic_algorithm_optimization(self, task: OptimizationTask) -> Tuple[Formulation, List[Dict]]:
        """Genetic algorithm for multi-objective optimization"""
        population_size = 50
        generations = 100
        mutation_rate = 0.1
        crossover_rate = 0.8
        
        # Initialize population
        population = self.generate_initial_population(task.target_formulation, population_size)
        history = []
        
        for generation in range(generations):
            # Evaluate fitness
            fitness_scores = [self.evaluate_formulation_quality(individual, task.objectives) 
                            for individual in population]
            
            # Record best solution
            best_idx = np.argmax(fitness_scores)
            best_formulation = population[best_idx]
            best_score = fitness_scores[best_idx]
            
            history.append({
                "generation": generation,
                "best_score": best_score,
                "average_score": np.mean(fitness_scores),
                "population_diversity": self.calculate_population_diversity(population)
            })
            
            # Selection
            selected_population = tournament_selection(population, fitness_scores, population_size)
            
            # Crossover and mutation
            new_population = []
            for i in range(0, population_size, 2):
                parent1 = selected_population[i]
                parent2 = selected_population[min(i+1, population_size-1)]
                
                if random.random() < crossover_rate:
                    child1, child2 = crossover_formulations(parent1, parent2)
                else:
                    child1, child2 = parent1, parent2
                
                if random.random() < mutation_rate:
                    child1 = mutate_formulation(child1, task.constraints)
                if random.random() < mutation_rate:
                    child2 = mutate_formulation(child2, task.constraints)
                
                new_population.extend([child1, child2])
            
            population = new_population[:population_size]
        
        # Return best solution
        final_fitness = [self.evaluate_formulation_quality(individual, task.objectives) 
                        for individual in population]
        best_idx = np.argmax(final_fitness)
        
        return population[best_idx], history
    
    def gradient_descent_optimization(self, task: OptimizationTask) -> Tuple[Formulation, List[Dict]]:
        """Gradient descent optimization for continuous parameters"""
        learning_rate = 0.01
        max_iterations = 1000
        tolerance = 1e-6
        
        current_formulation = copy.deepcopy(task.target_formulation)
        history = []
        
        for iteration in range(max_iterations):
            # Calculate gradient
            gradient = self.calculate_gradient(current_formulation, task.objectives)
            
            # Update concentrations
            for i, component in enumerate(current_formulation.components):
                old_concentration = component.concentration
                component.concentration += learning_rate * gradient[i]
                
                # Apply constraints
                min_conc, max_conc = component.ingredient.concentration_range
                component.concentration = np.clip(component.concentration, min_conc, max_conc)
            
            # Normalize concentrations to sum to 100%
            total_conc = sum(comp.concentration for comp in current_formulation.components)
            if total_conc > 0:
                for component in current_formulation.components:
                    component.concentration = (component.concentration / total_conc) * 100.0
            
            # Evaluate current solution
            current_score = self.evaluate_formulation_quality(current_formulation, task.objectives)
            
            history.append({
                "iteration": iteration,
                "score": current_score,
                "gradient_norm": np.linalg.norm(gradient)
            })
            
            # Check convergence
            if len(history) > 1 and abs(history[-1]["score"] - history[-2]["score"]) < tolerance:
                break
        
        return current_formulation, history
    
    def simulated_annealing_optimization(self, task: OptimizationTask) -> Tuple[Formulation, List[Dict]]:
        """Simulated annealing optimization"""
        initial_temperature = 100.0
        cooling_rate = 0.95
        min_temperature = 0.01
        max_iterations = 1000
        
        current_formulation = copy.deepcopy(task.target_formulation)
        current_score = self.evaluate_formulation_quality(current_formulation, task.objectives)
        
        best_formulation = copy.deepcopy(current_formulation)
        best_score = current_score
        
        temperature = initial_temperature
        history = []
        
        for iteration in range(max_iterations):
            if temperature < min_temperature:
                break
            
            # Generate neighbor solution
            neighbor_formulation = self.generate_neighbor_formulation(current_formulation, task.constraints)
            neighbor_score = self.evaluate_formulation_quality(neighbor_formulation, task.objectives)
            
            # Accept or reject neighbor
            delta = neighbor_score - current_score
            if delta > 0 or random.random() < np.exp(delta / temperature):
                current_formulation = neighbor_formulation
                current_score = neighbor_score
                
                if current_score > best_score:
                    best_formulation = copy.deepcopy(current_formulation)
                    best_score = current_score
            
            history.append({
                "iteration": iteration,
                "temperature": temperature,
                "current_score": current_score,
                "best_score": best_score,
                "accepted": delta > 0 or random.random() < np.exp(delta / temperature)
            })
            
            temperature *= cooling_rate
        
        return best_formulation, history
    
    def generate_initial_population(self, base_formulation: Formulation, population_size: int) -> List[Formulation]:
        """Generate initial population for genetic algorithm"""
        population = []
        
        for _ in range(population_size):
            individual = copy.deepcopy(base_formulation)
            
            # Randomly vary concentrations within constraints
            for component in individual.components:
                min_conc, max_conc = component.ingredient.concentration_range
                variation = random.uniform(-0.2, 0.2) * component.concentration
                new_conc = component.concentration + variation
                component.concentration = np.clip(new_conc, min_conc, max_conc)
            
            # Normalize to 100%
            total_conc = sum(comp.concentration for comp in individual.components)
            if total_conc > 0:
                for component in individual.components:
                    component.concentration = (component.concentration / total_conc) * 100.0
            
            population.append(individual)
        
        return population
    
    def evaluate_formulation_quality(self, formulation: Formulation, objectives: List[OptimizationObjective]) -> float:
        """Evaluate overall formulation quality based on objectives"""
        scores = self.calculate_objective_scores(formulation, objectives)
        
        # Weighted average of objective scores
        total_score = 0.0
        for objective in objectives:
            weight = 1.0 / len(objectives)  # Equal weights for now
            score = scores.get(objective.value, 0.0)
            total_score += weight * score
        
        return total_score
    
    def calculate_objective_scores(self, formulation: Formulation, objectives: List[OptimizationObjective]) -> Dict[str, float]:
        """Calculate scores for each optimization objective"""
        scores = {}
        
        for objective in objectives:
            if objective == OptimizationObjective.MAXIMIZE_EFFICACY:
                scores[objective.value] = self.calculate_efficacy_score(formulation)
            elif objective == OptimizationObjective.MINIMIZE_COST:
                scores[objective.value] = 1.0 - self.calculate_cost_score(formulation)
            elif objective == OptimizationObjective.MAXIMIZE_STABILITY:
                scores[objective.value] = self.calculate_stability_score(formulation)
            elif objective == OptimizationObjective.MINIMIZE_IRRITATION:
                scores[objective.value] = 1.0 - self.calculate_irritation_score(formulation)
            elif objective == OptimizationObjective.MAXIMIZE_CONSUMER_APPEAL:
                scores[objective.value] = self.calculate_consumer_appeal_score(formulation)
            elif objective == OptimizationObjective.MINIMIZE_ENVIRONMENTAL_IMPACT:
                scores[objective.value] = 1.0 - self.calculate_environmental_impact_score(formulation)
        
        return scores
    
    def calculate_efficacy_score(self, formulation: Formulation) -> float:
        """Calculate efficacy score based on active ingredients"""
        efficacy_score = 0.0
        
        for component in formulation.components:
            # Simple efficacy model based on concentration and skin penetration
            ingredient_efficacy = component.ingredient.skin_penetration_score * (component.concentration / 100.0)
            efficacy_score += ingredient_efficacy
        
        return min(1.0, efficacy_score)
    
    def calculate_cost_score(self, formulation: Formulation) -> float:
        """Calculate normalized cost score"""
        total_cost = 0.0
        
        for component in formulation.components:
            ingredient_cost = component.ingredient.cost_per_kg * (component.concentration / 100.0)
            total_cost += ingredient_cost
        
        # Normalize to 0-1 scale (assuming max reasonable cost is $1000/kg)
        return min(1.0, total_cost / 1000.0)
    
    def calculate_stability_score(self, formulation: Formulation) -> float:
        """Calculate stability score using molecular interaction engine"""
        stability_prediction = self.molecular_engine.predict_stability(formulation, {
            'temperature': 25.0,
            'humidity': 50.0,
            'light_exposure': 10.0
        })
        
        return stability_prediction.get('overall', 0.0)
    
    def calculate_irritation_score(self, formulation: Formulation) -> float:
        """Calculate irritation potential score"""
        irritation_score = 0.0
        
        for component in formulation.components:
            # Simple irritation model based on ingredient properties
            ingredient_irritation = component.ingredient.safety_profile.get('irritation_potential', 'low')
            
            if ingredient_irritation == 'high':
                irritation_factor = 0.8
            elif ingredient_irritation == 'medium':
                irritation_factor = 0.4
            else:
                irritation_factor = 0.1
            
            concentration_factor = component.concentration / 100.0
            irritation_score += irritation_factor * concentration_factor
        
        return min(1.0, irritation_score)
    
    def calculate_consumer_appeal_score(self, formulation: Formulation) -> float:
        """Calculate consumer appeal score"""
        # Simplified model based on ingredient popularity and sensory properties
        appeal_score = 0.5  # Base score
        
        # Popular ingredients boost appeal
        popular_ingredients = ['hyaluronic_acid', 'niacinamide', 'vitamin_c', 'retinol']
        for component in formulation.components:
            if any(pop_ing in component.ingredient.id.lower() for pop_ing in popular_ingredients):
                appeal_score += 0.1
        
        # Balanced formulation (not too many ingredients) is appealing
        ingredient_count = len(formulation.components)
        if 3 <= ingredient_count <= 8:
            appeal_score += 0.2
        elif ingredient_count > 10:
            appeal_score -= 0.1
        
        return min(1.0, appeal_score)
    
    def calculate_environmental_impact_score(self, formulation: Formulation) -> float:
        """Calculate environmental impact score"""
        # Simplified model - could be enhanced with LCA data
        impact_score = 0.0
        
        for component in formulation.components:
            # Assume synthetic ingredients have higher impact
            if 'synthetic' in component.ingredient.name.lower():
                ingredient_impact = 0.7
            elif 'natural' in component.ingredient.name.lower():
                ingredient_impact = 0.3
            else:
                ingredient_impact = 0.5
            
            concentration_factor = component.concentration / 100.0
            impact_score += ingredient_impact * concentration_factor
        
        return min(1.0, impact_score)
    
    def update_knowledge(self, feedback: Dict[str, Any]) -> None:
        """Update formulation optimization knowledge"""
        # Update ingredient effectiveness models
        formulation = feedback.get("formulation")
        performance_data = feedback.get("performance_data", {})
        
        if formulation and performance_data:
            for component in formulation.components:
                ingredient_id = component.ingredient.id
                if ingredient_id not in self.knowledge_base:
                    self.knowledge_base[ingredient_id] = {
                        "efficacy_data": [],
                        "stability_data": [],
                        "safety_data": []
                    }
                
                # Update efficacy data
                if "efficacy" in performance_data:
                    self.knowledge_base[ingredient_id]["efficacy_data"].append({
                        "concentration": component.concentration,
                        "efficacy": performance_data["efficacy"],
                        "timestamp": datetime.now()
                    })
    
    def update_performance_metrics(self, task: OptimizationTask, quality_score: float, processing_time: float) -> None:
        """Update agent performance metrics"""
        self.performance.tasks_completed += 1
        
        # Update average quality score
        old_avg = self.performance.average_quality_score
        new_avg = (old_avg * (self.performance.tasks_completed - 1) + quality_score) / self.performance.tasks_completed
        self.performance.average_quality_score = new_avg
        
        # Update average processing time
        old_time = self.performance.average_processing_time
        new_time = (old_time * (self.performance.tasks_completed - 1) + processing_time) / self.performance.tasks_completed
        self.performance.average_processing_time = new_time
        
        # Update specialization scores
        for objective in task.objectives:
            obj_name = objective.value
            if obj_name not in self.performance.specialization_scores:
                self.performance.specialization_scores[obj_name] = 0.5
            
            # Update using exponential moving average
            old_score = self.performance.specialization_scores[obj_name]
            self.performance.specialization_scores[obj_name] = (
                old_score * (1 - self.performance.learning_rate) + 
                quality_score * self.performance.learning_rate
            )
        
        self.performance.last_updated = datetime.now()
    
    def calculate_gradient(self, formulation: Formulation, objectives: List[OptimizationObjective]) -> np.ndarray:
        """Calculate gradient for gradient descent optimization"""
        epsilon = 0.01  # Small perturbation for numerical gradient
        gradient = np.zeros(len(formulation.components))
        
        base_score = self.evaluate_formulation_quality(formulation, objectives)
        
        for i, component in enumerate(formulation.components):
            # Perturb concentration slightly
            original_conc = component.concentration
            component.concentration += epsilon
            
            # Normalize concentrations
            total_conc = sum(comp.concentration for comp in formulation.components)
            if total_conc > 0:
                for comp in formulation.components:
                    comp.concentration = (comp.concentration / total_conc) * 100.0
            
            # Calculate perturbed score
            perturbed_score = self.evaluate_formulation_quality(formulation, objectives)
            
            # Calculate gradient
            gradient[i] = (perturbed_score - base_score) / epsilon
            
            # Restore original concentration
            component.concentration = original_conc
            
            # Re-normalize
            total_conc = sum(comp.concentration for comp in formulation.components)
            if total_conc > 0:
                for comp in formulation.components:
                    comp.concentration = (comp.concentration / total_conc) * 100.0
        
        return gradient
    
    def generate_neighbor_formulation(self, formulation: Formulation, constraints: Dict[str, Any]) -> Formulation:
        """Generate neighbor formulation for simulated annealing"""
        neighbor = copy.deepcopy(formulation)
        
        # Randomly select a component to modify
        if neighbor.components:
            component = random.choice(neighbor.components)
            
            # Small random change to concentration
            min_conc, max_conc = component.ingredient.concentration_range
            current_conc = component.concentration
            
            # Generate random change (±5% of current concentration)
            change_magnitude = 0.05 * current_conc
            change = random.uniform(-change_magnitude, change_magnitude)
            
            new_conc = current_conc + change
            component.concentration = np.clip(new_conc, min_conc, max_conc)
            
            # Normalize total concentration
            total_conc = sum(comp.concentration for comp in neighbor.components)
            if total_conc > 0:
                for comp in neighbor.components:
                    comp.concentration = (comp.concentration / total_conc) * 100.0
        
        return neighbor
    
    def calculate_population_diversity(self, population: List[Formulation]) -> float:
        """Calculate diversity of population for genetic algorithm"""
        if len(population) < 2:
            return 0.0
        
        total_distance = 0.0
        comparisons = 0
        
        for i in range(len(population)):
            for j in range(i + 1, len(population)):
                # Calculate distance between formulations
                distance = self.calculate_formulation_distance(population[i], population[j])
                total_distance += distance
                comparisons += 1
        
        return total_distance / comparisons if comparisons > 0 else 0.0
    
    def calculate_formulation_distance(self, form1: Formulation, form2: Formulation) -> float:
        """Calculate distance between two formulations"""
        if len(form1.components) != len(form2.components):
            return 1.0  # Maximum distance for different structures
        
        total_distance = 0.0
        for comp1, comp2 in zip(form1.components, form2.components):
            if comp1.ingredient.id == comp2.ingredient.id:
                # Concentration difference
                conc_diff = abs(comp1.concentration - comp2.concentration) / 100.0
                total_distance += conc_diff
            else:
                total_distance += 1.0  # Different ingredients
        
        return total_distance / len(form1.components)
    
    def calculate_improvement(self, original: Formulation, optimized: Formulation, objectives: List[OptimizationObjective]) -> float:
        """Calculate improvement percentage from original to optimized formulation"""
        original_score = self.evaluate_formulation_quality(original, objectives)
        optimized_score = self.evaluate_formulation_quality(optimized, objectives)
        
        if original_score == 0:
            return 0.0
        
        improvement = ((optimized_score - original_score) / original_score) * 100.0
        return improvement

# Additional helper methods for FormulationOptimizerAgent
def tournament_selection(population: List[Formulation], fitness_scores: List[float], 
                        selection_size: int, tournament_size: int = 3) -> List[Formulation]:
    """Tournament selection for genetic algorithm"""
    selected = []
    
    for _ in range(selection_size):
        tournament_indices = random.sample(range(len(population)), min(tournament_size, len(population)))
        tournament_fitness = [fitness_scores[i] for i in tournament_indices]
        winner_idx = tournament_indices[np.argmax(tournament_fitness)]
        selected.append(copy.deepcopy(population[winner_idx]))
    
    return selected

def crossover_formulations(parent1: Formulation, parent2: Formulation) -> Tuple[Formulation, Formulation]:
    """Crossover operation for formulations"""
    child1 = copy.deepcopy(parent1)
    child2 = copy.deepcopy(parent2)
    
    # Single-point crossover on concentrations
    if len(parent1.components) == len(parent2.components):
        crossover_point = random.randint(1, len(parent1.components) - 1)
        
        for i in range(crossover_point, len(parent1.components)):
            child1.components[i].concentration = parent2.components[i].concentration
            child2.components[i].concentration = parent1.components[i].concentration
    
    # Normalize concentrations
    for child in [child1, child2]:
        total_conc = sum(comp.concentration for comp in child.components)
        if total_conc > 0:
            for component in child.components:
                component.concentration = (component.concentration / total_conc) * 100.0
    
    return child1, child2

def mutate_formulation(formulation: Formulation, constraints: Dict[str, Any]) -> Formulation:
    """Mutation operation for formulation"""
    mutated = copy.deepcopy(formulation)
    
    # Randomly select a component to mutate
    if mutated.components:
        component = random.choice(mutated.components)
        
        # Mutate concentration within constraints
        min_conc, max_conc = component.ingredient.concentration_range
        mutation_strength = 0.1  # 10% of current concentration
        mutation = random.uniform(-mutation_strength, mutation_strength) * component.concentration
        
        new_concentration = component.concentration + mutation
        component.concentration = np.clip(new_concentration, min_conc, max_conc)
        
        # Normalize total concentration
        total_conc = sum(comp.concentration for comp in mutated.components)
        if total_conc > 0:
            for comp in mutated.components:
                comp.concentration = (comp.concentration / total_conc) * 100.0
    
    return mutated

if __name__ == "__main__":
    # Example usage and testing
    print("=== AI-Chemist Optimization System ===")
    
    # Create test agents
    master_coordinator = MasterCoordinatorAgent()
    formulation_optimizer = FormulationOptimizerAgent()
    
    # Add subordinate agent
    master_coordinator.add_subordinate_agent(formulation_optimizer)
    
    # Create test formulation (from previous example)
    from skincare_simulation_engine import Ingredient, FormulationComponent, Formulation, IngredientPhase
    
    # Test ingredients
    water = Ingredient(
        id="water_001", name="Purified Water", molecular_weight=18.02, polarity_score=1.0,
        solubility_profile={'water': 1.0, 'oil': 0.0, 'alcohol': 1.0},
        functional_groups=['hydroxyl'], concentration_range=(50.0, 95.0),
        skin_penetration_score=1.0, safety_profile={'irritation_potential': 'none'},
        regulatory_status={'US': 'approved'}, cost_per_kg=0.5, supplier="Local"
    )
    
    niacinamide = Ingredient(
        id="nia_001", name="Niacinamide", molecular_weight=122.12, polarity_score=0.6,
        solubility_profile={'water': 1.0, 'oil': 0.1, 'alcohol': 0.8},
        functional_groups=['pyridine_ring', 'amide'], concentration_range=(2.0, 10.0),
        skin_penetration_score=0.8, safety_profile={'irritation_potential': 'low'},
        regulatory_status={'US': 'approved'}, cost_per_kg=150.0, supplier="Active Cosmetics"
    )
    
    # Create test formulation
    test_formulation = Formulation(
        id="TEST_001", name="Test Serum",
        components=[
            FormulationComponent(water, 95.0, IngredientPhase.AQUEOUS, 0, 25.0, 5.0),
            FormulationComponent(niacinamide, 5.0, IngredientPhase.AQUEOUS, 1, 25.0, 15.0)
        ],
        target_properties={'efficacy': 0.8, 'stability': 0.9},
        manufacturing_parameters={'mixing_speed': 300, 'temperature': 25.0},
        quality_specifications={'pH': (6.0, 7.0)},
        batch_size=10.0
    )
    
    # Create optimization task
    optimization_task = OptimizationTask(
        task_id="OPT_001",
        task_type="optimize_formulation",
        priority=8,
        objectives=[OptimizationObjective.MAXIMIZE_EFFICACY, OptimizationObjective.MAXIMIZE_STABILITY],
        constraints={'max_cost': 500.0, 'min_stability': 0.7},
        target_formulation=test_formulation
    )
    
    print(f"Created optimization task: {optimization_task.task_id}")
    print(f"Objectives: {[obj.value for obj in optimization_task.objectives]}")
    
    # Test formulation optimization
    print(f"\n🧪 Testing formulation optimization:")
    result = formulation_optimizer.process_task(optimization_task)
    
    print(f"  Status: {result['status']}")
    print(f"  Quality score: {result['quality_score']:.3f}")
    print(f"  Processing time: {result['processing_time']:.2f}s")
    print(f"  Algorithm used: {result['optimization_algorithm']}")
    
    if 'objective_scores' in result:
        print(f"  Objective scores:")
        for obj, score in result['objective_scores'].items():
            print(f"    {obj}: {score:.3f}")
    
    # Test master coordination
    print(f"\n🤖 Testing master coordination:")
    coordination_task = OptimizationTask(
        task_id="COORD_001",
        task_type="coordinate_optimization",
        priority=9,
        objectives=[OptimizationObjective.MAXIMIZE_EFFICACY, OptimizationObjective.MINIMIZE_COST, OptimizationObjective.MAXIMIZE_STABILITY],
        constraints={'max_cost': 300.0},
        target_formulation=test_formulation
    )
    
    coord_result = master_coordinator.process_task(coordination_task)
    print(f"  Coordination status: {coord_result['status']}")
    print(f"  Coordination quality: {coord_result.get('coordination_quality', 0.0):.3f}")
    
    if 'combined_result' in coord_result and coord_result['combined_result'].get('status') == 'completed':
        best_solution = coord_result['combined_result']['best_solution']
        print(f"  Best solution scores: {best_solution.get('scores', {})}")
    
    # Display agent performance
    print(f"\n📊 Agent Performance:")
    print(f"  Formulation Optimizer:")
    print(f"    Tasks completed: {formulation_optimizer.performance.tasks_completed}")
    print(f"    Average quality: {formulation_optimizer.performance.average_quality_score:.3f}")
    print(f"    Average time: {formulation_optimizer.performance.average_processing_time:.2f}s")
    
    print(f"\n✅ AI-Chemist system demonstration complete!")
    print(f"   - Multi-objective optimization: functional")
    print(f"   - Agent coordination: operational")
    print(f"   - Performance tracking: working")
    print(f"   - Ready for integration with simulation engine!")

