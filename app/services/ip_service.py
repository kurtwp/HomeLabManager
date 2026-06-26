"""Service for IP address CRUD operations."""

import ipaddress as ipaddress_mod
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.ip_address import IPAddress, AssignmentType, IPStatus
from app.models.changelog import EntityType, ActionType
from app.services.changelog_service import log_change


def create_ip(
    session: Session,
    address: str,
    network_id: int,
    hostname: str | None = None,
    mac_address: str | None = None,
    assignment_type: AssignmentType = AssignmentType.DHCP,
    status: IPStatus = IPStatus.ACTIVE,
    device_id: int | None = None,
    notes: str | None = None,
) -> IPAddress:
    """Create a new IP address entry."""
    ip = IPAddress(
        address=address,
        network_id=network_id,
        hostname=hostname,
        mac_address=mac_address,
        assignment_type=assignment_type,
        status=status,
        device_id=device_id,
        notes=notes,
        last_seen=datetime.now(timezone.utc),
    )
    session.add(ip)
    session.flush()

    log_change(
        session,
        entity_type=EntityType.IP_ADDRESS,
        entity_id=ip.id,
        action=ActionType.CREATED,
        entity_name=address,
        new_values={
            "address": address,
            "hostname": hostname,
            "assignment_type": assignment_type.value,
        },
    )
    session.commit()
    return ip


def get_ips_for_network(session: Session, network_id: int) -> list[IPAddress]:
    """Get all IPs belonging to a network, sorted numerically."""
    ips = (
        session.query(IPAddress)
        .filter(IPAddress.network_id == network_id)
        .all()
    )
    ips.sort(key=lambda ip: ipaddress_mod.ip_address(ip.address))
    return ips


def get_ip_by_id(session: Session, ip_id: int) -> IPAddress | None:
    """Get a single IP by ID."""
    return session.query(IPAddress).filter(IPAddress.id == ip_id).first()


def get_ip_by_address(session: Session, address: str) -> IPAddress | None:
    """Find an IP entry by its address string."""
    return session.query(IPAddress).filter(IPAddress.address == address).first()


def update_ip(session: Session, ip_id: int, **kwargs) -> IPAddress | None:
    """Update an IP address entry."""
    ip = get_ip_by_id(session, ip_id)
    if not ip:
        return None

    old_values = {}
    new_values = {}
    for key, value in kwargs.items():
        if hasattr(ip, key):
            old_val = getattr(ip, key)
            # Convert enums for JSON serialization
            if hasattr(old_val, "value"):
                old_val = old_val.value
            old_values[key] = old_val
            setattr(ip, key, value)
            new_val = value
            if hasattr(new_val, "value"):
                new_val = new_val.value
            new_values[key] = new_val

    if new_values:
        log_change(
            session,
            entity_type=EntityType.IP_ADDRESS,
            entity_id=ip.id,
            action=ActionType.UPDATED,
            entity_name=ip.address,
            old_values=old_values,
            new_values=new_values,
        )
    session.commit()
    return ip


def delete_ip(session: Session, ip_id: int) -> bool:
    """Delete an IP entry, preserving changelog history."""
    ip = get_ip_by_id(session, ip_id)
    if not ip:
        return False

    log_change(
        session,
        entity_type=EntityType.IP_ADDRESS,
        entity_id=ip.id,
        action=ActionType.DELETED,
        entity_name=ip.address,
        old_values={
            "address": ip.address,
            "hostname": ip.hostname,
            "notes": ip.notes,
        },
    )
    session.delete(ip)
    session.commit()
    return True


def get_recently_modified_ips(session: Session, limit: int = 10) -> list[IPAddress]:
    """Get the most recently modified IP addresses."""
    return (
        session.query(IPAddress)
        .order_by(IPAddress.updated_at.desc())
        .limit(limit)
        .all()
    )


def search_ips(session: Session, query: str) -> list[IPAddress]:
    """Search IPs by address, hostname, or notes."""
    like_query = f"%{query}%"
    return (
        session.query(IPAddress)
        .filter(
            (IPAddress.address.ilike(like_query))
            | (IPAddress.hostname.ilike(like_query))
            | (IPAddress.notes.ilike(like_query))
        )
        .all()
    )
