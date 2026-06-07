"""CSV Import/Export UI page."""

from nicegui import ui, events

from app.database.db import get_session_direct as get_session
from app.services.export_service import export_ips_csv, export_devices_csv, import_ips_csv
from app.services.network_service import get_all_networks
from app.pages.layout import page_layout


def render_import_export():
    """Render the import/export page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        ui.label("Import & Export").classes("text-3xl font-bold")
        ui.separator().classes("my-4")

        with ui.row().classes("w-full gap-6 flex-wrap"):
            # --- Export Section ---
            with ui.card().classes("flex-1 min-w-[400px]"):
                ui.label("Export Data").classes("text-xl font-semibold mb-3")
                ui.label(
                    "Download your data as CSV files for backup or reporting."
                ).classes("text-sm text-gray-500 mb-4")

                networks = get_all_networks(session)
                network_options = {0: "All Networks"}
                network_options.update({n.id: f"{n.name} ({n.cidr})" for n in networks})

                export_net_select = ui.select(
                    network_options, value=0, label="Network (for IP export)"
                ).classes("w-full mb-2")

                with ui.row().classes("gap-2"):
                    ui.button(
                        "Export IPs (CSV)",
                        icon="download",
                        on_click=lambda: download_ips_csv(),
                    ).props("color=primary outline")
                    ui.button(
                        "Export Devices (CSV)",
                        icon="download",
                        on_click=lambda: download_devices_csv(),
                    ).props("color=primary outline")

                def download_ips_csv():
                    net_id = export_net_select.value if export_net_select.value != 0 else None
                    csv_data = export_ips_csv(session, network_id=net_id)
                    ui.download(
                        csv_data.encode("utf-8"),
                        "ip_addresses.csv",
                        "text/csv",
                    )
                    ui.notify("IP export ready!", type="positive")

                def download_devices_csv():
                    csv_data = export_devices_csv(session)
                    ui.download(
                        csv_data.encode("utf-8"),
                        "devices.csv",
                        "text/csv",
                    )
                    ui.notify("Device export ready!", type="positive")

            # --- Import Section ---
            with ui.card().classes("flex-1 min-w-[400px]"):
                ui.label("Import IPs from CSV").classes("text-xl font-semibold mb-3")
                ui.label(
                    "Upload a CSV file with columns: address, hostname, mac_address, "
                    "assignment_type, notes"
                ).classes("text-sm text-gray-500 mb-2")
                ui.label(
                    "• assignment_type values: static, dhcp, reserved"
                ).classes("text-xs text-gray-400 mb-1")
                ui.label(
                    "• Existing IPs will be skipped (no duplicates)"
                ).classes("text-xs text-gray-400 mb-4")

                import_net_options = {n.id: f"{n.name} ({n.cidr})" for n in networks}
                import_net_select = ui.select(
                    import_net_options, label="Target Network *"
                ).classes("w-full mb-2")

                import_result = ui.label("").classes("text-sm mt-2")

                async def handle_upload(e: events.UploadEventArguments):
                    if not import_net_select.value:
                        ui.notify("Select a target network first", type="warning")
                        return

                    content = e.content.read().decode("utf-8")
                    result = import_ips_csv(session, content, import_net_select.value)

                    msg = (
                        f"Import complete: {result['added']} added, "
                        f"{result['skipped']} skipped"
                    )
                    if result["errors"]:
                        msg += f", {len(result['errors'])} errors"
                    import_result.text = msg
                    ui.notify(msg, type="positive" if not result["errors"] else "warning")

                ui.upload(
                    label="Upload CSV",
                    on_upload=handle_upload,
                    auto_upload=True,
                ).props('accept=".csv" max-file-size="5242880"').classes("w-full")

    session.close()
