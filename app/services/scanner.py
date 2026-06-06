"""Network scanning service using nmap for host discovery."""

import ipaddress
import socket
import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.ip_address import IPAddress, AssignmentType, IPStatus
from app.models.network import Network
from app.models.scan_log import ScanLog
from app.models.changelog import EntityType, ActionType
from app.services.changelog_service import log_change


def resolve_hostname(ip: str) -> str | None:
    """Attempt reverse DNS lookup for an IP address."""
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except (socket.herror, socket.gaierror, OSError):
        return None


def scan_network(session: Session, network_id: int) -> ScanLog:
    """
    Scan a network for active hosts using nmap ping scan.

    - Adds newly discovered IPs to the database
    - Marks missing IPs as inactive
    - Resolves hostnames via reverse DNS
    - Logs the scan event
    """
    network = session.query(Network).filter(Network.id == network_id).first()
    if not network:
        raise ValueError(f"Network with id {network_id} not found")

    scan_log = ScanLog(
        network_id=network_id,
        scan_type="ping",
        started_at=datetime.now(timezone.utc),
    )
    session.add(scan_log)

    start_time = time.time()
    discovered_hosts: set[str] = set()

    try:
        import nmap

        nm = nmap.PortScanner()
        nm.scan(hosts=network.cidr, arguments="-sn")  # Ping scan only

        for host in nm.all_hosts():
            if nm[host].state() == "up":
                discovered_hosts.add(host)

    except ImportError:
        # Fallback: basic ping using ipaddress iteration
        # This is slower but doesn't require nmap installed
        net = ipaddress.ip_network(network.cidr, strict=False)
        for host_ip in net.hosts():
            host_str = str(host_ip)
            try:
                import ping3

                response = ping3.ping(host_str, timeout=1)
                if response is not None:
                    discovered_hosts.add(host_str)
            except (OSError, PermissionError):
                pass

    # Get existing IPs for this network
    existing_ips = (
        session.query(IPAddress).filter(IPAddress.network_id == network_id).all()
    )
    existing_addresses = {ip.address for ip in existing_ips}

    hosts_added = 0
    hosts_removed = 0

    # Add newly discovered hosts
    for host_addr in discovered_hosts:
        if host_addr not in existing_addresses:
            hostname = resolve_hostname(host_addr)
            new_ip = IPAddress(
                address=host_addr,
                network_id=network_id,
                hostname=hostname,
                assignment_type=AssignmentType.DHCP,
                status=IPStatus.ACTIVE,
                last_seen=datetime.now(timezone.utc),
            )
            session.add(new_ip)
            session.flush()

            log_change(
                session,
                entity_type=EntityType.IP_ADDRESS,
                entity_id=new_ip.id,
                action=ActionType.CREATED,
                entity_name=host_addr,
                new_values={"address": host_addr, "hostname": hostname, "source": "scan"},
                comment="Auto-discovered during network scan",
            )
            hosts_added += 1
        else:
            # Update last_seen for existing IPs
            ip_entry = next(ip for ip in existing_ips if ip.address == host_addr)
            ip_entry.last_seen = datetime.now(timezone.utc)
            ip_entry.status = IPStatus.ACTIVE
            # Update hostname if it wasn't set
            if not ip_entry.hostname:
                ip_entry.hostname = resolve_hostname(host_addr)

    # Mark IPs not found as inactive
    for ip_entry in existing_ips:
        if ip_entry.address not in discovered_hosts:
            if ip_entry.status == IPStatus.ACTIVE:
                ip_entry.status = IPStatus.INACTIVE
                hosts_removed += 1

    # Update scan log
    end_time = time.time()
    scan_log.hosts_found = len(discovered_hosts)
    scan_log.hosts_added = hosts_added
    scan_log.hosts_removed = hosts_removed
    scan_log.duration_seconds = round(end_time - start_time, 2)
    scan_log.completed_at = datetime.now(timezone.utc)

    session.commit()
    return scan_log
