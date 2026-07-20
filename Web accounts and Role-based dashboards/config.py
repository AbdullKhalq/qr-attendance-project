from __future__ import annotations

import os
from pathlib import Path


class Config:
    """Central configuration for the Step 2 web application."""

    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / "data"
    USER_DATA_FILE = DATA_DIR / "users.json"

    # Development-only default. Set SECRET_KEY in the environment before deployment.
    SECRET_KEY = os.getenv("SECRET_KEY", "overnight-demo-secret-key")

    # Prevents accidental lecturer registration during the demo.
    LECTURER_REGISTRATION_CODE = os.getenv(
        "LECTURER_REGISTRATION_CODE", "LECTURER-DEMO"
    )
