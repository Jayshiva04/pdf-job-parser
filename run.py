#!/usr/bin/env python3
"""
Startup script for the Job Notification PDF Summarizer API
"""

import uvicorn
from main import app

if __name__ == "__main__":
    print("Starting Job Notification PDF Summarizer API...")
    print("Server will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 