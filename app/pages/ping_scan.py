"""Ping-based network scan page — discovers hosts and saves to DB."""

import subprocess
import socket
import ipaddress
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.models.ip_address import IPAddress, AssignmentType, IPStatus
from app.models.network import Network
from app.services.network_service import get_all_networks
from app.pages.layout import page_layout


def render_ping_scan():
    """Render the ping scan page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        ui.label("Ping Scan").classes("text-3xl font-bold")
        ui.label(
            "Discover active hosts using ICMP ping. Discovered IPs are automatically saved to the database."
        ).classes("text-gray-500 mb-4")

        ui.separator()

        with ui.card().classes("w-full mt-4"):
            ui.label("Scan Settings").classes("text-lg font-semibold mb-2")

            networks = get_all_networks(session)
            net_options = {n.cidr: f"{n.name} ({n.cidr})" for n in networks}

            with ui.row().classes("gap-4 items-end flex-wrap"):
                target_input = ui.input(
                    "Target (IP or CIDR)",
                    placeholder="192.168.2.0/24 or 192.168.2.1",
                ).classes("w-72")

                if net_options:
                    net_select = ui.select(
                        net_options, label="Or pick a network"
                    ).classes("w-64")
                    net_select.on(
                        "update:model-value",
                        lambda: setattr(target_input, 'value', net_select.value) if net_select.value else None,
                    )

                timeout_input = ui.number(
                    "Timeout (sec)", value=1, min=1, max=5
                ).classes("w-32")

        results_container = ui.column().classes("w-full mt-4")

        def run_ping_scan():
            target = target_input.value
            if not target:
                ui.notify("Enter a target", type="warning")
                return

            # Determine list of IPs to ping
            try:
                net = ipaddress.ip_network(target, strict=False)
                ip_list = [str(ip) for ip in net.hosts()]
            except ValueError:
                # Single IP
                ip_list = [target]

            if len(ip_list) > 254:
                ip_list = ip_list[:254]

            results_container.clear()
            with results_container:
                with ui.row().classes("items-center gap-3"):
                    ui.spinner(size="lg")
                    ui.label(
                        f"Pinging {len(ip_list)} hosts (timeout: {int(timeout_input.value)}s)..."
                    ).classes("text-sm text-gray-500")

            # Run pings in parallel
            timeout_sec = int(timeout_input.value or 1)
            found_hosts = []

            def ping_host(host_str: str) -> tuple[str, float | None, str | None]:
                """Ping a host and attempt reverse DNS."""
                latency = None
                hostname = None
                try:
                    import re
                    result = subprocess.run(
                        ["ping", "-c", "1", "-W", str(timeout_sec), host_str],
                        capture_output=True, text=True, timeout=timeout_sec + 2,
                    )
                    if result.returncode == 0:
                        match = re.search(r"time=([\d.]+)", result.stdout)
                        latency = float(match.group(1)) if match else 0.0
                        # Try reverse DNS
                        try:
                            hostname, _, _ = socket.gethostbyaddr(host_str)
                        except (socket.herror, socket.gaierror, OSError):
                            pass
                except (subprocess.TimeoutExpired, OSError):
                    pass
                return (host_str, latency, hostname)

            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = {executor.submit(ping_host, ip): ip for ip in ip_list}
                for future in as_completed(futures):
                    ip, latency, hostname = future.result()
                    if latency is not None:
                        found_hosts.append({"ip": ip, "latency": latency, "hostname": hostname})

            # Sort by IP numerically
            found_hosts.sort(key=lambda x: ipaddress.ip_address(x["ip"]))

            # --- Save to database ---
            added = 0
            updated = 0
            skipped = 0

            # Try to fetch DHCP ranges from UniFi for smart static/DHCP classification
            dhcp_ranges = []
            try:
                from app.services.unifi_service import fetch_networks_from_unifi, is_configured
                if is_configured():
                    unifi_nets = fetch_networks_from_unifi()
                    for unet in unifi_nets:
                        ipv4_config = unet.get("ipv4Configuration")
                        if isinstance(ipv4_config, dict):
                            dhcp_config = ipv4_config.get("dhcpConfiguration")
                            if isinstance(dhcp_config, dict):
                                ip_range = dhcp_config.get("ipAddressRange")
                                if isinstance(ip_range, dict) and ip_range.get("start") and ip_range.get("stop"):
                                    try:
                                        start = ipaddress.ip_address(ip_range["start"])
                                        stop = ipaddress.ip_address(ip_range["stop"])
                                        dhcp_ranges.append((start, stop))
                                    except ValueError:
                                        pass
            except Exception:
                pass

            def determine_assignment(ip_str: str) -> AssignmentType:
                """Determine if IP is static or DHCP based on DHCP ranges."""
                if dhcp_ranges:
                    try:
                        ip_obj = ipaddress.ip_address(ip_str)
                        for start, stop in dhcp_ranges:
                            if start <= ip_obj <= stop:
                                return AssignmentType.DHCP
                        return AssignmentType.STATIC
                    except ValueError:
                        pass
                return AssignmentType.DHCP  # Default if no DHCP info available

            for host in found_hosts:
                ip_addr = host["ip"]
                hostname = host["hostname"]

                # Find matching network
                target_network = None
                for net_obj in networks:
                    try:
                        if ipaddress.ip_address(ip_addr) in ipaddress.ip_network(net_obj.cidr, strict=False):
                            target_network = net_obj
                            break
                    except ValueError:
                        continue

                if not target_network:
                    skipped += 1
                    continue

                # Check if IP already exists (no duplicates)
                existing = session.query(IPAddress).filter(IPAddress.address == ip_addr).first()

                if existing:
                    # Update last_seen and status
                    existing.last_seen = datetime.now(timezone.utc)
                    existing.status = IPStatus.ACTIVE
                    if hostname and not existing.hostname:
                        existing.hostname = hostname
                    updated += 1
                else:
                    # Add new IP
                    new_ip = IPAddress(
                        address=ip_addr,
                        network_id=target_network.id,
                        hostname=hostname,
                        assignment_type=determine_assignment(ip_addr),
                        status=IPStatus.ACTIVE,
                        last_seen=datetime.now(timezone.utc),
                        source="ping_scan",
                    )
                    session.add(new_ip)
                    added += 1

            session.commit()

            # --- Display results ---
            results_container.clear()
            with results_container:
                ui.notify(
                    f"Scan complete: {len(found_hosts)} alive, {added} added, {updated} updated",
                    type="positive",
                )

                with ui.card().classes("w-full"):
                    with ui.row().classes("items-center gap-4 mb-3"):
                        ui.badge(f"{len(found_hosts)} alive").props("color=green")
                        ui.badge(f"{len(ip_list) - len(found_hosts)} no response").props("color=red")
                        if added:
                            ui.badge(f"{added} new IPs added").props("color=blue")
                        if updated:
                            ui.badge(f"{updated} updated").props("color=teal outline")
                        if skipped:
                            ui.badge(f"{skipped} skipped (no matching network)").props("color=orange outline")
                        ui.label(f"Target: {target}").classes("text-sm text-gray-500")

                    if found_hosts:
                        columns = [
                            {"name": "ip", "label": "IP Address", "field": "ip", "align": "left"},
                            {"name": "hostname", "label": "Hostname", "field": "hostname", "align": "left"},
                            {"name": "latency", "label": "Latency (ms)", "field": "latency", "align": "right"},
                            {"name": "status", "label": "DB Status", "field": "status", "align": "center"},
                        ]
                        rows = []
                        for h in found_hosts:
                            # Check what happened in DB
                            existing = session.query(IPAddress).filter(IPAddress.address == h["ip"]).first()
                            if existing:
                                db_status = "✅ Saved"
                            else:
                                db_status = "⚠️ No network"
                            rows.append({
                                "ip": h["ip"],
                                "hostname": h["hostname"] or "—",
                                "latency": f"{h['latency']:.1f}",
                                "status": db_status,
                            })
                        ui.table(
                            columns=columns, rows=rows, row_key="ip"
                        ).classes("w-full").props("flat bordered dense")
                    else:
                        ui.label("No hosts responded.").classes("text-gray-500")

        def clear_scan():
            target_input.value = ""
            results_container.clear()

        with ui.row().classes("gap-2 mt-3"):
            ui.button("Run Ping Scan", icon="wifi_find", on_click=run_ping_scan).props(
                "color=primary"
            )
            ui.button("Clear", icon="clear_all", on_click=clear_scan).props(
                "flat color=grey"
            )

    session.close()
