"""SQLAlchemy models for Home Lab Manager."""

from app.models.network import Network
from app.models.ip_address import IPAddress
from app.models.device import Device, DeviceType
from app.models.tag import Tag, ip_tags, device_tags, network_tags
from app.models.documentation import Documentation
from app.models.changelog import Changelog
from app.models.scan_log import ScanLog
from app.models.custom_field import CustomFieldDefinition, CustomFieldValue
from app.models.saved_search import SavedSearch
from app.models.note import Note
from app.models.uptime_monitor import MonitoredHost, UptimeEvent, PingResult
from app.models.user import User
from app.models.ssl_certificate import SSLCertificate
from app.models.device_firmware import DeviceFirmware
from app.models.notification_log import NotificationLog
from app.models.notification_preference import NotificationPreference
from app.models.login_attempt import LoginAttempt
from app.models.firmware_history import FirmwareHistory
from app.models.controller_firmware import ControllerFirmware
from app.services.mac_watchlist_service import KnownMAC
from app.services.webhook_trigger_service import WebhookTrigger
from app.services.domain_service import TrackedDomain
from app.services.snmp_profiles import SNMPProfile

__all__ = [
    "Network",
    "IPAddress",
    "Device",
    "DeviceType",
    "Tag",
    "ip_tags",
    "device_tags",
    "network_tags",
    "Documentation",
    "Changelog",
    "ScanLog",
    "CustomFieldDefinition",
    "CustomFieldValue",
    "SavedSearch",
    "Note",
    "MonitoredHost",
    "UptimeEvent",
    "PingResult",
    "User",
    "SSLCertificate",
    "DeviceFirmware",
    "NotificationLog",
    "NotificationPreference",
    "LoginAttempt",
    "FirmwareHistory",
    "ControllerFirmware",
    "KnownMAC",
    "WebhookTrigger",
    "TrackedDomain",
    "SNMPProfile",
]
