from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.base import Base

url = make_url(settings.DATABASE_URL)
connect_args = {}
if url.drivername.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine: Engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    connect_args=connect_args,
)


if url.drivername.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_runtime_directories() -> None:
    for directory in [settings.UPLOAD_DIR, settings.EXPORT_DIR, settings.SNAPSHOT_DIR]:
        Path(directory).mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    from app.models import asset, evaluation_item, evaluation_record, evidence, extracted_field, project, template  # noqa: F401

    ensure_runtime_directories()
    Base.metadata.create_all(bind=engine)
