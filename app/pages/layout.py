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
            ui.link("Devices", "/devices").classes("nav-link")
            ui.link("IPs", "/ips").classes("nav-link")
            ui.link("Docs", "/docs").classes("nav-link")
            ui.link("Tags", "/tags").classes("nav-link")
            ui.link("Import/Export", "/import-export").classes("nav-link")
            ui.link("History", "/history").classes("nav-link")

        with ui.row().classes("items-center gap-2"):
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
