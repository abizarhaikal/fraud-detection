"""
Database connection and session management.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .models import Base
from utils.config import Config

class Database:
    """Database connection manager."""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize()
    
    def _initialize(self):
        """Initialize database connection."""
        database_url = Config.get_database_url()
        
        # Ensure the database directory exists
        db_dir = os.path.dirname(Config.get_database_path())
        os.makedirs(db_dir, exist_ok=True)
        
        self.engine = create_engine(
            database_url,
            echo=Config.get_debug_mode(),  # Enable SQL logging in debug mode
            pool_pre_ping=True  # Enable connection health checks
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all database tables. Use with caution!"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self):
        """Get a new database session."""
        return self.SessionLocal()
    
    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()


# Global database instance
db = Database()


def get_db():
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.
    """
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


def init_database():
    """Initialize the database and create tables."""
    print("Initializing database...")
    db.create_tables()
    print("Database initialized successfully!")