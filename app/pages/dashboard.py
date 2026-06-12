"""Dashboard page — overview of networks, devices, IPs with quick-add forms."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.models.network import Network
from app.models.ip_address import IPAddress, IPStatus, AssignmentType
from app.models.device import Device
from app.models.scan_log import ScanLog
from app.services.network_service import get_all_networks, get_network_utilization
from app.services.ip_service import get_recently_modified_ips, create_ip
from app.services.device_service import create_device, get_all_device_types
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

    # Source breakdown
    from sqlalchemy import func
    source_counts = dict(
        session.query(IPAddress.source, func.count())
        .filter(IPAddress.status == IPStatus.ACTIVE)
        .group_by(IPAddress.source)
        .all()
    )

    with ui.column().classes("page-container w-full"):
        ui.label("Dashboard").classes("text-3xl font-bold mb-4")

        # Stats cards
        with ui.row().classes("w-full gap-4 flex-wrap"):
            _stat_card("Networks", str(total_networks), "lan", "blue")
            _stat_card("IP Addresses", str(total_ips), "tag", "green")
            _stat_card("Active Hosts", str(active_ips), "wifi", "orange")
            _stat_card("Devices", str(total_devices), "devices", "purple")

        # Source breakdown
        if source_counts:
            with ui.row().classes("w-full gap-2 mt-2"):
                ui.label("Active by source:").classes("text-sm text-gray-500")
                source_labels = {
                    "unifi_client": ("UniFi Clients", "blue"),
                    "unifi_device": ("UniFi Infra", "purple"),
                    "nmap_scan": ("Nmap Scan", "green"),
                    "manual": ("Manual", "gray"),
                    None: ("Unknown", "gray"),
                }
                for source, count in sorted(source_counts.items(), key=lambda x: -(x[1])):
                    label, color = source_labels.get(source, (source or "Unknown", "gray"))
                    ui.badge(f"{label}: {count}").props(f"color={color} outline")

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
                            ui.link(
                                f"{net.name} ({net.cidr})", f"/networks/{net.id}"
                            ).classes("w-48 truncate")
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
                            # Show tags
                            for tag in ip.tags[:3]:
                                ui.html(
                                    f'<span style="font-size:0.6rem; padding:1px 6px; '
                                    f'border-radius:8px; background:{tag.color}20; '
                                    f'color:{tag.color}; border:1px solid {tag.color}40;">'
                                    f'{tag.name}</span>'
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

        # --- Quick-Add Section ---
        ui.separator().classes("my-4")
        ui.label("Quick Add").classes("text-xl font-semibold mb-2")

        with ui.row().classes("w-full gap-4 flex-wrap"):
            # Quick-add IP
            with ui.card().classes("flex-1 min-w-[350px]"):
                ui.label("Add IP Address").classes("text-md font-semibold mb-2")
                net_options = {n.id: f"{n.name} ({n.cidr})" for n in networks}

                qa_ip_addr = ui.input("IP Address", placeholder="192.168.1.100").classes("w-full")
                qa_ip_net = ui.select(net_options, label="Network").classes("w-full")
                qa_ip_host = ui.input("Hostname (optional)").classes("w-full")
                qa_ip_type = ui.select(
                    {t.value: t.value.upper() for t in AssignmentType},
                    value="static", label="Type"
                ).classes("w-full")

                def quick_add_ip():
                    if not qa_ip_addr.value or not qa_ip_net.value:
                        ui.notify("IP and network required", type="warning")
                        return
                    try:
                        create_ip(
                            session,
                            address=qa_ip_addr.value,
                            network_id=qa_ip_net.value,
                            hostname=qa_ip_host.value or None,
                            assignment_type=AssignmentType(qa_ip_type.value),
                        )
                        ui.notify(f"Added {qa_ip_addr.value}", type="positive")
                        qa_ip_addr.value = ""
                        qa_ip_host.value = ""
                    except Exception as e:
                        ui.notify(f"Error: {e}", type="negative")

                ui.button("Add IP", on_click=quick_add_ip).props("color=primary dense")

            # Quick-add Device
            with ui.card().classes("flex-1 min-w-[350px]"):
                ui.label("Add Device").classes("text-md font-semibold mb-2")
                device_types = get_all_device_types(session)
                dt_options = {dt.id: dt.name for dt in device_types}

                qa_dev_name = ui.input("Device Name", placeholder="My Server").classes("w-full")
                qa_dev_type = ui.select(dt_options, label="Type").classes("w-full")
                qa_dev_mac = ui.input("MAC Address (optional)", placeholder="AA:BB:CC:DD:EE:FF").classes("w-full")

                def quick_add_device():
                    if not qa_dev_name.value:
                        ui.notify("Name is required", type="warning")
                        return
                    try:
                        create_device(
                            session,
                            name=qa_dev_name.value,
                            device_type_id=qa_dev_type.value,
                            mac_address=qa_dev_mac.value or None,
                        )
                        ui.notify(f"Added {qa_dev_name.value}", type="positive")
                        qa_dev_name.value = ""
                        qa_dev_mac.value = ""
                    except Exception as e:
                        ui.notify(f"Error: {e}", type="negative")

                ui.button("Add Device", on_click=quick_add_device).props("color=primary dense")

    session.close()


def _stat_card(title: str, value: str, icon: str, color: str):
    """Render a dashboard statistic card."""
    with ui.card().classes("flex-1 min-w-[200px]"):
        with ui.row().classes("items-center gap-3"):
            ui.icon(icon).classes(f"text-3xl text-{color}")
            with ui.column().classes("gap-0"):
                ui.label(value).classes("text-2xl font-bold")
                ui.label(title).classes("text-sm text-gray-500")
