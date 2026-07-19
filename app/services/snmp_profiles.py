"""SNMP Profiles — save SNMP credentials for reuse across scans."""

from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, Session

from app.database.db import Base, SessionLocal


class SNMPProfile(Base):
    """Saved SNMP credential profile for reuse."""

    __tablename__ = "snmp_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(5), default="2c")  # 1, 2c, 3
    community: Mapped[str] = mapped_column(String(255), default="public")
    # SNMPv3 fields
    v3_user: Mapped[str | None] = mapped_column(String(255), nullable=True)
    v3_sec_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    v3_auth_proto: Mapped[str | None] = mapped_column(String(10), nullable=True)
    v3_auth_pass: Mapped[str | None] = mapped_column(String(255), nullable=True)
    v3_priv_proto: Mapped[str | None] = mapped_column(String(10), nullable=True)
    v3_priv_pass: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<SNMPProfile(name={self.name!r}, version={self.version})>"

    def to_kwargs(self) -> dict:
        """Convert profile to kwargs for SNMP functions."""
        return {
            "version": self.version,
            "community": self.community or "public",
            "v3_user": self.v3_user or "",
            "v3_sec_level": self.v3_sec_level or "authPriv",
            "v3_auth_proto": self.v3_auth_proto or "SHA",
            "v3_auth_pass": self.v3_auth_pass or "",
            "v3_priv_proto": self.v3_priv_proto or "AES",
            "v3_priv_pass": self.v3_priv_pass or "",
        }


def get_all_profiles(session: Session) -> list[SNMPProfile]:
    """Get all SNMP profiles."""
    return session.query(SNMPProfile).order_by(SNMPProfile.name).all()


def get_default_profile(session: Session) -> SNMPProfile | None:
    """Get the default SNMP profile."""
    return session.query(SNMPProfile).filter(SNMPProfile.is_default == True).first()


def create_profile(session: Session, name: str, version: str = "2c",
                   community: str = "public", is_default: bool = False,
                   **v3_kwargs) -> SNMPProfile:
    """Create a new SNMP profile."""
    if is_default:
        # Unset other defaults
        session.query(SNMPProfile).filter(SNMPProfile.is_default == True).update(
            {SNMPProfile.is_default: False}
        )
    profile = SNMPProfile(
        name=name, version=version, community=community,
        is_default=is_default,
        v3_user=v3_kwargs.get("v3_user"),
        v3_sec_level=v3_kwargs.get("v3_sec_level"),
        v3_auth_proto=v3_kwargs.get("v3_auth_proto"),
        v3_auth_pass=v3_kwargs.get("v3_auth_pass"),
        v3_priv_proto=v3_kwargs.get("v3_priv_proto"),
        v3_priv_pass=v3_kwargs.get("v3_priv_pass"),
    )
    session.add(profile)
    session.commit()
    return profile


def delete_profile(session: Session, profile_id: int) -> bool:
    """Delete an SNMP profile."""
    profile = session.query(SNMPProfile).filter(SNMPProfile.id == profile_id).first()
    if profile:
        session.delete(profile)
        session.commit()
        return True
    return False


# --- OID-based device type identification ---

# Common sysObjectID prefixes mapped to device types
DEVICE_TYPE_MAP = {
    "1.3.6.1.4.1.4413": "Router",         # Ubiquiti
    "1.3.6.1.4.1.41112": "Access Point",   # Ubiquiti UniFi
    "1.3.6.1.4.1.9": "Switch",            # Cisco
    "1.3.6.1.4.1.2636": "Router",          # Juniper
    "1.3.6.1.4.1.14988": "Router",         # MikroTik
    "1.3.6.1.4.1.11": "Switch",           # HP/Aruba
    "1.3.6.1.4.1.674": "Server",           # Dell
    "1.3.6.1.4.1.232": "Server",           # HP ProLiant
    "1.3.6.1.4.1.6876": "Server",          # VMware
    "1.3.6.1.4.1.8072": "Server",          # Net-SNMP (Linux)
    "1.3.6.1.4.1.2021": "Server",          # UCD-SNMP (Linux)
    "1.3.6.1.4.1.311": "Server",           # Microsoft
    "1.3.6.1.4.1.6574": "NAS",            # Synology
    "1.3.6.1.4.1.24681": "NAS",           # QNAP
}


def identify_device_type(sys_object_id: str) -> str | None:
    """Identify device type from sysObjectID."""
    if not sys_object_id:
        return None
    for prefix, device_type in DEVICE_TYPE_MAP.items():
        if sys_object_id.startswith(prefix) or sys_object_id.startswith(f".{prefix}"):
            return device_type
    return None


def identify_manufacturer(sys_object_id: str, sys_descr: str) -> str | None:
    """Try to identify manufacturer from SNMP data."""
    # Check sysObjectID
    manufacturer_map = {
        "1.3.6.1.4.1.4413": "Ubiquiti",
        "1.3.6.1.4.1.41112": "Ubiquiti",
        "1.3.6.1.4.1.9": "Cisco",
        "1.3.6.1.4.1.2636": "Juniper",
        "1.3.6.1.4.1.14988": "MikroTik",
        "1.3.6.1.4.1.11": "HP",
        "1.3.6.1.4.1.674": "Dell",
        "1.3.6.1.4.1.232": "HP",
        "1.3.6.1.4.1.6876": "VMware",
        "1.3.6.1.4.1.311": "Microsoft",
        "1.3.6.1.4.1.6574": "Synology",
        "1.3.6.1.4.1.24681": "QNAP",
    }
    if sys_object_id:
        for prefix, mfg in manufacturer_map.items():
            if sys_object_id.startswith(prefix) or sys_object_id.startswith(f".{prefix}"):
                return mfg

    # Fall back to sysDescr keywords
    descr_lower = (sys_descr or "").lower()
    keywords = {
        "cisco": "Cisco", "juniper": "Juniper", "mikrotik": "MikroTik",
        "ubiquiti": "Ubiquiti", "unifi": "Ubiquiti", "hp ": "HP",
        "aruba": "HP/Aruba", "dell": "Dell", "synology": "Synology",
        "qnap": "QNAP", "linux": "Linux", "windows": "Microsoft",
    }
    for kw, mfg in keywords.items():
        if kw in descr_lower:
            return mfg

    return None
