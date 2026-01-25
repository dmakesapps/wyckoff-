#!/usr/bin/env python3
"""
Run the Alpha Discovery API server
"""

import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Alpha Discovery API...")
    print("   Docs: http://localhost:8000/docs")
    print("   Health: http://localhost:8000/api/health")
    print()
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
    )


