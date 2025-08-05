import os

# MongoDB Configuration
MONGO_DB_URI = os.getenv("MONGO_DB_URI", "mongodb://localhost:27017/youtube_api")

# Telegram Configuration
TELEGRAM_BOT_TOKEN = "7412125068:AAE_xef9Tgq0MZXpknz3-WPPKK7hl6t3im0"
TELEGRAM_CHANNEL_ID = "-1002863131570"

# Flask Configuration
SECRET_KEY = os.getenv("SESSION_SECRET", "your-secret-key-change-in-production")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# API Configuration
API_RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", "1000"))  # requests per hour
MAX_CONCURRENT_USERS = int(os.getenv("MAX_CONCURRENT_USERS", "10000"))

# Redis Configuration for caching and session management
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Admin Configuration
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Performance Configuration
WORKER_CONNECTIONS = int(os.getenv("WORKER_CONNECTIONS", "1000"))
KEEP_ALIVE = int(os.getenv("KEEP_ALIVE", "2"))
