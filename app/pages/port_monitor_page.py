"""Port Monitoring page — manage TCP port monitors and view status."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.services.uptime_service import (
    add_monitor,
    remove_monitor,
    update_monitor,
    get_all_monitors,
    check_port,
)
from app.pages.layout import page_layout


def render_port_monitor():
    """Render the port monitoring page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Port Monitoring").classes("text-3xl font-bold")
            ui.button("Add Port Monitor", icon="add", on_click=lambda: add_dialog.open()).props(
                "color=primary"
            )

        ui.label("Monitor TCP services — check that specific ports are responding.").classes(
            "text-gray-500 mb-4"
        )

        ui.separator()

        # Status overview
        monitors_container = ui.column().classes("w-full mt-4 gap-3")

        def refresh_monitors():
            monitors_container.clear()
            all_monitors = get_all_monitors(session)
            # Only show port monitors
            monitors = [m for m in all_monitors if (getattr(m, 'monitor_type', 'ping') or 'ping') == 'port']

            with monitors_container:
                if not monitors:
                    ui.label("No port monitors configured. Click 'Add Port Monitor' to start.").classes(
                        "text-gray-500 italic"
                    )
                    return

                # Summary
                up_count = sum(1 for m in monitors if m.current_status == "up")
                down_count = sum(1 for m in monitors if m.current_status == "down")
                unknown_count = sum(1 for m in monitors if m.current_status == "unknown")

                with ui.row().classes("gap-4 mb-4 items-center"):
                    ui.badge(f"🟢 {up_count} Up").props("color=green")
                    if down_count:
                        ui.badge(f"🔴 {down_count} Down").props("color=red")
                    if unknown_count:
                        ui.badge(f"⚪ {unknown_count} Unknown").props("color=gray")
                    ui.label(f"{len(monitors)} services monitored").classes(
                        "text-sm text-gray-500"
                    )

                # Host cards
                for host in monitors:
                    status_color = {"up": "green", "down": "red", "unknown": "gray"}.get(
                        host.current_status, "gray"
                    )
                    status_icon = {"up": "check_circle", "down": "cancel", "unknown": "help"}.get(
                        host.current_status, "help"
                    )
                    port = getattr(host, 'port', None) or '?'

                    with ui.card().classes("w-full"):
                        with ui.row().classes("w-full items-center justify-between"):
                            with ui.row().classes("items-center gap-3 cursor-pointer").on(
                                "click", lambda h=host: ui.navigate.to(f"/uptime/{h.id}")
                            ):
                                ui.icon(status_icon).classes(f"text-2xl text-{status_color}")
                                with ui.column().classes("gap-0"):
                                    ui.label(host.name).classes("font-semibold text-lg")
                                    ui.label(f"{host.ip_address}:{port}").classes("text-sm font-mono text-gray-500")
                                ui.badge(host.current_status.upper()).props(f"color={status_color}")
                                ui.badge(f":{port}").props("color=teal outline")
                                ui.badge(f"{host.uptime_percent}% uptime").props("color=blue outline")

                            with ui.row().classes("items-center gap-4"):
                                ui.label(f"Checks: {host.total_checks}").classes("text-xs text-gray-400")
                                ui.label(
                                    f"Last: {host.last_check.strftime('%H:%M:%S') if host.last_check else 'Never'}"
                                ).classes("text-xs text-gray-400")
                                ui.label(f"Every {host.check_interval}s").classes("text-xs text-gray-400")

                                # Quick check button
                                def do_quick_check(h=host):
                                    p = getattr(h, 'port', None) or 80
                                    is_up, latency = check_port(h.ip_address, p)
                                    status = "OPEN" if is_up else "CLOSED"
                                    lat_str = f" ({latency:.1f}ms)" if latency else ""
                                    ui.notify(
                                        f"{h.name} :{p} — {status}{lat_str}",
                                        type="positive" if is_up else "negative",
                                    )

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

        def open_edit_dialog(host):
            with ui.dialog() as edit_dlg, ui.card().classes("w-[450px]"):
                ui.label(f"Edit: {host.name}").classes("text-xl font-bold mb-2")
                edit_name = ui.input("Name *", value=host.name).classes("w-full")
                edit_ip = ui.input("IP Address *", value=host.ip_address).classes("w-full")
                edit_port = ui.input("TCP Port *", value=str(getattr(host, 'port', '') or '')).classes("w-full")
                edit_interval = ui.select(
                    {20: "20 seconds", 30: "30 seconds", 60: "60 seconds", 120: "2 minutes", 300: "5 minutes"},
                    value=host.check_interval, label="Check Interval",
                ).classes("w-full")
                edit_retries = ui.select(
                    {1: "1 retry", 2: "2 retries", 3: "3 retries", 4: "4 retries", 5: "5 retries"},
                    value=getattr(host, 'max_retries', 3) or 3, label="Retries",
                ).classes("w-full")
                edit_retry_interval = ui.select(
                    {5: "5 seconds", 10: "10 seconds", 20: "20 seconds", 30: "30 seconds", 60: "60 seconds"},
                    value=getattr(host, 'retry_interval', 30) or 30, label="Retry Interval",
                ).classes("w-full")
                edit_enabled = ui.switch("Enabled", value=host.is_enabled)

                def save_edit():
                    if not edit_name.value or not edit_ip.value or not edit_port.value:
                        ui.notify("Name, IP, and Port are required", type="warning")
                        return
                    update_monitor(
                        session, host.id,
                        name=edit_name.value.strip(),
                        ip_address=edit_ip.value.strip(),
                        port=int(edit_port.value),
                        check_interval=edit_interval.value,
                        max_retries=edit_retries.value,
                        retry_interval=edit_retry_interval.value,
                        is_enabled=edit_enabled.value,
                        monitor_type="port",
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
                port = getattr(host, 'port', '?')
                ui.label(f"Stop monitoring '{host.name}' ({host.ip_address}:{port})?").classes("text-lg")
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

    # Add port monitor dialog
    with ui.dialog() as add_dialog, ui.card().classes("w-[450px]"):
        ui.label("Add Port Monitor").classes("text-xl font-bold mb-2")
        add_name = ui.input("Name *", placeholder="e.g. Web Server HTTP").classes("w-full")
        add_ip = ui.input("IP Address *", placeholder="192.168.2.5").classes("w-full")
        add_port = ui.input("TCP Port *", placeholder="e.g. 443").classes("w-full")

        # Port shortcuts
        ui.label("Common Ports").classes("text-xs text-gray-400 mt-1")
        with ui.row().classes("gap-1 flex-wrap"):
            for p, label in [(80, "HTTP"), (443, "HTTPS"), (22, "SSH"), (53, "DNS"),
                             (3389, "RDP"), (8080, "Alt HTTP"), (21, "FTP"), (25, "SMTP"),
                             (3306, "MySQL"), (5432, "Postgres"), (6379, "Redis"), (8443, "UniFi")]:
                ui.button(f"{label}:{p}", on_click=lambda port=p: setattr(add_port, 'value', str(port))).props(
                    "flat dense size=xs"
                )

        ui.separator().classes("my-2")

        add_interval = ui.select(
            {30: "30 seconds", 60: "60 seconds", 120: "2 minutes", 300: "5 minutes"},
            value=60, label="Check Interval",
        ).classes("w-full")
        add_retries = ui.select(
            {1: "1 retry", 2: "2 retries", 3: "3 retries", 4: "4 retries", 5: "5 retries"},
            value=3, label="Retries before Alert",
        ).classes("w-full")
        add_retry_interval = ui.select(
            {5: "5 seconds", 10: "10 seconds", 20: "20 seconds", 30: "30 seconds", 60: "60 seconds"},
            value=30, label="Retry Interval",
        ).classes("w-full")

        def save_new():
            if not add_name.value or not add_ip.value or not add_port.value:
                ui.notify("Name, IP, and Port are required", type="warning")
                return
            try:
                port_val = int(add_port.value)
            except ValueError:
                ui.notify("Port must be a number", type="warning")
                return

            # Check for duplicate (same IP + same port)
            from app.models.uptime_monitor import MonitoredHost as MH
            existing = session.query(MH).filter_by(
                ip_address=add_ip.value.strip(), monitor_type="port", port=port_val
            ).first()
            if existing:
                ui.notify(f"Port :{port_val} on {add_ip.value} is already monitored", type="negative")
                return

            add_monitor(
                session, add_ip.value.strip(), add_name.value.strip(),
                check_interval=add_interval.value,
                max_retries=add_retries.value,
                retry_interval=add_retry_interval.value,
                monitor_type="port",
                port=port_val,
            )
            ui.notify("Port monitor added!", type="positive")
            add_dialog.close()
            refresh_monitors()

        with ui.row().classes("justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=add_dialog.close).props("flat")
            ui.button("Save", on_click=save_new).props("color=primary")

    session.close()
