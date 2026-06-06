"""Service for network/VLAN CRUD operations."""

import ipaddress
from sqlalchemy.orm import Session

from app.models.network import Network
from app.models.changelog import EntityType, ActionType
from app.services.changelog_service import log_change


def create_network(
    session: Session,
    name: str,
    cidr: str,
    vlan_id: int | None = None,
    gateway: str | None = None,
    dns_servers: str | None = None,
    description: str | None = None,
    notes: str | None = None,
) -> Network:
    """Create a new network entry."""
    # Validate CIDR
    ipaddress.ip_network(cidr, strict=False)

    network = Network(
        name=name,
        cidr=cidr,
        vlan_id=vlan_id,
        gateway=gateway,
        dns_servers=dns_servers,
        description=description,
        notes=notes,
    )
    session.add(network)
    session.flush()

    log_change(
        session,
        entity_type=EntityType.NETWORK,
        entity_id=network.id,
        action=ActionType.CREATED,
        entity_name=name,
        new_values={"name": name, "cidr": cidr, "vlan_id": vlan_id},
    )
    session.commit()
    return network


def get_all_networks(session: Session) -> list[Network]:
    """Get all networks ordered by CIDR."""
    return session.query(Network).order_by(Network.name).all()


def get_network_by_id(session: Session, network_id: int) -> Network | None:
    """Get a single network by ID."""
    return session.query(Network).filter(Network.id == network_id).first()


def update_network(session: Session, network_id: int, **kwargs) -> Network | None:
    """Update a network's fields."""
    network = get_network_by_id(session, network_id)
    if not network:
        return None

    old_values = {}
    new_values = {}
    for key, value in kwargs.items():
        if hasattr(network, key):
            old_values[key] = getattr(network, key)
            setattr(network, key, value)
            new_values[key] = value

    if new_values:
        log_change(
            session,
            entity_type=EntityType.NETWORK,
            entity_id=network.id,
            action=ActionType.UPDATED,
            entity_name=network.name,
            old_values=old_values,
            new_values=new_values,
        )
    session.commit()
    return network


def delete_network(session: Session, network_id: int) -> bool:
    """Delete a network and log the change."""
    network = get_network_by_id(session, network_id)
    if not network:
        return False

    log_change(
        session,
        entity_type=EntityType.NETWORK,
        entity_id=network.id,
        action=ActionType.DELETED,
        entity_name=network.name,
        old_values={"name": network.name, "cidr": network.cidr},
    )
    session.delete(network)
    session.commit()
    return True


def get_network_utilization(session: Session, network_id: int) -> dict:
    """Calculate IP utilization for a network."""
    network = get_network_by_id(session, network_id)
    if not network:
        return {}

    net = ipaddress.ip_network(network.cidr, strict=False)
    total_hosts = net.num_addresses - 2  # Exclude network and broadcast
    if total_hosts < 0:
        total_hosts = net.num_addresses

    used = len(network.ip_addresses)
    free = total_hosts - used

    return {
        "total": total_hosts,
        "used": used,
        "free": free,
        "utilization_percent": round((used / total_hosts * 100), 1) if total_hosts > 0 else 0,
    }
