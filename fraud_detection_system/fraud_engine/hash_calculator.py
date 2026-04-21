"""
Image hash calculation module for fraud detection.
Extracts and modularizes hash calculation logic from the existing fraud detection system.
"""

import imagehash
import hashlib
from PIL import Image
from typing import Dict, Optional, NamedTuple
from dataclasses import dataclass


@dataclass
class ImageHashes:
    """Container for all calculated image hashes."""
    phash: str
    ahash: str
    dhash: str
    whash: str
    crop_resistant_hash: Optional[str] = None
    file_hash: Optional[str] = None


class HashCalculator:
    """Calculate various types of hashes for images."""
    
    # Hash algorithm parameters
    CROP_RESISTANT_MIN_SEGMENT_SIZE = 200
    CROP_RESISTANT_SEGMENTATION_SIZE = 300
    
    @classmethod
    def calculate_perceptual_hashes(cls, image_path: str) -> ImageHashes:
        """
        Calculate all perceptual hashes for an image.
        Based on existing fraud_detection.py logic.
        """
        try:
            with Image.open(image_path) as img:
                # Standard perceptual hashes
                phash = imagehash.phash(img)
                ahash = imagehash.average_hash(img)
                dhash = imagehash.dhash(img)
                whash = imagehash.whash(img)  # Wavelet hash for scale detection
                
                # Crop-resistant hash for detecting crops/zooms
                crop_hash = None
                try:
                    crop_hash = imagehash.crop_resistant_hash(
                        img,
                        min_segment_size=cls.CROP_RESISTANT_MIN_SEGMENT_SIZE,
                        segmentation_image_size=cls.CROP_RESISTANT_SEGMENTATION_SIZE
                    )
                except Exception:
                    # Crop-resistant hash can fail on some images
                    crop_hash = None
            
            # Calculate file hash (MD5)
            file_hash = cls.calculate_file_hash(image_path)
            
            return ImageHashes(
                phash=str(phash),
                ahash=str(ahash),
                dhash=str(dhash),
                whash=str(whash),
                crop_resistant_hash=str(crop_hash) if crop_hash else None,
                file_hash=file_hash
            )
        
        except Exception as e:
            raise ValueError(f"Failed to calculate hashes for {image_path}: {str(e)}")
    
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """Calculate MD5 hash of file content."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    @staticmethod
    def calculate_hash_similarities(hash1: ImageHashes, hash2: ImageHashes) -> Dict[str, float]:
        """
        Calculate similarity scores between two sets of hashes.
        Returns similarity percentages (0-100%).
        """
        try:
            # Convert string hashes back to imagehash objects for distance calculation
            phash1 = imagehash.hex_to_hash(hash1.phash)
            phash2 = imagehash.hex_to_hash(hash2.phash)
            ahash1 = imagehash.hex_to_hash(hash1.ahash)
            ahash2 = imagehash.hex_to_hash(hash2.ahash)
            dhash1 = imagehash.hex_to_hash(hash1.dhash)
            dhash2 = imagehash.hex_to_hash(hash2.dhash)
            whash1 = imagehash.hex_to_hash(hash1.whash)
            whash2 = imagehash.hex_to_hash(hash2.whash)
            
            # Calculate distances
            phash_distance = phash1 - phash2
            ahash_distance = ahash1 - ahash2
            dhash_distance = dhash1 - dhash2
            whash_distance = whash1 - whash2
            
            # Convert distances to similarity percentages
            phash_similarity = (1 - phash_distance / 64) * 100
            ahash_similarity = (1 - ahash_distance / 64) * 100
            dhash_similarity = (1 - dhash_distance / 64) * 100
            whash_similarity = (1 - whash_distance / 64) * 100
            
            # Ensure similarities are within 0-100 range
            phash_similarity = max(0, min(100, phash_similarity))
            ahash_similarity = max(0, min(100, ahash_similarity))
            dhash_similarity = max(0, min(100, dhash_similarity))
            whash_similarity = max(0, min(100, whash_similarity))
            
            similarities = {
                'phash': phash_similarity,
                'ahash': ahash_similarity,
                'dhash': dhash_similarity,
                'whash': whash_similarity
            }
            
            # Crop-resistant similarity (if available for both images)
            if hash1.crop_resistant_hash and hash2.crop_resistant_hash:
                try:
                    crhash1 = imagehash.hex_to_hash(hash1.crop_resistant_hash)
                    crhash2 = imagehash.hex_to_hash(hash2.crop_resistant_hash)
                    crop_distance = crhash1 - crhash2
                    crop_similarity = (1 - min(crop_distance, 100) / 100) * 100
                    crop_similarity = max(0, min(100, crop_similarity))
                    similarities['crop_resistant'] = crop_similarity
                except Exception:
                    similarities['crop_resistant'] = 0.0
            else:
                similarities['crop_resistant'] = 0.0
            
            return similarities
        
        except Exception as e:
            raise ValueError(f"Failed to calculate similarities: {str(e)}")
    
    @staticmethod
    def calculate_combined_similarity(similarities: Dict[str, float]) -> float:
        """
        Calculate combined visual similarity score.
        Based on the weighting from existing fraud_detection.py logic.
        """
        # Weights based on existing algorithm
        if similarities.get('crop_resistant', 0) > 0:
            # Include crop-resistant hash in calculation
            combined = (
                similarities['phash'] * 0.3 +
                similarities['ahash'] * 0.2 +
                similarities['dhash'] * 0.15 +
                similarities['whash'] * 0.25 +
                similarities['crop_resistant'] * 0.1
            )
        else:
            # Standard algorithm without crop-resistant hash
            combined = (
                similarities['phash'] * 0.4 +
                similarities['ahash'] * 0.25 +
                similarities['dhash'] * 0.2 +
                similarities['whash'] * 0.15
            )
        
        return max(0, min(100, combined))
    
    @staticmethod
    def are_files_identical(hash1: ImageHashes, hash2: ImageHashes) -> bool:
        """Check if two images are identical files based on MD5 hash."""
        if hash1.file_hash and hash2.file_hash:
            return hash1.file_hash == hash2.file_hash
        return False


class BatchHashProcessor:
    """Process multiple images for hash calculation."""
    
    def __init__(self):
        self.calculator = HashCalculator()
    
    def process_images(self, image_paths: list) -> Dict[str, ImageHashes]:
        """
        Process multiple images and return their hashes.
        Returns: {image_path: ImageHashes}
        """
        results = {}
        
        for image_path in image_paths:
            try:
                hashes = self.calculator.calculate_perceptual_hashes(image_path)
                results[image_path] = hashes
            except Exception as e:
                print(f"Warning: Failed to process {image_path}: {e}")
                # Continue processing other images
        
        return results
    
    def process_images_with_progress(self, image_paths: list, progress_callback=None) -> Dict[str, ImageHashes]:
        """
        Process multiple images with progress tracking.
        """
        results = {}
        total = len(image_paths)
        
        for i, image_path in enumerate(image_paths):
            try:
                hashes = self.calculator.calculate_perceptual_hashes(image_path)
                results[image_path] = hashes
                
                if progress_callback:
                    progress_callback(i + 1, total, image_path)
            
            except Exception as e:
                print(f"Warning: Failed to process {image_path}: {e}")
                if progress_callback:
                    progress_callback(i + 1, total, f"{image_path} (FAILED)")
        
        return results