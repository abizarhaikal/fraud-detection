#!/usr/bin/env python3
import sys
print("Python version:", sys.version)
print("Testing imports...")

try:
    import os
    print("✓ os imported")
    
    import time  
    print("✓ time imported")
    
    from PIL import Image
    print("✓ PIL.Image imported")
    
    import imagehash
    print("✓ imagehash imported")
    
    print("\nTesting file existence...")
    if os.path.exists("new.jpeg"):
        print("✓ new.jpeg exists")
    else:
        print("✗ new.jpeg not found")
        
    if os.path.exists("original.jpeg"):
        print("✓ original.jpeg exists") 
    else:
        print("✗ original.jpeg not found")
        
    print("\nTesting basic hash computation...")
    if os.path.exists("new.jpeg"):
        with Image.open("new.jpeg") as img:
            hash_val = imagehash.phash(img)
            print(f"✓ Hash computed: {hash_val}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("Test completed.")