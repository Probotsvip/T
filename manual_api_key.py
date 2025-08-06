#!/usr/bin/env python3
"""
Manual API key creation with direct form simulation
"""
import os
import sys
import uuid
from datetime import datetime
from pymongo import MongoClient

def create_manual_api_key():
    """Create API key manually through direct database insertion"""
    try:
        # Connect to MongoDB directly
        mongo_uri = os.getenv("MONGO_DB_URI", "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority")
        client = MongoClient(mongo_uri)
        db = client.youtube_api_db
        
        # Get test user
        user = db.users.find_one({'username': 'test_user'})
        if not user:
            print("❌ No test user found. Creating one...")
            user_id = str(uuid.uuid4())
            user_data = {
                '_id': user_id,
                'username': 'test_user',
                'email': 'test@example.com',
                'created_at': datetime.utcnow(),
                'is_active': True
            }
            db.users.insert_one(user_data)
            user = user_data
        
        # Create API key with correct structure for the template
        api_key = f"ytapi_{str(uuid.uuid4()).replace('-', '')[:16]}"
        api_key_data = {
            '_id': str(uuid.uuid4()),
            'key': api_key,
            'user_id': user['_id'],
            'name': f'Manual API Key {datetime.now().strftime("%H:%M:%S")}',
            'is_active': True,
            'rate_limit': 1000,
            'usage_count': 0,
            'created_at': datetime.utcnow(),
            'expires_at': None,
            'permissions': ['youtube_download', 'metadata_access', 'streaming'],
            'status': 'active',
            'tier': 'professional'
        }
        
        # Insert into database
        result = db.api_keys.insert_one(api_key_data)
        
        if result.inserted_id:
            print(f"✅ API key created successfully!")
            print(f"   Key: {api_key}")
            print(f"   User: {user['username']}")
            print(f"   ID: {result.inserted_id}")
            
            # Now test if we can retrieve it correctly
            print(f"\n🔍 Testing retrieval...")
            all_keys = list(db.api_keys.find({}))
            all_users = list(db.users.find({}))
            
            print(f"   Total keys found: {len(all_keys)}")
            print(f"   Total users found: {len(all_users)}")
            
            for key in all_keys:
                print(f"   - {key.get('name', 'Unknown')} ({key.get('key', 'No key')[:20]}...)")
            
            client.close()
            return True
        else:
            print("❌ Failed to insert API key")
            client.close()
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def simulate_form_request():
    """Simulate the form request that the admin panel sends"""
    import requests
    
    try:
        # Start session
        session = requests.Session()
        base_url = "http://localhost:5000"
        
        # Login first
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        login_response = session.post(f"{base_url}/admin/login", data=login_data)
        if login_response.status_code != 200:
            print("❌ Failed to login")
            return False
        
        print("✅ Logged into admin panel")
        
        # Get users first to find a user_id
        users_response = session.get(f"{base_url}/admin/api-keys")
        if users_response.status_code != 200:
            print("❌ Failed to access API keys page")
            return False
        
        print("✅ Accessed API keys page")
        
        # Get test user from database for form
        mongo_uri = os.getenv("MONGO_DB_URI", "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority")
        client = MongoClient(mongo_uri)
        db = client.youtube_api_db
        user = db.users.find_one({'username': 'test_user'})
        client.close()
        
        if not user:
            print("❌ No test user found")
            return False
        
        # Simulate form submission
        form_data = {
            'user_id': user['_id'],
            'name': f'Form Test Key {datetime.now().strftime("%H:%M:%S")}',
            'rate_limit': 1000
        }
        
        create_response = session.post(f"{base_url}/admin/api-keys/create", data=form_data)
        
        if create_response.status_code == 200:
            print("✅ Form submission successful")
            print(f"   Response URL: {create_response.url}")
            
            # Check if we can see the key now
            keys_response = session.get(f"{base_url}/admin/api-keys")
            if "No API Keys Found" in keys_response.text:
                print("❌ Still showing 'No API Keys Found' - there's a template/data issue")
                return False
            else:
                print("✅ API keys are now visible in the interface")
                return True
        else:
            print(f"❌ Form submission failed: {create_response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ Form simulation error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Creating manual API key...")
    if create_manual_api_key():
        print(f"\n🌐 Testing form simulation...")
        if simulate_form_request():
            print(f"\n🎉 API key creation is working through both methods!")
        else:
            print(f"\n⚠️ Manual creation works but form has issues")
    else:
        print(f"\n❌ Manual API key creation failed")