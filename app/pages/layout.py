"""Shared page layout with navigation."""

from nicegui import ui


def page_layout(title: str = "Home Lab Manager"):
    """Create the shared navigation layout. Call at the top of each page function."""
    # Enable dark mode by default
    dark = ui.dark_mode(True)

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

            # Devices dropdown — dynamically shows types that have devices
            with ui.button("Devices", icon="devices").props("flat color=white no-caps"):
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
            ui.link("Tags", "/tags").classes("nav-link")

            # Discovery dropdown (UniFi, SNMP, Nmap, Ping, Scheduler)
            with ui.button("Discovery", icon="radar").props("flat color=white no-caps"):
                with ui.menu():
                    ui.menu_item("UniFi Sync (Local)", lambda: ui.navigate.to("/unifi"))
                    ui.menu_item("Site Manager (Cloud)", lambda: ui.navigate.to("/site-manager"))
                    ui.separator()
                    ui.menu_item("SNMP Discovery", lambda: ui.navigate.to("/snmp"))
                    ui.menu_item("Nmap Scanner", lambda: ui.navigate.to("/nmap"))
                    ui.menu_item("Ping Scan", lambda: ui.navigate.to("/ping-scan"))
                    ui.separator()
                    ui.menu_item("Scheduled Scans", lambda: ui.navigate.to("/scheduler"))

            ui.link("Import/Export", "/import-export").classes("nav-link")
            ui.link("History", "/history").classes("nav-link")

        with ui.row().classes("items-center gap-2"):
            # Tools menu
            with ui.button(icon="build").props("flat round color=white size=sm"):
                with ui.menu():
                    ui.menu_item("Calculator", lambda: ui.navigate.to("/calculator"))
                    ui.menu_item("Reports", lambda: ui.navigate.to("/reports"))
                    ui.menu_item("Locations", lambda: ui.navigate.to("/locations"))
                    ui.menu_item("Custom Fields", lambda: ui.navigate.to("/custom-fields"))

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

            ui.button(
                icon="dark_mode",
                on_click=toggle_dark,
            ).props("flat round color=white size=sm").tooltip("Toggle dark/light mode")
