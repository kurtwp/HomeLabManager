"""Application configuration loaded from environment variables."""

import os
import secrets
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./home_lab_manager.db")

# App
APP_TITLE = os.getenv("APP_TITLE", "Home Lab Manager")
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8080"))
STORAGE_SECRET = os.getenv("STORAGE_SECRET", secrets.token_hex(32))

# UniFi Integration (Phase 2)
UNIFI_API_KEY = os.getenv("UNIFI_API_KEY", "")
UNIFI_BASE_URL = os.getenv("UNIFI_BASE_URL", "https://192.168.2.254")
UNIFI_SITE_ID = os.getenv("UNIFI_SITE_ID", "")
UNIFI_CLOUD_API_KEY = os.getenv("UNIFI_CLOUD_API_KEY", "")

# REST API
API_KEY = os.getenv("API_KEY", "")
