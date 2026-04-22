"""
Fraud analysis engine for the fraud detection system.
Integrates comparison results with fraud scoring and verdict determination.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from .hash_calculator import ImageHashes
from .comparator import ImageComparator, ComparisonResult
from .ai_analyzer import AIComparator
from database.models import EventImage, ImageHash, FraudAnalysis
from database.operations import FraudAnalysisOperations, ImageHashOperations


@dataclass
class FraudAnalysisResult:
    """Complete fraud analysis result for an image comparison."""
    comparison_result: ComparisonResult
    fraud_score: int
    verdict: str
    verdict_emoji: str
    recommendations: List[str]
    auto_triggers: List[str]
    analysis_summary: Dict


class FraudAnalyzer:
    """
    Main fraud analysis engine.
    Integrates comparison results with fraud scoring logic from existing system.
    """
    
    # Verdict thresholds based on existing logic
    HIGH_RISK_THRESHOLD = 80
    MODERATE_RISK_THRESHOLD = 60
    LOW_RISK_THRESHOLD = 40
    
    def __init__(self):
        self.comparator = ImageComparator()
        self.ai_engine = AIComparator()
    
    def analyze_image_fraud(self, new_image_hash: ImageHashes,
                           comparison_image_hash: ImageHashes,
                           metadata_flags: List[str] = None,
                           filename_flags: List[str] = None,
                           ai_score: float = 0.0) -> FraudAnalysisResult:
        """
        Perform complete fraud analysis between two images.
        Based on the scoring logic from existing fraud_detection.py.
        """
        metadata_flags = metadata_flags or []
        filename_flags = filename_flags or []
        
        # Get comparison results
        comparison = self.comparator.compare_images(
            new_image_hash, comparison_image_hash, 
            metadata_flags, filename_flags
        )
        
        # Calculate fraud score
        fraud_score, auto_triggers = self._calculate_fraud_score(
            comparison, metadata_flags, filename_flags, ai_score=ai_score
        )
        
        # Determine verdict
        verdict, verdict_emoji = self._determine_verdict(fraud_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(fraud_score, comparison)
        
        # Create analysis summary
        analysis_summary = self._create_analysis_summary(
            comparison, fraud_score, metadata_flags, filename_flags
        )
        
        return FraudAnalysisResult(
            comparison_result=comparison,
            fraud_score=fraud_score,
            verdict=verdict,
            verdict_emoji=verdict_emoji,
            recommendations=recommendations,
            auto_triggers=auto_triggers,
            analysis_summary=analysis_summary
        )
    
    def _calculate_fraud_score(self, comparison: ComparisonResult,
                             metadata_flags: List[str],
                             filename_flags: List[str], ai_score: float = 0.0) -> Tuple[int, List[str]]:
        """
        Calculate fraud score based on existing algorithm from fraud_detection.py.
        Returns: (fraud_score, auto_triggers)
        """
        fraud_score = 0
        auto_triggers = []
        
        visual_similarity = comparison.combined_similarity
        similarities = comparison.similarity_scores
        crop_similarity = similarities.get('crop_resistant', 0)
        whash_similarity = similarities.get('whash', 0)
        avg_standard_similarity = comparison.consensus_score
        
        # 1. Visual similarity component (0-60 points) - AGGRESSIVE scoring
        if visual_similarity > 85:
            fraud_score += 60  # Very high similarity = definite fraud
        elif visual_similarity > 75:
            fraud_score += 50  # High similarity = likely fraud
        elif visual_similarity > 65:
            fraud_score += 45  # Moderate-high similarity = HIGH RISK
        elif visual_similarity > 55:
            fraud_score += 35  # Moderate similarity = concerning
        elif visual_similarity > 45:
            fraud_score += 25  # Some similarity = worth noting
        elif visual_similarity > 35:
            fraud_score += 15  # Low similarity = monitor
        
        # 2. VALIDATED CROP/ZOOM DETECTION BONUS (0-25 points)
        if crop_similarity > 70 and not comparison.crop_outlier:
            if avg_standard_similarity > 50:
                fraud_score += 25  # Strong validated crop detection
            else:
                fraud_score += 10  # Weak consensus, reduced score
        elif crop_similarity > 50 and not comparison.crop_outlier:
            if avg_standard_similarity > 40:
                fraud_score += 15  # Moderate validated crop detection
            else:
                fraud_score += 5   # Very weak consensus
        
        # 3. WAVELET ANALYSIS BONUS (0-15 points) - Scale invariant detection
        if whash_similarity > 80 and avg_standard_similarity > 60:
            fraud_score += 15  # High wavelet similarity with consensus
        elif whash_similarity > 70 and avg_standard_similarity > 50:
            fraud_score += 10
        elif whash_similarity > 70:
            fraud_score += 5   # Reduced score without consensus
        
        # 4. Filename pattern flags (0-20 points)
        filename_score = len(filename_flags) * 8
        fraud_score += min(filename_score, 20)
        
        # 5. Metadata flags (0-15 points)
        metadata_score = len(metadata_flags) * 8
        fraud_score += min(metadata_score, 15)
        
        # 6. AUTOMATIC HIGH RISK TRIGGERS - Check for auto-escalation
        auto_triggers = self._check_auto_triggers(
            visual_similarity, crop_similarity, whash_similarity,
            avg_standard_similarity, comparison.crop_outlier,
            metadata_flags, filename_flags, similarities
        )
        
        # Apply auto-trigger escalations
        for trigger_score in auto_triggers:
            if isinstance(trigger_score, tuple) and len(trigger_score) == 2:
                trigger_desc, trigger_score_val = trigger_score
                fraud_score = max(fraud_score, trigger_score_val)
        
        # --- TAMBAHAN 3: AI MENGAMBIL ALIH KEPUTUSAN HASH ---
        if ai_score > 85:
            fraud_score = max(fraud_score, 85) # Maksa skor jadi merah
            auto_triggers.append(("AI CLIP: Identik (Beda Sudut)", 85))
        elif ai_score > 70:
            fraud_score = max(fraud_score, 75) # Maksa skor jadi kuning
            auto_triggers.append(("AI CLIP: Sangat Mirip Visualnya", 75))
        # ----------------------------------------------------

        return min(fraud_score, 100), [t[0] if isinstance(t, tuple) else t for t in auto_triggers]
    
    def _check_auto_triggers(self, visual_similarity: float, crop_similarity: float,
                           whash_similarity: float, avg_standard_similarity: float,
                           crop_outlier: bool, metadata_flags: List[str],
                           filename_flags: List[str], similarities: Dict[str, float]) -> List[Tuple[str, int]]:
        """Check for automatic high-risk triggers."""
        triggers = []
        
        # Pattern detection from flags
        same_entity_detected = any("SAME_ENTITY_NAME" in flag for flag in filename_flags)
        same_event_timeframe = any("SAME_EVENT_TIMEFRAME" in flag or "SAME_EVENT" in flag for flag in filename_flags)
        identical_dates = any("IDENTICAL_FILENAME_DATES" in flag or "IDENTICAL_DATE" in flag for flag in filename_flags)
        identical_dimensions = any("IDENTICAL_DIMENSIONS" in flag for flag in metadata_flags)
        
        # Consensus levels
        high_consensus = avg_standard_similarity > 65
        moderate_consensus = avg_standard_similarity > 55
        
        # Auto-trigger conditions based on existing logic
        if visual_similarity > 70 and high_consensus:
            triggers.append(("High visual similarity + consensus", 80))
        
        if crop_similarity > 70 and not crop_outlier and moderate_consensus:
            triggers.append(("Validated crop/zoom detection", 82))
        
        if whash_similarity > 75 and visual_similarity > 65 and moderate_consensus:
            triggers.append(("Scale similarity + consensus", 80))
        
        if same_entity_detected and visual_similarity > 50:
            triggers.append(("Same entity + similarity", 85))
        
        if same_event_timeframe and visual_similarity > 60:
            triggers.append(("Same timeframe + similarity", 75))
        
        if same_event_timeframe and crop_similarity > 85 and visual_similarity > 50:
            triggers.append(("Same event timeframe + high crop similarity", 82))
        
        if identical_dates and crop_similarity > 85 and visual_similarity > 45:
            triggers.append(("Identical dates + high crop similarity", 80))
        
        if identical_dimensions and visual_similarity > 65 and moderate_consensus:
            triggers.append(("Identical dimensions + similarity + consensus", 78))
        
        # Multiple algorithm consensus trigger
        standard_similarities = [similarities.get(alg, 0) for alg in ['phash', 'ahash', 'dhash', 'whash']]
        algorithms_above_60 = sum(1 for sim in standard_similarities if sim > 60)
        if algorithms_above_60 >= 3 and visual_similarity > 65:
            triggers.append((f"Multiple algorithm consensus ({algorithms_above_60}/4 >60%)", 79))
        
        return triggers
    
    def _determine_verdict(self, fraud_score: int) -> Tuple[str, str]:
        """Determine verdict based on fraud score."""
        if fraud_score >= self.HIGH_RISK_THRESHOLD:
            return "HIGH_RISK_FRAUD", "🚨"
        elif fraud_score >= self.MODERATE_RISK_THRESHOLD:
            return "MODERATE_RISK", "⚠️"
        elif fraud_score >= self.LOW_RISK_THRESHOLD:
            return "LOW_RISK", "🟡"
        else:
            return "LIKELY_LEGITIMATE", "✅"
    
    def _generate_recommendations(self, fraud_score: int, comparison: ComparisonResult) -> List[str]:
        """Generate action recommendations based on analysis results."""
        recommendations = []
        
        if fraud_score >= 80:
            recommendations.extend([
                "🚨 REJECT submission immediately",
                "📞 Contact vendor for explanation",
                "🔍 Review vendor's historical submissions",
                "📋 Document incident for compliance"
            ])
        elif fraud_score >= 60:
            recommendations.extend([
                "⚠️ HOLD submission for manual review",
                "🔍 Examine images in detail",
                "📞 May require vendor clarification",
                "📝 Monitor vendor for patterns"
            ])
        elif fraud_score >= 40:
            recommendations.extend([
                "🟡 Manual review required",
                "📞 Contact vendor for clarification"
            ])
        else:
            recommendations.extend([
                "✅ Accept submission - Appears legitimate"
            ])
        
        # Add specific technical recommendations
        if comparison.crop_outlier:
            recommendations.append("⚠️ Note: Crop detection may be giving false positive")
        
        if comparison.consensus_score > 70:
            recommendations.append("🎯 High algorithm consensus - results more reliable")
        elif comparison.consensus_score < 40:
            recommendations.append("❓ Low algorithm consensus - results less certain")
        
        return recommendations
    
    def _make_json_serializable(self, obj):
        """Convert numpy types to standard Python types for JSON serialization."""
        if hasattr(obj, 'item'):  # numpy scalar
            return obj.item()
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(v) for v in obj]
        else:
            return obj

    def _create_analysis_summary(self, comparison: ComparisonResult,
                               fraud_score: int, metadata_flags: List[str],
                               filename_flags: List[str]) -> Dict:
        """Create comprehensive analysis summary for storage."""
        summary = {
            'visual_similarities': comparison.similarity_scores,
            'combined_similarity': comparison.combined_similarity,
            'consensus_score': comparison.consensus_score,
            'hash_distances': comparison.hash_distances,
            'analysis_flags': comparison.analysis_flags,
            'metadata_flags': metadata_flags,
            'filename_flags': filename_flags,
            'crop_outlier_detected': comparison.crop_outlier,
            'fraud_score': fraud_score,
            'analysis_timestamp': datetime.utcnow().isoformat()
        }
        
        # Ensure all values are JSON serializable
        return self._make_json_serializable(summary)
    
    def analyze_new_event_submission(self, event_id: int, db_session) -> List[FraudAnalysisResult]:
        """
        Analyze all images in a new event submission against historical images.
        """
        from database.operations import EventImageOperations
        
        # Get all images for the new event
        new_images = EventImageOperations.get_images_by_event(db_session, event_id)
        
        # Get all historical images (excluding current event)
        historical_images = EventImageOperations.get_images_for_analysis(db_session, event_id)
        
        results = []
        
        for new_image in new_images:
            # Get hash for new image
            new_hash_record = ImageHashOperations.get_hash_by_image_id(db_session, new_image.id)
            if not new_hash_record:
                continue
            
            # --- TAMBAHAN 4A: AI Baca Foto Baru ---
            vektor_baru = self.ai_engine.hitung_vektor(new_image.file_path)
            
            new_hash = ImageHashes(
                phash=new_hash_record.phash,
                ahash=new_hash_record.ahash,
                dhash=new_hash_record.dhash,
                whash=new_hash_record.whash,
                crop_resistant_hash=new_hash_record.crop_resistant_hash,
                file_hash=new_hash_record.file_hash
            )
            
            # Compare against all historical images
            for historical_image in historical_images:
                historical_hash_record = ImageHashOperations.get_hash_by_image_id(db_session, historical_image.id)
                if not historical_hash_record:
                    continue
                
                # --- TAMBAHAN 4B: AI Baca Foto Lama & Bandingkan ---
                vektor_lama = self.ai_engine.hitung_vektor(historical_image.file_path)
                ai_score_final = self.ai_engine.bandingkan_vektor(vektor_baru, vektor_lama)
                
                historical_hash = ImageHashes(
                    phash=historical_hash_record.phash,
                    ahash=historical_hash_record.ahash,
                    dhash=historical_hash_record.dhash,
                    whash=historical_hash_record.whash,
                    crop_resistant_hash=historical_hash_record.crop_resistant_hash,
                    file_hash=historical_hash_record.file_hash
                )
                
                # Perform analysis (Jangan lupa lempar ai_score_final ke dalam sini)
                # Oiya, kita harus update juga di baris 46 biar analyze_image_fraud nerima ai_score
                analysis_result = self.analyze_image_fraud(new_hash, historical_hash, ai_score=ai_score_final)
                
                # Only store significant results
                if analysis_result.fraud_score >= 40 or analysis_result.comparison_result.combined_similarity > 50:
                    # Store in database
                    FraudAnalysisOperations.create_fraud_analysis(
                        db_session,
                        new_image_id=new_image.id,
                        comparison_image_id=historical_image.id,
                        similarity_score=analysis_result.comparison_result.combined_similarity,
                        fraud_score=analysis_result.fraud_score,
                        verdict=analysis_result.verdict,
                        analysis_details=analysis_result.analysis_summary
                    )
                    
                    results.append(analysis_result)
        
        return results