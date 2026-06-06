"""Dashboard page — overview of networks, devices, IPs."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.models.network import Network
from app.models.ip_address import IPAddress, IPStatus
from app.models.device import Device
from app.models.scan_log import ScanLog
from app.services.network_service import get_network_utilization
from app.services.ip_service import get_recently_modified_ips
from app.pages.layout import page_layout


def render_dashboard():
    """Render the main dashboard page."""
    page_layout()

    session = get_session()

    # Gather stats
    total_networks = session.query(Network).count()
    total_ips = session.query(IPAddress).count()
    active_ips = session.query(IPAddress).filter(IPAddress.status == IPStatus.ACTIVE).count()
    total_devices = session.query(Device).count()
    recent_scan = (
        session.query(ScanLog).order_by(ScanLog.started_at.desc()).first()
    )

    with ui.column().classes("page-container w-full"):
        ui.label("Dashboard").classes("text-3xl font-bold mb-4")

        # Stats cards
        with ui.row().classes("w-full gap-4 flex-wrap"):
            _stat_card("Networks", str(total_networks), "lan", "blue")
            _stat_card("IP Addresses", str(total_ips), "tag", "green")
            _stat_card("Active Hosts", str(active_ips), "wifi", "orange")
            _stat_card("Devices", str(total_devices), "devices", "purple")

        ui.separator().classes("my-4")

        with ui.row().classes("w-full gap-4 flex-wrap"):
            # Network utilization
            with ui.card().classes("flex-1 min-w-[400px]"):
                ui.label("Network Utilization").classes("text-lg font-semibold mb-2")
                networks = session.query(Network).all()
                if networks:
                    for net in networks[:8]:
                        util = get_network_utilization(session, net.id)
                        with ui.row().classes("items-center w-full gap-2"):
                            ui.label(f"{net.name} ({net.cidr})").classes("w-48 truncate")
                            ui.linear_progress(
                                value=util.get("utilization_percent", 0) / 100,
                                show_value=False,
                            ).classes("flex-1").props(
                                f'color={"red" if util.get("utilization_percent", 0) > 80 else "primary"}'
                            )
                            ui.label(
                                f'{util.get("used", 0)}/{util.get("total", 0)}'
                            ).classes("text-sm text-gray-500 w-16")
                else:
                    ui.label("No networks configured yet.").classes("text-gray-500")
                    ui.button(
                        "Add Network", on_click=lambda: ui.navigate.to("/networks")
                    ).props("flat color=primary")

            # Recently modified
            with ui.card().classes("flex-1 min-w-[400px]"):
                ui.label("Recently Modified").classes("text-lg font-semibold mb-2")
                recent_ips = get_recently_modified_ips(session, limit=8)
                if recent_ips:
                    for ip in recent_ips:
                        with ui.row().classes("items-center gap-2"):
                            status_color = {
                                IPStatus.ACTIVE: "green",
                                IPStatus.INACTIVE: "red",
                                IPStatus.UNKNOWN: "gray",
                            }.get(ip.status, "gray")
                            ui.icon("circle").classes(
                                f"text-xs text-{status_color}"
                            )
                            ui.link(
                                ip.address, f"/ips/{ip.id}"
                            ).classes("font-mono")
                            ui.label(ip.hostname or "").classes(
                                "text-sm text-gray-500"
                            )
                else:
                    ui.label("No IPs tracked yet.").classes("text-gray-500")

        # Last scan info
        if recent_scan:
            ui.separator().classes("my-4")
            with ui.card().classes("w-full"):
                ui.label("Last Network Scan").classes("text-lg font-semibold")
                with ui.row().classes("gap-4"):
                    ui.label(
                        f"Scanned at: {recent_scan.started_at.strftime('%Y-%m-%d %H:%M') if recent_scan.started_at else 'N/A'}"
                    )
                    ui.label(f"Hosts found: {recent_scan.hosts_found}")
                    ui.label(f"Added: {recent_scan.hosts_added}")
                    ui.label(f"Marked inactive: {recent_scan.hosts_removed}")

    session.close()


def _stat_card(title: str, value: str, icon: str, color: str):
    """Render a dashboard statistic card."""
    with ui.card().classes("flex-1 min-w-[200px]"):
        with ui.row().classes("items-center gap-3"):
            ui.icon(icon).classes(f"text-3xl text-{color}")
            with ui.column().classes("gap-0"):
                ui.label(value).classes("text-2xl font-bold")
                ui.label(title).classes("text-sm text-gray-500")
