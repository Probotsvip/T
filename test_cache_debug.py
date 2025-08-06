#!/usr/bin/env python3
"""
Debug script to check cache database entries
"""

import asyncio
from database.simple_mongo import init_db, get_content_cache_collection

async def debug_cache_database():
    """Check what's actually stored in cache database"""
    print("🔍 Debugging cache database entries...")
    
    # Initialize database
    await init_db()
    collection = get_content_cache_collection()
    
    if collection is None:
        print("❌ Failed to get cache collection")
        return
    
    # Count total entries
    total_count = await collection.count_documents({})
    print(f"📊 Total cache entries: {total_count}")
    
    # Get recent entries
    recent_entries = collection.find({}).sort('_id', -1).limit(5)
    
    print("\n📋 Recent cache entries:")
    async for entry in recent_entries:
        print(f"  📹 Video ID: {entry.get('youtube_id', 'N/A')}")
        print(f"  📝 Title: {entry.get('title', 'N/A')}")
        print(f"  📱 Telegram File ID: {entry.get('telegram_file_id', 'N/A')}")
        print(f"  📺 Type: {entry.get('file_type', 'N/A')}")
        print(f"  🎯 Quality: {entry.get('quality', 'N/A')}")
        print(f"  📊 Status: {entry.get('status', 'N/A')}")
        print(f"  📅 Created: {entry.get('created_at', 'N/A')}")
        print("  " + "-"*50)
    
    # Check specifically for our test video
    test_video_id = "dQw4w9WgXcQ"
    print(f"\n🎯 Checking for test video: {test_video_id}")
    
    test_entries = collection.find({'youtube_id': test_video_id})
    count = 0
    async for entry in test_entries:
        count += 1
        print(f"  Entry #{count}:")
        print(f"    📹 Video ID: {entry.get('youtube_id')}")
        print(f"    📝 Title: {entry.get('title')}")
        print(f"    📱 Telegram File ID: {entry.get('telegram_file_id')}")
        print(f"    📺 Type: {entry.get('file_type')}")
        print(f"    🎯 Quality: {entry.get('quality')}")
        print(f"    📊 Status: {entry.get('status')}")
    
    if count == 0:
        print(f"  ❌ No entries found for {test_video_id}")
        print("  🔍 This explains why cache is not working!")
    else:
        print(f"  ✅ Found {count} entries for {test_video_id}")

if __name__ == "__main__":
    asyncio.run(debug_cache_database())