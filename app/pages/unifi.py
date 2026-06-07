"""UniFi Integration page — sync devices, clients, networks from UDM."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.services.unifi_service import (
    is_configured,
    test_connection,
    sync_networks,
    sync_devices,
    sync_clients,
)
from app.pages.layout import page_layout
from config import UNIFI_BASE_URL, UNIFI_SITE_ID


def render_unifi():
    """Render the UniFi integration page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        ui.label("UniFi Integration").classes("text-3xl font-bold")
        ui.label(
            "Sync networks, devices, and clients from your UniFi controller."
        ).classes("text-gray-500 mb-4")

        ui.separator()

        # Connection status
        with ui.card().classes("w-full mt-4"):
            ui.label("Connection Status").classes("text-lg font-semibold mb-2")

            if not is_configured():
                ui.label(
                    "⚠️ UniFi integration not configured. Set UNIFI_API_KEY, "
                    "UNIFI_BASE_URL, and UNIFI_SITE_ID in your .env file."
                ).classes("text-orange")
                with ui.row().classes("gap-4 mt-2"):
                    ui.label(f"Base URL: {UNIFI_BASE_URL or '(not set)'}").classes("text-sm")
                    ui.label(f"Site ID: {UNIFI_SITE_ID or '(not set)'}").classes("text-sm")
            else:
                with ui.row().classes("gap-4 items-center"):
                    ui.label(f"Controller: {UNIFI_BASE_URL}").classes("text-sm")
                    ui.label(f"Site: {UNIFI_SITE_ID}").classes("text-sm font-mono")

                connection_status = ui.label("").classes("mt-2")

                def check_connection():
                    connection_status.text = "Testing connection..."
                    result = test_connection()
                    if result["success"]:
                        connection_status.text = (
                            f"✅ Connected! Found {result['sites']} site(s): "
                            f"{', '.join(result['site_names'])}"
                        )
                        connection_status.classes(remove="text-red", add="text-green")
                    else:
                        connection_status.text = f"❌ {result['error']}"
                        connection_status.classes(remove="text-green", add="text-red")

                ui.button("Test Connection", icon="wifi_find", on_click=check_connection).props(
                    "color=primary outline"
                )

        if not is_configured():
            session.close()
            return

        # Sync actions
        ui.separator().classes("my-4")
        ui.label("Sync Operations").classes("text-xl font-semibold mb-2")

        sync_log = ui.column().classes("w-full gap-2 mt-4")

        def log_result(title: str, result: dict):
            with sync_log:
                with ui.card().classes("w-full"):
                    ui.label(title).classes("font-semibold")
                    parts = []
                    if "created" in result:
                        parts.append(f"{result['created']} created")
                    if "updated" in result:
                        parts.append(f"{result['updated']} updated")
                    if "skipped" in result:
                        parts.append(f"{result['skipped']} skipped")
                    ui.label(" · ".join(parts)).classes("text-sm text-green")
                    if result.get("errors"):
                        for err in result["errors"][:5]:
                            ui.label(f"⚠️ {err}").classes("text-xs text-orange")
                        if len(result["errors"]) > 5:
                            ui.label(
                                f"...and {len(result['errors']) - 5} more errors"
                            ).classes("text-xs text-gray-500")

        with ui.row().classes("w-full gap-4 flex-wrap"):
            # Sync Networks
            with ui.card().classes("flex-1 min-w-[300px]"):
                ui.label("Networks / VLANs").classes("text-lg font-semibold")
                ui.label(
                    "Pull VLAN configurations and subnets from UniFi."
                ).classes("text-sm text-gray-500 mb-2")

                def do_sync_networks():
                    ui.notify("Syncing networks...", type="info")
                    try:
                        result = sync_networks(session)
                        log_result("Network Sync", result)
                        ui.notify(
                            f"Networks: {result['created']} created, {result['updated']} updated",
                            type="positive",
                        )
                    except Exception as e:
                        ui.notify(f"Sync failed: {e}", type="negative")

                ui.button("Sync Networks", icon="lan", on_click=do_sync_networks).props(
                    "color=primary"
                )

            # Sync Devices
            with ui.card().classes("flex-1 min-w-[300px]"):
                ui.label("Network Devices").classes("text-lg font-semibold")
                ui.label(
                    "Pull APs, switches, and gateways from UniFi."
                ).classes("text-sm text-gray-500 mb-2")

                def do_sync_devices():
                    ui.notify("Syncing devices...", type="info")
                    try:
                        result = sync_devices(session)
                        log_result("Device Sync", result)
                        ui.notify(
                            f"Devices: {result['created']} created, {result['updated']} updated",
                            type="positive",
                        )
                    except Exception as e:
                        ui.notify(f"Sync failed: {e}", type="negative")

                ui.button("Sync Devices", icon="router", on_click=do_sync_devices).props(
                    "color=primary"
                )

            # Sync Clients
            with ui.card().classes("flex-1 min-w-[300px]"):
                ui.label("Active Clients").classes("text-lg font-semibold")
                ui.label(
                    "Pull connected clients and their IPs from UniFi."
                ).classes("text-sm text-gray-500 mb-2")

                def do_sync_clients():
                    ui.notify("Syncing clients...", type="info")
                    try:
                        result = sync_clients(session)
                        log_result("Client Sync", result)
                        ui.notify(
                            f"Clients: {result['created']} created, {result['updated']} updated, "
                            f"{result['skipped']} skipped",
                            type="positive",
                        )
                    except Exception as e:
                        ui.notify(f"Sync failed: {e}", type="negative")

                ui.button("Sync Clients", icon="people", on_click=do_sync_clients).props(
                    "color=primary"
                )

        # Sync All button
        ui.separator().classes("my-4")

        def sync_all():
            ui.notify("Running full sync...", type="info")
            try:
                net_result = sync_networks(session)
                log_result("Network Sync", net_result)
                dev_result = sync_devices(session)
                log_result("Device Sync", dev_result)
                client_result = sync_clients(session)
                log_result("Client Sync", client_result)
                ui.notify("Full sync complete!", type="positive")
            except Exception as e:
                ui.notify(f"Sync failed: {e}", type="negative")

        ui.button(
            "Sync Everything", icon="sync", on_click=sync_all
        ).props("color=primary size=lg")

        # Debug section — raw API data inspection
        ui.separator().classes("my-4")
        with ui.expansion("Debug: Raw API Data", icon="bug_report").classes("w-full"):
            debug_output = ui.column().classes("w-full")

            def show_raw_networks():
                from app.services.unifi_service import fetch_raw_networks
                debug_output.clear()
                with debug_output:
                    try:
                        raw = fetch_raw_networks()
                        ui.label(f"Got {len(raw)} networks from UniFi").classes("font-semibold")
                        for i, net in enumerate(raw[:5]):
                            ui.label(f"Network {i+1}: {net.get('name', '?')}").classes("font-semibold mt-2")
                            ui.code(str(net), language="json").classes("w-full text-xs")
                    except Exception as e:
                        ui.label(f"Error: {e}").classes("text-red")

            def show_raw_clients():
                from app.services.unifi_service import fetch_raw_clients
                debug_output.clear()
                with debug_output:
                    try:
                        raw = fetch_raw_clients()
                        ui.label(f"Got {len(raw)} clients from UniFi").classes("font-semibold")
                        for i, client in enumerate(raw[:5]):
                            ui.label(f"Client {i+1}: {client.get('name', client.get('hostname', client.get('mac', '?')))}").classes("font-semibold mt-2")
                            ui.code(str(client), language="json").classes("w-full text-xs")
                    except Exception as e:
                        ui.label(f"Error: {e}").classes("text-red")

            with ui.row().classes("gap-2"):
                ui.button("Show Raw Networks", on_click=show_raw_networks).props("flat size=sm")
                ui.button("Show Raw Clients", on_click=show_raw_clients).props("flat size=sm")

    session.close()
