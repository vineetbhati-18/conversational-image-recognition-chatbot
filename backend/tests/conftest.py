import sys
from pathlib import Path
from sqlalchemy import create_engine

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import get_settings
from app.core.database import Base
import app.models  # ensure models are registered


def pytest_sessionstart(session):
    """
    Called once at the very start of the pytest test run.
    Synchronously creates all database tables if database is available.
    """
    settings = get_settings()
    try:
        sync_engine = create_engine(settings.SYNC_DATABASE_URL)
        Base.metadata.create_all(bind=sync_engine)
        sync_engine.dispose()
    except Exception as e:
        print(f"Test DB init notice: {e}")
