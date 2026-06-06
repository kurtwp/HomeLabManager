"""Global search service across all entities."""

from sqlalchemy.orm import Session

from app.models.network import Network
from app.models.ip_address import IPAddress
from app.models.device import Device
from app.models.documentation import Documentation


def global_search(session: Session, query: str) -> dict:
    """
    Search across all entities (networks, IPs, devices, docs).
    Returns categorized results.
    """
    like_query = f"%{query}%"

    networks = (
        session.query(Network)
        .filter(
            (Network.name.ilike(like_query))
            | (Network.cidr.ilike(like_query))
            | (Network.description.ilike(like_query))
            | (Network.notes.ilike(like_query))
        )
        .limit(20)
        .all()
    )

    ips = (
        session.query(IPAddress)
        .filter(
            (IPAddress.address.ilike(like_query))
            | (IPAddress.hostname.ilike(like_query))
            | (IPAddress.notes.ilike(like_query))
        )
        .limit(20)
        .all()
    )

    devices = (
        session.query(Device)
        .filter(
            (Device.name.ilike(like_query))
            | (Device.manufacturer.ilike(like_query))
            | (Device.model.ilike(like_query))
            | (Device.serial_number.ilike(like_query))
            | (Device.mac_address.ilike(like_query))
            | (Device.notes.ilike(like_query))
        )
        .limit(20)
        .all()
    )

    docs = (
        session.query(Documentation)
        .filter(
            (Documentation.title.ilike(like_query))
            | (Documentation.body.ilike(like_query))
        )
        .limit(20)
        .all()
    )

    return {
        "networks": networks,
        "ip_addresses": ips,
        "devices": devices,
        "documentation": docs,
        "total": len(networks) + len(ips) + len(devices) + len(docs),
    }
