"""Global search results page."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.services.search_service import global_search
from app.pages.layout import page_layout


def render_search(query: str = ""):
    """Render search results page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        ui.label(f'Search Results for "{query}"').classes("text-3xl font-bold")
        ui.separator().classes("my-4")

        if not query:
            ui.label("Enter a search term in the header search bar.").classes(
                "text-gray-500"
            )
            session.close()
            return

        results = global_search(session, query)
        ui.label(f"{results['total']} results found").classes("text-sm text-gray-500 mb-4")

        # Networks
        if results["networks"]:
            ui.label("Networks").classes("text-xl font-semibold mt-4")
            for net in results["networks"]:
                with ui.card().classes("w-full cursor-pointer").on(
                    "click", lambda n=net: ui.navigate.to(f"/networks/{n.id}")
                ):
                    ui.label(f"{net.name} — {net.cidr}").classes("font-semibold")
                    if net.description:
                        ui.label(net.description).classes("text-sm text-gray-500")

        # IPs
        if results["ip_addresses"]:
            ui.label("IP Addresses").classes("text-xl font-semibold mt-4")
            for ip in results["ip_addresses"]:
                with ui.card().classes("w-full cursor-pointer").on(
                    "click", lambda i=ip: ui.navigate.to(f"/ips/{i.id}")
                ):
                    ui.label(f"{ip.address} — {ip.hostname or 'No hostname'}").classes(
                        "font-semibold font-mono"
                    )

        # Devices
        if results["devices"]:
            ui.label("Devices").classes("text-xl font-semibold mt-4")
            for dev in results["devices"]:
                with ui.card().classes("w-full cursor-pointer").on(
                    "click", lambda d=dev: ui.navigate.to(f"/devices/{d.id}")
                ):
                    ui.label(dev.name).classes("font-semibold")
                    ui.label(
                        f"{dev.manufacturer or ''} {dev.model or ''}".strip() or "—"
                    ).classes("text-sm text-gray-500")

        # Documentation
        if results["documentation"]:
            ui.label("Documentation").classes("text-xl font-semibold mt-4")
            for doc in results["documentation"]:
                with ui.card().classes("w-full cursor-pointer").on(
                    "click", lambda d=doc: ui.navigate.to(f"/docs/{d.id}")
                ):
                    ui.label(doc.title).classes("font-semibold")
                    preview = doc.body[:120] + "..." if len(doc.body) > 120 else doc.body
                    ui.label(preview).classes("text-sm text-gray-500")

    session.close()
