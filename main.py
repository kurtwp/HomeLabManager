"""Home Lab IP Management & Equipment Application — NiceGUI entry point."""

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


# Initialize database and seed defaults
init_db()
with get_session() as session:
    seed_defaults(session)


# --- Page routes ---

@ui.page("/")
def home():
    render_dashboard()


@ui.page("/networks")
def networks_page():
    render_networks()


@ui.page("/networks/{network_id}")
def network_detail_page(network_id: int):
    # Placeholder — will expand with subnet visualization
    from app.pages.layout import page_layout
    from app.services.network_service import get_network_by_id, get_network_utilization
    from app.services.ip_service import get_ips_for_network
    from app.database.db import get_session_direct

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

        # IP list
        ui.label("IP Addresses").classes("text-xl font-semibold mt-4")
        if ips:
            columns = [
                {"name": "address", "label": "Address", "field": "address", "align": "left"},
                {"name": "hostname", "label": "Hostname", "field": "hostname", "align": "left"},
                {"name": "status", "label": "Status", "field": "status", "align": "center"},
                {"name": "type", "label": "Type", "field": "type", "align": "center"},
            ]
            rows = [
                {
                    "id": ip.id,
                    "address": ip.address,
                    "hostname": ip.hostname or "—",
                    "status": ip.status.value,
                    "type": ip.assignment_type.value.upper(),
                }
                for ip in ips
            ]
            ui.table(columns=columns, rows=rows, row_key="id").classes("w-full").props(
                "flat bordered dense"
            )
        else:
            ui.label("No IPs tracked in this network yet.").classes("text-gray-500")

        # Notes
        if network.notes:
            ui.label("Notes").classes("text-xl font-semibold mt-4")
            ui.markdown(network.notes).classes("w-full")

    session.close()


@ui.page("/devices")
def devices_page():
    render_devices()


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


@ui.page("/search")
def search_page(q: str = ""):
    render_search(q)


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
