"""Home Lab IP Management & Equipment Application — NiceGUI entry point."""
#
from nicegui import ui, app

from config import APP_TITLE, APP_PORT
from app.database.db import init_db, get_session
from app.database.pstn_db import init_pstn_db
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
from app.pages.site_manager import render_site_manager
from app.pages.pstn.pstn_dashboard import render_pstn_dashboard
from app.pages.pstn.ranges import render_ranges, render_range_detail
from app.pages.pstn.numbers import render_numbers
from app.pages.pstn.customers import render_customers, render_customer_detail
from app.pages.pstn.audit import render_pstn_audit
from app.pages.pstn.bulk_import import render_bulk_import
from app.pages.pstn.export import render_pstn_export
from app.pages.uptime_page import render_uptime
from app.pages.help_page import render_help
from app.pages.notifications_page import render_notifications
from app.pages.firmware_page import render_firmware
from app.pages.settings_page import render_settings
from app.services.scheduler import start_scheduler, stop_scheduler


# Initialize databases and seed defaults
init_db()
init_pstn_db()
with get_session() as session:
    seed_defaults(session)

# Start background scheduler for automatic scans
start_scheduler()

# Add uptime monitoring job (runs every 30 seconds)
from app.services.scheduler import scheduler
from app.services.uptime_service import run_checks
scheduler.add_job(run_checks, "interval", seconds=30, id="uptime_checks", replace_existing=True)

# Add firmware check job (runs every 6 hours)
from app.services.firmware_service import sync_firmware_info
scheduler.add_job(sync_firmware_info, "interval", hours=6, id="firmware_check", replace_existing=True)


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

        # Tags + DHCP Range (side by side)
        with ui.row().classes("w-full gap-4 mt-4 flex-wrap"):
            # Tags (left half)
            with ui.card().classes("flex-1 min-w-[300px]"):
                ui.label("Tags").classes("text-lg font-semibold mb-2")
                # Inline tag assignment (from the reusable component logic)
                from app.models.tag import Tag
                all_tags = session.query(Tag).order_by(Tag.name).all()
                current_tags = network.tags
                current_tag_ids = {t.id for t in current_tags}

                tags_display = ui.row().classes("flex-wrap gap-1 mb-3")

                def refresh_tag_display():
                    tags_display.clear()
                    with tags_display:
                        if not network.tags:
                            ui.label("No tags").classes("text-sm text-gray-400 italic")
                        else:
                            for tag in network.tags:
                                with ui.row().classes("items-center gap-0"):
                                    ui.html(
                                        f'<span style="display:inline-flex; align-items:center; '
                                        f"padding:2px 10px; border-radius:12px; font-size:0.75rem; "
                                        f"font-weight:500; background:{tag.color}20; "
                                        f'color:{tag.color}; border:1px solid {tag.color}40;">'
                                        f"{tag.name}</span>"
                                    )
                                    ui.button(
                                        icon="close",
                                        on_click=lambda t=tag: (
                                            network.tags.remove(t),
                                            session.commit(),
                                            refresh_tag_display(),
                                        ),
                                    ).props("flat round size=xs").classes("ml-0")

                refresh_tag_display()

                available_tags = {t.id: t.name for t in all_tags if t.id not in current_tag_ids}
                if available_tags:
                    with ui.row().classes("items-center gap-2"):
                        tag_select = ui.select(available_tags, label="Add tag", with_input=True).classes("w-36")

                        def add_net_tag():
                            if tag_select.value:
                                tag = session.query(Tag).filter(Tag.id == tag_select.value).first()
                                if tag and tag not in network.tags:
                                    network.tags.append(tag)
                                    session.commit()
                                    refresh_tag_display()

                        ui.button("Add", on_click=add_net_tag).props("flat color=primary size=sm")

            # DHCP Range (right half)
            with ui.card().classes("flex-1 min-w-[300px]"):
                ui.label("DHCP Range").classes("text-lg font-semibold mb-2")
                ui.label(
                    "IPs within this range → DHCP. Outside → Static."
                ).classes("text-xs text-gray-500 mb-2")

                with ui.row().classes("gap-2 items-end"):
                    dhcp_start_edit = ui.input(
                        "Start", value=network.dhcp_start or "", placeholder="e.g. 192.168.2.100"
                    ).classes("w-40")
                    dhcp_end_edit = ui.input(
                        "End", value=network.dhcp_end or "", placeholder="e.g. 192.168.2.245"
                    ).classes("w-40")

                    def save_dhcp_range():
                        update_network(
                            session, network.id,
                            dhcp_start=dhcp_start_edit.value or None,
                            dhcp_end=dhcp_end_edit.value or None,
                        )
                        ui.notify("DHCP range saved!", type="positive")

                    ui.button("Save", on_click=save_dhcp_range).props("color=primary size=sm")

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

            with ui.tab_panels(tabs, value=preview_tab).classes("w-full"):
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
def devices_page(category: str = ""):
    render_devices(category)


@ui.page("/device-types")
def device_types_page():
    from app.pages.device_types import render_device_types
    render_device_types()


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


@ui.page("/site-manager")
def site_manager_page():
    render_site_manager()


@ui.page("/uptime")
def uptime_page():
    render_uptime()


@ui.page("/help")
def help_page():
    render_help()


@ui.page("/help/{selected_file}")
def help_detail_page(selected_file: str):
    render_help(selected_file)


@ui.page("/notifications")
def notifications_page():
    render_notifications()


@ui.page("/firmware")
def firmware_page():
    render_firmware()


@ui.page("/settings")
def settings_page():
    render_settings()


# --- PSTN / Telephony routes ---

@ui.page("/pstn")
def pstn_dashboard_page():
    render_pstn_dashboard()


@ui.page("/pstn/ranges")
def pstn_ranges_page():
    render_ranges()


@ui.page("/pstn/ranges/{range_id}")
def pstn_range_detail_page(range_id: int):
    render_range_detail(range_id)


@ui.page("/pstn/numbers")
def pstn_numbers_page():
    render_numbers()


@ui.page("/pstn/customers")
def pstn_customers_page():
    render_customers()


@ui.page("/pstn/customers/{customer_id}")
def pstn_customer_detail_page(customer_id: int):
    render_customer_detail(customer_id)


@ui.page("/pstn/audit")
def pstn_audit_page():
    render_pstn_audit()


@ui.page("/pstn/import")
def pstn_import_page():
    render_bulk_import()


@ui.page("/pstn/export")
def pstn_export_page():
    render_pstn_export()


# --- Serve static CSS ---
app.add_static_files("/static", "static")


# --- Run ---
ui.run(
    title=APP_TITLE,
    port=APP_PORT,
    native=False,
    reload=False,
    favicon="🌐",
    storage_secret="homelab-manager-secret",
)
