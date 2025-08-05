# How to Use the YouTube API Server

This is a high-performance YouTube API server that provides video downloading, streaming, and metadata extraction services with MongoDB storage and caching.

## Quick Start

The server is currently running on port 5000. You can use it in several ways:

### 1. Direct HTTP Requests

#### Get Video Information
```python
import requests

# Basic video info
response = requests.get(
    "http://localhost:5000/api/v1/info",
    params={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    headers={"X-API-Key": "your-api-key"}
)
info = response.json()
print(f"Title: {info['title']}")
print(f"Duration: {info['duration']}")
```

#### Download Video
```python
import requests

# Get video download URL
response = requests.get(
    "http://localhost:5000/api/v1/video", 
    params={
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "quality": "720"  # Options: 144, 240, 360, 480, 720, 1080
    },
    headers={"X-API-Key": "your-api-key"}
)
video_data = response.json()
download_url = video_data['download_url']

# Download the video file
video_response = requests.get(download_url)
with open("video.mp4", "wb") as f:
    f.write(video_response.content)
```

#### Download Audio Only
```python
import requests

# Get audio download URL
response = requests.get(
    "http://localhost:5000/api/v1/audio",
    params={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    headers={"X-API-Key": "your-api-key"}
)
audio_data = response.json()
download_url = audio_data['download_url']

# Download the audio file
audio_response = requests.get(download_url)
with open("audio.mp3", "wb") as f:
    f.write(audio_response.content)
```

### 2. Python Client Class

Create a reusable client for easier integration:

```python
import requests
import json
from typing import Dict, Any, Optional

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
    
    def download_video(self, youtube_url: str, quality: str = "360") -> bytes:
        """Download video and return content"""
        response = self.session.get(
            f"{self.base_url}/api/v1/video",
            params={"url": youtube_url, "quality": quality}
        )
        response.raise_for_status()
        data = response.json()
        
        # Download the actual video
        video_response = self.session.get(data['download_url'])
        video_response.raise_for_status()
        return video_response.content
    
    def download_audio(self, youtube_url: str) -> bytes:
        """Download audio and return content"""
        response = self.session.get(
            f"{self.base_url}/api/v1/audio",
            params={"url": youtube_url}
        )
        response.raise_for_status()
        data = response.json()
        
        # Download the actual audio
        audio_response = self.session.get(data['download_url'])
        audio_response.raise_for_status()
        return audio_response.content
    
    def get_status(self) -> Dict[str, Any]:
        """Get API server status"""
        response = self.session.get(f"{self.base_url}/api/v1/status")
        response.raise_for_status()
        return response.json()

# Usage example
client = YouTubeAPIClient(api_key="your-api-key")

# Get video information
info = client.get_video_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
print(f"Video: {info['title']} ({info['duration']}s)")

# Download video
video_content = client.download_video(
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ", 
    quality="720"
)
with open("downloaded_video.mp4", "wb") as f:
    f.write(video_content)

# Download audio only
audio_content = client.download_audio("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
with open("downloaded_audio.mp3", "wb") as f:
    f.write(audio_content)
```

### 3. Async Python Client

For high-performance applications with many requests:

```python
import asyncio
import aiohttp
from typing import Dict, Any

class AsyncYouTubeAPIClient:
    def __init__(self, base_url: str = "http://localhost:5000", api_key: str = "demo-key"):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key}
    
    async def get_video_info(self, session: aiohttp.ClientSession, youtube_url: str) -> Dict[str, Any]:
        async with session.get(
            f"{self.base_url}/api/v1/info",
            params={"url": youtube_url},
            headers=self.headers
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def download_video(self, session: aiohttp.ClientSession, youtube_url: str, quality: str = "360") -> bytes:
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
                return await video_response.read()

# Usage example
async def main():
    client = AsyncYouTubeAPIClient(api_key="your-api-key")
    
    async with aiohttp.ClientSession() as session:
        # Process multiple videos concurrently
        urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=oHg5SJYRHA0"
        ]
        
        # Get info for all videos concurrently
        tasks = [client.get_video_info(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        
        for info in results:
            print(f"Video: {info['title']}")

# Run the async example
asyncio.run(main())
```

## API Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/api/v1/info` | GET | Get video metadata | `url` (required) |
| `/api/v1/video` | GET | Get video download URL | `url` (required), `quality` (optional) |
| `/api/v1/audio` | GET | Get audio download URL | `url` (required) |
| `/api/v1/status` | GET | Get server status | None |
| `/stream/video/<video_id>` | GET | Stream video directly | `quality` (optional) |
| `/stream/audio/<video_id>` | GET | Stream audio directly | None |

## Authentication

All API requests require an API key passed via:
- Header: `X-API-Key: your-api-key`
- URL parameter: `?api_key=your-api-key`

## Admin Panel

Access the admin panel at `http://localhost:5000/admin` to:
- Create and manage API keys
- View usage statistics
- Monitor server performance
- Manage cached content

Default admin credentials:
- Username: `admin`
- Password: `admin123`

## Error Handling

The API returns standard HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid URL or parameters)
- `401`: Unauthorized (missing or invalid API key)
- `429`: Rate limit exceeded
- `500`: Internal server error

Example error response:
```json
{
    "status": false,
    "error": "Invalid YouTube URL",
    "message": "Please provide a valid YouTube video URL"
}
```

## Rate Limits

- Default: 1000 requests per hour per API key
- Configurable per API key in admin panel
- Concurrent user support: 10,000+ users

## MongoDB Integration

The server uses MongoDB Atlas for:
- User and API key management
- Usage statistics tracking
- Content caching metadata
- Real-time analytics

## Features

- **High Performance**: Supports 10,000+ concurrent users
- **Smart Caching**: Telegram-based content caching for faster responses
- **Multiple Quality Options**: 144p to 1080p video downloads
- **Audio Extraction**: High-quality audio-only downloads
- **Real-time Analytics**: Live dashboard with usage statistics
- **Rate Limiting**: Configurable per-key rate limits
- **MongoDB Integration**: Professional data storage and analytics