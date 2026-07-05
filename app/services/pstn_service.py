"""Service layer for PSTN/Telephony module — CRUD and utilities."""

from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.pstn.number_range import NumberRange
from app.models.pstn.phone_number import PhoneNumber


# ─── Number Range CRUD ──────────────────────────────────────────────────────────

def create_range(session: Session, **kwargs) -> NumberRange:
    """Create a new number range."""
    nr = NumberRange(**kwargs)
    session.add(nr)
    session.commit()
    session.refresh(nr)
    return nr


def get_all_ranges(session: Session) -> list[NumberRange]:
    """Get all number ranges ordered by name."""
    return session.query(NumberRange).order_by(NumberRange.name).all()


def get_range_by_id(session: Session, range_id: int) -> NumberRange | None:
    """Get a single range by ID."""
    return session.query(NumberRange).filter(NumberRange.id == range_id).first()


def update_range(session: Session, range_id: int, **kwargs) -> NumberRange | None:
    """Update a number range."""
    nr = get_range_by_id(session, range_id)
    if not nr:
        return None
    for key, value in kwargs.items():
        if hasattr(nr, key):
            setattr(nr, key, value)
    nr.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(nr)
    return nr


def delete_range(session: Session, range_id: int) -> bool:
    """Delete a number range. Returns True if deleted."""
    nr = get_range_by_id(session, range_id)
    if not nr:
        return False
    session.delete(nr)
    session.commit()
    return True


# ─── Phone Number CRUD ──────────────────────────────────────────────────────────

def create_phone_number(session: Session, **kwargs) -> PhoneNumber:
    """Create a new phone number."""
    pn = PhoneNumber(**kwargs)
    session.add(pn)
    session.commit()
    session.refresh(pn)
    return pn


def get_all_phone_numbers(session: Session) -> list[PhoneNumber]:
    """Get all phone numbers ordered by number."""
    return session.query(PhoneNumber).order_by(PhoneNumber.number).all()


def get_phone_number_by_id(session: Session, phone_id: int) -> PhoneNumber | None:
    """Get a phone number by ID."""
    return session.query(PhoneNumber).filter(PhoneNumber.id == phone_id).first()


def update_phone_number(session: Session, phone_id: int, **kwargs) -> PhoneNumber | None:
    """Update a phone number."""
    pn = get_phone_number_by_id(session, phone_id)
    if not pn:
        return None
    for key, value in kwargs.items():
        if hasattr(pn, key):
            setattr(pn, key, value)
    pn.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(pn)
    return pn


def delete_phone_number(session: Session, phone_id: int) -> bool:
    """Delete a phone number. Returns True if deleted."""
    pn = get_phone_number_by_id(session, phone_id)
    if not pn:
        return False
    session.delete(pn)
    session.commit()
    return True


def get_numbers_by_range(session: Session, range_id: int) -> list[PhoneNumber]:
    """Get all phone numbers belonging to a specific range."""
    return (
        session.query(PhoneNumber)
        .filter(PhoneNumber.range_id == range_id)
        .order_by(PhoneNumber.number)
        .all()
    )


# ─── Utilization & Search ───────────────────────────────────────────────────────

def get_range_utilization(session: Session, range_id: int) -> dict:
    """
    Get utilization stats for a number range.
    Returns dict with total, allocated, active, reserved, inactive, utilization_percent.
    """
    nr = get_range_by_id(session, range_id)
    if not nr:
        return {"total": 0, "allocated": 0, "utilization_percent": 0}

    total = nr.total_numbers or 0
    allocated = session.query(PhoneNumber).filter(PhoneNumber.range_id == range_id).count()
    active = (
        session.query(PhoneNumber)
        .filter(PhoneNumber.range_id == range_id, PhoneNumber.status == "active")
        .count()
    )
    reserved = (
        session.query(PhoneNumber)
        .filter(PhoneNumber.range_id == range_id, PhoneNumber.status == "reserved")
        .count()
    )
    inactive = (
        session.query(PhoneNumber)
        .filter(PhoneNumber.range_id == range_id, PhoneNumber.status == "inactive")
        .count()
    )
    future_use = (
        session.query(PhoneNumber)
        .filter(PhoneNumber.range_id == range_id, PhoneNumber.status == "future_use")
        .count()
    )

    utilization_percent = round((allocated / total * 100), 1) if total > 0 else 0.0

    return {
        "total": total,
        "allocated": allocated,
        "active": active,
        "reserved": reserved,
        "inactive": inactive,
        "future_use": future_use,
        "utilization_percent": utilization_percent,
    }


def search_numbers(session: Session, query: str) -> list[PhoneNumber]:
    """Search phone numbers by number, extension, assigned_to, or description."""
    q = f"%{query}%"
    return (
        session.query(PhoneNumber)
        .filter(
            or_(
                PhoneNumber.number.ilike(q),
                PhoneNumber.extension.ilike(q),
                PhoneNumber.assigned_to.ilike(q),
                PhoneNumber.description.ilike(q),
                PhoneNumber.department.ilike(q),
                PhoneNumber.device_name.ilike(q),
            )
        )
        .order_by(PhoneNumber.number)
        .all()
    )
