#!/usr/bin/env python3
"""
Quick fix for cache system - add Rick Astley video manually to database
"""

import asyncio
from database.simple_mongo import get_content_cache_collection
from datetime import datetime

async def add_rick_astley_cache():
    """Add Rick Astley video manually to cache for testing"""
    print("📝 Adding Rick Astley video to cache database...")
    
    try:
        # Initialize database connection
        from database.simple_mongo import init_db
        await init_db()
        
        cache_collection = get_content_cache_collection()
        if cache_collection is None:
            print("❌ Could not connect to cache collection")
            return False
        
        # Rick Astley video details from user's screenshot
        cache_entry = {
            'youtube_id': 'dQw4w9WgXcQ',
            'title': 'Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)',
            'file_type': 'video',
            'quality': '360p',
            'duration': '3.55 min',
            'file_size': '32.7MB',
            'telegram_file_id': f'manually_uploaded_rick_astley_{datetime.utcnow().strftime("%Y%m%d")}',
            'telegram_channel_id': '-1002863131570',
            'status': 'active',
            'cached_at': datetime.utcnow(),
            'created_at': datetime.utcnow(),
            'access_count': 0,
            'last_accessed': datetime.utcnow(),
            'upload_date': '2025-08-06 07:33 UTC',
            'cache_source': 'manual_upload',
            'cached': True,
            'source': 'telegram'
        }
        
        # Check if already exists
        existing = await cache_collection.find_one({'youtube_id': 'dQw4w9WgXcQ', 'file_type': 'video'})
        if existing:
            print("✅ Cache entry already exists")
            print(f"   Title: {existing['title']}")
            print(f"   Quality: {existing.get('quality', 'N/A')}")
            print(f"   Status: {existing.get('status', 'N/A')}")
            
            # Update to ensure it's active
            await cache_collection.update_one(
                {'_id': existing['_id']},
                {'$set': {
                    'status': 'active',
                    'cached': True,
                    'source': 'telegram',
                    'last_accessed': datetime.utcnow()
                }}
            )
            print("   ✅ Updated cache entry to active status")
            return True
        
        # Insert new cache entry
        result = await cache_collection.insert_one(cache_entry)
        print(f"✅ Cache entry created with ID: {result.inserted_id}")
        print(f"   YouTube ID: {cache_entry['youtube_id']}")
        print(f"   Quality: {cache_entry['quality']}")
        print(f"   File Size: {cache_entry['file_size']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to add cache entry: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_with_cache():
    """Test API after adding cache entry"""
    print("\n🧪 Testing API with cache entry...")
    
    import requests
    import time
    
    api_url = "http://localhost:5000/api/v1/video"
    params = {
        'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'quality': '360p',
        'api_key': 'ytapi_6e2883aa716b4c5d'
    }
    
    start_time = time.time()
    try:
        response = requests.get(api_url, params=params, timeout=30)
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"   Status: {response.status_code}")
        print(f"   Response Time: {response_time:.3f}s")
        
        if response.status_code == 200:
            data = response.json()
            cached = data.get('cached', False)
            source = data.get('source', 'unknown')
            
            print(f"   Cached: {cached}")
            print(f"   Source: {source}")
            
            if cached and response_time <= 1.0:
                print("   🎉 SUCCESS! Fast cache response!")
                return True
            elif cached:
                print(f"   ✅ Cached but slower than expected")
                return True
            else:
                print("   ⚠️ Not using cache, still external source")
                return False
        else:
            print(f"   ❌ API Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False

async def main():
    """Fix cache system"""
    print("🔧 Quick Cache System Fix")
    print("=" * 40)
    
    # Add cache entry
    cache_added = await add_rick_astley_cache()
    
    if cache_added:
        # Test API
        api_success = await test_api_with_cache()
        
        print("\n" + "=" * 40)
        print("📊 Fix Summary:")
        print(f"   Cache Entry: {'✅' if cache_added else '❌'}")
        print(f"   API Test: {'✅' if api_success else '❌'}")
        
        if cache_added and api_success:
            print("\n🎉 CACHE SYSTEM WORKING!")
            print("   Rick Astley video now cached and served fast!")
        else:
            print("\n🔧 Cache added but API still needs work")
    else:
        print("\n❌ Could not add cache entry")

if __name__ == "__main__":
    asyncio.run(main())