#!/usr/bin/env python3
"""
Test production cache with proper initialization
"""

import asyncio
from database.simple_mongo import init_db, get_content_cache_collection

async def test_production_cache():
    """Test cache with production data"""
    print("🔍 Testing production cache system...")
    
    # Initialize database properly
    success = await init_db()
    print(f"📊 Database init result: {success}")
    
    collection = get_content_cache_collection()
    if collection is None:
        print("❌ Failed to get cache collection")
        return
    
    # Test video ID
    video_id = "dQw4w9WgXcQ"
    print(f"🎬 Testing video: {video_id}")
    
    # Direct database query
    cached_entry = await collection.find_one({
        'youtube_id': video_id,
        'file_type': 'video',
        'status': 'active'
    })
    
    if cached_entry:
        print("✅ PRODUCTION CACHE HIT!")
        print(f"📝 Title: {cached_entry['title']}")
        print(f"📱 Telegram File ID: {cached_entry['telegram_file_id']}")
        print(f"📺 Type: {cached_entry['file_type']}")
        print(f"🎯 Quality: {cached_entry.get('quality', 'N/A')}")
        print(f"📊 Status: {cached_entry['status']}")
        print(f"📅 Created: {cached_entry.get('created_at', 'N/A')}")
        
        # Simulate cache response
        cache_response = {
            'status': True,
            'cached': True,
            'source': 'telegram_cache',
            'video_id': video_id,
            'title': cached_entry['title'],
            'duration': cached_entry['duration'],
            'telegram_file_id': cached_entry['telegram_file_id'],
            'file_type': cached_entry['file_type'],
            'quality': cached_entry.get('quality', '360p'),
            'file_size': cached_entry.get('file_size', 'Unknown'),
            'upload_date': cached_entry.get('upload_date', 'Unknown'),
            'message': 'Ultra-fast response from Telegram cache!'
        }
        
        print("\n🚀 Production cache response:")
        print(cache_response)
        
    else:
        print("❌ No production cache found")
        
        # Check all entries to debug
        all_entries = collection.find({'youtube_id': video_id}).limit(3)
        print("\nAll entries for this video:")
        async for entry in all_entries:
            print(f"  Status: {entry.get('status', 'N/A')}")
            print(f"  Type: {entry.get('file_type', 'N/A')}")
            print(f"  Telegram ID: {entry.get('telegram_file_id', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_production_cache())