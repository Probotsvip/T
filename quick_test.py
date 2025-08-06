#!/usr/bin/env python3
"""
Quick test and fix for the admin panel database issue
"""
import os
from pymongo import MongoClient

def test_direct_database_access():
    """Test direct database access to see the exact issue"""
    try:
        mongo_uri = os.getenv("MONGO_DB_URI", "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority")
        client = MongoClient(mongo_uri)
        db = client.youtube_api_db
        
        # Test the exact queries that the admin panel uses
        print("🔍 Testing direct database queries...")
        
        # Get API keys
        api_keys = list(db.api_keys.find({}))
        print(f"   API Keys found: {len(api_keys)}")
        
        # Get users  
        users = list(db.users.find({}))
        print(f"   Users found: {len(users)}")
        
        # Test the aggregation pipeline that's causing issues
        pipeline = [
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'user_id',
                    'foreignField': '_id',
                    'as': 'user_info'
                }
            }
        ]
        
        aggregated_keys = list(db.api_keys.aggregate(pipeline))
        print(f"   Aggregated keys: {len(aggregated_keys)}")
        
        # Test what the admin panel should see
        formatted_keys = []
        for key in aggregated_keys:
            formatted_key = {
                '_id': key.get('_id'),
                'name': key.get('name'),
                'key': key.get('key'),
                'user_id': key.get('user_id'),
                'is_active': key.get('is_active', True),
                'rate_limit': key.get('rate_limit', 1000),
                'usage_count': key.get('usage_count', 0),
                'created_at': key.get('created_at'),
                'user_info': key.get('user_info', [{}])[0] if key.get('user_info') else {},
            }
            formatted_keys.append(formatted_key)
            
        print(f"   Formatted keys for template: {len(formatted_keys)}")
        
        # Print sample data to debug template
        if formatted_keys:
            sample_key = formatted_keys[0]
            print(f"   Sample key data:")
            for field, value in sample_key.items():
                print(f"     {field}: {value}")
        
        client.close()
        return formatted_keys, users
        
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return [], []

if __name__ == "__main__":
    keys, users = test_direct_database_access()
    
    if keys and users:
        print(f"\n✅ Database access is working correctly!")
        print(f"   Keys: {len(keys)}, Users: {len(users)}")
        print(f"   The issue is in the utils/sync_db.py query logic")
        
        # Create a simple replacement
        print(f"\n📝 Creating simple database replacement...")
        
        replacement_code = f'''
def get_all_api_keys_simple():
    """Simple API keys retrieval"""
    import os
    from pymongo import MongoClient
    
    mongo_uri = os.getenv("MONGO_DB_URI", "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority")
    client = MongoClient(mongo_uri)
    db = client.youtube_api_db
    
    # Simple aggregation
    pipeline = [{{
        '$lookup': {{
            'from': 'users',
            'localField': 'user_id',
            'foreignField': '_id',
            'as': 'user_info'
        }}
    }}]
    
    keys = list(db.api_keys.aggregate(pipeline))
    
    # Format for template
    formatted_keys = []
    for key in keys:
        user_info = key.get('user_info', [{{}}])[0] if key.get('user_info') else {{}}
        formatted_key = {{
            '_id': key.get('_id'),
            'name': key.get('name'),
            'key': key.get('key'),
            'user_id': key.get('user_id'),
            'is_active': key.get('is_active', True),
            'rate_limit': key.get('rate_limit', 1000),
            'usage_count': key.get('usage_count', 0),
            'created_at': key.get('created_at'),
            'user': {{
                'username': user_info.get('username', 'Unknown'),
                'email': user_info.get('email', 'Unknown')
            }}
        }}
        formatted_keys.append(formatted_key)
    
    client.close()
    return formatted_keys

def get_all_users_simple():
    """Simple users retrieval"""
    import os
    from pymongo import MongoClient
    
    mongo_uri = os.getenv("MONGO_DB_URI", "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority")
    client = MongoClient(mongo_uri)
    db = client.youtube_api_db
    
    users = list(db.users.find({{}}))
    client.close()
    return users
'''
        
        print("Use this simple code to replace the complex database queries")
        
    else:
        print(f"\n❌ Database access failed completely")