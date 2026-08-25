#!/usr/bin/env python3
"""
scripts/run_dev.py
───────────────────
Convenience script to start the Uvicorn development server.

Usage (from backend/ directory):
    python scripts/run_dev.py
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",
    )
