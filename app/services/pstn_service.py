"""Service layer for PSTN/Telephony module — CRUD and utilities."""

import json
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.pstn.number_range import NumberRange
from app.models.pstn.phone_number import PhoneNumber
from app.models.pstn.customer import Customer
from app.models.pstn.pstn_audit import PSTNAudit


# ─── Audit Logging ──────────────────────────────────────────────────────────────

def log_pstn_audit(session: Session, entity_type: str, entity_id: int, action: str, details: str | None = None):
    """Create an audit trail entry."""
    entry = PSTNAudit(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        details=details,
        timestamp=datetime.utcnow(),
    )
    session.add(entry)
    session.commit()
    return entry


def get_pstn_audit_log(session: Session, entity_type: str | None = None, limit: int = 50) -> list[PSTNAudit]:
    """Retrieve audit log entries, optionally filtered by entity type."""
    query = session.query(PSTNAudit).order_by(PSTNAudit.timestamp.desc())
    if entity_type:
        query = query.filter(PSTNAudit.entity_type == entity_type)
    return query.limit(limit).all()


# ─── Customer CRUD ──────────────────────────────────────────────────────────────

def create_customer(session: Session, **kwargs) -> Customer:
    """Create a new customer."""
    c = Customer(**kwargs)
    session.add(c)
    session.commit()
    session.refresh(c)
    log_pstn_audit(session, "customer", c.id, "created", json.dumps({"name": c.name}))
    return c


def get_all_customers(session: Session) -> list[Customer]:
    """Get all customers ordered by name."""
    return session.query(Customer).order_by(Customer.name).all()


def get_customer_by_id(session: Session, customer_id: int) -> Customer | None:
    """Get a single customer by ID."""
    return session.query(Customer).filter(Customer.id == customer_id).first()


def update_customer(session: Session, customer_id: int, **kwargs) -> Customer | None:
    """Update a customer."""
    c = get_customer_by_id(session, customer_id)
    if not c:
        return None
    changes = {}
    for key, value in kwargs.items():
        if hasattr(c, key):
            old_val = getattr(c, key)
            if old_val != value:
                changes[key] = {"old": old_val, "new": value}
            setattr(c, key, value)
    c.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(c)
    if changes:
        log_pstn_audit(session, "customer", c.id, "updated", json.dumps(changes, default=str))
    return c


def delete_customer(session: Session, customer_id: int) -> bool:
    """Delete a customer. Returns True if deleted."""
    c = get_customer_by_id(session, customer_id)
    if not c:
        return False
    name = c.name
    session.delete(c)
    session.commit()
    log_pstn_audit(session, "customer", customer_id, "deleted", json.dumps({"name": name}))
    return True


# ─── Number Range CRUD ──────────────────────────────────────────────────────────

def create_range(session: Session, **kwargs) -> NumberRange:
    """Create a new number range."""
    nr = NumberRange(**kwargs)
    session.add(nr)
    session.commit()
    session.refresh(nr)
    log_pstn_audit(session, "range", nr.id, "created", json.dumps({"name": nr.name, "range": f"{nr.range_start}-{nr.range_end}"}))
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
    changes = {}
    for key, value in kwargs.items():
        if hasattr(nr, key):
            old_val = getattr(nr, key)
            if old_val != value:
                changes[key] = {"old": old_val, "new": value}
            setattr(nr, key, value)
    nr.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(nr)
    if changes:
        log_pstn_audit(session, "range", nr.id, "updated", json.dumps(changes, default=str))
    return nr


def delete_range(session: Session, range_id: int) -> bool:
    """Delete a number range. Returns True if deleted."""
    nr = get_range_by_id(session, range_id)
    if not nr:
        return False
    name = nr.name
    session.delete(nr)
    session.commit()
    log_pstn_audit(session, "range", range_id, "deleted", json.dumps({"name": name}))
    return True


# ─── Phone Number CRUD ──────────────────────────────────────────────────────────

def create_phone_number(session: Session, **kwargs) -> PhoneNumber:
    """Create a new phone number."""
    pn = PhoneNumber(**kwargs)
    session.add(pn)
    session.commit()
    session.refresh(pn)
    log_pstn_audit(session, "number", pn.id, "created", json.dumps({"number": pn.number}))
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
    changes = {}
    for key, value in kwargs.items():
        if hasattr(pn, key):
            old_val = getattr(pn, key)
            if old_val != value:
                changes[key] = {"old": old_val, "new": value}
            setattr(pn, key, value)
    pn.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(pn)
    if changes:
        log_pstn_audit(session, "number", pn.id, "updated", json.dumps(changes, default=str))
    return pn


def delete_phone_number(session: Session, phone_id: int) -> bool:
    """Delete a phone number. Returns True if deleted."""
    pn = get_phone_number_by_id(session, phone_id)
    if not pn:
        return False
    number = pn.number
    session.delete(pn)
    session.commit()
    log_pstn_audit(session, "number", phone_id, "deleted", json.dumps({"number": number}))
    return True


def get_numbers_by_range(session: Session, range_id: int) -> list[PhoneNumber]:
    """Get all phone numbers belonging to a specific range."""
    return (
        session.query(PhoneNumber)
        .filter(PhoneNumber.range_id == range_id)
        .order_by(PhoneNumber.number)
        .all()
    )


def get_numbers_by_customer(session: Session, customer_id: int) -> list[PhoneNumber]:
    """Get all phone numbers belonging to a specific customer."""
    return (
        session.query(PhoneNumber)
        .filter(PhoneNumber.customer_id == customer_id)
        .order_by(PhoneNumber.number)
        .all()
    )


def get_ranges_by_customer(session: Session, customer_id: int) -> list[NumberRange]:
    """Get all number ranges belonging to a specific customer."""
    return (
        session.query(NumberRange)
        .filter(NumberRange.customer_id == customer_id)
        .order_by(NumberRange.name)
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
