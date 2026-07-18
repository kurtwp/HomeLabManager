"""SSL Certificate Tracker page — monitor certificate expiry dates."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.services.ssl_service import (
    get_all_certificates,
    add_certificate,
    remove_certificate,
    refresh_certificate,
    refresh_all_certificates,
    check_certificate,
)
from app.pages.layout import page_layout


def render_ssl_tracker():
    """Render the SSL certificate tracker page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("SSL Certificate Tracker").classes("text-3xl font-bold")
            with ui.row().classes("gap-2"):
                ui.button("Add Certificate", icon="add", on_click=lambda: add_dialog.open()).props(
                    "color=primary"
                )
                ui.button("Check All", icon="refresh", on_click=lambda: do_check_all()).props(
                    "color=blue outline"
                )

        ui.label(
            "Monitor SSL/TLS certificate expiry dates. Get alerted before they expire."
        ).classes("text-gray-500 mb-4")

        ui.separator()

        certs_container = ui.column().classes("w-full mt-4 gap-3")

        def do_check_all():
            ui.notify("Checking all certificates...", type="info")
            result = refresh_all_certificates()
            ui.notify(
                f"Checked {result['checked']}: {result['expiring']} expiring, "
                f"{result['expired']} expired, {result['errors']} errors",
                type="positive" if result["expired"] == 0 else "warning",
            )
            refresh_list()

        def refresh_list():
            certs_container.clear()
            certs = get_all_certificates(session)

            with certs_container:
                if not certs:
                    ui.label("No certificates being tracked. Click 'Add Certificate' to start.").classes(
                        "text-gray-500 italic"
                    )
                    return

                # Summary
                valid_count = sum(1 for c in certs if c.is_valid and c.days_remaining and c.days_remaining > 30)
                expiring_count = sum(1 for c in certs if c.days_remaining and 0 < c.days_remaining <= 30)
                expired_count = sum(1 for c in certs if c.days_remaining is not None and c.days_remaining <= 0)
                unchecked = sum(1 for c in certs if c.last_checked is None)

                with ui.row().classes("gap-4 mb-4"):
                    if valid_count:
                        ui.badge(f"✅ {valid_count} Valid").props("color=green")
                    if expiring_count:
                        ui.badge(f"⚠️ {expiring_count} Expiring Soon").props("color=orange")
                    if expired_count:
                        ui.badge(f"❌ {expired_count} Expired").props("color=red")
                    if unchecked:
                        ui.badge(f"❓ {unchecked} Not Checked").props("color=gray")

                # Certificate cards
                for cert in certs:
                    # Determine status color
                    if cert.last_error:
                        status_color = "red"
                        status_icon = "error"
                        status_text = "Error"
                    elif cert.days_remaining is None:
                        status_color = "gray"
                        status_icon = "help"
                        status_text = "Not checked"
                    elif cert.days_remaining <= 0:
                        status_color = "red"
                        status_icon = "cancel"
                        status_text = "EXPIRED"
                    elif cert.days_remaining <= 7:
                        status_color = "red"
                        status_icon = "warning"
                        status_text = f"{cert.days_remaining}d left"
                    elif cert.days_remaining <= 30:
                        status_color = "orange"
                        status_icon = "schedule"
                        status_text = f"{cert.days_remaining}d left"
                    else:
                        status_color = "green"
                        status_icon = "verified"
                        status_text = f"{cert.days_remaining}d left"

                    with ui.card().classes("w-full"):
                        with ui.row().classes("w-full items-center justify-between"):
                            with ui.row().classes("items-center gap-3"):
                                ui.icon(status_icon).classes(f"text-2xl text-{status_color}")
                                with ui.column().classes("gap-0"):
                                    ui.label(cert.name).classes("font-semibold text-lg")
                                    ui.label(f"{cert.host}:{cert.port}").classes("text-sm font-mono text-gray-500")
                                ui.badge(status_text).props(f"color={status_color}")

                            with ui.row().classes("items-center gap-3"):
                                if cert.not_after:
                                    ui.label(
                                        f"Expires: {cert.not_after.strftime('%Y-%m-%d')}"
                                    ).classes("text-xs text-gray-400")
                                if cert.last_checked:
                                    ui.label(
                                        f"Checked: {cert.last_checked.strftime('%m-%d %H:%M')}"
                                    ).classes("text-xs text-gray-400")

                                ui.button(
                                    icon="refresh",
                                    on_click=lambda c=cert: do_refresh_one(c.id),
                                ).props("flat round size=sm").tooltip("Check now")
                                ui.button(
                                    icon="delete",
                                    on_click=lambda c=cert: confirm_delete(c),
                                ).props("flat round size=sm color=red")

                        # Details row
                        if cert.issuer or cert.subject:
                            with ui.row().classes("gap-4 mt-1"):
                                if cert.subject:
                                    ui.label(f"Subject: {cert.subject[:60]}").classes("text-xs text-gray-400")
                                if cert.issuer:
                                    ui.label(f"Issuer: {cert.issuer[:60]}").classes("text-xs text-gray-400")

                        if cert.last_error:
                            ui.label(f"Error: {cert.last_error}").classes("text-xs text-red mt-1")

        def do_refresh_one(cert_id):
            result = refresh_certificate(session, cert_id)
            if result["success"]:
                ui.notify(f"Certificate OK — {result['days_remaining']} days remaining", type="positive")
            else:
                ui.notify(f"Check failed: {result['error']}", type="negative")
            refresh_list()

        def confirm_delete(cert):
            with ui.dialog() as dlg, ui.card():
                ui.label(f"Stop tracking '{cert.name}'?").classes("text-lg")
                with ui.row().classes("justify-end gap-2 mt-2"):
                    ui.button("Cancel", on_click=dlg.close).props("flat")
                    ui.button("Remove", on_click=lambda: (
                        remove_certificate(session, cert.id),
                        dlg.close(),
                        refresh_list(),
                        ui.notify("Certificate removed", type="warning"),
                    )).props("color=red")
            dlg.open()

        refresh_list()

    # Add certificate dialog
    with ui.dialog() as add_dialog, ui.card().classes("w-[450px]"):
        ui.label("Add SSL Certificate").classes("text-xl font-bold mb-2")
        add_name = ui.input("Name *", placeholder="e.g. Proxmox Web UI").classes("w-full")
        add_host = ui.input("Host *", placeholder="192.168.2.5 or proxmox.local").classes("w-full")
        add_port = ui.input("Port", value="443", placeholder="443").classes("w-full")
        add_alert = ui.select(
            {7: "7 days", 14: "14 days", 30: "30 days", 60: "60 days", 90: "90 days"},
            value=30, label="Alert when fewer than",
        ).classes("w-full")

        # Quick test
        test_result = ui.label("").classes("text-sm mt-2")

        def test_cert():
            if not add_host.value:
                ui.notify("Enter a host", type="warning")
                return
            port = int(add_port.value or 443)
            result = check_certificate(add_host.value.strip(), port)
            if result["success"]:
                test_result.text = f"✅ Valid — {result['days_remaining']} days remaining ({result['subject'][:40]})"
                test_result.classes(remove="text-red", add="text-green")
            else:
                test_result.text = f"❌ {result['error']}"
                test_result.classes(remove="text-green", add="text-red")

        ui.button("Test Connection", icon="wifi_find", on_click=test_cert).props(
            "flat size=sm color=blue"
        )

        def save_new():
            if not add_name.value or not add_host.value:
                ui.notify("Name and Host are required", type="warning")
                return
            port = int(add_port.value or 443)
            add_certificate(session, add_name.value.strip(), add_host.value.strip(),
                           port=port, alert_days=add_alert.value)
            ui.notify("Certificate added!", type="positive")
            add_dialog.close()
            refresh_list()

        with ui.row().classes("justify-end gap-2 mt-3"):
            ui.button("Cancel", on_click=add_dialog.close).props("flat")
            ui.button("Save", on_click=save_new).props("color=primary")

    session.close()
