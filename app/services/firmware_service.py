"""Firmware tracking service — monitors UniFi device firmware versions."""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session

from app.database.db import get_session
from app.models.device_firmware import DeviceFirmware
from app.models.firmware_history import FirmwareHistory
from app.services.unifi_service import fetch_devices_from_unifi, is_configured


# --- Service Functions ---

def sync_firmware_info() -> dict:
    """
    Fetch firmware info from UniFi devices and update the tracking table.
    Returns summary: {"checked": int, "updates_available": int, "new_devices": int, "errors": list}
    """
    if not is_configured():
        return {"checked": 0, "updates_available": 0, "new_devices": 0,
                "errors": ["UniFi not configured"]}

    with get_session() as session:
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

                # Check upgrade state / updatable flags
                # UniFi Integration API v1 uses 'firmwareUpdatable' (boolean)
                upgrade_state = dev.get("upgradeState") or dev.get("upgrade_state") or ""
                is_upgradable = (
                    dev.get("firmwareUpdatable", False)
                    or bool(available_fw and available_fw != current_fw)
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

                    # Detect if firmware was just updated — record history
                    if old_version and current_fw and old_version != current_fw:
                        existing.last_updated = now
                        history_entry = FirmwareHistory(
                            device_mac=mac,
                            device_name=name,
                            old_version=old_version,
                            new_version=current_fw,
                        )
                        session.add(history_entry)

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

            # Fire webhook triggers for firmware updates
            try:
                from app.services.webhook_trigger_service import fire_event
                for item in newly_available:
                    fire_event("firmware_update", {
                        "device": item["name"],
                        "current_version": item["current"],
                        "available_version": item["available"],
                    })
            except Exception as e:
                logger.debug("Webhook fire_event firmware_update failed: %s", e)

        return {
            "checked": checked,
            "updates_available": updates_available,
            "new_devices": new_devices,
            "newly_available": len(newly_available),
            "errors": errors,
        }


def get_all_firmware(session: Session = None) -> list[DeviceFirmware]:
    """Get all firmware tracking records."""
    if session is not None:
        return session.query(DeviceFirmware).order_by(DeviceFirmware.device_name).all()
    with get_session() as s:
        return s.query(DeviceFirmware).order_by(DeviceFirmware.device_name).all()


def get_devices_with_updates(session: Session = None) -> list[DeviceFirmware]:
    """Get only devices that have firmware updates available."""
    if session is not None:
        return (
            session.query(DeviceFirmware)
            .filter(DeviceFirmware.update_available == True)
            .order_by(DeviceFirmware.device_name)
            .all()
        )
    with get_session() as s:
        return (
            s.query(DeviceFirmware)
            .filter(DeviceFirmware.update_available == True)
            .order_by(DeviceFirmware.device_name)
            .all()
        )


def get_firmware_history(limit: int = 50) -> list[FirmwareHistory]:
    """Get recent firmware version change history."""
    with get_session() as session:
        return (
            session.query(FirmwareHistory)
            .order_by(FirmwareHistory.detected_at.desc())
            .limit(limit)
            .all()
        )
