"""
DLHUB - Main Entry Point
========================
Simple entry point for deployment platforms.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )