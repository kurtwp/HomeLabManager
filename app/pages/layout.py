"""Shared page layout with navigation."""

from nicegui import ui


def page_layout(title: str = "Home Lab Manager"):
    """Create the shared navigation layout. Call at the top of each page function."""
    from nicegui import app
    from app.services.auth_service import is_auth_enabled

    # Auth check — redirect to login if auth is enabled and user not authenticated
    if is_auth_enabled() and not app.storage.user.get("authenticated"):
        ui.navigate.to("/login")
        return

    # Persist dark mode preference per user using NiceGUI's storage
    is_dark = app.storage.user.get("dark_mode", True)
    dark = ui.dark_mode(is_dark)

    ui.add_css("""
        .nav-link { color: white !important; text-decoration: none; font-size: 1.1rem; }
        .nav-link:hover { opacity: 0.8; }
        .page-container { padding: 24px; max-width: 1400px; margin: 0 auto; }
        body.body--dark .q-card { background: #1e1e1e; }
        body.body--dark .q-table { background: #1e1e1e; }
    """)

    with ui.header().classes("bg-primary items-center justify-between px-6 py-3"):
        with ui.row().classes("items-center gap-4"):
            ui.icon("lan").classes("text-3xl")
            ui.link("Home Lab Manager", "/").classes("nav-link text-2xl font-bold")

        with ui.row().classes("items-center gap-4"):
            ui.link("Dashboard", "/").classes("nav-link")
            ui.link("Networks", "/networks").classes("nav-link")

            # Discovery dropdown (UniFi, SNMP, Nmap, Ping, Scheduler)
            with ui.button("Discovery").props("flat color=white no-caps"):
                with ui.menu():
                    ui.menu_item("UniFi Sync (Local)", lambda: ui.navigate.to("/unifi"))
                    ui.menu_item("Site Manager (Cloud)", lambda: ui.navigate.to("/site-manager"))
                    ui.separator()
                    ui.menu_item("SNMP Discovery", lambda: ui.navigate.to("/snmp"))
                    ui.menu_item("Nmap Scanner", lambda: ui.navigate.to("/nmap"))
                    ui.menu_item("Ping Scan", lambda: ui.navigate.to("/ping-scan"))
                    ui.separator()
                    ui.menu_item("Scheduled Scans", lambda: ui.navigate.to("/scheduler"))

            # Monitor dropdown
            with ui.button("Monitor").props("flat color=white no-caps"):
                with ui.menu():
                    ui.menu_item("Uptime Monitor", lambda: ui.navigate.to("/uptime"))
                    ui.menu_item("Port Monitor", lambda: ui.navigate.to("/port-monitor"))
                    ui.menu_item("SSL Certificates", lambda: ui.navigate.to("/ssl-tracker"))
                    ui.menu_item("Domain Tracker", lambda: ui.navigate.to("/domain-tracker"))
                    ui.menu_item("Firmware Tracker", lambda: ui.navigate.to("/firmware"))

            # Devices dropdown — dynamically shows types that have devices
            with ui.button("Devices").props("flat color=white no-caps"):
                with ui.menu():
                    ui.menu_item("All Devices", lambda: ui.navigate.to("/devices"))
                    ui.separator()

                    # Show categories that actually have devices
                    from app.database.db import get_session_direct as _get_session
                    from app.models.device import Device as _Device, DeviceType as _DeviceType
                    _s = _get_session()
                    _types_with_devices = (
                        _s.query(_DeviceType)
                        .filter(_DeviceType.id.in_(
                            _s.query(_Device.device_type_id).filter(_Device.device_type_id.isnot(None)).distinct()
                        ))
                        .order_by(_DeviceType.name)
                        .all()
                    )
                    for dt in _types_with_devices:
                        count = _s.query(_Device).filter(_Device.device_type_id == dt.id).count()
                        ui.menu_item(
                            f"{dt.name} ({count})",
                            lambda d=dt: ui.navigate.to(f"/devices?category=type_{d.id}"),
                        )
                    # Check for untyped devices
                    untyped = _s.query(_Device).filter(_Device.device_type_id.is_(None)).count()
                    if untyped:
                        ui.menu_item(f"Unclassified ({untyped})", lambda: ui.navigate.to("/devices?category=unclassified"))
                    _s.close()

                    ui.separator()
                    ui.menu_item("Manage Device Types", lambda: ui.navigate.to("/device-types"))

            ui.link("IPs", "/ips").classes("nav-link")
            ui.link("Docs", "/docs").classes("nav-link")

            # Telephony dropdown
            with ui.button("Telephony").props("flat color=white no-caps"):
                with ui.menu():
                    ui.menu_item("Dashboard", lambda: ui.navigate.to("/pstn"))
                    ui.menu_item("Number Ranges", lambda: ui.navigate.to("/pstn/ranges"))
                    ui.menu_item("Phone Numbers", lambda: ui.navigate.to("/pstn/numbers"))
                    ui.menu_item("Customers", lambda: ui.navigate.to("/pstn/customers"))
                    ui.separator()
                    ui.menu_item("Bulk Import", lambda: ui.navigate.to("/pstn/import"))
                    ui.menu_item("Export", lambda: ui.navigate.to("/pstn/export"))
                    ui.separator()
                    ui.menu_item("Audit Trail", lambda: ui.navigate.to("/pstn/audit"))

            ui.link("Import/Export", "/import-export").classes("nav-link")
            ui.link("History", "/history").classes("nav-link")
            ui.link("Help", "/help").classes("nav-link")

        with ui.row().classes("items-center gap-2"):
            # Tools menu
            with ui.button(icon="build").props("flat round color=white size=sm"):
                with ui.menu():
                    ui.menu_item("Tags", lambda: ui.navigate.to("/tags"))
                    ui.menu_item("Calculator", lambda: ui.navigate.to("/calculator"))
                    ui.menu_item("Reports", lambda: ui.navigate.to("/reports"))
                    ui.menu_item("Locations", lambda: ui.navigate.to("/locations"))
                    ui.menu_item("Custom Fields", lambda: ui.navigate.to("/custom-fields"))
                    ui.menu_item("MAC Watchlist", lambda: ui.navigate.to("/mac-watchlist"))
                    ui.separator()
                    ui.menu_item("Notifications", lambda: ui.navigate.to("/notifications"))
                    ui.menu_item("Webhook Triggers", lambda: ui.navigate.to("/webhook-triggers"))
                    ui.menu_item("Settings", lambda: ui.navigate.to("/settings"))
                    ui.menu_item("Backup & Restore", lambda: ui.navigate.to("/backup"))

            search_input = ui.input(placeholder="Search...").props(
                'dense outlined dark color="white"'
            ).classes("w-64")
            search_input.on(
                "keydown.enter",
                lambda e: ui.navigate.to(f"/search?q={search_input.value}"),
            )

            # Dark/Light mode toggle
            def toggle_dark():
                dark.toggle()
                app.storage.user["dark_mode"] = dark.value

            ui.button(
                icon="dark_mode",
                on_click=toggle_dark,
            ).props("flat round color=white size=sm").tooltip("Toggle dark/light mode")

            # Logout button (only shown when auth is enabled)
            if is_auth_enabled():
                def do_logout():
                    app.storage.user["authenticated"] = False
                    app.storage.user["username"] = ""
                    app.storage.user["role"] = ""
                    ui.navigate.to("/login")

                ui.button(
                    icon="logout",
                    on_click=do_logout,
                ).props("flat round color=white size=sm").tooltip(
                    f"Logout ({app.storage.user.get('username', '')})"
                )
