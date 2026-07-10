"""Uptime Monitoring page — manage monitored hosts and view status."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.services.uptime_service import (
    add_monitor,
    remove_monitor,
    update_monitor,
    get_all_monitors,
    get_events_for_host,
    check_host,
)
from app.services.oui_service import lookup_manufacturer
from app.pages.layout import page_layout


def render_uptime():
    """Render the uptime monitoring page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Uptime Monitoring").classes("text-3xl font-bold")
            ui.button("Add Host", icon="add", on_click=lambda: add_dialog.open()).props(
                "color=primary"
            )

        ui.label("Monitor critical hosts — get alerted when they go down.").classes(
            "text-gray-500 mb-4"
        )

        ui.separator()

        # Status overview
        monitors_container = ui.column().classes("w-full mt-4 gap-3")

        # Filter state: None = show all, "up" = only up, "down" = only down
        active_filter = {"status": None}

        def set_filter(status: str | None):
            """Toggle filter — clicking the same badge again clears it."""
            if active_filter["status"] == status:
                active_filter["status"] = None
            else:
                active_filter["status"] = status
            refresh_monitors()

        def refresh_monitors():
            monitors_container.clear()
            monitors = get_all_monitors(session)
            with monitors_container:
                if not monitors:
                    ui.label("No hosts being monitored. Click 'Add Host' to start.").classes(
                        "text-gray-500 italic"
                    )
                    return

                # Summary
                up_count = sum(1 for m in monitors if m.current_status == "up")
                down_count = sum(1 for m in monitors if m.current_status == "down")
                unknown_count = sum(1 for m in monitors if m.current_status == "unknown")

                with ui.row().classes("gap-4 mb-4 items-center"):
                    # Up badge — clickable filter
                    up_badge = ui.badge(f"🟢 {up_count} Up").props("color=green")
                    up_badge.classes("cursor-pointer")
                    if active_filter["status"] == "up":
                        up_badge.props("outline")
                    up_badge.on("click", lambda: set_filter("up"))
                    up_badge.tooltip("Click to filter — show only UP hosts")

                    # Down badge — clickable filter
                    if down_count:
                        down_badge = ui.badge(f"🔴 {down_count} Down").props("color=red")
                        down_badge.classes("cursor-pointer")
                        if active_filter["status"] == "down":
                            down_badge.props("outline")
                        down_badge.on("click", lambda: set_filter("down"))
                        down_badge.tooltip("Click to filter — show only DOWN hosts")

                    if unknown_count:
                        ui.badge(f"⚪ {unknown_count} Unknown").props("color=gray")

                    # Show active filter indicator
                    if active_filter["status"]:
                        ui.label(
                            f"Showing: {active_filter['status'].upper()} only"
                        ).classes("text-sm text-gray-500 italic ml-2")
                        ui.button(
                            "Show All", on_click=lambda: set_filter(None)
                        ).props("flat dense size=sm color=primary")

                # Apply filter
                filtered = monitors
                if active_filter["status"]:
                    filtered = [m for m in monitors if m.current_status == active_filter["status"]]

                if not filtered:
                    ui.label(
                        f"No hosts with status '{active_filter['status'].upper()}'."
                    ).classes("text-gray-500 italic")
                    return

                # Host cards
                for host in filtered:
                    status_color = {"up": "green", "down": "red", "unknown": "gray"}.get(
                        host.current_status, "gray"
                    )
                    status_icon = {"up": "check_circle", "down": "cancel", "unknown": "help"}.get(
                        host.current_status, "help"
                    )

                    with ui.card().classes("w-full"):
                        with ui.row().classes("w-full items-center justify-between"):
                            with ui.row().classes("items-center gap-3"):
                                ui.icon(status_icon).classes(f"text-2xl text-{status_color}")
                                with ui.column().classes("gap-0"):
                                    ui.label(host.name).classes("font-semibold text-lg")
                                    ui.label(host.ip_address).classes("text-sm font-mono text-gray-500")
                                ui.badge(host.current_status.upper()).props(f"color={status_color}")
                                ui.badge(f"{host.uptime_percent}% uptime").props("color=blue outline")

                            with ui.row().classes("items-center gap-4"):
                                ui.label(f"Checks: {host.total_checks}").classes("text-xs text-gray-400")
                                ui.label(
                                    f"Last: {host.last_check.strftime('%H:%M:%S') if host.last_check else 'Never'}"
                                ).classes("text-xs text-gray-400")
                                ui.label(f"Every {host.check_interval}s").classes("text-xs text-gray-400")

                                # Quick check button
                                def do_quick_check(h=host):
                                    is_up, latency = check_host(h.ip_address)
                                    status = "UP" if is_up else "DOWN"
                                    lat_str = f" ({latency:.1f}ms)" if latency else ""
                                    ui.notify(f"{h.name}: {status}{lat_str}", type="positive" if is_up else "negative")

                                ui.button(icon="refresh", on_click=do_quick_check).props(
                                    "flat round size=sm"
                                ).tooltip("Quick check now")

                                ui.button(
                                    icon="edit",
                                    on_click=lambda h=host: open_edit_dialog(h),
                                ).props("flat round size=sm color=blue").tooltip("Edit monitor")

                                ui.button(
                                    icon="delete",
                                    on_click=lambda h=host: confirm_remove(h),
                                ).props("flat round size=sm color=red")

                        # Events (collapsible)
                        events = get_events_for_host(session, host.id, limit=10)
                        if events:
                            with ui.expansion("Recent Events", icon="history").classes("w-full mt-2"):
                                for event in events:
                                    ev_color = {"down": "red", "recovered": "green", "up": "green"}.get(
                                        event.event_type, "gray"
                                    )
                                    with ui.row().classes("items-center gap-2"):
                                        ui.icon("circle").classes(f"text-xs text-{ev_color}")
                                        ui.label(
                                            f"{event.timestamp.strftime('%Y-%m-%d %H:%M:%S') if event.timestamp else '—'}"
                                        ).classes("text-xs text-gray-400")
                                        ui.label(event.event_type.upper()).classes(f"text-xs font-bold text-{ev_color}")
                                        if event.details:
                                            ui.label(event.details).classes("text-xs text-gray-500")
                                        if event.latency_ms:
                                            ui.label(f"{event.latency_ms:.1f}ms").classes("text-xs text-gray-400")

        def open_edit_dialog(host):
            with ui.dialog() as edit_dlg, ui.card().classes("w-96"):
                ui.label(f"Edit Monitor: {host.name}").classes("text-xl font-bold mb-2")
                edit_name = ui.input("Name *", value=host.name).classes("w-full")
                edit_ip = ui.input("IP Address *", value=host.ip_address).classes("w-full")
                edit_interval = ui.select(
                    {30: "Every 30 seconds", 60: "Every minute", 120: "Every 2 minutes", 300: "Every 5 minutes"},
                    value=host.check_interval, label="Check Interval",
                ).classes("w-full")
                edit_enabled = ui.switch("Enabled", value=host.is_enabled)

                def save_edit():
                    if not edit_name.value or not edit_ip.value:
                        ui.notify("Name and IP are required", type="warning")
                        return
                    update_monitor(
                        session,
                        host.id,
                        name=edit_name.value.strip(),
                        ip_address=edit_ip.value.strip(),
                        check_interval=edit_interval.value,
                        is_enabled=edit_enabled.value,
                    )
                    ui.notify(f"Updated '{edit_name.value}'", type="positive")
                    edit_dlg.close()
                    refresh_monitors()

                with ui.row().classes("justify-end gap-2 mt-2"):
                    ui.button("Cancel", on_click=edit_dlg.close).props("flat")
                    ui.button("Save", on_click=save_edit).props("color=primary")
            edit_dlg.open()

        def confirm_remove(host):
            with ui.dialog() as dlg, ui.card():
                ui.label(f"Stop monitoring '{host.name}' ({host.ip_address})?").classes("text-lg")
                with ui.row().classes("justify-end gap-2 mt-2"):
                    ui.button("Cancel", on_click=dlg.close).props("flat")
                    ui.button("Remove", on_click=lambda: (
                        remove_monitor(session, host.id),
                        dlg.close(),
                        refresh_monitors(),
                        ui.notify("Monitor removed", type="warning"),
                    )).props("color=red")
            dlg.open()

        refresh_monitors()

    # Add host dialog
    with ui.dialog() as add_dialog, ui.card().classes("w-96"):
        ui.label("Add Monitored Host").classes("text-xl font-bold mb-2")
        add_name = ui.input("Name *", placeholder="e.g. Main Server").classes("w-full")
        add_ip = ui.input("IP Address *", placeholder="192.168.2.5").classes("w-full")
        add_interval = ui.select(
            {30: "Every 30 seconds", 60: "Every minute", 120: "Every 2 minutes", 300: "Every 5 minutes"},
            value=60, label="Check Interval",
        ).classes("w-full")

        def save_new_monitor():
            if not add_name.value or not add_ip.value:
                ui.notify("Name and IP are required", type="warning")
                return
            # Check for duplicate
            existing = session.query(
                __import__('app.models.uptime_monitor', fromlist=['MonitoredHost']).MonitoredHost
            ).filter_by(ip_address=add_ip.value.strip()).first()
            if existing:
                ui.notify("This IP is already being monitored", type="negative")
                return
            add_monitor(session, add_ip.value.strip(), add_name.value.strip(), add_interval.value)
            ui.notify("Monitor added!", type="positive")
            add_dialog.close()
            refresh_monitors()

        with ui.row().classes("justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=add_dialog.close).props("flat")
            ui.button("Save", on_click=save_new_monitor).props("color=primary")

    session.close()
