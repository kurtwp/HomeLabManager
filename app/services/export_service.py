"""Import/Export service for CSV data."""

import csv
import io
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.ip_address import IPAddress, AssignmentType, IPStatus
from app.models.network import Network
from app.models.device import Device


def export_ips_csv(session: Session, network_id: int | None = None) -> str:
    """Export IP addresses to CSV string."""
    query = session.query(IPAddress)
    if network_id:
        query = query.filter(IPAddress.network_id == network_id)
    ips = query.order_by(IPAddress.address).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "address", "hostname", "mac_address", "assignment_type",
        "status", "network", "last_seen", "notes",
    ])
    for ip in ips:
        writer.writerow([
            ip.address,
            ip.hostname or "",
            ip.mac_address or "",
            ip.assignment_type.value,
            ip.status.value,
            ip.network.name if ip.network else "",
            ip.last_seen.isoformat() if ip.last_seen else "",
            ip.notes or "",
        ])
    return output.getvalue()


def export_devices_csv(session: Session) -> str:
    """Export devices to CSV string."""
    devices = session.query(Device).order_by(Device.name).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "name", "type", "manufacturer", "model",
        "serial_number", "mac_address", "notes",
    ])
    for d in devices:
        writer.writerow([
            d.name,
            d.device_type.name if d.device_type else "",
            d.manufacturer or "",
            d.model or "",
            d.serial_number or "",
            d.mac_address or "",
            d.notes or "",
        ])
    return output.getvalue()


def import_ips_csv(
    session: Session, csv_content: str, network_id: int
) -> dict:
    """
    Import IPs from CSV content into a given network.
    Expected columns: address, hostname, mac_address, assignment_type, notes
    Returns summary of operations.
    """
    reader = csv.DictReader(io.StringIO(csv_content))
    added = 0
    skipped = 0
    errors = []

    for row in reader:
        address = row.get("address", "").strip()
        if not address:
            skipped += 1
            continue

        # Check if already exists
        existing = session.query(IPAddress).filter(IPAddress.address == address).first()
        if existing:
            skipped += 1
            continue

        try:
            assignment = AssignmentType(row.get("assignment_type", "dhcp").lower())
        except ValueError:
            assignment = AssignmentType.DHCP

        try:
            ip = IPAddress(
                address=address,
                network_id=network_id,
                hostname=row.get("hostname", "").strip() or None,
                mac_address=row.get("mac_address", "").strip() or None,
                assignment_type=assignment,
                status=IPStatus.ACTIVE,
                notes=row.get("notes", "").strip() or None,
                last_seen=datetime.now(timezone.utc),
            )
            session.add(ip)
            added += 1
        except Exception as e:
            errors.append(f"{address}: {e}")

    session.commit()
    return {"added": added, "skipped": skipped, "errors": errors}
