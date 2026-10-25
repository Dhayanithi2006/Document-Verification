# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Isolated Test Backend Server Runner
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ["DATABASE_URL"] = "sqlite:///./data/test_frontend.db"
os.environ["STORAGE_DIR"] = "storage/test_storage"
os.environ["ENVIRONMENT"] = "testing"

import uvicorn
from backend.main import app

if __name__ == "__main__":
    port = int(os.environ.get("TEST_BACKEND_PORT", 8001))
    print(f"Starting isolated test backend on port {port} with DATABASE_URL={os.environ['DATABASE_URL']}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
