#!/usr/bin/env python3
import asyncio
from database.simple_mongo import get_api_keys_collection
from datetime import datetime
import secrets

async def create_test_api_key():
    """Create a test API key for Rick Astley video testing"""
    print("Creating test API key for Rick Astley video testing...")
    
    collection = get_api_keys_collection()
    if not collection:
        print("❌ Could not connect to API keys collection")
        return None
    
    # Generate secure API key
    api_key = f"rick_test_{secrets.token_urlsafe(32)}"
    
    key_data = {
        'key_name': 'rick_astley_test',
        'api_key': api_key,
        'daily_limit': 1000,
        'is_active': True,
        'created_at': datetime.utcnow(),
        'created_by': 'test_system'
    }
    
    try:
        result = await collection.insert_one(key_data)
        print(f"✅ API key created successfully!")
        print(f"Key Name: {key_data['key_name']}")
        print(f"API Key: {api_key}")
        print(f"Daily Limit: {key_data['daily_limit']}")
        return api_key
    except Exception as e:
        print(f"❌ Error creating API key: {e}")
        return None

if __name__ == "__main__":
    api_key = asyncio.run(create_test_api_key())
    if api_key:
        print(f"\n🎯 Test URL:")
        print(f"curl -X GET \"http://localhost:5000/api/v1/video?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&quality=360p&api_key={api_key}\"")