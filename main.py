"""Home Lab Manager Application — NiceGUI entry point."""
#
import logging
from nicegui import ui, app as nicegui_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from config import APP_TITLE, APP_HOST, APP_PORT, STORAGE_SECRET
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
from app.pages.backup_page import render_backup
from app.services.scheduler import start_scheduler, stop_scheduler

# Mount REST API alongside NiceGUI
import app.api.app  # noqa: F401 — mounts /api routes on the NiceGUI Starlette app


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
from app.services.firmware_service import sync_firmware_info, sync_controller_updates
scheduler.add_job(sync_firmware_info, "interval", hours=6, id="firmware_check", replace_existing=True)
# Controller/application updates via cloud Site Manager API (runs every 6 hours)
scheduler.add_job(sync_controller_updates, "interval", hours=6, id="controller_update_check", replace_existing=True)

# Add SSL certificate check job (runs every 12 hours)
from app.services.ssl_service import refresh_all_certificates
scheduler.add_job(refresh_all_certificates, "interval", hours=12, id="ssl_cert_check", replace_existing=True)

# Add domain expiry check job (runs daily)
from app.services.domain_service import refresh_all_domains
scheduler.add_job(refresh_all_domains, "interval", hours=24, id="domain_check", replace_existing=True)


# --- Page routes ---

@ui.page("/login")
def login_page():
    from app.pages.login_page import render_login
    render_login()


@ui.page("/")
def home():
    render_dashboard()


@ui.page("/networks")
def networks_page():
    render_networks()


@ui.page("/networks/{network_id}")
def network_detail_page(network_id: int):
    from app.pages.network_detail import render_network_detail
    render_network_detail(network_id)


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


@ui.page("/firewall")
def firewall_page():
    from app.pages.firewall import render_firewall
    render_firewall()


@ui.page("/dhcp-leases")
def dhcp_leases_page():
    from app.pages.dhcp_leases import render_dhcp_leases
    render_dhcp_leases()


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


@ui.page("/uptime/{monitor_id}")
def uptime_detail_page(monitor_id: int):
    from app.pages.uptime_detail import render_uptime_detail
    render_uptime_detail(monitor_id)


@ui.page("/port-monitor")
def port_monitor_page():
    from app.pages.port_monitor_page import render_port_monitor
    render_port_monitor()


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


@ui.page("/backup")
def backup_page():
    render_backup()


@ui.page("/mac-watchlist")
def mac_watchlist_page():
    from app.pages.mac_watchlist_page import render_mac_watchlist
    render_mac_watchlist()


@ui.page("/webhook-triggers")
def webhook_triggers_page():
    from app.pages.webhook_triggers_page import render_webhook_triggers
    render_webhook_triggers()


@ui.page("/ssl-tracker")
def ssl_tracker_page():
    from app.pages.ssl_page import render_ssl_tracker
    render_ssl_tracker()


@ui.page("/domain-tracker")
def domain_tracker_page():
    from app.pages.domain_page import render_domain_tracker
    render_domain_tracker()


@ui.page("/inventory-export")
def inventory_export_page():
    from app.pages.inventory_export_page import render_inventory_export
    render_inventory_export()


@ui.page("/archived-notes")
def archived_notes_page():
    from app.pages.archived_notes_page import render_archived_notes
    render_archived_notes()


@ui.page("/users")
def user_management_page():
    from app.pages.user_management_page import render_user_management
    render_user_management()


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
nicegui_app.add_static_files("/static", "static")


# --- Run ---
ui.run(
    title=APP_TITLE,
    host=APP_HOST,
    port=APP_PORT,
    native=False,
    reload=False,
    favicon="🌐",
    storage_secret=STORAGE_SECRET,
)
