"""
Batch processing service for calculating and storing image hashes.
Handles pre-calculation of hashes for historical images and database integration.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Callable
import time

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from .hash_calculator import HashCalculator, ImageHashes, BatchHashProcessor
from database.operations import EventImageOperations, ImageHashOperations
from database.database import get_db
from utils.config import Config


class DatabaseHashProcessor:
    """Process images from database and store calculated hashes."""
    
    def __init__(self):
        self.calculator = HashCalculator()
        self.batch_processor = BatchHashProcessor()
    
    def process_image_and_store(self, image_id: int, image_path: str, db_session) -> bool:
        """
        Calculate hashes for a single image and store in database.
        Returns: True if successful, False otherwise
        """
        try:
            # Check if hashes already exist
            existing_hash = ImageHashOperations.get_hash_by_image_id(db_session, image_id)
            if existing_hash:
                return True  # Already processed
            
            # Calculate hashes
            hashes = self.calculator.calculate_perceptual_hashes(image_path)
            
            # Store in database
            ImageHashOperations.create_image_hash(
                db_session,
                image_id=image_id,
                phash=hashes.phash,
                ahash=hashes.ahash,
                dhash=hashes.dhash,
                whash=hashes.whash,
                crop_resistant_hash=hashes.crop_resistant_hash,
                file_hash=hashes.file_hash
            )
            
            return True
        
        except Exception as e:
            print(f"Error processing image {image_id} ({image_path}): {e}")
            return False
    
    def process_all_unprocessed_images(self, progress_callback: Optional[Callable] = None) -> Dict[str, int]:
        """
        Process all images in database that don't have hashes calculated.
        Returns: Statistics about processing results
        """
        stats = {
            'total_images': 0,
            'processed': 0,
            'already_processed': 0,
            'failed': 0,
            'missing_files': 0
        }
        
        with next(get_db()) as db:
            # Get all images from database
            all_images = EventImageOperations.get_all_images(db)
            stats['total_images'] = len(all_images)
            
            if progress_callback:
                progress_callback(0, stats['total_images'], "Starting batch processing...")
            
            for i, image in enumerate(all_images):
                try:
                    # Check if already processed
                    existing_hash = ImageHashOperations.get_hash_by_image_id(db, image.id)
                    if existing_hash:
                        stats['already_processed'] += 1
                        if progress_callback:
                            progress_callback(i + 1, stats['total_images'], 
                                            f"Skipped {image.filename} (already processed)")
                        continue
                    
                    # Check if file exists
                    if not os.path.exists(image.file_path):
                        stats['missing_files'] += 1
                        if progress_callback:
                            progress_callback(i + 1, stats['total_images'], 
                                            f"Missing file: {image.filename}")
                        continue
                    
                    # Process the image
                    success = self.process_image_and_store(image.id, image.file_path, db)
                    
                    if success:
                        stats['processed'] += 1
                        if progress_callback:
                            progress_callback(i + 1, stats['total_images'], 
                                            f"Processed {image.filename}")
                    else:
                        stats['failed'] += 1
                        if progress_callback:
                            progress_callback(i + 1, stats['total_images'], 
                                            f"Failed {image.filename}")
                
                except Exception as e:
                    stats['failed'] += 1
                    if progress_callback:
                        progress_callback(i + 1, stats['total_images'], 
                                        f"Error processing {image.filename}: {e}")
        
        return stats
    
    def process_event_images(self, event_id: int, progress_callback: Optional[Callable] = None) -> Dict[str, int]:
        """
        Process all images for a specific event.
        Returns: Processing statistics
        """
        stats = {
            'total_images': 0,
            'processed': 0,
            'already_processed': 0,
            'failed': 0,
            'missing_files': 0
        }
        
        with next(get_db()) as db:
            # Get images for the event
            event_images = EventImageOperations.get_images_by_event(db, event_id)
            stats['total_images'] = len(event_images)
            
            if progress_callback:
                progress_callback(0, stats['total_images'], f"Processing event {event_id} images...")
            
            for i, image in enumerate(event_images):
                try:
                    # Check if already processed
                    existing_hash = ImageHashOperations.get_hash_by_image_id(db, image.id)
                    if existing_hash:
                        stats['already_processed'] += 1
                        if progress_callback:
                            progress_callback(i + 1, stats['total_images'], 
                                            f"Skipped {image.filename}")
                        continue
                    
                    # Check if file exists
                    if not os.path.exists(image.file_path):
                        stats['missing_files'] += 1
                        if progress_callback:
                            progress_callback(i + 1, stats['total_images'], 
                                            f"Missing: {image.filename}")
                        continue
                    
                    # Process the image
                    success = self.process_image_and_store(image.id, image.file_path, db)
                    
                    if success:
                        stats['processed'] += 1
                        if progress_callback:
                            progress_callback(i + 1, stats['total_images'], 
                                            f"Processed {image.filename}")
                    else:
                        stats['failed'] += 1
                        if progress_callback:
                            progress_callback(i + 1, stats['total_images'], 
                                            f"Failed {image.filename}")
                
                except Exception as e:
                    stats['failed'] += 1
                    if progress_callback:
                        progress_callback(i + 1, stats['total_images'], 
                                        f"Error: {image.filename} - {e}")
        
        return stats
    
    def get_processing_status(self) -> Dict[str, int]:
        """
        Get current processing status from database.
        Returns: Status statistics
        """
        with next(get_db()) as db:
            all_images = EventImageOperations.get_all_images(db)
            all_hashes = ImageHashOperations.get_all_hashes(db)
            
            total_images = len(all_images)
            processed_images = len(all_hashes)
            unprocessed_images = total_images - processed_images
            
            # Check for missing files
            missing_files = 0
            for image in all_images:
                if not os.path.exists(image.file_path):
                    missing_files += 1
            
            return {
                'total_images': total_images,
                'processed_images': processed_images,
                'unprocessed_images': unprocessed_images,
                'missing_files': missing_files,
                'processing_percentage': (processed_images / total_images * 100) if total_images > 0 else 0
            }
    
    def recalculate_hashes(self, force: bool = False, progress_callback: Optional[Callable] = None) -> Dict[str, int]:
        """
        Recalculate hashes for all images, optionally forcing recalculation of existing hashes.
        """
        stats = {
            'total_images': 0,
            'processed': 0,
            'updated': 0,
            'failed': 0,
            'missing_files': 0
        }
        
        with next(get_db()) as db:
            all_images = EventImageOperations.get_all_images(db)
            stats['total_images'] = len(all_images)
            
            if progress_callback:
                progress_callback(0, stats['total_images'], "Starting hash recalculation...")
            
            for i, image in enumerate(all_images):
                try:
                    # Check if file exists
                    if not os.path.exists(image.file_path):
                        stats['missing_files'] += 1
                        if progress_callback:
                            progress_callback(i + 1, stats['total_images'], 
                                            f"Missing: {image.filename}")
                        continue
                    
                    # Check if hash exists and whether to skip
                    existing_hash = ImageHashOperations.get_hash_by_image_id(db, image.id)
                    
                    if existing_hash and not force:
                        # Skip existing hashes unless forced
                        if progress_callback:
                            progress_callback(i + 1, stats['total_images'], 
                                            f"Skipped {image.filename}")
                        continue
                    
                    # Calculate new hashes
                    hashes = self.calculator.calculate_perceptual_hashes(image.file_path)
                    
                    if existing_hash:
                        # Update existing hash record
                        existing_hash.phash = hashes.phash
                        existing_hash.ahash = hashes.ahash
                        existing_hash.dhash = hashes.dhash
                        existing_hash.whash = hashes.whash
                        existing_hash.crop_resistant_hash = hashes.crop_resistant_hash
                        existing_hash.file_hash = hashes.file_hash
                        existing_hash.calculated_at = time.time()
                        db.commit()
                        stats['updated'] += 1
                    else:
                        # Create new hash record
                        ImageHashOperations.create_image_hash(
                            db,
                            image_id=image.id,
                            phash=hashes.phash,
                            ahash=hashes.ahash,
                            dhash=hashes.dhash,
                            whash=hashes.whash,
                            crop_resistant_hash=hashes.crop_resistant_hash,
                            file_hash=hashes.file_hash
                        )
                        stats['processed'] += 1
                    
                    if progress_callback:
                        action = "Updated" if existing_hash else "Processed"
                        progress_callback(i + 1, stats['total_images'], 
                                        f"{action} {image.filename}")
                
                except Exception as e:
                    stats['failed'] += 1
                    if progress_callback:
                        progress_callback(i + 1, stats['total_images'], 
                                        f"Failed {image.filename}: {e}")
        
        return stats


# Convenience functions for easy access
def process_all_images(progress_callback: Optional[Callable] = None) -> Dict[str, int]:
    """Process all unprocessed images with optional progress callback."""
    processor = DatabaseHashProcessor()
    return processor.process_all_unprocessed_images(progress_callback)


def get_processing_status() -> Dict[str, int]:
    """Get current hash processing status."""
    processor = DatabaseHashProcessor()
    return processor.get_processing_status()


def process_new_image(image_id: int, image_path: str) -> bool:
    """Process a single new image and store its hashes."""
    processor = DatabaseHashProcessor()
    with next(get_db()) as db:
        return processor.process_image_and_store(image_id, image_path, db)