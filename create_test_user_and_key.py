#!/usr/bin/env python3
"""
Quick test script to create a user and API key for admin panel testing
"""
import os
import sys
import uuid
from datetime import datetime
from pymongo import MongoClient

def create_test_user_and_api_key():
    """Create test user and API key directly in MongoDB"""
    try:
        # Connect to MongoDB
        mongo_uri = os.getenv("MONGO_DB_URI", "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority")
        client = MongoClient(mongo_uri)
        db = client.youtube_api_db
        
        # Create test user
        test_user_id = str(uuid.uuid4())
        user_data = {
            '_id': test_user_id,
            'username': 'test_user',
            'email': 'test@example.com',
            'created_at': datetime.utcnow(),
            'is_active': True
        }
        
        # Insert user (if not exists)
        existing_user = db.users.find_one({'username': 'test_user'})
        if not existing_user:
            result = db.users.insert_one(user_data)
            print(f"✅ Created test user: {result.inserted_id}")
        else:
            test_user_id = existing_user['_id']
            print(f"✅ Using existing test user: {test_user_id}")
        
        # Create API key
        api_key = f"ytapi_test_{str(uuid.uuid4()).replace('-', '')[:16]}"
        api_key_data = {
            '_id': str(uuid.uuid4()),
            'key': api_key,
            'user_id': test_user_id,
            'name': 'Test API Key',
            'is_active': True,
            'rate_limit': 1000,
            'usage_count': 0,
            'created_at': datetime.utcnow(),
            'expires_at': None,
            'permissions': ['youtube_download', 'metadata_access', 'streaming'],
            'status': 'active',
            'tier': 'professional'
        }
        
        result = db.api_keys.insert_one(api_key_data)
        print(f"✅ Created API key: {api_key}")
        print(f"   Key ID: {result.inserted_id}")
        print(f"   User: test_user ({test_user_id})")
        
        client.close()
        return api_key
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        return None

if __name__ == "__main__":
    print("Creating test user and API key...")
    api_key = create_test_user_and_api_key()
    if api_key:
        print(f"\n🎉 Success! You can now test the admin panel.")
        print(f"   API Key: {api_key}")
        print(f"   Admin URL: http://localhost:5000/admin")
        print(f"   Login: admin / admin123")
    else:
        print("\n❌ Failed to create test data.")