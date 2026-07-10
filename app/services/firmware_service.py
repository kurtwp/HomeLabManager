"""Firmware tracking service — monitors UniFi device firmware versions."""

from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, Session

from app.database.db import Base, SessionLocal
from app.services.unifi_service import fetch_devices_from_unifi, is_configured


# --- Firmware Model ---

class DeviceFirmware(Base):
    """Tracks firmware versions for network devices."""

    __tablename__ = "device_firmware"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_mac: Mapped[str] = mapped_column(String(17), nullable=False, unique=True)
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    available_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    update_available: Mapped[bool] = mapped_column(Boolean, default=False)
    last_checked: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    auto_update_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<DeviceFirmware({self.device_name} v={self.current_version})>"


# --- Service Functions ---

def sync_firmware_info() -> dict:
    """
    Fetch firmware info from UniFi devices and update the tracking table.
    Returns summary: {"checked": int, "updates_available": int, "new_devices": int, "errors": list}
    """
    if not is_configured():
        return {"checked": 0, "updates_available": 0, "new_devices": 0,
                "errors": ["UniFi not configured"]}

    session = SessionLocal()
    try:
        devices = fetch_devices_from_unifi()
        checked = 0
        updates_available = 0
        new_devices = 0
        newly_available = []
        errors = []

        now = datetime.now(timezone.utc)

        for dev in devices:
            try:
                mac = (dev.get("mac") or dev.get("macAddress") or "").upper().replace("-", ":")
                if not mac:
                    continue

                name = dev.get("name") or dev.get("hostname") or mac
                model = dev.get("model") or dev.get("shortname") or ""

                # Extract firmware version - try multiple fields
                current_fw = (
                    dev.get("firmwareVersion")
                    or dev.get("version")
                    or dev.get("displayableVersion")
                    or dev.get("currentFirmwareVersion")
                    or ""
                )

                # Extract available firmware update
                available_fw = (
                    dev.get("upgradeToFirmware")
                    or dev.get("upgradableFirmwareVersion")
                    or dev.get("latestFirmwareVersion")
                    or ""
                )

                # Check upgrade state field
                upgrade_state = dev.get("upgradeState") or dev.get("upgrade_state") or ""
                is_upgradable = (
                    bool(available_fw and available_fw != current_fw)
                    or upgrade_state in ("available", "pending")
                    or dev.get("upgradable", False)
                    or dev.get("isUpgradable", False)
                )

                # Find or create firmware record
                existing = session.query(DeviceFirmware).filter(
                    DeviceFirmware.device_mac == mac
                ).first()

                if existing:
                    old_version = existing.current_version
                    old_update_available = existing.update_available

                    existing.device_name = name
                    existing.model = model
                    existing.current_version = current_fw
                    existing.available_version = available_fw if is_upgradable else None
                    existing.update_available = is_upgradable
                    existing.last_checked = now

                    # Detect if firmware was just updated
                    if old_version and current_fw and old_version != current_fw:
                        existing.last_updated = now

                    # Detect newly available updates for notifications
                    if is_upgradable and not old_update_available:
                        newly_available.append({
                            "name": name,
                            "current": current_fw,
                            "available": available_fw,
                        })
                else:
                    firmware_record = DeviceFirmware(
                        device_mac=mac,
                        device_name=name,
                        model=model,
                        current_version=current_fw,
                        available_version=available_fw if is_upgradable else None,
                        update_available=is_upgradable,
                        last_checked=now,
                    )
                    session.add(firmware_record)
                    new_devices += 1

                    if is_upgradable:
                        newly_available.append({
                            "name": name,
                            "current": current_fw,
                            "available": available_fw,
                        })

                checked += 1
                if is_upgradable:
                    updates_available += 1

            except Exception as e:
                errors.append(f"Device '{dev.get('name', '?')}': {e}")

        session.commit()

        # Send notifications for newly discovered firmware updates
        if newly_available:
            try:
                from app.services.notification_service import (
                    notify_firmware_update, is_notifications_enabled
                )
                if is_notifications_enabled():
                    for item in newly_available:
                        notify_firmware_update(
                            item["name"], item["current"], item["available"]
                        )
            except Exception as e:
                errors.append(f"Notification error: {e}")

        return {
            "checked": checked,
            "updates_available": updates_available,
            "new_devices": new_devices,
            "newly_available": len(newly_available),
            "errors": errors,
        }

    except Exception as e:
        session.rollback()
        return {"checked": 0, "updates_available": 0, "new_devices": 0,
                "errors": [str(e)]}
    finally:
        session.close()


def get_all_firmware(session: Session = None) -> list[DeviceFirmware]:
    """Get all firmware tracking records."""
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    try:
        return session.query(DeviceFirmware).order_by(DeviceFirmware.device_name).all()
    finally:
        if close_session:
            session.close()


def get_devices_with_updates(session: Session = None) -> list[DeviceFirmware]:
    """Get only devices that have firmware updates available."""
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    try:
        return (
            session.query(DeviceFirmware)
            .filter(DeviceFirmware.update_available == True)
            .order_by(DeviceFirmware.device_name)
            .all()
        )
    finally:
        if close_session:
            session.close()
