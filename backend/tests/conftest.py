import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.core.database import get_db
from app.models import Base
from main import app


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test.db"
    upload_dir = tmp_path / "uploads"
    export_dir = tmp_path / "exports"
    snapshot_dir = tmp_path / "snapshots"

    settings.DATABASE_URL = f"sqlite:///{db_path}"
    settings.UPLOAD_DIR = str(upload_dir)
    settings.EXPORT_DIR = str(export_dir)
    settings.SNAPSHOT_DIR = str(snapshot_dir)

    upload_dir.mkdir(parents=True, exist_ok=True)
    export_dir.mkdir(parents=True, exist_ok=True)
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
