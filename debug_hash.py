#!/usr/bin/env python3
"""
Debug script to understand imagehash behavior
"""

import os
from PIL import Image
import imagehash

def debug_hash_info():
    """Debug hash information"""
    
    # Check if files exist
    image1_path = "new.jpeg"
    image2_path = "original.jpeg"
    
    if not os.path.exists(image1_path) or not os.path.exists(image2_path):
        print("Images not found!")
        return
        
    print("Loading images...")
    
    # Load images and compute hashes
    with Image.open(image1_path) as img1:
        hash1 = imagehash.phash(img1)
        
    with Image.open(image2_path) as img2:
        hash2 = imagehash.phash(img2)
    
    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")
    print(f"Hash 1 type: {type(hash1)}")
    print(f"Hash 1 hash attribute: {hash1.hash}")
    print(f"Hash 1 hash shape: {hash1.hash.shape}")
    print(f"Hash 1 hash size: {hash1.hash.size}")
    
    # Calculate Hamming distance
    hamming_dist = hash1 - hash2
    print(f"Hamming distance: {hamming_dist}")
    
    # Calculate similarity manually
    total_bits = hash1.hash.size
    similarity = (1 - (hamming_dist / total_bits)) * 100
    print(f"Total bits: {total_bits}")
    print(f"Similarity: {similarity:.2f}%")
    
    # Alternative calculation
    different_bits = hamming_dist
    same_bits = total_bits - different_bits
    alt_similarity = (same_bits / total_bits) * 100
    print(f"Alternative calculation: {alt_similarity:.2f}%")

if __name__ == "__main__":
    debug_hash_info()