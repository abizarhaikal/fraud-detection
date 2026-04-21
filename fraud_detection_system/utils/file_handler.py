"""
File handling utilities for the fraud detection system.
"""

import os
import uuid
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image

from .config import Config


class FileHandler:
    """File handling utilities for image uploads and storage."""
    
    def __init__(self):
        Config.ensure_directories()
    
    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """Generate a unique filename while preserving the extension."""
        file_extension = Path(original_filename).suffix.lower()
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{file_extension}"
    
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """Calculate MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    @staticmethod
    def validate_image_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if the file is a valid image.
        Returns: (is_valid, error_message)
        """
        try:
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > Config.get_max_file_size_bytes():
                return False, f"File size ({file_size / (1024*1024):.1f}MB) exceeds maximum allowed size ({Config.MAX_FILE_SIZE_MB}MB)"
            
            # Check if it's a valid image
            with Image.open(file_path) as img:
                img.verify()  # Verify it's a valid image
            
            # Re-open for format check (verify() closes the image)
            with Image.open(file_path) as img:
                # Check image format
                if not img.format:
                    return False, "Could not determine image format"
                
                # Check minimum dimensions (optional)
                width, height = img.size
                if width < 50 or height < 50:
                    return False, f"Image dimensions ({width}x{height}) are too small (minimum 50x50)"
                
                return True, None
        
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"
    
    @staticmethod
    def save_uploaded_file(file_content: bytes, original_filename: str) -> Tuple[str, str]:
        """
        Save uploaded file content to storage.
        Returns: (unique_filename, full_file_path)
        """
        # Check file extension
        if not Config.is_allowed_file(original_filename):
            raise ValueError(f"File type not allowed. Allowed types: {Config.ALLOWED_EXTENSIONS}")
        
        # Generate unique filename
        unique_filename = FileHandler.generate_unique_filename(original_filename)
        file_path = os.path.join(Config.get_uploads_dir(), unique_filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Validate the saved image
        is_valid, error_msg = FileHandler.validate_image_file(file_path)
        if not is_valid:
            # Remove invalid file
            os.remove(file_path)
            raise ValueError(f"Invalid image file: {error_msg}")
        
        return unique_filename, file_path
    
    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """Get comprehensive file information."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = os.stat(file_path)
        file_hash = FileHandler.calculate_file_hash(file_path)
        
        # Get image dimensions
        dimensions = None
        try:
            with Image.open(file_path) as img:
                dimensions = img.size
        except Exception:
            pass  # Not an image or corrupted
        
        return {
            'size': stat.st_size,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'hash': file_hash,
            'dimensions': dimensions
        }
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Delete a file safely."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            return False
    
    @staticmethod
    def get_storage_stats() -> dict:
        """Get storage usage statistics."""
        uploads_dir = Config.get_uploads_dir()
        
        total_files = 0
        total_size = 0
        
        if os.path.exists(uploads_dir):
            for filename in os.listdir(uploads_dir):
                file_path = os.path.join(uploads_dir, filename)
                if os.path.isfile(file_path):
                    total_files += 1
                    total_size += os.path.getsize(file_path)
        
        return {
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'uploads_directory': uploads_dir
        }


class StreamlitFileHandler:
    """Specialized file handler for Streamlit uploads."""
    
    @staticmethod
    def process_streamlit_upload(uploaded_file) -> Tuple[str, str, int]:
        """
        Process a Streamlit uploaded file.
        Returns: (unique_filename, full_file_path, file_size)
        """
        # Read file content
        file_content = uploaded_file.read()
        file_size = len(file_content)
        
        # Check file size before processing
        if file_size > Config.get_max_file_size_bytes():
            raise ValueError(f"File size ({file_size / (1024*1024):.1f}MB) exceeds maximum allowed size ({Config.MAX_FILE_SIZE_MB}MB)")
        
        # Save file
        unique_filename, file_path = FileHandler.save_uploaded_file(file_content, uploaded_file.name)
        
        return unique_filename, file_path, file_size
    
    @staticmethod
    def process_multiple_uploads(uploaded_files) -> list:
        """
        Process multiple Streamlit uploaded files.
        Returns: List of (original_name, unique_filename, full_file_path, file_size)
        """
        results = []
        
        for uploaded_file in uploaded_files:
            try:
                unique_filename, file_path, file_size = StreamlitFileHandler.process_streamlit_upload(uploaded_file)
                results.append({
                    'original_name': uploaded_file.name,
                    'unique_filename': unique_filename,
                    'file_path': file_path,
                    'file_size': file_size,
                    'status': 'success',
                    'error': None
                })
            except Exception as e:
                results.append({
                    'original_name': uploaded_file.name,
                    'unique_filename': None,
                    'file_path': None,
                    'file_size': None,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results