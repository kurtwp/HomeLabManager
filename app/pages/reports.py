"""Reporting and charts page."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.models.network import Network
from app.models.device import Device, DeviceType
from app.models.scan_log import ScanLog
from app.services.network_service import get_network_utilization
from app.pages.layout import page_layout


def render_reports():
    """Render the reports and charts page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        ui.label("Reports & Analytics").classes("text-3xl font-bold")
        ui.separator().classes("my-4")

        # --- Subnet Utilization Chart ---
        with ui.card().classes("w-full"):
            ui.label("Subnet Utilization").classes("text-xl font-semibold mb-2")

            networks = session.query(Network).order_by(Network.name).all()
            if networks:
                net_names = []
                used_data = []
                free_data = []
                warnings = []

                for net in networks:
                    util = get_network_utilization(session, net.id)
                    if util.get("total", 0) > 0:
                        net_names.append(f"{net.name} ({net.cidr})")
                        used_data.append(util.get("used", 0))
                        free_data.append(util.get("free", 0))
                        if util.get("utilization_percent", 0) >= 80:
                            warnings.append({
                                "name": net.name,
                                "cidr": net.cidr,
                                "percent": util["utilization_percent"],
                                "used": util["used"],
                                "total": util["total"],
                            })

                ui.echart({
                    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                    "legend": {"data": ["Used", "Free"]},
                    "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
                    "xAxis": {"type": "category", "data": net_names},
                    "yAxis": {"type": "value", "name": "IP Addresses"},
                    "series": [
                        {
                            "name": "Used",
                            "type": "bar",
                            "stack": "total",
                            "data": used_data,
                            "itemStyle": {"color": "#ef4444"},
                        },
                        {
                            "name": "Free",
                            "type": "bar",
                            "stack": "total",
                            "data": free_data,
                            "itemStyle": {"color": "#22c55e"},
                        },
                    ],
                }).classes("w-full h-80")
            else:
                ui.label("No networks configured yet.").classes("text-gray-500")

        # --- Capacity Warnings ---
        with ui.card().classes("w-full mt-4"):
            ui.label("Capacity Warnings (>80% Used)").classes("text-xl font-semibold mb-2")

            if networks:
                # Recompute warnings (already computed above)
                capacity_warnings = []
                for net in networks:
                    util = get_network_utilization(session, net.id)
                    if util.get("utilization_percent", 0) >= 80:
                        capacity_warnings.append({
                            "name": net.name,
                            "cidr": net.cidr,
                            "percent": util["utilization_percent"],
                            "used": util["used"],
                            "total": util["total"],
                        })

                if capacity_warnings:
                    for w in capacity_warnings:
                        with ui.row().classes("items-center gap-2 mb-2"):
                            ui.icon("warning").classes("text-orange text-xl")
                            ui.label(
                                f"{w['name']} ({w['cidr']}): {w['percent']}% used "
                                f"({w['used']}/{w['total']} IPs)"
                            ).classes("font-semibold")
                            color = "red" if w["percent"] >= 95 else "orange"
                            ui.linear_progress(
                                value=w["percent"] / 100, show_value=False
                            ).classes("w-48").props(f'color="{color}"')
                else:
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("check_circle").classes("text-green text-xl")
                        ui.label("All networks are below 80% capacity.").classes(
                            "text-green"
                        )
            else:
                ui.label("No networks configured yet.").classes("text-gray-500")

        # --- Device Type Distribution ---
        with ui.card().classes("w-full mt-4"):
            ui.label("Device Type Distribution").classes("text-xl font-semibold mb-2")

            device_types = session.query(DeviceType).all()
            if device_types:
                pie_data = []
                for dt in device_types:
                    count = session.query(Device).filter(Device.device_type_id == dt.id).count()
                    if count > 0:
                        pie_data.append({"name": dt.name, "value": count})

                # Also count devices with no type
                no_type_count = session.query(Device).filter(Device.device_type_id.is_(None)).count()
                if no_type_count > 0:
                    pie_data.append({"name": "Unclassified", "value": no_type_count})

                if pie_data:
                    ui.echart({
                        "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
                        "legend": {"orient": "vertical", "left": "left"},
                        "series": [
                            {
                                "name": "Device Types",
                                "type": "pie",
                                "radius": "60%",
                                "data": pie_data,
                                "emphasis": {
                                    "itemStyle": {
                                        "shadowBlur": 10,
                                        "shadowOffsetX": 0,
                                        "shadowColor": "rgba(0, 0, 0, 0.5)",
                                    }
                                },
                            }
                        ],
                    }).classes("w-full h-80")
                else:
                    ui.label("No devices with types assigned.").classes("text-gray-500")
            else:
                ui.label("No device types configured.").classes("text-gray-500")

        # --- Recent Scan Activity ---
        with ui.card().classes("w-full mt-4"):
            ui.label("Recent Scan Activity").classes("text-xl font-semibold mb-2")

            recent_scans = (
                session.query(ScanLog)
                .order_by(ScanLog.started_at.desc())
                .limit(10)
                .all()
            )

            if recent_scans:
                # Build a network_id -> name map
                net_map = {n.id: f"{n.name} ({n.cidr})" for n in networks}

                columns = [
                    {"name": "network", "label": "Network", "field": "network", "align": "left"},
                    {"name": "started", "label": "Started", "field": "started", "align": "left"},
                    {"name": "type", "label": "Scan Type", "field": "type", "align": "center"},
                    {"name": "found", "label": "Hosts Found", "field": "found", "align": "right"},
                    {"name": "added", "label": "Added", "field": "added", "align": "right"},
                    {"name": "duration", "label": "Duration", "field": "duration", "align": "right"},
                ]
                rows = []
                for scan in recent_scans:
                    duration = f"{scan.duration_seconds:.1f}s" if scan.duration_seconds else "—"

                    rows.append({
                        "network": net_map.get(scan.network_id, f"Network #{scan.network_id}"),
                        "started": scan.started_at.strftime("%Y-%m-%d %H:%M") if scan.started_at else "—",
                        "type": scan.scan_type,
                        "found": scan.hosts_found,
                        "added": scan.hosts_added,
                        "duration": duration,
                    })

                ui.table(columns=columns, rows=rows, row_key="started").classes(
                    "w-full"
                ).props("flat bordered dense")
            else:
                ui.label("No scans recorded yet.").classes("text-gray-500")

    session.close()
