"""Domain tracking service — monitor domain registration expiry dates."""

import subprocess
import re
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, Session

from app.database.db import Base, SessionLocal


class TrackedDomain(Base):
    """A domain being tracked for registration expiry."""

    __tablename__ = "tracked_domains"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    registrar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    creation_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    days_remaining: Mapped[int | None] = mapped_column(Integer, nullable=True)
    name_servers: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma-separated
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    alert_days: Mapped[int] = mapped_column(Integer, default=30)
    last_checked: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<TrackedDomain({self.domain} expires={self.expiry_date})>"


def whois_lookup(domain: str) -> dict:
    """
    Perform a WHOIS lookup on a domain.

    Returns:
        {"success": bool, "registrar": str, "creation_date": datetime,
         "expiry_date": datetime, "days_remaining": int, "name_servers": list, "error": str|None}
    """
    try:
        result = subprocess.run(
            ["whois", domain],
            capture_output=True, text=True, timeout=15,
        )

        if result.returncode != 0 and not result.stdout:
            return {"success": False, "error": f"WHOIS failed: {result.stderr[:200]}"}

        output = result.stdout

        # Parse expiry date — try multiple field names used by different registrars
        expiry_date = None
        expiry_patterns = [
            r"Registry Expiry Date:\s*(.+)",
            r"Registrar Registration Expiration Date:\s*(.+)",
            r"Expir(?:y|ation) Date:\s*(.+)",
            r"paid-till:\s*(.+)",
            r"Expiry date:\s*(.+)",
            r"renewal date:\s*(.+)",
            r"expire:\s*(.+)",
        ]
        for pattern in expiry_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                expiry_date = _parse_whois_date(match.group(1).strip())
                if expiry_date:
                    break

        # Parse creation date
        creation_date = None
        creation_patterns = [
            r"Creation Date:\s*(.+)",
            r"Created Date:\s*(.+)",
            r"Registration Date:\s*(.+)",
            r"created:\s*(.+)",
        ]
        for pattern in creation_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                creation_date = _parse_whois_date(match.group(1).strip())
                if creation_date:
                    break

        # Parse registrar
        registrar = None
        registrar_match = re.search(r"Registrar:\s*(.+)", output, re.IGNORECASE)
        if registrar_match:
            registrar = registrar_match.group(1).strip()

        # Parse name servers
        ns_matches = re.findall(r"Name Server:\s*(\S+)", output, re.IGNORECASE)
        name_servers = list(set(ns.lower() for ns in ns_matches)) if ns_matches else []

        if not expiry_date:
            return {"success": False, "error": "Could not parse expiry date from WHOIS response"}

        now = datetime.now(timezone.utc)
        days_remaining = (expiry_date - now).days

        return {
            "success": True,
            "registrar": registrar,
            "creation_date": creation_date,
            "expiry_date": expiry_date,
            "days_remaining": days_remaining,
            "name_servers": name_servers,
            "error": None,
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "WHOIS lookup timed out"}
    except FileNotFoundError:
        return {"success": False, "error": "whois command not found. Install with: sudo apt install whois"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_whois_date(date_str: str) -> datetime | None:
    """Parse various WHOIS date formats."""
    # Remove trailing comments or extra text
    date_str = date_str.split("#")[0].strip()
    date_str = date_str.split("(")[0].strip()

    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d-%b-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d.%m.%Y",
        "%Y.%m.%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


# --- CRUD ---

def add_domain(session: Session, domain: str, alert_days: int = 30,
               auto_renew: bool = False, notes: str | None = None) -> TrackedDomain:
    """Add a domain to track."""
    entry = TrackedDomain(
        domain=domain.strip().lower(),
        alert_days=alert_days,
        auto_renew=auto_renew,
        notes=notes,
    )
    session.add(entry)
    session.commit()
    return entry


def remove_domain(session: Session, domain_id: int) -> bool:
    """Remove a tracked domain."""
    entry = session.query(TrackedDomain).filter(TrackedDomain.id == domain_id).first()
    if entry:
        session.delete(entry)
        session.commit()
        return True
    return False


def get_all_domains(session: Session) -> list[TrackedDomain]:
    """Get all tracked domains."""
    return session.query(TrackedDomain).order_by(TrackedDomain.domain).all()


def refresh_domain(session: Session, domain_id: int) -> dict:
    """Check a single domain and update its record."""
    entry = session.query(TrackedDomain).filter(TrackedDomain.id == domain_id).first()
    if not entry:
        return {"success": False, "error": "Domain not found"}

    result = whois_lookup(entry.domain)
    now = datetime.now(timezone.utc)
    entry.last_checked = now

    if result["success"]:
        entry.registrar = result["registrar"]
        entry.creation_date = result["creation_date"]
        entry.expiry_date = result["expiry_date"]
        entry.days_remaining = result["days_remaining"]
        entry.name_servers = ", ".join(result["name_servers"]) if result["name_servers"] else None
        entry.last_error = None
    else:
        entry.last_error = result["error"]
        entry.days_remaining = None

    session.commit()
    return result


def refresh_all_domains() -> dict:
    """Check all tracked domains. Returns summary."""
    session = SessionLocal()
    try:
        domains = session.query(TrackedDomain).all()
        checked = 0
        expiring = 0
        expired = 0
        errors = 0
        newly_expiring = []

        for entry in domains:
            old_days = entry.days_remaining
            result = whois_lookup(entry.domain)
            now = datetime.now(timezone.utc)
            entry.last_checked = now

            if result["success"]:
                entry.registrar = result["registrar"]
                entry.creation_date = result["creation_date"]
                entry.expiry_date = result["expiry_date"]
                entry.days_remaining = result["days_remaining"]
                entry.name_servers = ", ".join(result["name_servers"]) if result["name_servers"] else None
                entry.last_error = None

                if result["days_remaining"] <= 0:
                    expired += 1
                elif result["days_remaining"] <= entry.alert_days:
                    expiring += 1
                    if old_days is None or old_days > entry.alert_days:
                        newly_expiring.append(entry)
            else:
                entry.last_error = result["error"]
                errors += 1

            checked += 1

        session.commit()

        # Send notifications for newly expiring domains
        if newly_expiring:
            try:
                from app.services.notification_service import send_notification, is_notifications_enabled
                if is_notifications_enabled():
                    for d in newly_expiring:
                        send_notification(
                            subject=f"⚠️ Domain expiring: {d.domain}",
                            message=(
                                f"Domain '{d.domain}' expires in {d.days_remaining} days.\n"
                                f"Expiry: {d.expiry_date.strftime('%Y-%m-%d') if d.expiry_date else '?'}\n"
                                f"Registrar: {d.registrar or '?'}\n"
                                f"Auto-renew: {'Yes' if d.auto_renew else 'No'}"
                            ),
                            priority="high" if d.days_remaining <= 7 else "normal",
                        )
            except Exception:
                pass

        return {"checked": checked, "expiring": expiring, "expired": expired, "errors": errors}

    except Exception:
        session.rollback()
        return {"checked": 0, "expiring": 0, "expired": 0, "errors": 1}
    finally:
        session.close()
