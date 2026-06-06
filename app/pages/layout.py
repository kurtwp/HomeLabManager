"""Shared page layout with navigation."""

from nicegui import ui


def page_layout(title: str = "Home Lab Manager"):
    """Create the shared navigation layout. Call at the top of each page function."""
    ui.add_css("""
        .nav-link { color: white !important; text-decoration: none; }
        .nav-link:hover { opacity: 0.8; }
        .page-container { padding: 24px; max-width: 1400px; margin: 0 auto; }
    """)

    with ui.header().classes("bg-primary items-center justify-between"):
        with ui.row().classes("items-center gap-4"):
            ui.icon("lan").classes("text-2xl")
            ui.link("Home Lab Manager", "/").classes("nav-link text-xl font-bold")

        with ui.row().classes("items-center gap-2"):
            ui.link("Dashboard", "/").classes("nav-link")
            ui.link("Networks", "/networks").classes("nav-link")
            ui.link("Devices", "/devices").classes("nav-link")
            ui.link("IPs", "/ips").classes("nav-link")
            ui.link("Docs", "/docs").classes("nav-link")
            ui.link("History", "/history").classes("nav-link")

        with ui.row().classes("items-center"):
            search_input = ui.input(placeholder="Search...").props(
                'dense outlined dark color="white"'
            ).classes("w-64")
            search_input.on(
                "keydown.enter",
                lambda e: ui.navigate.to(f"/search?q={search_input.value}"),
            )
