"""
Image comparison service for fraud detection.
Handles comparison logic between images and calculates similarity scores.
"""

from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
import json

from .hash_calculator import HashCalculator, ImageHashes


@dataclass
class ComparisonResult:
    """Results of comparing two images."""
    similarity_scores: Dict[str, float]
    combined_similarity: float
    hash_distances: Dict[str, int]
    analysis_flags: List[str]
    consensus_score: float
    crop_outlier: bool = False


class ImageComparator:
    """Compare images for fraud detection."""
    
    def __init__(self):
        self.calculator = HashCalculator()
    
    def compare_images(self, hash1: ImageHashes, hash2: ImageHashes, 
                      metadata_flags: List[str] = None, 
                      filename_flags: List[str] = None) -> ComparisonResult:
        """
        Compare two images using their hashes and return detailed comparison results.
        Based on the existing fraud_detection.py comparison logic.
        """
        metadata_flags = metadata_flags or []
        filename_flags = filename_flags or []
        
        # Calculate similarity scores
        similarities = self.calculator.calculate_hash_similarities(hash1, hash2)
        combined_similarity = self.calculator.calculate_combined_similarity(similarities)
        
        # Calculate hash distances for analysis
        hash_distances = self._calculate_hash_distances(hash1, hash2)
        
        # Analyze consensus between algorithms
        consensus_analysis = self._analyze_algorithm_consensus(similarities)
        
        # Detect crop outliers
        crop_outlier = self._detect_crop_outlier(similarities, consensus_analysis['avg_standard'])
        
        # Generate analysis flags
        analysis_flags = self._generate_analysis_flags(
            similarities, consensus_analysis, crop_outlier, 
            metadata_flags, filename_flags
        )
        
        return ComparisonResult(
            similarity_scores=similarities,
            combined_similarity=combined_similarity,
            hash_distances=hash_distances,
            analysis_flags=analysis_flags,
            consensus_score=consensus_analysis['avg_standard'],
            crop_outlier=crop_outlier
        )
    
    def _calculate_hash_distances(self, hash1: ImageHashes, hash2: ImageHashes) -> Dict[str, int]:
        """Calculate raw hash distances."""
        import imagehash
        
        try:
            # Convert hashes back to imagehash objects
            phash1 = imagehash.hex_to_hash(hash1.phash)
            phash2 = imagehash.hex_to_hash(hash2.phash)
            ahash1 = imagehash.hex_to_hash(hash1.ahash)
            ahash2 = imagehash.hex_to_hash(hash2.ahash)
            dhash1 = imagehash.hex_to_hash(hash1.dhash)
            dhash2 = imagehash.hex_to_hash(hash2.dhash)
            whash1 = imagehash.hex_to_hash(hash1.whash)
            whash2 = imagehash.hex_to_hash(hash2.whash)
            
            distances = {
                'phash': phash1 - phash2,
                'ahash': ahash1 - ahash2,
                'dhash': dhash1 - dhash2,
                'whash': whash1 - whash2
            }
            
            # Crop-resistant distance if available
            if hash1.crop_resistant_hash and hash2.crop_resistant_hash:
                try:
                    crhash1 = imagehash.hex_to_hash(hash1.crop_resistant_hash)
                    crhash2 = imagehash.hex_to_hash(hash2.crop_resistant_hash)
                    distances['crop_resistant'] = crhash1 - crhash2
                except Exception:
                    distances['crop_resistant'] = 100  # Max distance on error
            
            return distances
        
        except Exception:
            # Return max distances on error
            return {
                'phash': 64,
                'ahash': 64,
                'dhash': 64,
                'whash': 64,
                'crop_resistant': 100
            }
    
    def _analyze_algorithm_consensus(self, similarities: Dict[str, float]) -> Dict[str, float]:
        """Analyze consensus between standard algorithms."""
        standard_algorithms = ['phash', 'ahash', 'dhash', 'whash']
        standard_similarities = [similarities[alg] for alg in standard_algorithms if alg in similarities]
        
        if standard_similarities:
            avg_standard = sum(standard_similarities) / len(standard_similarities)
        else:
            avg_standard = 0.0
        
        return {
            'avg_standard': avg_standard,
            'algorithms_above_60': sum(1 for sim in standard_similarities if sim > 60),
            'algorithms_above_70': sum(1 for sim in standard_similarities if sim > 70),
            'high_consensus': avg_standard > 65,
            'moderate_consensus': avg_standard > 55
        }
    
    def _detect_crop_outlier(self, similarities: Dict[str, float], avg_standard: float) -> bool:
        """
        Detect if crop-resistant algorithm is giving false positives.
        Based on existing logic from fraud_detection.py.
        """
        crop_similarity = similarities.get('crop_resistant', 0)
        
        if crop_similarity > 0:
            crop_vs_avg_diff = abs(crop_similarity - avg_standard)
            # Crop shows high similarity but others don't
            if crop_vs_avg_diff > 30 and crop_similarity > 80:
                return True
        
        return False
    
    def _generate_analysis_flags(self, similarities: Dict[str, float], 
                               consensus_analysis: Dict[str, float],
                               crop_outlier: bool,
                               metadata_flags: List[str],
                               filename_flags: List[str]) -> List[str]:
        """Generate analysis flags based on comparison results."""
        flags = []
        
        visual_similarity = self.calculator.calculate_combined_similarity(similarities)
        crop_similarity = similarities.get('crop_resistant', 0)
        whash_similarity = similarities.get('whash', 0)
        avg_standard = consensus_analysis['avg_standard']
        
        # Visual similarity flags
        if visual_similarity > 85:
            flags.append("VERY_HIGH_SIMILARITY: >85% visual match")
        elif visual_similarity > 75:
            flags.append("HIGH_SIMILARITY: >75% visual match")
        elif visual_similarity > 65:
            flags.append("MODERATE_HIGH_SIMILARITY: >65% visual match")
        
        # Consensus flags
        if consensus_analysis['high_consensus']:
            flags.append("HIGH_ALGORITHM_CONSENSUS: Multiple algorithms agree (>65%)")
        elif consensus_analysis['moderate_consensus']:
            flags.append("MODERATE_ALGORITHM_CONSENSUS: Some algorithms agree (>55%)")
        
        # Crop detection flags
        if crop_similarity > 70 and not crop_outlier:
            if avg_standard > 50:
                flags.append("VALIDATED_CROP_DETECTION: Strong crop/zoom evidence")
            else:
                flags.append("WEAK_CROP_DETECTION: Possible crop/zoom with low consensus")
        elif crop_outlier:
            flags.append("CROP_OUTLIER_DETECTED: Crop algorithm showing possible false positive")
        
        # Wavelet/scale analysis flags
        if whash_similarity > 80 and avg_standard > 60:
            flags.append("SCALE_SIMILARITY_DETECTED: Strong scale-invariant match")
        elif whash_similarity > 70 and avg_standard > 50:
            flags.append("SIMILAR_SCALE_DETECTED: Moderate scale similarity")
        
        # Multi-algorithm consensus
        if consensus_analysis['algorithms_above_60'] >= 3:
            flags.append(f"MULTI_ALGORITHM_CONSENSUS: {consensus_analysis['algorithms_above_60']}/4 algorithms >60%")
        
        # Filename pattern analysis
        same_entity = any("SAME_ENTITY_NAME" in flag for flag in filename_flags)
        same_event_timeframe = any("SAME_EVENT_TIMEFRAME" in flag for flag in filename_flags)
        identical_dates = any("IDENTICAL_FILENAME_DATES" in flag for flag in filename_flags)
        
        if same_entity:
            flags.append("SAME_ENTITY_DETECTED: Filename indicates same entity")
        if same_event_timeframe:
            flags.append("SAME_EVENT_TIMEFRAME_DETECTED: Filename dates suggest same event")
        if identical_dates:
            flags.append("IDENTICAL_DATES_DETECTED: Exact date match in filenames")
        
        # Metadata analysis
        identical_dimensions = any("IDENTICAL_DIMENSIONS" in flag for flag in metadata_flags)
        if identical_dimensions:
            flags.append("IDENTICAL_DIMENSIONS_DETECTED: Same image dimensions")
        
        return flags
    
    def compare_with_database_images(self, new_hash: ImageHashes, 
                                   historical_hashes: List[Tuple[int, ImageHashes]],
                                   exclude_event_id: Optional[int] = None) -> List[Tuple[int, ComparisonResult]]:
        """
        Compare a new image hash against all historical image hashes.
        Returns: List of (image_id, ComparisonResult) for significant matches.
        """
        results = []
        
        for image_id, historical_hash in historical_hashes:
            # Skip images from the same event if specified
            if exclude_event_id and hasattr(historical_hash, 'event_id') and historical_hash.event_id == exclude_event_id:
                continue
            
            comparison = self.compare_images(new_hash, historical_hash)
            
            # Only include results with significant similarity
            if (comparison.combined_similarity > 30 or 
                any(score > 40 for score in comparison.similarity_scores.values())):
                results.append((image_id, comparison))
        
        # Sort by combined similarity (highest first)
        results.sort(key=lambda x: x[1].combined_similarity, reverse=True)
        
        return results