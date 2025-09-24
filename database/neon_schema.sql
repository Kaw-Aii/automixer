-- Neon Schema for Automixer Laboratory Automation System
-- Generated on: 2025-09-24T19:00:17.245973

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "timescaledb";

-- Table: ingredients
-- Skincare ingredients with properties and safety data
CREATE TABLE IF NOT EXISTS ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    supplier VARCHAR(255) NOT NULL,
    batch_number VARCHAR(100) NOT NULL,
    expiration_date TIMESTAMP NOT NULL,
    concentration_range JSONB NOT NULL,
    properties JSONB DEFAULT '{}',
    safety_data JSONB DEFAULT '{}',
    cost_per_gram DECIMAL(10,4) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ingredients_name ON ingredients USING BTREE (name);
CREATE INDEX IF NOT EXISTS idx_ingredients_supplier ON ingredients USING BTREE (supplier);
CREATE INDEX IF NOT EXISTS idx_ingredients_expiration ON ingredients USING BTREE (expiration_date);

-- Table: recipes
-- Skincare formulation recipes with ingredients and parameters
CREATE TABLE IF NOT EXISTS recipes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    ingredients JSONB NOT NULL,
    target_batch_size DECIMAL(10,2) NOT NULL,
    mixing_parameters JSONB DEFAULT '{}',
    processing_steps JSONB DEFAULT '[]',
    quality_targets JSONB DEFAULT '{}',
    optimization_score DECIMAL(5,3),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_recipes_name ON recipes USING BTREE (name);
CREATE INDEX IF NOT EXISTS idx_recipes_version ON recipes USING BTREE (version);
CREATE INDEX IF NOT EXISTS idx_recipes_score ON recipes USING BTREE (optimization_score);

-- Table: equipment
-- Manufacturing equipment with status and capabilities
CREATE TABLE IF NOT EXISTS equipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    capacity DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'idle',
    current_batch_id UUID,
    last_maintenance TIMESTAMP NOT NULL,
    next_maintenance TIMESTAMP NOT NULL,
    calibration_data JSONB DEFAULT '{}',
    sensors JSONB DEFAULT '[]',
    location VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_equipment_type ON equipment USING BTREE (type);
CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment USING BTREE (status);
CREATE INDEX IF NOT EXISTS idx_equipment_maintenance ON equipment USING BTREE (next_maintenance);

-- Table: batches
-- Production batches with tracking and quality data
CREATE TABLE IF NOT EXISTS batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID NOT NULL,
    batch_number VARCHAR(100) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    target_quantity DECIMAL(10,2) NOT NULL,
    actual_quantity DECIMAL(10,2),
    assigned_equipment JSONB DEFAULT '[]',
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    quality_results JSONB DEFAULT '{}',
    processing_log JSONB DEFAULT '[]',
    operator VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_batches_recipe ON batches USING BTREE (recipe_id);
CREATE INDEX IF NOT EXISTS idx_batches_status ON batches USING BTREE (status);
CREATE INDEX IF NOT EXISTS idx_batches_number ON batches USING BTREE (batch_number);
CREATE INDEX IF NOT EXISTS idx_batches_start_time ON batches USING BTREE (start_time);

-- Table: quality_checks
-- Quality control checks and test results
CREATE TABLE IF NOT EXISTS quality_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL,
    test_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    target_values JSONB NOT NULL,
    measured_values JSONB DEFAULT '{}',
    tolerance JSONB DEFAULT '{}',
    test_method VARCHAR(255) NOT NULL,
    operator VARCHAR(255),
    equipment_used VARCHAR(255),
    test_date TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quality_batch ON quality_checks USING BTREE (batch_id);
CREATE INDEX IF NOT EXISTS idx_quality_type ON quality_checks USING BTREE (test_type);
CREATE INDEX IF NOT EXISTS idx_quality_status ON quality_checks USING BTREE (status);
CREATE INDEX IF NOT EXISTS idx_quality_date ON quality_checks USING BTREE (test_date);

-- Table: digital_twin_states
-- Digital twin state snapshots and synchronization data
CREATE TABLE IF NOT EXISTS digital_twin_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    equipment_states JSONB NOT NULL,
    process_parameters JSONB NOT NULL,
    environmental_conditions JSONB NOT NULL,
    active_batches JSONB DEFAULT '[]',
    alerts JSONB DEFAULT '[]',
    sync_status VARCHAR(50) DEFAULT 'synced',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dt_states_timestamp ON digital_twin_states USING BTREE (timestamp);
CREATE INDEX IF NOT EXISTS idx_dt_states_sync ON digital_twin_states USING BTREE (sync_status);

-- Table: optimization_results
-- AI optimization results and recommendations
CREATE TABLE IF NOT EXISTS optimization_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID NOT NULL,
    optimization_type VARCHAR(100) NOT NULL,
    original_score DECIMAL(8,4) NOT NULL,
    optimized_score DECIMAL(8,4) NOT NULL,
    parameter_changes JSONB NOT NULL,
    confidence DECIMAL(5,3) NOT NULL,
    validation_required BOOLEAN DEFAULT true,
    applied BOOLEAN DEFAULT false,
    applied_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_opt_recipe ON optimization_results USING BTREE (recipe_id);
CREATE INDEX IF NOT EXISTS idx_opt_type ON optimization_results USING BTREE (optimization_type);
CREATE INDEX IF NOT EXISTS idx_opt_score ON optimization_results USING BTREE (optimized_score);
CREATE INDEX IF NOT EXISTS idx_opt_applied ON optimization_results USING BTREE (applied);

-- Table: hardware_devices
-- Hardware device registry and communication settings
CREATE TABLE IF NOT EXISTS hardware_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(100) NOT NULL UNIQUE,
    device_name VARCHAR(255) NOT NULL,
    device_type VARCHAR(100) NOT NULL,
    protocol VARCHAR(50) NOT NULL,
    connection_config JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'offline',
    last_communication TIMESTAMP,
    capabilities JSONB DEFAULT '{}',
    calibration_status VARCHAR(50) DEFAULT 'unknown',
    maintenance_schedule JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hw_device_id ON hardware_devices USING BTREE (device_id);
CREATE INDEX IF NOT EXISTS idx_hw_type ON hardware_devices USING BTREE (device_type);
CREATE INDEX IF NOT EXISTS idx_hw_status ON hardware_devices USING BTREE (status);
CREATE INDEX IF NOT EXISTS idx_hw_protocol ON hardware_devices USING BTREE (protocol);

-- Table: sensor_data
-- Real-time sensor data from equipment
CREATE TABLE IF NOT EXISTS sensor_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL,
    sensor_name VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    value DECIMAL(15,6) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    quality VARCHAR(20) DEFAULT 'good',
    batch_id UUID,
    equipment_id UUID
);

CREATE INDEX IF NOT EXISTS idx_sensor_device ON sensor_data USING BTREE (device_id);
CREATE INDEX IF NOT EXISTS idx_sensor_timestamp ON sensor_data USING BTREE (timestamp);
CREATE INDEX IF NOT EXISTS idx_sensor_batch ON sensor_data USING BTREE (batch_id);
CREATE INDEX IF NOT EXISTS idx_sensor_name_time ON sensor_data USING BTREE (sensor_name, timestamp);

-- Table: safety_events
-- Safety system events and emergency responses
CREATE TABLE IF NOT EXISTS safety_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    source VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    equipment_id UUID,
    batch_id UUID,
    response_actions JSONB DEFAULT '[]',
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(255),
    root_cause TEXT
);

CREATE INDEX IF NOT EXISTS idx_safety_type ON safety_events USING BTREE (event_type);
CREATE INDEX IF NOT EXISTS idx_safety_severity ON safety_events USING BTREE (severity);
CREATE INDEX IF NOT EXISTS idx_safety_timestamp ON safety_events USING BTREE (timestamp);
CREATE INDEX IF NOT EXISTS idx_safety_resolved ON safety_events USING BTREE (resolved);

-- Table: workflow_executions
-- Automated workflow execution tracking
CREATE TABLE IF NOT EXISTS workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_name VARCHAR(255) NOT NULL,
    workflow_version VARCHAR(50) NOT NULL,
    batch_id UUID NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    start_time TIMESTAMP DEFAULT NOW(),
    end_time TIMESTAMP,
    current_step VARCHAR(255),
    progress DECIMAL(5,2) DEFAULT 0.00,
    execution_log JSONB DEFAULT '[]',
    error_details JSONB,
    parameters JSONB DEFAULT '{}',
    results JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_workflow_name ON workflow_executions USING BTREE (workflow_name);
CREATE INDEX IF NOT EXISTS idx_workflow_batch ON workflow_executions USING BTREE (batch_id);
CREATE INDEX IF NOT EXISTS idx_workflow_status ON workflow_executions USING BTREE (status);
CREATE INDEX IF NOT EXISTS idx_workflow_start ON workflow_executions USING BTREE (start_time);

-- Table: process_analytics
-- Aggregated process performance analytics
CREATE TABLE IF NOT EXISTS process_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_date DATE NOT NULL,
    recipe_id UUID,
    equipment_id UUID,
    batch_count INTEGER NOT NULL,
    avg_cycle_time DECIMAL(10,2),
    avg_yield DECIMAL(5,2),
    quality_score DECIMAL(5,3),
    efficiency_score DECIMAL(5,3),
    cost_per_batch DECIMAL(10,2),
    energy_consumption DECIMAL(10,2),
    waste_percentage DECIMAL(5,2),
    oee_score DECIMAL(5,3),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analytics_date ON process_analytics USING BTREE (analysis_date);
CREATE INDEX IF NOT EXISTS idx_analytics_recipe ON process_analytics USING BTREE (recipe_id);
CREATE INDEX IF NOT EXISTS idx_analytics_equipment ON process_analytics USING BTREE (equipment_id);
CREATE INDEX IF NOT EXISTS idx_analytics_oee ON process_analytics USING BTREE (oee_score);

-- Table: quality_trends
-- Quality parameter trends and statistical analysis
CREATE TABLE IF NOT EXISTS quality_trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parameter_name VARCHAR(100) NOT NULL,
    recipe_id UUID,
    analysis_period VARCHAR(20) NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    sample_count INTEGER NOT NULL,
    mean_value DECIMAL(15,6) NOT NULL,
    std_deviation DECIMAL(15,6) NOT NULL,
    min_value DECIMAL(15,6) NOT NULL,
    max_value DECIMAL(15,6) NOT NULL,
    cp_index DECIMAL(8,4),
    cpk_index DECIMAL(8,4),
    trend_direction VARCHAR(20),
    control_status VARCHAR(20) DEFAULT 'in_control',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trends_parameter ON quality_trends USING BTREE (parameter_name);
CREATE INDEX IF NOT EXISTS idx_trends_recipe ON quality_trends USING BTREE (recipe_id);
CREATE INDEX IF NOT EXISTS idx_trends_period ON quality_trends USING BTREE (period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_trends_cpk ON quality_trends USING BTREE (cpk_index);

-- Table: predictive_models
-- Machine learning model metadata and performance
CREATE TABLE IF NOT EXISTS predictive_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(255) NOT NULL,
    model_type VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    target_variable VARCHAR(100) NOT NULL,
    input_features JSONB NOT NULL,
    training_data_size INTEGER NOT NULL,
    training_date TIMESTAMP NOT NULL,
    accuracy_score DECIMAL(5,4),
    r2_score DECIMAL(5,4),
    mae DECIMAL(10,6),
    rmse DECIMAL(10,6),
    model_parameters JSONB,
    feature_importance JSONB,
    validation_results JSONB,
    deployment_status VARCHAR(50) DEFAULT 'development',
    deployed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_models_name ON predictive_models USING BTREE (model_name);
CREATE INDEX IF NOT EXISTS idx_models_type ON predictive_models USING BTREE (model_type);
CREATE INDEX IF NOT EXISTS idx_models_accuracy ON predictive_models USING BTREE (accuracy_score);
CREATE INDEX IF NOT EXISTS idx_models_deployment ON predictive_models USING BTREE (deployment_status);

-- Table: hypergraph_nodes
-- Nodes in the manufacturing hypergraph (entities)
CREATE TABLE IF NOT EXISTS hypergraph_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    entity_table VARCHAR(50) NOT NULL,
    properties JSONB DEFAULT '{}',
    weight DECIMAL(10,6) DEFAULT 1.0,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hg_nodes_type ON hypergraph_nodes USING BTREE (node_type);
CREATE INDEX IF NOT EXISTS idx_hg_nodes_entity ON hypergraph_nodes USING BTREE (entity_id, entity_table);
CREATE INDEX IF NOT EXISTS idx_hg_nodes_status ON hypergraph_nodes USING BTREE (status);

-- Table: hypergraph_edges
-- Hyperedges connecting multiple nodes (relationships)
CREATE TABLE IF NOT EXISTS hypergraph_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    edge_type VARCHAR(50) NOT NULL,
    connected_nodes JSONB NOT NULL,
    relationship_strength DECIMAL(5,4) DEFAULT 1.0,
    properties JSONB DEFAULT '{}',
    temporal_validity TSRANGE,
    confidence DECIMAL(5,4) DEFAULT 1.0,
    source VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hg_edges_type ON hypergraph_edges USING BTREE (edge_type);
CREATE INDEX IF NOT EXISTS idx_hg_edges_strength ON hypergraph_edges USING BTREE (relationship_strength);
CREATE INDEX IF NOT EXISTS idx_hg_edges_temporal ON hypergraph_edges USING BTREE (temporal_validity);
CREATE INDEX IF NOT EXISTS idx_hg_edges_nodes ON hypergraph_edges USING GIN (connected_nodes);

-- Table: hypergraph_dynamics
-- Temporal evolution of hypergraph structure
CREATE TABLE IF NOT EXISTS hypergraph_dynamics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    change_type VARCHAR(50) NOT NULL,
    affected_nodes JSONB DEFAULT '[]',
    affected_edges JSONB DEFAULT '[]',
    change_magnitude DECIMAL(10,6) NOT NULL,
    trigger_event VARCHAR(100),
    context JSONB DEFAULT '{}',
    stability_metric DECIMAL(5,4),
    complexity_metric DECIMAL(10,6),
    entropy_change DECIMAL(10,6)
);

CREATE INDEX IF NOT EXISTS idx_hg_dynamics_timestamp ON hypergraph_dynamics USING BTREE (timestamp);
CREATE INDEX IF NOT EXISTS idx_hg_dynamics_type ON hypergraph_dynamics USING BTREE (change_type);
CREATE INDEX IF NOT EXISTS idx_hg_dynamics_magnitude ON hypergraph_dynamics USING BTREE (change_magnitude);
CREATE INDEX IF NOT EXISTS idx_hg_dynamics_stability ON hypergraph_dynamics USING BTREE (stability_metric);

-- Table: tensor_field_states
-- Multiscale tensor field representations
CREATE TABLE IF NOT EXISTS tensor_field_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    scale_level INTEGER NOT NULL,
    spatial_coordinates JSONB NOT NULL,
    tensor_components JSONB NOT NULL,
    field_strength DECIMAL(15,8) NOT NULL,
    gradient_vector JSONB,
    divergence DECIMAL(15,8),
    curl JSONB,
    associated_batch UUID,
    associated_equipment UUID,
    field_type VARCHAR(50) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tensor_timestamp ON tensor_field_states USING BTREE (timestamp);
CREATE INDEX IF NOT EXISTS idx_tensor_scale ON tensor_field_states USING BTREE (scale_level);
CREATE INDEX IF NOT EXISTS idx_tensor_strength ON tensor_field_states USING BTREE (field_strength);
CREATE INDEX IF NOT EXISTS idx_tensor_batch ON tensor_field_states USING BTREE (associated_batch);
CREATE INDEX IF NOT EXISTS idx_tensor_coords ON tensor_field_states USING GIN (spatial_coordinates);

-- Create TimescaleDB Hypertables
SELECT create_hypertable('sensor_data', 'timestamp', chunk_time_interval => INTERVAL '1 day');
SELECT create_hypertable('digital_twin_states', 'timestamp', chunk_time_interval => INTERVAL '1 hour');
SELECT create_hypertable('hypergraph_dynamics', 'timestamp', chunk_time_interval => INTERVAL '1 hour');

-- Create Materialized Views
-- Hourly aggregated sensor data
-- CREATE MATERIALIZED VIEW hourly_sensor_aggregates AS ...
-- Refresh: CONTINUOUS

-- Daily batch production summary
-- CREATE MATERIALIZED VIEW daily_batch_summary AS ...
-- Refresh: DAILY

-- Real-time equipment utilization
-- CREATE MATERIALIZED VIEW equipment_utilization AS ...
-- Refresh: CONTINUOUS
