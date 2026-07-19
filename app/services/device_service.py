"""Service for device CRUD operations."""

from sqlalchemy.orm import Session

from app.models.device import Device, DeviceType
from app.models.changelog import EntityType, ActionType
from app.services.changelog_service import log_change


def create_device_type(session: Session, name: str, icon: str | None = None) -> DeviceType:
    """Create a new device type category."""
    dt = DeviceType(name=name, icon=icon)
    session.add(dt)
    session.commit()
    return dt


def get_all_device_types(session: Session) -> list[DeviceType]:
    """Get all device type categories."""
    return session.query(DeviceType).order_by(DeviceType.name).all()


def create_device(
    session: Session,
    name: str,
    device_type_id: int | None = None,
    manufacturer: str | None = None,
    model: str | None = None,
    serial_number: str | None = None,
    mac_address: str | None = None,
    notes: str | None = None,
) -> Device:
    """Create a new device."""
    device = Device(
        name=name,
        device_type_id=device_type_id,
        manufacturer=manufacturer,
        model=model,
        serial_number=serial_number,
        mac_address=mac_address,
        notes=notes,
    )
    session.add(device)
    session.flush()

    log_change(
        session,
        entity_type=EntityType.DEVICE,
        entity_id=device.id,
        action=ActionType.CREATED,
        entity_name=name,
        new_values={"name": name, "manufacturer": manufacturer, "model": model},
    )
    session.commit()
    return device


def get_all_devices(session: Session) -> list[Device]:
    """Get all devices."""
    return session.query(Device).order_by(Device.name).all()


def get_device_by_id(session: Session, device_id: int) -> Device | None:
    """Get a single device by ID."""
    return session.query(Device).filter(Device.id == device_id).first()


def update_device(session: Session, device_id: int, **kwargs) -> Device | None:
    """Update a device's fields."""
    device = get_device_by_id(session, device_id)
    if not device:
        return None

    old_values = {}
    new_values = {}
    for key, value in kwargs.items():
        if hasattr(device, key):
            old_values[key] = getattr(device, key)
            setattr(device, key, value)
            new_values[key] = value

    if new_values:
        log_change(
            session,
            entity_type=EntityType.DEVICE,
            entity_id=device.id,
            action=ActionType.UPDATED,
            entity_name=device.name,
            old_values=old_values,
            new_values=new_values,
        )
    session.commit()
    return device


def delete_device(session: Session, device_id: int) -> bool:
    """Delete a device."""
    device = get_device_by_id(session, device_id)
    if not device:
        return False

    log_change(
        session,
        entity_type=EntityType.DEVICE,
        entity_id=device.id,
        action=ActionType.DELETED,
        entity_name=device.name,
        old_values={"name": device.name, "manufacturer": device.manufacturer},
    )

    # Archive associated notes (preserve for future reference)
    from app.models.note import Note
    notes_to_archive = session.query(Note).filter(
        Note.entity_type == "device", Note.entity_id == device.id, Note.is_archived == 0
    ).all()
    for note in notes_to_archive:
        note.is_archived = 1
        note.archived_hostname = device.name

    session.delete(device)
    session.commit()
    return True
