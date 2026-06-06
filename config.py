"""Application configuration loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./home_lab_manager.db")

# App
APP_TITLE = os.getenv("APP_TITLE", "Home Lab Manager")
APP_PORT = int(os.getenv("APP_PORT", "8080"))

# UniFi Integration (Phase 2)
UNIFI_API_KEY = os.getenv("UNIFI_API_KEY", "")
UNIFI_BASE_URL = os.getenv("UNIFI_BASE_URL", "https://192.168.2.254")
UNIFI_SITE_ID = os.getenv("UNIFI_SITE_ID", "")
UNIFI_CLOUD_API_KEY = os.getenv("UNIFI_CLOUD_API_KEY", "")
