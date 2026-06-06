"""Data formatting utilities."""

from datetime import datetime


def format_timestamp(dt: datetime | None) -> str:
    """Format a datetime for display."""
    if not dt:
        return "Never"
    return dt.strftime("%Y-%m-%d %H:%M")


def format_mac(mac: str | None) -> str:
    """Normalize MAC address to uppercase colon-separated format."""
    if not mac:
        return ""
    cleaned = mac.replace("-", ":").upper()
    return cleaned


def truncate(text: str, max_length: int = 80) -> str:
    """Truncate text with ellipsis."""
    if not text or len(text) <= max_length:
        return text or ""
    return text[:max_length - 3] + "..."
