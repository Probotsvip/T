#!/usr/bin/env python3
"""
Fix production API key issues and ensure real data only
"""

import asyncio
from datetime import datetime
from database.simple_mongo import init_db, get_api_keys_collection

async def create_production_api_key():
    """Create a proper production API key"""
    await init_db()
    collection = get_api_keys_collection()
    
    # Create production API key
    api_key_data = {
        'key': 'prod_youtube_api_2025',
        'name': 'Production YouTube API Key',
        'is_active': True,
        'rate_limit': 10000,  # High limit for production
        'usage_count': 0,
        'created_at': datetime.utcnow(),
        'last_used': None,
        'created_by': 'system'
    }
    
    # Upsert (insert or update)
    await collection.update_one(
        {'key': 'prod_youtube_api_2025'},
        {'$set': api_key_data},
        upsert=True
    )
    
    print("✅ Production API key created: prod_youtube_api_2025")
    print("🔧 Rate limit: 10,000 requests/hour")
    print("🎯 Ready for production use with real YouTube data")

if __name__ == "__main__":
    asyncio.run(create_production_api_key())