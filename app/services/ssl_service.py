"""SSL Certificate tracking service — checks cert expiry on HTTPS services."""

import subprocess
import re
from datetime import datetime, timezone, timedelta

from sqlalchemy import String, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, Session

from app.database.db import Base, SessionLocal


class SSLCertificate(Base):
    """Tracked SSL certificate for a host:port."""

    __tablename__ = "ssl_certificates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, default=443)
    issuer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    not_before: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    not_after: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    days_remaining: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    last_checked: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    alert_days: Mapped[int] = mapped_column(Integer, default=30)  # Alert when fewer days remain
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<SSLCertificate({self.name} {self.host}:{self.port} expires={self.not_after})>"


def check_certificate(host: str, port: int = 443, timeout: int = 5) -> dict:
    """
    Connect to a host and retrieve SSL certificate info.
    Uses openssl s_client which handles more edge cases than Python's ssl module.

    Returns:
        {"success": bool, "issuer": str, "subject": str, "not_before": datetime,
         "not_after": datetime, "days_remaining": int, "error": str|None}
    """
    import subprocess

    try:
        # Use openssl s_client to fetch the cert — handles more TLS quirks
        cmd = [
            "openssl", "s_client",
            "-connect", f"{host}:{port}",
            "-servername", host,
            "-showcerts",
        ]
        result = subprocess.run(
            cmd,
            input="",  # Send empty input to close connection
            capture_output=True, text=True, timeout=timeout + 5,
        )

        # Extract the first certificate from output
        cert_pem = ""
        in_cert = False
        for line in result.stdout.split("\n"):
            if "-----BEGIN CERTIFICATE-----" in line:
                in_cert = True
                cert_pem = line + "\n"
            elif "-----END CERTIFICATE-----" in line:
                cert_pem += line + "\n"
                break
            elif in_cert:
                cert_pem += line + "\n"

        if not cert_pem:
            # Try without -servername (some devices don't support SNI)
            cmd_no_sni = [
                "openssl", "s_client",
                "-connect", f"{host}:{port}",
                "-showcerts",
            ]
            result = subprocess.run(
                cmd_no_sni,
                input="",
                capture_output=True, text=True, timeout=timeout + 5,
            )
            for line in result.stdout.split("\n"):
                if "-----BEGIN CERTIFICATE-----" in line:
                    in_cert = True
                    cert_pem = line + "\n"
                elif "-----END CERTIFICATE-----" in line:
                    cert_pem += line + "\n"
                    break
                elif in_cert:
                    cert_pem += line + "\n"

        if not cert_pem:
            # Provide a clear error message
            if "unexpected eof" in (result.stderr or "").lower():
                return {"success": False, "error": f"Server has no SSL certificate installed ({host}:{port}). The server accepts connections but does not present a TLS certificate."}
            elif "connection refused" in (result.stderr or "").lower():
                return {"success": False, "error": f"Connection refused ({host}:{port})"}
            elif "timed out" in (result.stderr or "").lower() or "no route" in (result.stderr or "").lower():
                return {"success": False, "error": f"Cannot reach {host}:{port} (timeout or no route)"}
            else:
                stderr_snippet = result.stderr[:150] if result.stderr else "No certificate received"
                return {"success": False, "error": f"No SSL certificate found on {host}:{port} — {stderr_snippet}"}

        # Parse the certificate with openssl x509
        parse_result = subprocess.run(
            ["openssl", "x509", "-noout", "-dates", "-subject", "-issuer"],
            input=cert_pem, capture_output=True, text=True, timeout=5,
        )

        if parse_result.returncode != 0:
            return {"success": False, "error": f"Certificate parse error: {parse_result.stderr[:200]}"}

        # Parse output
        not_before = None
        not_after = None
        subject = ""
        issuer = ""

        for line in parse_result.stdout.strip().split("\n"):
            if line.startswith("notBefore="):
                date_str = line.split("=", 1)[1]
                not_before = _parse_openssl_date(date_str)
            elif line.startswith("notAfter="):
                date_str = line.split("=", 1)[1]
                not_after = _parse_openssl_date(date_str)
            elif line.startswith("subject="):
                subject = line.split("=", 1)[1].strip()
            elif line.startswith("issuer="):
                issuer = line.split("=", 1)[1].strip()

        if not not_after:
            return {"success": False, "error": "Could not parse certificate expiry date"}

        now = datetime.now(timezone.utc)
        days_remaining = (not_after - now).days

        return {
            "success": True,
            "issuer": issuer,
            "subject": subject,
            "not_before": not_before,
            "not_after": not_after,
            "days_remaining": days_remaining,
            "error": None,
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Connection timed out ({host}:{port})"}
    except FileNotFoundError:
        return {"success": False, "error": "openssl not found. Install with: sudo apt install openssl"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_openssl_date(date_str: str) -> datetime | None:
    """Parse openssl date format: 'Jul 18 12:00:00 2026 GMT'"""
    formats = [
        "%b %d %H:%M:%S %Y %Z",
        "%b  %d %H:%M:%S %Y %Z",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def add_certificate(session: Session, name: str, host: str, port: int = 443,
                    alert_days: int = 30) -> SSLCertificate:
    """Add a new SSL certificate to track."""
    cert = SSLCertificate(
        name=name,
        host=host,
        port=port,
        alert_days=alert_days,
    )
    session.add(cert)
    session.commit()
    return cert


def remove_certificate(session: Session, cert_id: int) -> bool:
    """Remove a tracked certificate."""
    cert = session.query(SSLCertificate).filter(SSLCertificate.id == cert_id).first()
    if cert:
        session.delete(cert)
        session.commit()
        return True
    return False


def get_all_certificates(session: Session) -> list[SSLCertificate]:
    """Get all tracked certificates."""
    return session.query(SSLCertificate).order_by(SSLCertificate.name).all()


def refresh_certificate(session: Session, cert_id: int) -> dict:
    """Check a single certificate and update its record."""
    cert = session.query(SSLCertificate).filter(SSLCertificate.id == cert_id).first()
    if not cert:
        return {"success": False, "error": "Certificate not found"}

    result = check_certificate(cert.host, cert.port)
    now = datetime.now(timezone.utc)

    cert.last_checked = now

    if result["success"]:
        cert.issuer = result["issuer"]
        cert.subject = result["subject"]
        cert.not_before = result["not_before"]
        cert.not_after = result["not_after"]
        cert.days_remaining = result["days_remaining"]
        cert.is_valid = result["days_remaining"] > 0
        cert.last_error = None
    else:
        cert.last_error = result["error"]
        cert.is_valid = False
        cert.days_remaining = None

    session.commit()
    return result


def refresh_all_certificates() -> dict:
    """Check all tracked certificates. Returns summary."""
    session = SessionLocal()
    try:
        certs = session.query(SSLCertificate).all()
        checked = 0
        expiring = 0
        expired = 0
        errors = 0
        newly_expiring = []

        for cert in certs:
            old_days = cert.days_remaining
            result = check_certificate(cert.host, cert.port)
            now = datetime.now(timezone.utc)
            cert.last_checked = now

            if result["success"]:
                cert.issuer = result["issuer"]
                cert.subject = result["subject"]
                cert.not_before = result["not_before"]
                cert.not_after = result["not_after"]
                cert.days_remaining = result["days_remaining"]
                cert.is_valid = result["days_remaining"] > 0
                cert.last_error = None

                if result["days_remaining"] <= 0:
                    expired += 1
                elif result["days_remaining"] <= cert.alert_days:
                    expiring += 1
                    # Notify if newly entering the warning zone
                    if old_days is None or old_days > cert.alert_days:
                        newly_expiring.append(cert)
            else:
                cert.last_error = result["error"]
                cert.is_valid = False
                errors += 1

            checked += 1

        session.commit()

        # Send notifications for newly expiring certs
        if newly_expiring:
            try:
                from app.services.notification_service import send_notification, is_notifications_enabled
                if is_notifications_enabled():
                    for c in newly_expiring:
                        send_notification(
                            subject=f"⚠️ SSL cert expiring: {c.name}",
                            message=(
                                f"Certificate for {c.host}:{c.port} expires in {c.days_remaining} days.\n"
                                f"Expiry: {c.not_after.strftime('%Y-%m-%d') if c.not_after else '?'}\n"
                                f"Subject: {c.subject or '?'}\n"
                                f"Issuer: {c.issuer or '?'}"
                            ),
                            priority="high" if c.days_remaining <= 7 else "normal",
                        )
            except Exception:
                pass

        return {"checked": checked, "expiring": expiring, "expired": expired, "errors": errors}

    except Exception as e:
        session.rollback()
        return {"checked": 0, "expiring": 0, "expired": 0, "errors": 1}
    finally:
        session.close()
