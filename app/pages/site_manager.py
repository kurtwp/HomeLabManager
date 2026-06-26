"""UniFi Site Manager page — cloud API for cross-site overview."""

from nicegui import ui

from app.services.site_manager_service import (
    is_configured,
    test_connection,
    fetch_hosts,
    fetch_sites,
    fetch_devices,
    fetch_isp_metrics,
)
from app.pages.layout import page_layout


def render_site_manager():
    """Render the Site Manager page."""
    page_layout()

    with ui.column().classes("page-container w-full"):
        ui.label("UniFi Site Manager").classes("text-3xl font-bold")
        ui.label(
            "Cloud API — cross-site overview of all your UniFi deployments."
        ).classes("text-gray-500 mb-4")

        ui.separator()

        # Connection status
        with ui.card().classes("w-full mt-4"):
            ui.label("Connection").classes("text-lg font-semibold mb-2")

            if not is_configured():
                ui.label(
                    "⚠️ Site Manager API not configured."
                ).classes("text-orange")
                ui.label(
                    "Set UNIFI_CLOUD_API_KEY in your .env file. "
                    "Get it from unifi.ui.com → Settings → API Keys."
                ).classes("text-sm text-gray-500")
                return

            status_label = ui.label("").classes("mt-2")

            def check_connection():
                status_label.text = "Testing..."
                result = test_connection()
                if result["success"]:
                    status_label.text = f"✅ Connected — {result['hosts']} host(s) found"
                    status_label.classes(remove="text-red", add="text-green")
                else:
                    status_label.text = f"❌ {result['error']}"
                    status_label.classes(remove="text-green", add="text-red")

            ui.button("Test Connection", icon="cloud", on_click=check_connection).props(
                "color=primary outline"
            )

        ui.separator().classes("my-4")

        with ui.tabs().classes("w-full") as tabs:
            hosts_tab = ui.tab("Hosts")
            sites_tab = ui.tab("Sites")
            devices_tab = ui.tab("Devices")
            isp_tab = ui.tab("ISP Metrics")

        with ui.tab_panels(tabs, value=hosts_tab).classes("w-full"):
            # --- Hosts ---
            with ui.tab_panel(hosts_tab):
                hosts_container = ui.column().classes("w-full")

                def load_hosts():
                    hosts_container.clear()
                    with hosts_container:
                        with ui.row().classes("items-center gap-3"):
                            ui.spinner(size="lg")
                            ui.label("Loading hosts...").classes("text-sm text-gray-500")

                    try:
                        hosts = fetch_hosts()
                    except Exception as e:
                        hosts_container.clear()
                        with hosts_container:
                            ui.label(f"❌ Error: {e}").classes("text-red")
                        return

                    hosts_container.clear()
                    with hosts_container:
                        if not hosts:
                            ui.label("No hosts found.").classes("text-gray-500")
                            return

                        ui.label(f"{len(hosts)} host(s)").classes("text-sm text-gray-400 mb-2")

                        for host in hosts:
                            with ui.card().classes("w-full"):
                                with ui.row().classes("items-center gap-3"):
                                    ui.icon("dns").classes("text-2xl text-primary")
                                    with ui.column().classes("gap-0"):
                                        ui.label(
                                            host.get("reportedState", {}).get("hostname")
                                            or host.get("name")
                                            or host.get("id", "Unknown")
                                        ).classes("text-lg font-semibold")
                                        ui.label(f"ID: {host.get('id', '—')}").classes(
                                            "text-xs font-mono text-gray-500"
                                        )
                                # Show available fields
                                state = host.get("reportedState", {})
                                if state:
                                    details = []
                                    if state.get("firmwareVersion"):
                                        details.append(f"Firmware: {state['firmwareVersion']}")
                                    if state.get("ipAddress"):
                                        details.append(f"IP: {state['ipAddress']}")
                                    if state.get("isSetup") is not None:
                                        details.append(f"Setup: {'Yes' if state['isSetup'] else 'No'}")
                                    if details:
                                        ui.label(" · ".join(details)).classes("text-sm text-gray-500")

                ui.button("Load Hosts", icon="refresh", on_click=load_hosts).props(
                    "color=primary"
                ).classes("mt-2")

            # --- Sites ---
            with ui.tab_panel(sites_tab):
                sites_container = ui.column().classes("w-full")

                def load_sites():
                    sites_container.clear()
                    with sites_container:
                        with ui.row().classes("items-center gap-3"):
                            ui.spinner(size="lg")
                            ui.label("Loading sites...").classes("text-sm text-gray-500")

                    try:
                        sites = fetch_sites()
                    except Exception as e:
                        sites_container.clear()
                        with sites_container:
                            ui.label(f"❌ Error: {e}").classes("text-red")
                        return

                    sites_container.clear()
                    with sites_container:
                        if not sites:
                            ui.label("No sites found.").classes("text-gray-500")
                            return

                        ui.label(f"{len(sites)} site(s)").classes("text-sm text-gray-400 mb-2")

                        columns = [
                            {"name": "name", "label": "Site Name", "field": "name", "align": "left"},
                            {"name": "id", "label": "Site ID", "field": "id", "align": "left"},
                            {"name": "host", "label": "Host", "field": "host", "align": "left"},
                            {"name": "devices", "label": "Devices", "field": "devices", "align": "center"},
                        ]
                        rows = []
                        for site in sites:
                            rows.append({
                                "name": site.get("name") or site.get("meta", {}).get("name", "—"),
                                "id": site.get("siteId") or site.get("id", "—"),
                                "host": site.get("hostId") or site.get("host", {}).get("hostname", "—"),
                                "devices": site.get("deviceCount") or site.get("statistics", {}).get("totalDeviceCount", "—"),
                            })

                        ui.table(columns=columns, rows=rows, row_key="id").classes(
                            "w-full"
                        ).props("flat bordered dense")

                ui.button("Load Sites", icon="refresh", on_click=load_sites).props(
                    "color=primary"
                ).classes("mt-2")

            # --- Devices ---
            with ui.tab_panel(devices_tab):
                devices_container = ui.column().classes("w-full")

                def load_devices():
                    devices_container.clear()
                    with devices_container:
                        with ui.row().classes("items-center gap-3"):
                            ui.spinner(size="lg")
                            ui.label("Loading devices...").classes("text-sm text-gray-500")

                    try:
                        current_devices, old_devices = fetch_devices()
                    except Exception as e:
                        devices_container.clear()
                        with devices_container:
                            ui.label(f"❌ Error: {e}").classes("text-red")
                        return

                    devices_container.clear()
                    with devices_container:
                        if not current_devices and not old_devices:
                            ui.label("No devices found.").classes("text-gray-500")
                            return

                        columns = [
                            {"name": "name", "label": "Name", "field": "name", "align": "left"},
                            {"name": "model", "label": "Model", "field": "model", "align": "left"},
                            {"name": "mac", "label": "MAC", "field": "mac", "align": "left"},
                            {"name": "ip", "label": "IP", "field": "ip", "align": "left"},
                            {"name": "state", "label": "State", "field": "state", "align": "center"},
                            {"name": "firmware", "label": "Firmware", "field": "firmware", "align": "left"},
                            {"name": "host", "label": "Host", "field": "host", "align": "left"},
                        ]

                        def _build_rows(device_list):
                            return [
                                {
                                    "name": dev.get("name") or "—",
                                    "model": dev.get("model") or dev.get("shortname") or "—",
                                    "mac": dev.get("mac") or "—",
                                    "ip": dev.get("ip") or "—",
                                    "state": dev.get("status") or dev.get("state") or "—",
                                    "firmware": dev.get("version") or "—",
                                    "host": dev.get("_hostName") or "—",
                                }
                                for dev in device_list
                            ]

                        # Current devices table
                        ui.label(f"Current Devices ({len(current_devices)})").classes(
                            "text-lg font-semibold mb-2"
                        )
                        ui.table(
                            columns=columns, rows=_build_rows(current_devices), row_key="mac"
                        ).classes("w-full").props("flat bordered dense")

                        # Old/previous locations table
                        if old_devices:
                            ui.separator().classes("my-4")
                            ui.label(f"Previous Locations ({len(old_devices)})").classes(
                                "text-lg font-semibold mb-2 text-gray-400"
                            )
                            ui.label(
                                "Devices that were previously managed by a different host or have stale entries."
                            ).classes("text-xs text-gray-500 mb-2")
                            ui.table(
                                columns=columns, rows=_build_rows(old_devices), row_key="mac"
                            ).classes("w-full opacity-70").props("flat bordered dense")

                ui.button("Load Devices", icon="refresh", on_click=load_devices).props(
                    "color=primary"
                ).classes("mt-2")

            # --- ISP Metrics ---
            with ui.tab_panel(isp_tab):
                isp_container = ui.column().classes("w-full")

                def load_isp_metrics():
                    isp_container.clear()
                    with isp_container:
                        with ui.row().classes("items-center gap-3"):
                            ui.spinner(size="lg")
                            ui.label("Loading ISP metrics...").classes("text-sm text-gray-500")

                    try:
                        metrics = fetch_isp_metrics()
                    except Exception as e:
                        isp_container.clear()
                        with isp_container:
                            ui.label(f"❌ Error: {e}").classes("text-red")
                        return

                    isp_container.clear()
                    with isp_container:
                        if not metrics:
                            ui.label("No ISP metrics available.").classes("text-gray-500")
                            return

                        # Check if the response is an error message
                        if isinstance(metrics, dict) and "error" in metrics:
                            with ui.card().classes("w-full"):
                                with ui.row().classes("items-center gap-2"):
                                    ui.icon("info").classes("text-orange text-2xl")
                                    ui.label("ISP Metrics Unavailable").classes("text-lg font-semibold")
                                ui.label(metrics["error"]).classes("text-sm text-gray-500 mt-2")
                                ui.label(
                                    "To enable: sign in at unifi.ui.com → Settings → "
                                    "enable Early Access, then try again."
                                ).classes("text-xs text-gray-400 mt-1")
                            return

                        # Display as formatted JSON or key-value pairs
                        data_list = metrics if isinstance(metrics, list) else metrics.get("data", [metrics])

                        for entry in data_list:
                            with ui.card().classes("w-full"):
                                site_name = (
                                    entry.get("siteName")
                                    or entry.get("site", {}).get("name", "")
                                    or "Site"
                                )
                                ui.label(site_name).classes("text-lg font-semibold")

                                # Common ISP metric fields
                                metric_fields = [
                                    ("ISP", entry.get("isp") or entry.get("ispName")),
                                    ("Download (Mbps)", entry.get("download") or entry.get("rxRate")),
                                    ("Upload (Mbps)", entry.get("upload") or entry.get("txRate")),
                                    ("Latency (ms)", entry.get("latency") or entry.get("avgLatency")),
                                    ("Uptime (%)", entry.get("uptime") or entry.get("availability")),
                                    ("WAN IP", entry.get("wanIp") or entry.get("wanAddress")),
                                ]

                                for label, value in metric_fields:
                                    if value is not None:
                                        ui.label(f"{label}: {value}").classes("text-sm")

                                # If there are nested metrics show raw
                                if not any(v for _, v in metric_fields):
                                    ui.code(str(entry), language="json").classes(
                                        "w-full text-xs mt-2"
                                    )

                ui.button("Load ISP Metrics", icon="speed", on_click=load_isp_metrics).props(
                    "color=primary"
                ).classes("mt-2")
