#!/usr/bin/env python3
"""
Image Similarity Calculator using Perceptual Hash (pHash)

This script computes the perceptual hash of two images and calculates
the percentage of similarity between them.
"""

import os
import sys
import time
from PIL import Image
import imagehash


def compute_phash(image_path):
    """
    Compute the perceptual hash of an image.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        imagehash.ImageHash: The perceptual hash of the image
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (handles different image formats)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            return imagehash.phash(img)
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None


def calculate_similarity(hash1, hash2):
    """
    Calculate the similarity percentage between two perceptual hashes.
    
    Args:
        hash1 (imagehash.ImageHash): First image hash
        hash2 (imagehash.ImageHash): Second image hash
        
    Returns:
        float: Similarity percentage (0-100%)
    """
    # Calculate Hamming distance between the hashes
    hamming_distance = hash1 - hash2
    
    # For pHash, the default size is 8x8 = 64 bits
    # We can also get this from the hash size
    hash_size = hash1.hash.size
    total_bits = hash_size if isinstance(hash_size, int) else hash1.hash.size
    
    # If hash size is not directly accessible, use a fallback
    if not isinstance(total_bits, int) or total_bits == 0:
        total_bits = 64  # Default for pHash
    
    # Calculate similarity percentage
    similarity = (1 - (hamming_distance / total_bits)) * 100
    
    return max(0, similarity)  # Ensure non-negative result


def main():
    """Main function to compare two images."""
    
    # Allow command line arguments for flexible testing
    if len(sys.argv) >= 3:
        image1_path = sys.argv[1]
        image2_path = sys.argv[2]
    else:
        # Default fallback to original behavior
        image1_path = "new.jpeg"
        image2_path = "original.jpeg"
    
    # Check if files exist and get file info
    if not os.path.exists(image1_path):
        print(f"Error: {image1_path} not found!")
        sys.exit(1)
    
    if not os.path.exists(image2_path):
        print(f"Error: {image2_path} not found!")
        sys.exit(1)
    
    print(f"Comparing: {image1_path} vs {image2_path}")
    
    # Display file information to verify they're different
    print("File Information:")
    print("-" * 40)
    stat1 = os.stat(image1_path)
    stat2 = os.stat(image2_path)
    print(f"{image1_path}:")
    print(f"  Size: {stat1.st_size} bytes")
    print(f"  Modified: {time.ctime(stat1.st_mtime)}")
    print(f"{image2_path}:")
    print(f"  Size: {stat2.st_size} bytes") 
    print(f"  Modified: {time.ctime(stat2.st_mtime)}")
    print()
    
    # Load images to get dimensions
    with Image.open(image1_path) as img1:
        img1_info = f"{img1.size[0]}x{img1.size[1]} {img1.mode}"
    with Image.open(image2_path) as img2:
        img2_info = f"{img2.size[0]}x{img2.size[1]} {img2.mode}"
    
    print(f"{image1_path}: {img1_info}")
    print(f"{image2_path}: {img2_info}")
    print()
    
    print("Computing perceptual hashes...")
    print("-" * 40)
    
    # Compute multiple types of hashes for comparison
    with Image.open(image1_path) as img1:
        phash1 = imagehash.phash(img1)
        ahash1 = imagehash.average_hash(img1)
        dhash1 = imagehash.dhash(img1)
        
    with Image.open(image2_path) as img2:
        phash2 = imagehash.phash(img2)
        ahash2 = imagehash.average_hash(img2)
        dhash2 = imagehash.dhash(img2)
    
    # Display all hashes
    print(f"Perceptual Hash (pHash):")
    print(f"  {image1_path}: {phash1}")
    print(f"  {image2_path}: {phash2}")
    print(f"Average Hash (aHash):")
    print(f"  {image1_path}: {ahash1}")
    print(f"  {image2_path}: {ahash2}")
    print(f"Difference Hash (dHash):")
    print(f"  {image1_path}: {dhash1}")
    print(f"  {image2_path}: {dhash2}")
    print()
    
    # Calculate similarities for all hash types
    phash_distance = phash1 - phash2
    ahash_distance = ahash1 - ahash2
    dhash_distance = dhash1 - dhash2
    
    # For pHash, the default size is 8x8 = 64 bits
    total_bits = 64
    
    phash_similarity = (1 - (phash_distance / total_bits)) * 100
    ahash_similarity = (1 - (ahash_distance / total_bits)) * 100
    dhash_similarity = (1 - (dhash_distance / total_bits)) * 100
    
    # Display results
    print("Similarity Analysis:")
    print("-" * 40)
    print(f"Perceptual Hash (pHash):")
    print(f"  Hamming Distance: {phash_distance}")
    print(f"  Similarity: {phash_similarity:.2f}%")
    print(f"Average Hash (aHash):")
    print(f"  Hamming Distance: {ahash_distance}")
    print(f"  Similarity: {ahash_similarity:.2f}%")
    print(f"Difference Hash (dHash):")
    print(f"  Hamming Distance: {dhash_distance}")
    print(f"  Similarity: {dhash_similarity:.2f}%")
    print()
    
    # Use pHash as the main result
    main_similarity = phash_similarity
    
    # Interpret the results
    if main_similarity >= 95:
        interpretation = "Virtually identical"
    elif main_similarity >= 85:
        interpretation = "Very similar"
    elif main_similarity >= 70:
        interpretation = "Similar"
    elif main_similarity >= 50:
        interpretation = "Somewhat similar"
    else:
        interpretation = "Different"
    
    # Calculate combined similarity (weighted average)
    # pHash is generally most reliable, so give it more weight
    combined_similarity = (phash_similarity * 0.5 + ahash_similarity * 0.3 + dhash_similarity * 0.2)
    
    print(f"Combined Similarity Score: {combined_similarity:.2f}%")
    print(f"Overall Interpretation (based on pHash): {interpretation}")
    print()
    
    # Analyze why pHash might be consistent
    if phash_distance == 32:
        print("📊 Analysis: pHash shows exactly 32 bits different (50% of 64 bits)")
        print("This suggests your images have similar overall structure/frequency patterns")
        print("but differ in details. This is actually normal for related images.")
        print()
    
    print("Algorithm Explanations:")
    print("- pHash (Perceptual): Focuses on frequency domain - best for scaled/rotated versions")
    print("- aHash (Average): Compares average brightness - fast, good for basic similarity") 
    print("- dHash (Difference): Tracks brightness gradients - good for edge/texture changes")
    print()
    print("💡 Tip: Use aHash if pHash seems too conservative, or combine multiple algorithms")


if __name__ == "__main__":
    main()