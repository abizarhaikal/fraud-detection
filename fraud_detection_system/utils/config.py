"""
Configuration management for the fraud detection system.
"""

import os
from pathlib import Path


class Config:
    """Configuration class for the fraud detection system."""
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent.parent  # fraud_detection_system parent directory
    SYSTEM_DIR = BASE_DIR / "fraud_detection_system"
    STORAGE_DIR = SYSTEM_DIR / "storage"
    UPLOADS_DIR = STORAGE_DIR / "uploads"
    
    # Database settings
    DATABASE_NAME = "fraud_detection.db"
    DATABASE_PATH = STORAGE_DIR / DATABASE_NAME
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
    
    # Application settings
    DEBUG_MODE = True
    MAX_FILE_SIZE_MB = 50
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    
    # Streamlit settings
    STREAMLIT_TITLE = "Vendor Event Fraud Detection System"
    STREAMLIT_ICON = "🕵️"
    
    @classmethod
    def get_database_url(cls):
        """Get database URL."""
        return str(cls.DATABASE_URL)
    
    @classmethod
    def get_database_path(cls):
        """Get database file path."""
        return str(cls.DATABASE_PATH)
    
    @classmethod
    def get_uploads_dir(cls):
        """Get uploads directory path."""
        return str(cls.UPLOADS_DIR)
    
    @classmethod
    def get_debug_mode(cls):
        """Get debug mode setting."""
        return cls.DEBUG_MODE
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist."""
        cls.STORAGE_DIR.mkdir(exist_ok=True)
        cls.UPLOADS_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def is_allowed_file(cls, filename):
        """Check if file extension is allowed."""
        return Path(filename).suffix.lower() in cls.ALLOWED_EXTENSIONS
    
    @classmethod
    def get_max_file_size_bytes(cls):
        """Get maximum file size in bytes."""
        return cls.MAX_FILE_SIZE_MB * 1024 * 1024