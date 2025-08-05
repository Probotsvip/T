#!/usr/bin/env python3
"""
Async YouTube API Client Example for High Performance
"""

import asyncio
import aiohttp
import aiofiles
import time
from typing import Dict, Any, List

class AsyncYouTubeAPIClient:
    def __init__(self, base_url: str = "http://localhost:5000", api_key: str = "demo-key"):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key}
    
    async def get_video_info(self, session: aiohttp.ClientSession, youtube_url: str) -> Dict[str, Any]:
        """Get video metadata"""
        async with session.get(
            f"{self.base_url}/api/v1/info",
            params={"url": youtube_url},
            headers=self.headers
        ) as response:
            response.raise_for_status()
            data = await response.json()
            data['url'] = youtube_url  # Add original URL for reference
            return data
    
    async def download_video(self, session: aiohttp.ClientSession, youtube_url: str, quality: str = "360") -> Dict[str, Any]:
        """Download video"""
        async with session.get(
            f"{self.base_url}/api/v1/video",
            params={"url": youtube_url, "quality": quality},
            headers=self.headers
        ) as response:
            response.raise_for_status()
            data = await response.json()
            
            # Download the actual video
            async with session.get(data['download_url']) as video_response:
                video_response.raise_for_status()
                content = await video_response.read()
                
                # Save to file
                video_id = youtube_url.split('v=')[1].split('&')[0]
                filename = f"video_{video_id}_{quality}p.mp4"
                
                async with aiofiles.open(filename, 'wb') as f:
                    await f.write(content)
                
                return {
                    'url': youtube_url,
                    'quality': quality,
                    'filename': filename,
                    'size': len(content)
                }
    
    async def download_audio(self, session: aiohttp.ClientSession, youtube_url: str) -> Dict[str, Any]:
        """Download audio"""
        async with session.get(
            f"{self.base_url}/api/v1/audio",
            params={"url": youtube_url},
            headers=self.headers
        ) as response:
            response.raise_for_status()
            data = await response.json()
            
            # Download the actual audio
            async with session.get(data['download_url']) as audio_response:
                audio_response.raise_for_status()
                content = await audio_response.read()
                
                # Save to file
                video_id = youtube_url.split('v=')[1].split('&')[0]
                filename = f"audio_{video_id}.mp3"
                
                async with aiofiles.open(filename, 'wb') as f:
                    await f.write(content)
                
                return {
                    'url': youtube_url,
                    'filename': filename,
                    'size': len(content)
                }

async def batch_download_info(urls: List[str], api_key: str = "demo-key"):
    """Download info for multiple videos concurrently"""
    client = AsyncYouTubeAPIClient(api_key=api_key)
    
    async with aiohttp.ClientSession() as session:
        # Create tasks for all URLs
        tasks = [client.get_video_info(session, url) for url in urls]
        
        # Execute all tasks concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        print(f"Downloaded info for {len(urls)} videos in {end_time - start_time:.2f} seconds")
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Error for URL {i+1}: {result}")
            else:
                print(f"✅ {result.get('title', 'Unknown')} ({result.get('duration', 0)}s)")
        
        return results

async def batch_download_videos(urls: List[str], quality: str = "360", api_key: str = "demo-key"):
    """Download multiple videos concurrently"""
    client = AsyncYouTubeAPIClient(api_key=api_key)
    
    async with aiohttp.ClientSession() as session:
        # Create tasks for all URLs
        tasks = [client.download_video(session, url, quality) for url in urls]
        
        # Execute all tasks concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        print(f"Downloaded {len(urls)} videos in {end_time - start_time:.2f} seconds")
        
        total_size = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Error downloading video {i+1}: {result}")
            else:
                size_mb = result['size'] / (1024 * 1024)
                total_size += result['size']
                print(f"✅ {result['filename']} ({size_mb:.1f} MB)")
        
        print(f"Total downloaded: {total_size / (1024 * 1024):.1f} MB")
        return results

async def main():
    """Example usage of async client"""
    print("Async YouTube API Client Example")
    print("=" * 50)
    
    # Example URLs
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=oHg5SJYRHA0",
        # Add more URLs as needed
    ]
    
    try:
        # 1. Get info for multiple videos concurrently
        print("1. Getting video information (concurrent)...")
        info_results = await batch_download_info(test_urls)
        
        # 2. Download videos concurrently
        print("\n2. Downloading videos (concurrent)...")
        video_results = await batch_download_videos(test_urls[:2], quality="360")  # Limit to 2 for demo
        
        # 3. Example with semaphore for rate limiting
        print("\n3. Rate-limited concurrent downloads...")
        semaphore = asyncio.Semaphore(2)  # Limit to 2 concurrent downloads
        
        async def limited_download(session, url):
            async with semaphore:
                client = AsyncYouTubeAPIClient()
                return await client.download_audio(session, url)
        
        async with aiohttp.ClientSession() as session:
            tasks = [limited_download(session, url) for url in test_urls[:3]]
            audio_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in audio_results:
                if not isinstance(result, Exception):
                    size_mb = result['size'] / (1024 * 1024)
                    print(f"✅ Audio: {result['filename']} ({size_mb:.1f} MB)")
        
        print("\n✅ All async operations completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Install required packages: pip install aiohttp aiofiles
    asyncio.run(main())