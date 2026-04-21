#!/usr/bin/env python3
"""
Test Runner for Individual Case Analysis
Demonstrates how to run individual fraud detection scripts on specific test cases.
"""

import os
import subprocess
import sys


def run_case_analysis(case_name, script_name="fraud_detection.py"):
    """Run analysis on a specific test case."""
    
    case_dir = f"cases/{case_name}"
    
    if not os.path.exists(case_dir):
        print(f"Error: Case directory {case_dir} not found!")
        return
    
    # Get images in the case directory
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    images = [
        f for f in os.listdir(case_dir)
        if os.path.splitext(f.lower())[1] in image_extensions
    ]
    
    if len(images) < 2:
        print(f"Error: {case_name} needs at least 2 images!")
        return
    
    print(f"\n{'='*60}")
    print(f"🔍 RUNNING {script_name.upper()} ON {case_name.upper()}")
    print(f"{'='*60}")
    
    if len(images) == 2:
        # Simple case with 2 images
        img1_path = os.path.join(case_dir, images[0])
        img2_path = os.path.join(case_dir, images[1])
        
        print(f"Analyzing: {images[0]} vs {images[1]}")
        
        # Run the script
        cmd = [sys.executable, script_name, img1_path, img2_path]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running script: {e}")
            
    else:
        # Multiple images - analyze first two
        img1_path = os.path.join(case_dir, images[0])
        img2_path = os.path.join(case_dir, images[1])
        
        print(f"Multiple images found. Analyzing: {images[0]} vs {images[1]}")
        print(f"(Use comprehensive_fraud_report.py for all pairs)")
        
        # Run the script
        cmd = [sys.executable, script_name, img1_path, img2_path]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running script: {e}")


def main():
    """Main function to demonstrate case analysis."""
    
    print("🧪 TEST CASE ANALYSIS RUNNER")
    print("This script demonstrates how to run individual analysis on test cases.")
    
    # Available test cases
    cases_dir = "cases"
    if not os.path.exists(cases_dir):
        print(f"Error: {cases_dir} directory not found!")
        sys.exit(1)
    
    case_dirs = [d for d in os.listdir(cases_dir) if os.path.isdir(os.path.join(cases_dir, d))]
    case_dirs.sort()
    
    print(f"\nAvailable test cases: {case_dirs}")
    
    # Run analysis on each case
    for case_name in case_dirs:
        print(f"\n🎯 Testing {case_name}...")
        
        # Run fraud detection
        run_case_analysis(case_name, "fraud_detection.py")
        
        # Optional: Also run similarity analysis
        print(f"\n📊 Running similarity analysis on {case_name}...")
        run_case_analysis(case_name, "image_similarity.py")
    
    print(f"\n{'='*60}")
    print("✅ Individual case testing complete!")
    print("💡 For comprehensive analysis of all cases, run: comprehensive_fraud_report.py")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()