"""Home Lab IP Management & Equipment Application — NiceGUI entry point."""
#
from nicegui import ui, app

from config import APP_TITLE, APP_PORT
from app.database.db import init_db, get_session
from app.services.seed import seed_defaults
from app.pages.dashboard import render_dashboard
from app.pages.networks import render_networks
from app.pages.devices import render_devices
from app.pages.ips import render_ips, render_ip_detail
from app.pages.documentation import render_documentation, render_doc_detail
from app.pages.history import render_history
from app.pages.search import render_search
from app.pages.tags import render_tags
from app.pages.import_export import render_import_export
from app.pages.unifi import render_unifi
from app.pages.scheduler_page import render_scheduler
from app.pages.calculator import render_calculator
from app.pages.reports import render_reports
from app.pages.locations import render_locations
from app.pages.custom_fields import render_custom_fields
from app.pages.snmp_page import render_snmp
from app.pages.nmap_page import render_nmap
from app.pages.ping_scan import render_ping_scan
from app.services.scheduler import start_scheduler, stop_scheduler


# Initialize database and seed defaults
init_db()
with get_session() as session:
    seed_defaults(session)

# Start background scheduler for automatic scans
start_scheduler()


# --- Page routes ---

@ui.page("/")
def home():
    render_dashboard()


@ui.page("/networks")
def networks_page():
    render_networks()


@ui.page("/networks/{network_id}")
def network_detail_page(network_id: int):
    from app.pages.layout import page_layout
    from app.services.network_service import get_network_by_id, get_network_utilization, update_network
    from app.services.ip_service import get_ips_for_network
    from app.services.scanner import resolve_hostname
    from app.database.db import get_session_direct
    from app.pages.subnet_grid import render_subnet_grid
    from app.pages.tag_assignment import render_tag_assignment

    page_layout()
    session = get_session_direct()
    network = get_network_by_id(session, network_id)

    if not network:
        with ui.column().classes("page-container"):
            ui.label("Network not found").classes("text-xl text-red")
        session.close()
        return

    util = get_network_utilization(session, network_id)
    ips = get_ips_for_network(session, network_id)

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("items-center gap-4"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/networks")).props(
                "flat round"
            )
            ui.label(network.name).classes("text-3xl font-bold")
            ui.label(network.cidr).classes("text-xl font-mono text-gray-500")
            if network.vlan_id:
                ui.badge(f"VLAN {network.vlan_id}").props("color=blue outline")

        ui.separator().classes("my-4")

        # Utilization bar
        with ui.card().classes("w-full"):
            ui.label("Utilization").classes("text-lg font-semibold")
            ui.linear_progress(
                value=util.get("utilization_percent", 0) / 100,
                show_value=False,
            ).classes("w-full mt-2")
            ui.label(
                f'{util.get("used", 0)} used / {util.get("free", 0)} free / '
                f'{util.get("total", 0)} total — {util.get("utilization_percent", 0)}%'
            ).classes("text-sm text-gray-500")

        # Visual subnet grid
        with ui.card().classes("w-full mt-4"):
            ui.label("Subnet Map").classes("text-lg font-semibold mb-2")
            render_subnet_grid(network.cidr, ips)

        # Tags
        render_tag_assignment(session, network)

        # IP table with hostname refresh
        with ui.row().classes("items-center justify-between mt-4"):
            ui.label("IP Addresses").classes("text-xl font-semibold")
            def refresh_hostnames():
                updated = 0
                for ip in ips:
                    new_hostname = resolve_hostname(ip.address)
                    if new_hostname and new_hostname != ip.hostname:
                        ip.hostname = new_hostname
                        updated += 1
                session.commit()
                ui.notify(f"Refreshed hostnames: {updated} updated", type="positive")
                ui.navigate.to(f"/networks/{network_id}")

            ui.button("Refresh Hostnames", icon="dns", on_click=refresh_hostnames).props(
                "flat color=primary size=sm"
            )

        if ips:
            columns = [
                {"name": "address", "label": "Address", "field": "address", "align": "left"},
                {"name": "hostname", "label": "Hostname", "field": "hostname", "align": "left"},
                {"name": "status", "label": "Status", "field": "status", "align": "center"},
                {"name": "type", "label": "Type", "field": "type", "align": "center"},
                {"name": "tags", "label": "Tags", "field": "tags", "align": "left"},
            ]
            rows = [
                {
                    "id": ip.id,
                    "address": ip.address,
                    "hostname": ip.hostname or "—",
                    "status": ip.status.value,
                    "type": ip.assignment_type.value.upper(),
                    "tags": ", ".join(t.name for t in ip.tags) if ip.tags else "—",
                }
                for ip in ips
            ]
            ui.table(columns=columns, rows=rows, row_key="id").classes("w-full").props(
                "flat bordered dense"
            )
        else:
            ui.label("No IPs tracked in this network yet.").classes("text-gray-500")

        # Notes editor
        with ui.card().classes("w-full mt-4"):
            ui.label("Network Notes").classes("text-lg font-semibold mb-2")

            with ui.tabs().classes("w-full") as tabs:
                edit_tab = ui.tab("Edit")
                preview_tab = ui.tab("Preview")

            with ui.tab_panels(tabs, value=edit_tab).classes("w-full"):
                with ui.tab_panel(edit_tab):
                    notes_editor = ui.textarea(
                        value=network.notes or ""
                    ).classes("w-full").props('rows="8"')

                    def save_network_notes():
                        update_network(session, network.id, notes=notes_editor.value)
                        ui.notify("Notes saved!", type="positive")

                    ui.button("Save Notes", on_click=save_network_notes).props(
                        "color=primary"
                    )

                with ui.tab_panel(preview_tab):
                    ui.markdown(network.notes or "*No notes yet*").classes("w-full")

    session.close()


@ui.page("/devices")
def devices_page():
    render_devices()


@ui.page("/devices/{device_id}")
def device_detail_page(device_id: int):
    from app.pages.device_detail import render_device_detail
    render_device_detail(device_id)


@ui.page("/ips")
def ips_page():
    render_ips()


@ui.page("/ips/{ip_id}")
def ip_detail_page(ip_id: int):
    render_ip_detail(ip_id)


@ui.page("/docs")
def docs_page():
    render_documentation()


@ui.page("/docs/{doc_id}")
def doc_detail_page(doc_id: int):
    render_doc_detail(doc_id)


@ui.page("/history")
def history_page():
    render_history()


@ui.page("/tags")
def tags_page():
    render_tags()


@ui.page("/import-export")
def import_export_page():
    render_import_export()


@ui.page("/unifi")
def unifi_page():
    render_unifi()


@ui.page("/scheduler")
def scheduler_page():
    render_scheduler()


@ui.page("/search")
def search_page(q: str = ""):
    render_search(q)


@ui.page("/calculator")
def calculator_page():
    render_calculator()


@ui.page("/reports")
def reports_page():
    render_reports()


@ui.page("/locations")
def locations_page():
    render_locations()


@ui.page("/custom-fields")
def custom_fields_page():
    render_custom_fields()


@ui.page("/snmp")
def snmp_page():
    render_snmp()


@ui.page("/nmap")
def nmap_page():
    render_nmap()


@ui.page("/ping-scan")
def ping_scan_page():
    render_ping_scan()


# --- Serve static CSS ---
app.add_static_files("/static", "static")


# --- Run ---
ui.run(
    title=APP_TITLE,
    port=APP_PORT,
    native=False,
    reload=True,
    favicon="🌐",
)
