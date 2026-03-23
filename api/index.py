"""Vercel serverless entry point — wraps the FastAPI app and auto-seeds on cold start."""

import os
import sys
import asyncio

# Make backend/ importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from database import DB_PATH, init_db

# Auto-seed demo data on Vercel cold start if DB doesn't exist
if os.environ.get("VERCEL") and not DB_PATH.exists():
    from seed_data import seed
    asyncio.get_event_loop().run_until_complete(seed())

# Import the FastAPI app (this triggers lifespan/init_db too)
from main import app  # noqa: F401 — Vercel picks up `app` as the ASGI handler
