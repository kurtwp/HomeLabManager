"""Ping-based network scan page."""

import subprocess
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.services.network_service import get_all_networks
from app.pages.layout import page_layout


def render_ping_scan():
    """Render the ping scan page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        ui.label("Ping Scan").classes("text-3xl font-bold")
        ui.label("Discover active hosts using ICMP ping. No root required.").classes(
            "text-gray-500 mb-4"
        )

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

            def ping_host(host_str: str) -> tuple[str, float | None]:
                try:
                    result = subprocess.run(
                        ["ping", "-c", "1", "-W", str(timeout_sec), host_str],
                        capture_output=True, text=True, timeout=timeout_sec + 2,
                    )
                    if result.returncode == 0:
                        # Extract latency
                        import re
                        match = re.search(r"time=([\d.]+)", result.stdout)
                        latency = float(match.group(1)) if match else None
                        return (host_str, latency)
                except (subprocess.TimeoutExpired, OSError):
                    pass
                return (host_str, None)

            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = {executor.submit(ping_host, ip): ip for ip in ip_list}
                for future in as_completed(futures):
                    ip, latency = future.result()
                    if latency is not None:
                        found_hosts.append({"ip": ip, "latency": latency})

            # Sort by IP
            found_hosts.sort(key=lambda x: ipaddress.ip_address(x["ip"]))

            results_container.clear()
            with results_container:
                ui.notify(
                    f"Scan complete: {len(found_hosts)}/{len(ip_list)} hosts responding",
                    type="positive",
                )

                with ui.card().classes("w-full"):
                    with ui.row().classes("items-center gap-4 mb-3"):
                        ui.badge(f"{len(found_hosts)} alive").props("color=green")
                        ui.badge(f"{len(ip_list) - len(found_hosts)} no response").props("color=red")
                        ui.label(f"Target: {target}").classes("text-sm text-gray-500")

                    if found_hosts:
                        columns = [
                            {"name": "ip", "label": "IP Address", "field": "ip", "align": "left"},
                            {"name": "latency", "label": "Latency (ms)", "field": "latency", "align": "right"},
                        ]
                        rows = [
                            {"ip": h["ip"], "latency": f"{h['latency']:.1f}"}
                            for h in found_hosts
                        ]
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
