#!/usr/bin/env python3
"""
Create API Key for YouTube API Server
"""

import asyncio
import uuid
from datetime import datetime
from database.simple_mongo import init_db, get_api_keys_collection, get_users_collection
from werkzeug.security import generate_password_hash

async def create_api_key(username="user", email=None, rate_limit=1000):
    """Create a new API key and user"""
    
    # Initialize database
    await init_db()
    
    # Generate unique API key
    api_key = f"api_{uuid.uuid4().hex[:24]}"
    
    # Create user data
    if not email:
        email = f"{username}@example.com"
    
    user_data = {
        "username": username,
        "email": email,
        "password_hash": generate_password_hash("default123"),
        "api_key": api_key,
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    # Create API key data
    api_key_data = {
        "key": api_key,
        "user_id": username,
        "rate_limit": rate_limit,
        "created_at": datetime.utcnow(),
        "is_active": True,
        "usage_count": 0,
        "last_used": None
    }
    
    try:
        # Insert user
        users_collection = get_users_collection()
        if users_collection:
            await users_collection.insert_one(user_data)
            print(f"✅ User created: {username}")
        
        # Insert API key
        api_keys_collection = get_api_keys_collection()
        if api_keys_collection:
            await api_keys_collection.insert_one(api_key_data)
            print(f"✅ API key created: {api_key}")
        
        return api_key
        
    except Exception as e:
        print(f"❌ Error creating API key: {e}")
        return None

async def main():
    """Main function to create API key"""
    print("YouTube API Key Creator")
    print("=" * 30)
    
    # Create API key
    username = f"user_{int(datetime.now().timestamp())}"
    api_key = await create_api_key(username, rate_limit=5000)
    
    if api_key:
        print(f"\n🎉 API Key Created Successfully!")
        print(f"📝 Username: {username}")
        print(f"🔑 API Key: {api_key}")
        print(f"📊 Rate Limit: 5000 requests/hour")
        print(f"\n📖 Usage Instructions:")
        print(f"   1. Use this API key in X-API-Key header")
        print(f"   2. Or add ?api_key={api_key} to URL")
        print(f"   3. See USAGE.md for complete examples")
        print(f"\n🔗 Test your API key:")
        print(f"   curl -H 'X-API-Key: {api_key}' 'http://localhost:5000/api/v1/status'")
    else:
        print("❌ Failed to create API key")

if __name__ == "__main__":
    asyncio.run(main())