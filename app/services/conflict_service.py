"""IP/MAC conflict detection service — finds duplicate addresses."""

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.ip_address import IPAddress, IPStatus


def detect_ip_conflicts(session: Session) -> list[dict]:
    """
    Detect IP address conflicts — multiple active entries with the same IP.

    Returns:
        List of conflict dicts: [{"address": str, "count": int, "entries": list}]
    """
    # Find duplicate IP addresses (same address, both active)
    duplicates = (
        session.query(IPAddress.address, func.count(IPAddress.id).label("cnt"))
        .filter(IPAddress.status == IPStatus.ACTIVE)
        .group_by(IPAddress.address)
        .having(func.count(IPAddress.id) > 1)
        .all()
    )

    conflicts = []
    for address, count in duplicates:
        entries = (
            session.query(IPAddress)
            .filter(IPAddress.address == address, IPAddress.status == IPStatus.ACTIVE)
            .all()
        )
        conflicts.append({
            "type": "ip",
            "address": address,
            "count": count,
            "entries": [
                {
                    "id": e.id,
                    "hostname": e.hostname or "—",
                    "mac_address": e.mac_address or "—",
                    "network": e.network.name if e.network else "—",
                    "source": e.source or "—",
                    "last_seen": e.last_seen,
                }
                for e in entries
            ],
        })

    return conflicts


def detect_mac_conflicts(session: Session) -> list[dict]:
    """
    Detect MAC address conflicts — same MAC used by multiple active IPs.

    Returns:
        List of conflict dicts: [{"mac": str, "count": int, "entries": list}]
    """
    # Find duplicate MACs across active IPs (excluding None/empty)
    duplicates = (
        session.query(IPAddress.mac_address, func.count(IPAddress.id).label("cnt"))
        .filter(
            IPAddress.status == IPStatus.ACTIVE,
            IPAddress.mac_address.isnot(None),
            IPAddress.mac_address != "",
        )
        .group_by(IPAddress.mac_address)
        .having(func.count(IPAddress.id) > 1)
        .all()
    )

    conflicts = []
    for mac, count in duplicates:
        entries = (
            session.query(IPAddress)
            .filter(
                IPAddress.mac_address == mac,
                IPAddress.status == IPStatus.ACTIVE,
            )
            .all()
        )
        # A device with multiple IPs is normal — only flag if IPs are on the SAME network
        # or if assigned to different devices
        networks_seen = set()
        for e in entries:
            networks_seen.add(e.network_id)

        # Only report as conflict if same MAC on same network (true conflict)
        # or if the IPs are clearly different hosts
        if len(networks_seen) == 1 and count > 1:
            conflicts.append({
                "type": "mac",
                "mac_address": mac,
                "count": count,
                "entries": [
                    {
                        "id": e.id,
                        "address": e.address,
                        "hostname": e.hostname or "—",
                        "network": e.network.name if e.network else "—",
                        "source": e.source or "—",
                    }
                    for e in entries
                ],
            })

    return conflicts


def detect_all_conflicts(session: Session) -> dict:
    """
    Run all conflict detection checks.

    Returns:
        {"ip_conflicts": list, "mac_conflicts": list, "total": int}
    """
    ip_conflicts = detect_ip_conflicts(session)
    mac_conflicts = detect_mac_conflicts(session)

    return {
        "ip_conflicts": ip_conflicts,
        "mac_conflicts": mac_conflicts,
        "total": len(ip_conflicts) + len(mac_conflicts),
    }
