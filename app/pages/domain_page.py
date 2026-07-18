"""Domain Tracker page — monitor domain registration expiry dates."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.services.domain_service import (
    get_all_domains,
    add_domain,
    remove_domain,
    refresh_domain,
    refresh_all_domains,
    whois_lookup,
)
from app.pages.layout import page_layout


def render_domain_tracker():
    """Render the domain tracker page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Domain Tracker").classes("text-3xl font-bold")
            with ui.row().classes("gap-2"):
                ui.button("Add Domain", icon="add", on_click=lambda: add_dialog.open()).props(
                    "color=primary"
                )
                ui.button("Check All", icon="refresh", on_click=lambda: do_check_all()).props(
                    "color=blue outline"
                )

        ui.label(
            "Track domain registration expiry dates. Get alerted before they lapse."
        ).classes("text-gray-500 mb-4")

        ui.separator()

        domains_container = ui.column().classes("w-full mt-4 gap-3")

        def do_check_all():
            ui.notify("Checking all domains...", type="info")
            result = refresh_all_domains()
            ui.notify(
                f"Checked {result['checked']}: {result['expiring']} expiring, "
                f"{result['expired']} expired, {result['errors']} errors",
                type="positive" if result["expired"] == 0 else "warning",
            )
            refresh_list()

        def refresh_list():
            domains_container.clear()
            domains = get_all_domains(session)

            with domains_container:
                if not domains:
                    ui.label("No domains being tracked. Click 'Add Domain' to start.").classes(
                        "text-gray-500 italic"
                    )
                    return

                # Summary
                valid_count = sum(1 for d in domains if d.days_remaining and d.days_remaining > 30)
                expiring_count = sum(1 for d in domains if d.days_remaining and 0 < d.days_remaining <= 30)
                expired_count = sum(1 for d in domains if d.days_remaining is not None and d.days_remaining <= 0)

                with ui.row().classes("gap-4 mb-4"):
                    if valid_count:
                        ui.badge(f"✅ {valid_count} Valid").props("color=green")
                    if expiring_count:
                        ui.badge(f"⚠️ {expiring_count} Expiring Soon").props("color=orange")
                    if expired_count:
                        ui.badge(f"❌ {expired_count} Expired").props("color=red")

                for entry in domains:
                    # Status
                    if entry.last_error:
                        status_color = "red"
                        status_icon = "error"
                        status_text = "Error"
                    elif entry.days_remaining is None:
                        status_color = "gray"
                        status_icon = "help"
                        status_text = "Not checked"
                    elif entry.days_remaining <= 0:
                        status_color = "red"
                        status_icon = "cancel"
                        status_text = "EXPIRED"
                    elif entry.days_remaining <= 7:
                        status_color = "red"
                        status_icon = "warning"
                        status_text = f"{entry.days_remaining}d left"
                    elif entry.days_remaining <= 30:
                        status_color = "orange"
                        status_icon = "schedule"
                        status_text = f"{entry.days_remaining}d left"
                    else:
                        status_color = "green"
                        status_icon = "verified"
                        status_text = f"{entry.days_remaining}d left"

                    with ui.card().classes("w-full"):
                        with ui.row().classes("w-full items-center justify-between"):
                            with ui.row().classes("items-center gap-3"):
                                ui.icon(status_icon).classes(f"text-2xl text-{status_color}")
                                with ui.column().classes("gap-0"):
                                    ui.label(entry.domain).classes("font-semibold text-lg font-mono")
                                    if entry.registrar:
                                        ui.label(f"Registrar: {entry.registrar}").classes("text-xs text-gray-400")
                                ui.badge(status_text).props(f"color={status_color}")
                                if entry.auto_renew:
                                    ui.badge("Auto-Renew").props("color=blue outline").classes("text-xs")

                            with ui.row().classes("items-center gap-3"):
                                if entry.expiry_date:
                                    ui.label(
                                        f"Expires: {entry.expiry_date.strftime('%Y-%m-%d')}"
                                    ).classes("text-xs text-gray-400")
                                if entry.last_checked:
                                    ui.label(
                                        f"Checked: {entry.last_checked.strftime('%m-%d %H:%M')}"
                                    ).classes("text-xs text-gray-400")

                                ui.button(
                                    icon="refresh",
                                    on_click=lambda d=entry: do_refresh_one(d.id),
                                ).props("flat round size=sm").tooltip("Check now")
                                ui.button(
                                    icon="delete",
                                    on_click=lambda d=entry: confirm_delete(d),
                                ).props("flat round size=sm color=red")

                        # Details
                        if entry.name_servers:
                            ui.label(f"NS: {entry.name_servers}").classes("text-xs text-gray-400 mt-1")
                        if entry.notes:
                            ui.label(f"Notes: {entry.notes}").classes("text-xs text-gray-500 mt-1")
                        if entry.last_error:
                            ui.label(f"Error: {entry.last_error}").classes("text-xs text-red mt-1")

        def do_refresh_one(domain_id):
            result = refresh_domain(session, domain_id)
            if result["success"]:
                ui.notify(f"Domain OK — {result['days_remaining']} days remaining", type="positive")
            else:
                ui.notify(f"Check failed: {result['error']}", type="negative")
            refresh_list()

        def confirm_delete(entry):
            with ui.dialog() as dlg, ui.card():
                ui.label(f"Stop tracking '{entry.domain}'?").classes("text-lg")
                with ui.row().classes("justify-end gap-2 mt-2"):
                    ui.button("Cancel", on_click=dlg.close).props("flat")
                    ui.button("Remove", on_click=lambda: (
                        remove_domain(session, entry.id),
                        dlg.close(),
                        refresh_list(),
                        ui.notify("Domain removed", type="warning"),
                    )).props("color=red")
            dlg.open()

        refresh_list()

    # Add domain dialog
    with ui.dialog() as add_dialog, ui.card().classes("w-[450px]"):
        ui.label("Add Domain").classes("text-xl font-bold mb-2")
        add_domain_input = ui.input("Domain *", placeholder="e.g. example.com").classes("w-full")
        add_alert = ui.select(
            {7: "7 days", 14: "14 days", 30: "30 days", 60: "60 days", 90: "90 days"},
            value=30, label="Alert when fewer than",
        ).classes("w-full")
        add_auto_renew = ui.switch("Auto-Renew enabled at registrar")
        add_notes = ui.input("Notes (optional)", placeholder="e.g. GoDaddy account").classes("w-full")

        # Quick test
        test_result = ui.label("").classes("text-sm mt-2")

        def test_domain():
            if not add_domain_input.value:
                ui.notify("Enter a domain", type="warning")
                return
            test_result.text = "Checking..."
            result = whois_lookup(add_domain_input.value.strip())
            if result["success"]:
                test_result.text = (
                    f"✅ Expires: {result['expiry_date'].strftime('%Y-%m-%d')} "
                    f"({result['days_remaining']} days) — "
                    f"Registrar: {result['registrar'] or '?'}"
                )
                test_result.classes(remove="text-red", add="text-green")
            else:
                test_result.text = f"❌ {result['error']}"
                test_result.classes(remove="text-green", add="text-red")

        ui.button("Test WHOIS Lookup", icon="search", on_click=test_domain).props(
            "flat size=sm color=blue"
        )

        def save_new():
            if not add_domain_input.value:
                ui.notify("Domain is required", type="warning")
                return
            add_domain(session, add_domain_input.value.strip(),
                      alert_days=add_alert.value,
                      auto_renew=add_auto_renew.value,
                      notes=add_notes.value.strip() or None)
            ui.notify("Domain added!", type="positive")
            add_dialog.close()
            refresh_list()

        with ui.row().classes("justify-end gap-2 mt-3"):
            ui.button("Cancel", on_click=add_dialog.close).props("flat")
            ui.button("Save", on_click=save_new).props("color=primary")

    session.close()
