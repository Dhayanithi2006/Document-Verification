# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Curated Demo Backend Server Runner (scripts/run_demo_backend.py)

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ["DATABASE_URL"] = "sqlite:///./data/demo.db"
os.environ["STORAGE_DIR"] = "storage/demo_documents"
os.environ["ENVIRONMENT"] = "development"

import uvicorn
from backend.main import app

if __name__ == "__main__":
    port = int(os.environ.get("DEMO_BACKEND_PORT", 8002))
    print(f"Starting Demo Backend on port {port} with DATABASE_URL={os.environ['DATABASE_URL']}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
