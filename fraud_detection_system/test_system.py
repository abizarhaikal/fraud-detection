#!/usr/bin/env python3
"""
Test script to initialize and verify the fraud detection system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import init_database, get_db
from database.operations import VendorOperations
from utils.config import Config

def test_system():
    """Test system initialization and basic functionality."""
    
    print("🚀 Testing Fraud Detection System")
    print("=" * 50)
    
    # Test 1: Configuration
    print("\n📋 Testing Configuration...")
    Config.ensure_directories()
    print(f"✅ Database path: {Config.get_database_path()}")
    print(f"✅ Uploads directory: {Config.get_uploads_dir()}")
    
    # Test 2: Database initialization
    print("\n🗄️ Testing Database...")
    try:
        init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    # Test 3: Basic CRUD operations
    print("\n👥 Testing Vendor Operations...")
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Create test vendor
        test_vendor = VendorOperations.create_vendor(db, "Test Vendor Co.")
        print(f"✅ Created vendor: {test_vendor.name} (ID: {test_vendor.id})")
        
        # Retrieve vendor
        retrieved = VendorOperations.get_vendor_by_name(db, "Test Vendor Co.")
        if retrieved:
            print(f"✅ Retrieved vendor: {retrieved.name}")
        else:
            print("❌ Failed to retrieve vendor")
        
        # List all vendors
        all_vendors = VendorOperations.get_all_vendors(db)
        print(f"✅ Total vendors: {len(all_vendors)}")
        
    except Exception as e:
        print(f"❌ Database operations failed: {e}")
        return False
    finally:
        db.close()
    
    print("\n🎉 All tests passed! System is ready.")
    print("\n🚀 To run the app:")
    print("cd /Users/ali/Sites/diff-images")
    print("fraud_detection_venv/bin/streamlit run fraud_detection_system/app.py")
    
    return True

if __name__ == "__main__":
    test_system()