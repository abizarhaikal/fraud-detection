#!/usr/bin/env python3
"""
Batch Event Fraud Detection
Analyzes multiple image pairs for same-event fraud detection.
"""

import os
import sys
import json
from fraud_detection import detect_event_fraud


def batch_fraud_analysis(image_directory):
    """
    Analyze all image pairs in a directory for fraud detection.
    """
    
    # Get all image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    image_files = [
        f for f in os.listdir(image_directory) 
        if os.path.splitext(f.lower())[1] in image_extensions
    ]
    
    if len(image_files) < 2:
        print("Need at least 2 images for comparison")
        return
    
    print(f"Found {len(image_files)} images: {image_files}")
    print("\nAnalyzing all pairs for fraud detection...")
    print("=" * 80)
    
    results = []
    
    # Compare each pair of images
    for i in range(len(image_files)):
        for j in range(i + 1, len(image_files)):
            img1 = os.path.join(image_directory, image_files[i])
            img2 = os.path.join(image_directory, image_files[j])
            
            print(f"\nComparing: {image_files[i]} vs {image_files[j]}")
            print("-" * 50)
            
            try:
                result = detect_event_fraud(img1, img2)
                result['image_pair'] = (image_files[i], image_files[j])
                results.append(result)
                
            except Exception as e:
                print(f"Error analyzing {image_files[i]} vs {image_files[j]}: {e}")
    
    # Summary report
    print(f"\n" + "=" * 80)
    print("📊 BATCH ANALYSIS SUMMARY")
    print("=" * 80)
    
    high_risk_pairs = [r for r in results if r['fraud_score'] >= 80]
    moderate_risk_pairs = [r for r in results if 60 <= r['fraud_score'] < 80]
    
    print(f"Total pairs analyzed: {len(results)}")
    print(f"🚨 High risk pairs: {len(high_risk_pairs)}")
    print(f"⚠️  Moderate risk pairs: {len(moderate_risk_pairs)}")
    
    if high_risk_pairs:
        print(f"\n🚨 HIGH RISK FRAUD DETECTED:")
        for result in high_risk_pairs:
            pair = result['image_pair']
            print(f"   {pair[0]} ↔ {pair[1]} (Score: {result['fraud_score']}/100)")
    
    if moderate_risk_pairs:
        print(f"\n⚠️  MODERATE RISK PAIRS:")
        for result in moderate_risk_pairs:
            pair = result['image_pair'] 
            print(f"   {pair[0]} ↔ {pair[1]} (Score: {result['fraud_score']}/100)")
    
    # Save detailed results to JSON
    output_file = 'fraud_analysis_results.json'
    with open(output_file, 'w') as f:
        # Convert results to JSON-serializable format
        json_results = []
        for r in results:
            json_result = {
                'image_pair': r['image_pair'],
                'fraud_score': r['fraud_score'],
                'verdict': r['verdict'],
                'visual_similarity': r['visual_similarity'],
                'metadata_flags': r['metadata_flags']
            }
            json_results.append(json_result)
        
        json.dump(json_results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    return results


def main():
    """Main function for batch fraud detection."""
    
    # Use current directory
    current_dir = "."
    
    print("🕵️  BATCH EVENT FRAUD DETECTION")
    print("Analyzing all image pairs in current directory...")
    
    batch_fraud_analysis(current_dir)


if __name__ == "__main__":
    main()