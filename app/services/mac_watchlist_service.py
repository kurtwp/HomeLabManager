"""MAC Watchlist service — track known MACs and flag unknown devices."""

from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, Session

from app.database.db import Base, SessionLocal
from app.models.ip_address import IPAddress, IPStatus


class KnownMAC(Base):
    """A MAC address that's been approved/recognized."""

    __tablename__ = "known_macs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mac_address: Mapped[str] = mapped_column(String(17), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<KnownMAC({self.mac_address} name={self.name!r})>"


def get_all_known_macs(session: Session) -> list[KnownMAC]:
    """Get all known/approved MAC addresses."""
    return session.query(KnownMAC).order_by(KnownMAC.name).all()


def add_known_mac(session: Session, mac_address: str, name: str, notes: str | None = None) -> KnownMAC:
    """Add a MAC to the known list."""
    normalized = mac_address.upper().replace("-", ":")
    existing = session.query(KnownMAC).filter(KnownMAC.mac_address == normalized).first()
    if existing:
        return existing
    entry = KnownMAC(mac_address=normalized, name=name, notes=notes)
    session.add(entry)
    session.commit()
    return entry


def remove_known_mac(session: Session, mac_id: int) -> bool:
    """Remove a MAC from the known list."""
    entry = session.query(KnownMAC).filter(KnownMAC.id == mac_id).first()
    if entry:
        session.delete(entry)
        session.commit()
        return True
    return False


def approve_all_current_macs(session: Session) -> int:
    """Add all currently active MACs to the known list (bulk approve)."""
    active_ips = (
        session.query(IPAddress)
        .filter(
            IPAddress.status == IPStatus.ACTIVE,
            IPAddress.mac_address.isnot(None),
            IPAddress.mac_address != "",
        )
        .all()
    )
    added = 0
    for ip in active_ips:
        normalized = ip.mac_address.upper().replace("-", ":")
        existing = session.query(KnownMAC).filter(KnownMAC.mac_address == normalized).first()
        if not existing:
            entry = KnownMAC(
                mac_address=normalized,
                name=ip.hostname or ip.address,
            )
            session.add(entry)
            added += 1
    session.commit()
    return added


def detect_unknown_macs(session: Session) -> list[dict]:
    """
    Find active MACs that are NOT in the known list.

    Returns:
        List of dicts: [{"mac": str, "address": str, "hostname": str, "network": str, "source": str}]
    """
    # Get all known MACs as a set
    known = {km.mac_address for km in session.query(KnownMAC).all()}

    # Get all active IPs with MACs
    active_ips = (
        session.query(IPAddress)
        .filter(
            IPAddress.status == IPStatus.ACTIVE,
            IPAddress.mac_address.isnot(None),
            IPAddress.mac_address != "",
        )
        .all()
    )

    unknown = []
    seen_macs = set()
    for ip in active_ips:
        normalized = ip.mac_address.upper().replace("-", ":")
        if normalized not in known and normalized not in seen_macs:
            seen_macs.add(normalized)
            unknown.append({
                "mac": normalized,
                "address": ip.address,
                "hostname": ip.hostname or "—",
                "network": ip.network.name if ip.network else "—",
                "source": ip.source or "—",
                "ip_id": ip.id,
            })

    return unknown
