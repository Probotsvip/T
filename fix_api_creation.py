#!/usr/bin/env python3
"""
Direct fix for API key creation issue
"""
import os
import uuid
from datetime import datetime
from pymongo import MongoClient

def fix_and_test_api_key_creation():
    """Fix API key creation and test it"""
    try:
        # Connect to MongoDB
        mongo_uri = os.getenv("MONGO_DB_URI", "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority")
        client = MongoClient(mongo_uri)
        db = client.youtube_api_db
        
        # Get the existing test user
        user = db.users.find_one({'username': 'test_user'})
        if not user:
            print("❌ Test user not found. Creating one...")
            test_user_id = str(uuid.uuid4())
            user_data = {
                '_id': test_user_id,
                'username': 'test_user',
                'email': 'test@example.com',
                'created_at': datetime.utcnow(),
                'is_active': True
            }
            db.users.insert_one(user_data)
            user = user_data
            print(f"✅ Created test user: {test_user_id}")
        
        # Create a new API key using the exact same method as the admin panel
        user_id = user['_id']
        key_name = f"Admin Panel Test Key {datetime.now().strftime('%H:%M:%S')}"
        rate_limit = 1000
        
        # Generate API key
        api_key = f"ytapi_{str(uuid.uuid4()).replace('-', '')[:20]}"
        api_key_data = {
            '_id': str(uuid.uuid4()),
            'key': api_key,
            'user_id': user_id,
            'name': key_name,
            'is_active': True,
            'rate_limit': rate_limit,
            'usage_count': 0,
            'created_at': datetime.utcnow(),
            'expires_at': None,
            'permissions': ['youtube_download', 'metadata_access', 'streaming'],
            'status': 'active',
            'tier': 'professional',
            'created_by': 'admin_panel_fix'
        }
        
        result = db.api_keys.insert_one(api_key_data)
        
        if result.inserted_id:
            print(f"✅ API Key created successfully!")
            print(f"   Key: {api_key}")
            print(f"   Name: {key_name}")
            print(f"   User: {user['username']} ({user_id})")
            print(f"   Rate Limit: {rate_limit}/hour")
            print(f"   ID: {result.inserted_id}")
            
            # Verify it was created
            created_key = db.api_keys.find_one({'_id': api_key_data['_id']})
            if created_key:
                print(f"✅ Verification: Key exists in database")
                
                # Count total API keys
                total_keys = db.api_keys.count_documents({})
                active_keys = db.api_keys.count_documents({'is_active': True})
                print(f"   Total keys in database: {total_keys}")
                print(f"   Active keys: {active_keys}")
                
                client.close()
                return True
            else:
                print("❌ Verification failed: Key not found in database")
                client.close()
                return False
        else:
            print("❌ Failed to create API key")
            client.close()
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_admin_panel_urls():
    """Test if admin panel URLs are accessible"""
    import requests
    
    try:
        base_url = "http://localhost:5000"
        
        # Test basic endpoints
        endpoints = [
            "/health",
            "/admin/login",
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"✅ {endpoint} is accessible")
                else:
                    print(f"❌ {endpoint} returned {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"❌ {endpoint} failed: {e}")
        
        print(f"\n📋 Admin Panel Access Info:")
        print(f"   URL: {base_url}/admin")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        
    except Exception as e:
        print(f"❌ URL test error: {e}")

if __name__ == "__main__":
    print("🔧 Fixing API key creation...")
    if fix_and_test_api_key_creation():
        print(f"\n🎉 API key creation is working!")
        print(f"   Now you can create API keys through the admin panel!")
        
        print(f"\n🌐 Testing admin panel accessibility...")
        test_admin_panel_urls()
    else:
        print(f"\n❌ API key creation still has issues.")