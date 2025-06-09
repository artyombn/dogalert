from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config.config import settings

sync_db_url = settings.get_db_url().replace("postgresql+asyncpg://", "postgresql://")

celery_sync_engine = create_engine(
    sync_db_url,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

celery_sync_session_maker = sessionmaker(
    bind=celery_sync_engine,
    autoflush=True,
    autocommit=False,
)
