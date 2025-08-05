#!/usr/bin/env python3
"""
Simple YouTube API Client Example
"""

import requests
import json
from typing import Dict, Any

class YouTubeAPIClient:
    def __init__(self, base_url: str = "http://localhost:5000", api_key: str = "demo-key"):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": api_key})
    
    def get_video_info(self, youtube_url: str) -> Dict[str, Any]:
        """Get video metadata"""
        response = self.session.get(
            f"{self.base_url}/api/v1/info",
            params={"url": youtube_url}
        )
        response.raise_for_status()
        return response.json()
    
    def download_video(self, youtube_url: str, quality: str = "360", save_path: str = None) -> str:
        """Download video and save to file"""
        response = self.session.get(
            f"{self.base_url}/api/v1/video",
            params={"url": youtube_url, "quality": quality}
        )
        response.raise_for_status()
        data = response.json()
        
        # Download the actual video
        video_response = self.session.get(data['download_url'])
        video_response.raise_for_status()
        
        # Save to file
        if not save_path:
            video_id = youtube_url.split('v=')[1].split('&')[0]
            save_path = f"video_{video_id}_{quality}p.mp4"
        
        with open(save_path, 'wb') as f:
            f.write(video_response.content)
        
        return save_path
    
    def download_audio(self, youtube_url: str, save_path: str = None) -> str:
        """Download audio and save to file"""
        response = self.session.get(
            f"{self.base_url}/api/v1/audio",
            params={"url": youtube_url}
        )
        response.raise_for_status()
        data = response.json()
        
        # Download the actual audio
        audio_response = self.session.get(data['download_url'])
        audio_response.raise_for_status()
        
        # Save to file
        if not save_path:
            video_id = youtube_url.split('v=')[1].split('&')[0]
            save_path = f"audio_{video_id}.mp3"
        
        with open(save_path, 'wb') as f:
            f.write(audio_response.content)
        
        return save_path
    
    def get_status(self) -> Dict[str, Any]:
        """Get API server status"""
        response = self.session.get(f"{self.base_url}/api/v1/status")
        response.raise_for_status()
        return response.json()

def main():
    """Example usage"""
    # Initialize client
    client = YouTubeAPIClient(api_key="demo-key")
    
    # Example YouTube URL
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print("YouTube API Client Example")
    print("=" * 40)
    
    try:
        # Get server status
        print("1. Checking server status...")
        status = client.get_status()
        print(f"   Server: {status.get('status', 'unknown')}")
        print(f"   Concurrent users: {status.get('concurrent_users', 0)}")
        
        # Get video information
        print("\n2. Getting video information...")
        info = client.get_video_info(youtube_url)
        print(f"   Title: {info.get('title', 'Unknown')}")
        print(f"   Duration: {info.get('duration', 0)} seconds")
        print(f"   Thumbnail: {info.get('thumbnail', 'N/A')}")
        
        # Download video (360p)
        print("\n3. Downloading video (360p)...")
        video_path = client.download_video(youtube_url, quality="360")
        print(f"   Video saved to: {video_path}")
        
        # Download audio only
        print("\n4. Downloading audio...")
        audio_path = client.download_audio(youtube_url)
        print(f"   Audio saved to: {audio_path}")
        
        print("\n✅ All operations completed successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()