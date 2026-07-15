from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class Database:
    def __init__(self):
        self.database_url = settings.database_url
        # For SQLite, we might need connect_args={"check_same_thread": False}
        connect_args = {}
        if self.database_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
            
        self.engine = create_engine(
            self.database_url,
            connect_args=connect_args,
            pool_size=20,
            max_overflow=30,
            pool_timeout=60,
            pool_recycle=1800,
            pool_pre_ping=True
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully.")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise e

    def get_db(self):
        """Dependency to get database session"""
        db_session = self.SessionLocal()
        try:
            yield db_session
        finally:
            db_session.close()

db = Database()
