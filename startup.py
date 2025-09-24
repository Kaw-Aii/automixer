#!/usr/bin/env python3
"""
Startup script for the Automixer system.
"""

import asyncio
import uvicorn
from automixer.api.main import app

def main():
    """Main startup function."""
    print("🔬 Starting Automixer - AI-Driven Digital Twin for Skincare Manufacturing")
    print("=" * 80)
    print()
    print("Features:")
    print("✅ Recipe Management: Scalable formulations with automatic optimization")
    print("✅ Quality Control Integration: Real-time monitoring and adjustment")
    print("✅ Resource Scheduling: Intelligent equipment and material allocation")
    print("✅ Batch Tracking: Complete traceability from raw materials to finished products")
    print("✅ Digital Twin Interface: Real-time connection to physical equipment")
    print()
    print("🌐 Starting API server on http://localhost:8000")
    print("📚 API Documentation available at http://localhost:8000/docs")
    print("💡 System Status: http://localhost:8000/system/status")
    print()
    print("🚀 System ready for automated laboratory operations!")
    print("=" * 80)
    
    # Start the FastAPI server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )

if __name__ == "__main__":
    main()