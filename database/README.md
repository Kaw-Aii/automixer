# Automixer Database Documentation

## Overview
This document describes the database schema for the Automixer Laboratory Automation System, deployed to both Supabase and Neon databases.

## Schema Statistics
- **Total Tables**: 18
- **Core Tables**: 5
- **Automation Tables**: 7
- **Analytics Tables**: 3
- **Hypergraph Tables**: 4

## Database Platforms

### Supabase Features
- **Row Level Security (RLS)**: Enabled on all tables
- **Realtime Subscriptions**: Enabled for critical tables
- **Built-in Authentication**: Integrated with Supabase Auth
- **REST API**: Auto-generated REST endpoints
- **GraphQL API**: Auto-generated GraphQL schema

### Neon Features
- **TimescaleDB Extension**: For time-series data optimization
- **Advanced Extensions**: uuid-ossp, pgcrypto, pg_stat_statements
- **Materialized Views**: For performance optimization
- **Stored Procedures**: For complex business logic
- **Connection Pooling**: Built-in connection management

## Table Categories

### Core Tables
1. **ingredients** - Skincare ingredients with properties and safety data
2. **recipes** - Skincare formulation recipes with ingredients and parameters
3. **equipment** - Manufacturing equipment with status and capabilities
4. **batches** - Production batches with tracking and quality data
5. **quality_checks** - Quality control checks and test results

### Automation Tables
1. **digital_twin_states** - Digital twin state snapshots and synchronization
2. **optimization_results** - AI optimization results and recommendations
3. **hardware_devices** - Hardware device registry and communication settings
4. **sensor_data** - Real-time sensor data from equipment (partitioned)
5. **safety_events** - Safety system events and emergency responses
6. **workflow_executions** - Automated workflow execution tracking

### Analytics Tables
1. **process_analytics** - Aggregated process performance analytics
2. **quality_trends** - Quality parameter trends and statistical analysis
3. **predictive_models** - Machine learning model metadata and performance

### Hypergraph Tables
1. **hypergraph_nodes** - Nodes in the manufacturing hypergraph (entities)
2. **hypergraph_edges** - Hyperedges connecting multiple nodes (relationships)
3. **hypergraph_dynamics** - Temporal evolution of hypergraph structure
4. **tensor_field_states** - Multiscale tensor field representations

## Key Features

### Time-Series Optimization
- **TimescaleDB Hypertables**: sensor_data, digital_twin_states, hypergraph_dynamics
- **Automated Partitioning**: By timestamp with configurable intervals
- **Compression**: Automatic compression for historical data
- **Retention Policies**: Configurable data retention

### Real-Time Capabilities
- **Supabase Realtime**: Live updates for critical tables
- **WebSocket Connections**: Real-time data streaming
- **Event Triggers**: Automated responses to data changes
- **Pub/Sub Messaging**: Inter-system communication

### Security Features
- **Row Level Security**: Fine-grained access control
- **API Key Authentication**: Secure API access
- **SSL/TLS Encryption**: Encrypted connections
- **Audit Logging**: Complete activity tracking

### Performance Optimization
- **Strategic Indexing**: Optimized for common query patterns
- **Materialized Views**: Pre-computed aggregations
- **Connection Pooling**: Efficient connection management
- **Query Optimization**: Optimized for analytical workloads

## Deployment Information
- **Deployment Date**: 2025-09-24T19:01:43.021424
- **Schema Version**: 2.0.0
- **Migration Scripts**: Available in /migrations directory
- **Backup Strategy**: Automated daily backups

## Connection Information

### Supabase Connection
```javascript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://your-project.supabase.co'
const supabaseKey = 'your-supabase-anon-key'
const supabase = createClient(supabaseUrl, supabaseKey)
```

### Neon Connection
```python
import asyncpg

async def connect_neon():
    conn = await asyncpg.connect(
        host='neon-host.neon.tech',
        port=5432,
        database='automixer_db',
        user='neon_user',
        password='neon_password',
        ssl='require'
    )
    return conn
```

## Maintenance

### Regular Tasks
- **Statistics Update**: Weekly ANALYZE on all tables
- **Index Maintenance**: Monthly REINDEX on heavily used indexes
- **Partition Maintenance**: Automated partition management
- **Backup Verification**: Daily backup integrity checks

### Monitoring
- **Performance Metrics**: Query performance and resource usage
- **Connection Monitoring**: Active connections and pool status
- **Storage Monitoring**: Table sizes and growth trends
- **Error Monitoring**: Failed queries and connection errors

## Support
For database-related issues or questions, please refer to:
- Supabase Documentation: https://supabase.com/docs
- Neon Documentation: https://neon.tech/docs
- TimescaleDB Documentation: https://docs.timescale.com
