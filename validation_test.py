#!/usr/bin/env python3
"""
Quick validation test for false positive fixes
"""

import subprocess
import sys

def test_case(img1, img2, expected_risk, description):
    """Test a specific case and report results."""
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {description}")
    print(f"Expected: {expected_risk}")
    print(f"{'='*60}")
    
    cmd = [sys.executable, "fraud_detection.py", img1, img2]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Extract fraud score from output
        lines = result.stdout.split('\n')
        fraud_score = None
        verdict = None
        
        for line in lines:
            if "Fraud Score:" in line:
                fraud_score = line.split("Fraud Score:")[1].split("/")[0].strip()
            if "Verdict:" in line:
                verdict = line.split("Verdict:")[1].strip()
        
        if fraud_score and verdict:
            print(f"✅ RESULT: {fraud_score}/100 - {verdict}")
            
            # Check if result matches expectation
            score = int(fraud_score)
            if expected_risk == "LOW" and score < 60:
                print("✅ PASS: Correctly identified as low risk")
            elif expected_risk == "HIGH" and score >= 80:
                print("✅ PASS: Correctly identified as high risk")  
            elif expected_risk == "MODERATE" and 60 <= score < 80:
                print("✅ PASS: Correctly identified as moderate risk")
            else:
                print(f"❌ FAIL: Expected {expected_risk} risk but got score {score}")
        else:
            print("❌ ERROR: Could not extract results")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def main():
    """Run validation tests."""
    print("🔍 FRAUD DETECTION SYSTEM VALIDATION")
    
    # Test cases
    test_case(
        "cases/case-1/donita 06022023.jpg", 
        "cases/case-3/01092025.jpeg",
        "LOW", 
        "False Positive Test - Different Events (should be LOW RISK)"
    )
    
    test_case(
        "cases/case-3/01092025.jpeg", 
        "cases/case-3/24052025.jpeg",
        "HIGH", 
        "True Positive Test - Same Event Different Zoom (should be HIGH RISK)"
    )
    
    test_case(
        "cases/case-1/donita 06022023.jpg", 
        "cases/case-1/donita 22052023.jpg",
        "HIGH", 
        "Same Person Test - Same Entity Name (should be HIGH RISK)"
    )
    
    print(f"\n{'='*60}")
    print("🎯 VALIDATION COMPLETE")
    print("The system should now properly distinguish between:")
    print("  ✅ Real fraud (same event/person) → HIGH RISK") 
    print("  ✅ Different events → LOW RISK")
    print("  ✅ Crop/zoom detection with validation")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()