#!/usr/bin/env python3
"""
Event Fraud Detection Script
Detects if images are from the same event to prevent vendor fraud.
"""

import os
import sys
import time
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import imagehash
import hashlib


def extract_exif_metadata(image_path):
    """Extract comprehensive EXIF metadata from image."""
    metadata = {}
    
    try:
        with Image.open(image_path) as img:
            # Get EXIF data
            exif_data = img._getexif()
            
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    metadata[tag] = value
                    
            # Get basic image info
            metadata['ImageSize'] = img.size
            metadata['ImageMode'] = img.mode
            metadata['ImageFormat'] = img.format
            
    except Exception as e:
        print(f"Error extracting EXIF from {image_path}: {e}")
        
    return metadata


def analyze_filename_patterns(image1_path, image2_path):
    """Analyze filename patterns for fraud indicators."""
    fraud_flags = []
    
    import re
    from datetime import datetime
    
    file1 = os.path.basename(image1_path).lower()
    file2 = os.path.basename(image2_path).lower()
    
    # Extract potential person/entity names (common first part)
    name1 = re.split(r'[\s_\-\d]', file1)[0]
    name2 = re.split(r'[\s_\-\d]', file2)[0]
    
    if len(name1) > 2 and len(name2) > 2 and name1 == name2:
        fraud_flags.append(f"SAME_ENTITY_NAME: Both files contain '{name1}'")
    
    # Extract dates from filenames
    date_patterns = [
        r'(\d{8})',          # DDMMYYYY or YYYYMMDD
        r'(\d{2}\d{2}\d{4})', # DDMMYYYY  
        r'(\d{4}\d{2}\d{2})', # YYYYMMDD
        r'(\d{2}-\d{2}-\d{4})', # DD-MM-YYYY
        r'(\d{4}-\d{2}-\d{2})'  # YYYY-MM-DD
    ]
    
    dates1 = []
    dates2 = []
    
    for pattern in date_patterns:
        dates1.extend(re.findall(pattern, file1))
        dates2.extend(re.findall(pattern, file2))
    
    if dates1 and dates2:
        # Try to parse dates and check if they're close
        try:
            for d1 in dates1:
                for d2 in dates2:
                    # Try different date formats
                    date_formats = ['%d%m%Y', '%Y%m%d', '%d-%m-%Y', '%Y-%m-%d']
                    for fmt in date_formats:
                        try:
                            dt1 = datetime.strptime(d1.replace('-', ''), fmt.replace('-', ''))
                            dt2 = datetime.strptime(d2.replace('-', ''), fmt.replace('-', ''))
                            
                            time_diff = abs((dt1 - dt2).days)
                            if time_diff == 0:
                                fraud_flags.append("IDENTICAL_FILENAME_DATES: Same date in filenames")
                            elif time_diff <= 21:  # Within 3 weeks = same event
                                fraud_flags.append(f"SAME_EVENT_TIMEFRAME: {time_diff} days apart (likely same event)")
                            elif time_diff <= 60:  # Within 2 months 
                                fraud_flags.append(f"CLOSE_FILENAME_DATES: {time_diff} days apart in filenames")
                            elif time_diff <= 120:  # Within 4 months (same event season)
                                fraud_flags.append(f"POSSIBLE_SAME_EVENT: {time_diff} days apart (possible same event)")
                            break
                        except ValueError:
                            continue
        except:
            pass
    
    return fraud_flags


def analyze_metadata_for_fraud(metadata1, metadata2, image1_path, image2_path):
    """Analyze metadata to detect potential fraud indicators."""
    fraud_flags = []
    
    # Check GPS coordinates
    gps1 = metadata1.get('GPSInfo')
    gps2 = metadata2.get('GPSInfo')
    if gps1 and gps2 and gps1 == gps2:
        fraud_flags.append("IDENTICAL_GPS: Exact same GPS coordinates")
    
    # Check timestamps  
    datetime1 = metadata1.get('DateTime')
    datetime2 = metadata2.get('DateTime')
    if datetime1 and datetime2:
        if datetime1 == datetime2:
            fraud_flags.append("IDENTICAL_TIMESTAMP: Exact same capture time")
        else:
            try:
                dt1 = datetime.strptime(datetime1, '%Y:%m:%d %H:%M:%S')
                dt2 = datetime.strptime(datetime2, '%Y:%m:%d %H:%M:%S')
                time_diff = abs((dt1 - dt2).total_seconds())
                if time_diff < 3600:  # Within 1 hour
                    fraud_flags.append(f"CLOSE_TIMESTAMPS: {time_diff/60:.1f} minutes apart")
            except:
                pass
    
    # Check camera info
    camera1 = f"{metadata1.get('Make', '')} {metadata1.get('Model', '')}"
    camera2 = f"{metadata2.get('Make', '')} {metadata2.get('Model', '')}"
    if camera1 == camera2 and camera1.strip():
        # Check if camera settings are identical (suspicious)
        settings1 = (metadata1.get('ISO'), metadata1.get('FNumber'), metadata1.get('ExposureTime'))
        settings2 = (metadata2.get('ISO'), metadata2.get('FNumber'), metadata2.get('ExposureTime'))
        if settings1 == settings2 and any(settings1):
            fraud_flags.append("IDENTICAL_CAMERA_SETTINGS: Same camera with identical settings")
    
    # Check image dimensions
    size1 = metadata1.get('ImageSize')
    size2 = metadata2.get('ImageSize') 
    if size1 and size2 and size1 == size2:
        fraud_flags.append("IDENTICAL_DIMENSIONS: Same image dimensions")
    
    return fraud_flags


def calculate_file_hash(file_path):
    """Calculate MD5 hash of file for exact duplicate detection."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return None


def detect_event_fraud(image1_path, image2_path):
    """
    Comprehensive fraud detection for event images.
    Returns fraud score and detailed analysis.
    """
    
    print("=" * 60)
    print("🕵️  EVENT FRAUD DETECTION ANALYSIS")
    print("=" * 60)
    
    # File information
    stat1 = os.stat(image1_path)
    stat2 = os.stat(image2_path)
    
    print(f"\n📁 File Analysis:")
    print(f"   {image1_path}:")
    print(f"     Size: {stat1.st_size:,} bytes")
    print(f"     Modified: {time.ctime(stat1.st_mtime)}")
    print(f"   {image2_path}:")
    print(f"     Size: {stat2.st_size:,} bytes")
    print(f"     Modified: {time.ctime(stat2.st_mtime)}")
    
    # Check for exact duplicates
    hash1 = calculate_file_hash(image1_path)
    hash2 = calculate_file_hash(image2_path)
    
    if hash1 and hash2 and hash1 == hash2:
        print(f"\n🚨 CRITICAL: EXACT DUPLICATE FILES DETECTED!")
        return {"fraud_score": 100, "verdict": "DEFINITE_FRAUD", "reason": "Identical files"}
    
    # Extract metadata
    print(f"\n📋 Extracting metadata...")
    metadata1 = extract_exif_metadata(image1_path)
    metadata2 = extract_exif_metadata(image2_path)
    
    # Analyze metadata for fraud indicators
    metadata_flags = analyze_metadata_for_fraud(metadata1, metadata2, image1_path, image2_path)
    
    # Analyze filename patterns for fraud indicators
    filename_flags = analyze_filename_patterns(image1_path, image2_path)
    
    # Combine all fraud flags
    fraud_flags = metadata_flags + filename_flags
    
    # Visual similarity analysis with ADVANCED ALGORITHMS
    print(f"\n🖼️  Advanced visual similarity analysis...")
    with Image.open(image1_path) as img1:
        phash1 = imagehash.phash(img1)
        ahash1 = imagehash.average_hash(img1)
        dhash1 = imagehash.dhash(img1)
        whash1 = imagehash.whash(img1)  # Wavelet hash for scale detection
        
        # Crop-resistant hash for detecting crops/zooms
        try:
            crhash1 = imagehash.crop_resistant_hash(img1, min_segment_size=200, segmentation_image_size=300)
        except:
            crhash1 = None
        
    with Image.open(image2_path) as img2:
        phash2 = imagehash.phash(img2)
        ahash2 = imagehash.average_hash(img2)
        dhash2 = imagehash.dhash(img2)
        whash2 = imagehash.whash(img2)  # Wavelet hash for scale detection
        
        # Crop-resistant hash for detecting crops/zooms
        try:
            crhash2 = imagehash.crop_resistant_hash(img2, min_segment_size=200, segmentation_image_size=300)
        except:
            crhash2 = None
    
    # Calculate similarities for all algorithms
    phash_distance = phash1 - phash2
    ahash_distance = ahash1 - ahash2
    dhash_distance = dhash1 - dhash2
    whash_distance = whash1 - whash2
    
    phash_similarity = (1 - phash_distance / 64) * 100
    ahash_similarity = (1 - ahash_distance / 64) * 100
    dhash_similarity = (1 - dhash_distance / 64) * 100
    whash_similarity = (1 - whash_distance / 64) * 100
    
    # Crop-resistant similarity (if available)
    crop_similarity = 0
    if crhash1 and crhash2:
        try:
            crop_distance = crhash1 - crhash2
            crop_similarity = (1 - min(crop_distance, 100) / 100) * 100
        except:
            crop_similarity = 0
    
    # Enhanced visual similarity with crop/zoom detection
    if crop_similarity > 0:
        visual_similarity = (phash_similarity * 0.3 + ahash_similarity * 0.2 + 
                           dhash_similarity * 0.15 + whash_similarity * 0.25 + 
                           crop_similarity * 0.1)
    else:
        visual_similarity = (phash_similarity * 0.4 + ahash_similarity * 0.25 + 
                           dhash_similarity * 0.2 + whash_similarity * 0.15)
    
    # Display results
    print(f"\n📊 ADVANCED FRAUD ANALYSIS RESULTS:")
    print(f"   Combined Visual Similarity: {visual_similarity:.1f}%")
    print(f"   pHash: {phash_similarity:.1f}% (distance: {phash_distance})")
    print(f"   aHash: {ahash_similarity:.1f}% (distance: {ahash_distance})")
    print(f"   dHash: {dhash_similarity:.1f}% (distance: {dhash_distance})")
    print(f"   wHash: {whash_similarity:.1f}% (distance: {whash_distance})")
    if crop_similarity > 0:
        print(f"   Crop-Resistant: {crop_similarity:.1f}% (SAME SCENE DETECTION)")
    
    if filename_flags:
        print(f"\n🚩 FILENAME PATTERN FLAGS:")
        for flag in filename_flags:
            print(f"   • {flag}")
    
    if metadata_flags:
        print(f"\n🚩 METADATA FLAGS:")
        for flag in metadata_flags:
            print(f"   • {flag}")
    
    if not filename_flags and not metadata_flags:
        print(f"\n✅ No fraud indicators detected")
    
    # Calculate fraud score with AGGRESSIVE SAME-EVENT detection
    fraud_score = 0
    
    # Visual similarity component (0-60 points) - MUCH MORE AGGRESSIVE
    if visual_similarity > 85:
        fraud_score += 60  # Very high similarity = definite fraud
    elif visual_similarity > 75:
        fraud_score += 50  # High similarity = likely fraud  
    elif visual_similarity > 65:
        fraud_score += 45  # Moderate-high similarity = HIGH RISK for same event
    elif visual_similarity > 55:
        fraud_score += 35  # Moderate similarity = concerning
    elif visual_similarity > 45:
        fraud_score += 25  # Some similarity = worth noting
    elif visual_similarity > 35:
        fraud_score += 15  # Low similarity = monitor
    
    # ALGORITHM CONSENSUS VALIDATION - Prevent false positives
    standard_similarities = [phash_similarity, ahash_similarity, dhash_similarity, whash_similarity]
    avg_standard_similarity = sum(standard_similarities) / len(standard_similarities)
    
    # Detect outlier algorithms (crop-resistant can give false positives)
    crop_outlier = False
    if crop_similarity > 0:
        crop_vs_avg_diff = abs(crop_similarity - avg_standard_similarity)
        if crop_vs_avg_diff > 30 and crop_similarity > 80:  # Crop shows high similarity but others don't
            crop_outlier = True
            print(f"\n⚠️  CROP OUTLIER DETECTED: Crop {crop_similarity:.1f}% vs Avg {avg_standard_similarity:.1f}% - Possible false positive")
    
    # VALIDATED CROP/ZOOM DETECTION BONUS (0-25 points)
    if crop_similarity > 70 and not crop_outlier:
        # Require consensus: crop detection + reasonable standard similarity
        if avg_standard_similarity > 50:
            fraud_score += 25  # Strong validated crop detection
            print(f"\n🎯 VALIDATED CROP/ZOOM: +25 points (crop: {crop_similarity:.1f}%, consensus: {avg_standard_similarity:.1f}%)")
        else:
            fraud_score += 10  # Weak consensus, reduced score
            print(f"\n🎯 WEAK CROP DETECTION: +10 points (crop: {crop_similarity:.1f}%, low consensus: {avg_standard_similarity:.1f}%)")
    elif crop_similarity > 50 and not crop_outlier:
        if avg_standard_similarity > 40:
            fraud_score += 15  # Moderate validated crop detection
            print(f"\n🎯 POSSIBLE VALIDATED CROP: +15 points (crop: {crop_similarity:.1f}%, consensus: {avg_standard_similarity:.1f}%)")
        else:
            fraud_score += 5   # Very weak consensus
            print(f"\n🎯 UNCERTAIN CROP: +5 points (crop: {crop_similarity:.1f}%, weak consensus: {avg_standard_similarity:.1f}%)")
    elif crop_outlier:
        print(f"\n🚫 CROP DETECTION IGNORED: Likely false positive (crop: {crop_similarity:.1f}% vs avg: {avg_standard_similarity:.1f}%)")
    
    # WAVELET ANALYSIS BONUS (0-15 points) - Scale invariant detection  
    if whash_similarity > 80 and avg_standard_similarity > 60:
        fraud_score += 15  # High wavelet similarity with consensus
        print(f"\n📐 SCALE SIMILARITY DETECTED: +15 points (wavelet: {whash_similarity:.1f}%)")
    elif whash_similarity > 70 and avg_standard_similarity > 50:
        fraud_score += 10
        print(f"\n📐 SIMILAR SCALE DETECTED: +10 points (wavelet: {whash_similarity:.1f}%)")
    elif whash_similarity > 70:
        fraud_score += 5   # Reduced score without consensus
        print(f"\n📐 WEAK SCALE SIMILARITY: +5 points (wavelet: {whash_similarity:.1f}%, low consensus)")
    
    # Filename pattern flags (0-20 points) - REDUCED WEIGHT
    filename_score = len(filename_flags) * 8
    fraud_score += min(filename_score, 20)
    
    # Metadata flags component (0-15 points) - FURTHER REDUCED WEIGHT  
    metadata_score = len(metadata_flags) * 8
    fraud_score += min(metadata_score, 15)
    
    # AUTOMATIC HIGH RISK TRIGGERS - MORE AGGRESSIVE
    same_entity_detected = any("SAME_ENTITY_NAME" in flag for flag in filename_flags)
    same_event_timeframe = any("SAME_EVENT_TIMEFRAME" in flag for flag in filename_flags)
    
    # CONSENSUS-BASED AUTOMATIC TRIGGERS - Require multiple evidence sources
    high_consensus = avg_standard_similarity > 65
    moderate_consensus = avg_standard_similarity > 55
    
    if visual_similarity > 70 and high_consensus:  # Raised threshold, require consensus
        fraud_score = max(fraud_score, 80)  # Auto HIGH RISK for high similarity with consensus
        print(f"\n⚡ AUTO-TRIGGER: High visual similarity + consensus ({visual_similarity:.1f}%) = HIGH RISK")
    
    if crop_similarity > 70 and not crop_outlier and moderate_consensus:  # VALIDATED crop detection
        fraud_score = max(fraud_score, 82)  # Force HIGH RISK for validated crop detection
        print(f"\n⚡ AUTO-TRIGGER: Validated crop/zoom detection = HIGH RISK")
    
    if whash_similarity > 75 and visual_similarity > 65 and moderate_consensus:  # Scale + consensus
        fraud_score = max(fraud_score, 80)  # Force HIGH RISK for scale similarity with consensus
        print(f"\n⚡ AUTO-TRIGGER: Scale similarity + consensus = HIGH RISK")
    
    if same_entity_detected and visual_similarity > 50:  # Filename + similarity
        fraud_score = max(fraud_score, 85)  # Force HIGH RISK
        print(f"\n⚡ AUTO-TRIGGER: Same entity + similarity = HIGH RISK")
    
    if same_event_timeframe and visual_similarity > 60:  # Raised threshold
        fraud_score = max(fraud_score, 75)  # Force HIGH RISK for same event + similarity
        print(f"   ⚡ AUTO-TRIGGER: Same timeframe + similarity = HIGH RISK")
    
    # SAME EVENT WITH STRONG CROP EVIDENCE - Override outlier detection
    if same_event_timeframe and crop_similarity > 85 and visual_similarity > 50:
        fraud_score = max(fraud_score, 82)  # Force HIGH RISK - strong filename + crop evidence
        print(f"   ⚡ AUTO-TRIGGER: Same event timeframe + high crop similarity ({crop_similarity:.1f}%) = HIGH RISK")
    
    # IDENTICAL DATE WITH CROP EVIDENCE
    identical_dates = any("IDENTICAL_FILENAME_DATES" in flag for flag in filename_flags)
    if identical_dates and crop_similarity > 85 and visual_similarity > 45:
        fraud_score = max(fraud_score, 80)  # Force HIGH RISK - same date + crop evidence
        print(f"   ⚡ AUTO-TRIGGER: Identical dates + high crop similarity ({crop_similarity:.1f}%) = HIGH RISK")
    
    # IDENTICAL DIMENSIONS + HIGH SIMILARITY + CONSENSUS = SAME EVENT
    identical_dimensions = any("IDENTICAL_DIMENSIONS" in flag for flag in metadata_flags)
    if identical_dimensions and visual_similarity > 65 and moderate_consensus:  # Require consensus
        fraud_score = max(fraud_score, 78)  # Force HIGH RISK
        print(f"\n⚡ AUTO-TRIGGER: Identical dimensions + similarity + consensus = SAME EVENT")
    
    # MULTIPLE ALGORITHM CONSENSUS TRIGGER
    algorithms_above_60 = sum(1 for sim in standard_similarities if sim > 60)
    if algorithms_above_60 >= 3 and visual_similarity > 65:  # 3+ algorithms agree
        fraud_score = max(fraud_score, 79)  # Force HIGH RISK for strong consensus
        print(f"\n⚡ AUTO-TRIGGER: Multiple algorithm consensus ({algorithms_above_60}/4 algorithms >60%) = HIGH RISK")
    
    # Determine verdict
    if fraud_score >= 80:
        verdict = "HIGH_RISK_FRAUD"
        verdict_emoji = "🚨"
    elif fraud_score >= 60:
        verdict = "MODERATE_RISK"
        verdict_emoji = "⚠️"
    elif fraud_score >= 40:
        verdict = "LOW_RISK"
        verdict_emoji = "🟡"
    else:
        verdict = "LIKELY_LEGITIMATE"
        verdict_emoji = "✅"
    
    print(f"\n{verdict_emoji} FINAL ASSESSMENT:")
    print(f"   Fraud Score: {fraud_score}/100")
    print(f"   Verdict: {verdict}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if fraud_score >= 80:
        print("   🔴 REJECT submission - High probability of fraud")
        print("   🔍 Flag vendor for investigation")
    elif fraud_score >= 60:
        print("   🟡 Manual review required")
        print("   📞 Contact vendor for clarification")
    elif fraud_score >= 40:
        print("   ⚪ Monitor vendor for patterns")
        print("   📝 Document for future reference")
    else:
        print("   ✅ Accept submission - Appears legitimate")
    
    return {
        "fraud_score": fraud_score,
        "verdict": verdict,
        "visual_similarity": visual_similarity,
        "metadata_flags": fraud_flags,
        "hash_distances": {
            "phash": phash1 - phash2,
            "ahash": ahash1 - ahash2, 
            "dhash": dhash1 - dhash2
        }
    }


def main():
    """Main function to detect event fraud between two images."""
    
    # Allow command line arguments for flexible testing
    if len(sys.argv) >= 3:
        image1_path = sys.argv[1]
        image2_path = sys.argv[2]
    else:
        # Default fallback to original behavior
        image1_path = "new.jpeg"
        image2_path = "original.jpeg"
    
    # Check if files exist
    if not os.path.exists(image1_path):
        print(f"Error: {image1_path} not found!")
        sys.exit(1)
    if not os.path.exists(image2_path):
        print(f"Error: {image2_path} not found!")
        sys.exit(1)
    
    print(f"Analyzing: {image1_path} vs {image2_path}")
    
    # Run fraud detection
    result = detect_event_fraud(image1_path, image2_path)
    
    print(f"\n" + "=" * 60)
    print(f"Analysis complete. Fraud score: {result['fraud_score']}/100")
    print("=" * 60)


if __name__ == "__main__":
    main()