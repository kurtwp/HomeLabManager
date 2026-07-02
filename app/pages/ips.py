"""IP address listing and detail pages."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.models.ip_address import IPAddress, AssignmentType, IPStatus
from app.models.network import Network
from app.models.tag import Tag, ip_tags
from app.services.ip_service import create_ip, get_ips_for_network, get_ip_by_id, update_ip, delete_ip
from app.services.network_service import get_all_networks
from app.utils.formatters import format_timestamp
from app.pages.layout import page_layout


def render_ips():
    """Render the IP address list page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("IP Addresses").classes("text-3xl font-bold")
            with ui.row().classes("gap-2"):
                ui.button("Add IP", on_click=lambda: add_dialog.open()).props(
                    "color=primary icon=add"
                )
                ui.button("Delete All", on_click=lambda: confirm_delete_all()).props(
                    "color=red icon=delete_sweep outline"
                )

        ui.separator().classes("my-4")

        # Filter controls
        networks = get_all_networks(session)
        network_options = {0: "All Networks"}
        network_options.update({n.id: f"{n.name} ({n.cidr})" for n in networks})

        all_tags = session.query(Tag).order_by(Tag.name).all()
        tag_options = {0: "All Tags"}
        tag_options.update({t.id: t.name for t in all_tags})

        with ui.row().classes("w-full gap-2 items-center flex-wrap"):
            network_filter = ui.select(
                network_options, value=0, label="Network"
            ).classes("w-56")
            status_filter = ui.select(
                {"all": "All", "active": "Active", "inactive": "Inactive"},
                value="all",
                label="Status",
            ).classes("w-36")
            tag_filter = ui.select(
                tag_options, value=0, label="Tag"
            ).classes("w-44")
            ui.button("Filter", on_click=lambda: refresh_ips()).props("flat")

        # IP list
        ip_container = ui.column().classes("w-full mt-4 gap-1")

        def refresh_ips():
            ip_container.clear()
            with ip_container:
                query = session.query(IPAddress)
                if network_filter.value and network_filter.value != 0:
                    query = query.filter(IPAddress.network_id == network_filter.value)
                if status_filter.value != "all":
                    query = query.filter(
                        IPAddress.status == IPStatus(status_filter.value)
                    )
                if tag_filter.value and tag_filter.value != 0:
                    query = query.filter(
                        IPAddress.tags.any(Tag.id == tag_filter.value)
                    )
                ips = query.order_by(IPAddress.address).all()

                # Sort numerically by IP
                import ipaddress as _ipa
                ips.sort(key=lambda ip: _ipa.ip_address(ip.address))

                if not ips:
                    ui.label("No IP addresses found.").classes("text-gray-500")
                    return

                ui.label(f"{len(ips)} IPs").classes("text-sm text-gray-400 mb-1")

                for ip in ips:
                    with ui.card().classes("w-full"):
                        with ui.row().classes("w-full items-center justify-between"):
                            with ui.row().classes("items-center gap-3 cursor-pointer flex-1").on(
                                "click", lambda i=ip: ui.navigate.to(f"/ips/{i.id}")
                            ):
                                status_icon = "🟢" if ip.status == IPStatus.ACTIVE else "🔴" if ip.status == IPStatus.INACTIVE else "⚪"
                                ui.label(status_icon)
                                ui.label(ip.address).classes("font-mono font-semibold")
                                ui.label(ip.hostname or "—").classes("text-gray-500")
                                ui.badge(ip.assignment_type.value.upper()).props(
                                    f'color={"blue" if ip.assignment_type == AssignmentType.STATIC else "orange"} outline'
                                ).classes("text-xs")
                                # Source indicator
                                if ip.source:
                                    source_colors = {"unifi_client": "teal", "unifi_device": "purple", "nmap_scan": "green", "manual": "gray"}
                                    source_labels = {"unifi_client": "UniFi", "unifi_device": "Infra", "nmap_scan": "Nmap", "manual": "Manual"}
                                    ui.badge(source_labels.get(ip.source, ip.source)).props(
                                        f'color={source_colors.get(ip.source, "gray")} outline'
                                    ).classes("text-xs")
                                for tag in ip.tags:
                                    ui.html(
                                        f'<span style="font-size:0.65rem; padding:1px 8px; '
                                        f'border-radius:10px; background:{tag.color}20; '
                                        f'color:{tag.color}; border:1px solid {tag.color}40; '
                                        f'font-weight:500;">{tag.name}</span>'
                                    )

                            with ui.row().classes("items-center gap-2"):
                                ui.label(ip.network.name if ip.network else "").classes(
                                    "text-sm text-gray-400"
                                )
                                ui.label(format_timestamp(ip.last_seen)).classes(
                                    "text-xs text-gray-400"
                                )
                                ui.button(
                                    icon="delete",
                                    on_click=lambda i=ip: confirm_delete_ip(i),
                                ).props("flat round size=sm color=red")

        def confirm_delete_ip(ip):
            with ui.dialog() as dlg, ui.card():
                ui.label(f"Delete IP {ip.address}?").classes("text-lg font-semibold")
                if ip.hostname:
                    ui.label(f"Hostname: {ip.hostname}").classes("text-sm text-gray-500")
                with ui.row().classes("justify-end gap-2 mt-3"):
                    ui.button("Cancel", on_click=dlg.close).props("flat")
                    ui.button("Delete", on_click=lambda: (
                        delete_ip(session, ip.id),
                        dlg.close(),
                        refresh_ips(),
                        ui.notify(f"Deleted {ip.address}", type="warning"),
                    )).props("color=red")
            dlg.open()

        def confirm_delete_all():
            with ui.dialog() as dlg, ui.card():
                total = session.query(IPAddress).count()
                ui.label(f"Delete ALL {total} IP addresses?").classes("text-lg font-semibold")
                ui.label("This cannot be undone. Changelog history will be preserved.").classes(
                    "text-sm text-red"
                )
                with ui.row().classes("justify-end gap-2 mt-3"):
                    ui.button("Cancel", on_click=dlg.close).props("flat")
                    ui.button("Delete All", on_click=lambda: (
                        _delete_all_ips(),
                        dlg.close(),
                    )).props("color=red")
            dlg.open()

        def _delete_all_ips():
            count = session.query(IPAddress).count()
            session.query(IPAddress).delete()
            session.commit()
            refresh_ips()
            ui.notify(f"Deleted {count} IP addresses", type="warning")

        refresh_ips()

    # Add IP dialog
    with ui.dialog() as add_dialog, ui.card().classes("w-96"):
        ui.label("Add IP Address").classes("text-xl font-bold mb-2")

        net_options = {n.id: f"{n.name} ({n.cidr})" for n in networks}
        addr_input = ui.input("IP Address *", placeholder="e.g. 192.168.1.100").classes("w-full")
        net_select = ui.select(net_options, label="Network *").classes("w-full")
        host_input = ui.input("Hostname", placeholder="e.g. my-server").classes("w-full")
        mac_input = ui.input("MAC Address", placeholder="AA:BB:CC:DD:EE:FF").classes("w-full")
        type_select = ui.select(
            {t.value: t.value.upper() for t in AssignmentType},
            value=AssignmentType.STATIC.value,
            label="Assignment Type",
        ).classes("w-full")
        notes_input = ui.textarea("Notes (markdown)").classes("w-full")

        def save_ip():
            if not addr_input.value or not net_select.value:
                ui.notify("IP address and network are required", type="warning")
                return
            try:
                create_ip(
                    session,
                    address=addr_input.value,
                    network_id=net_select.value,
                    hostname=host_input.value or None,
                    mac_address=mac_input.value or None,
                    assignment_type=AssignmentType(type_select.value),
                    notes=notes_input.value or None,
                )
                ui.notify("IP added!", type="positive")
                add_dialog.close()
                refresh_ips()
            except Exception as e:
                ui.notify(f"Error: {e}", type="negative")

        with ui.row().classes("justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=add_dialog.close).props("flat")
            ui.button("Save", on_click=save_ip).props("color=primary")

    session.close()


def render_ip_detail(ip_id: int):
    """Render a single IP's detail page with notes editor."""
    page_layout()

    session = get_session()
    ip = get_ip_by_id(session, ip_id)

    if not ip:
        with ui.column().classes("page-container"):
            ui.label("IP not found").classes("text-xl text-red")
        session.close()
        return

    from app.pages.tag_assignment import render_tag_assignment

    with ui.column().classes("page-container w-full"):
        # Header
        with ui.row().classes("items-center gap-4"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/ips")).props(
                "flat round"
            )
            ui.label(ip.address).classes("text-3xl font-bold font-mono")
            status_color = "green" if ip.status == IPStatus.ACTIVE else "red"
            ui.badge(ip.status.value.upper()).props(f"color={status_color}")
            ui.badge(ip.assignment_type.value.upper()).props("color=blue outline")

            def do_delete():
                delete_ip(session, ip.id)
                ui.notify(f"Deleted {ip.address}", type="warning")
                ui.navigate.to("/ips")

            ui.button("Delete", icon="delete", on_click=do_delete).props(
                "color=red outline size=sm"
            )

        ui.separator().classes("my-4")

        with ui.row().classes("w-full gap-4 flex-wrap"):
            # Info panel
            with ui.card().classes("w-80"):
                ui.label("Details").classes("text-lg font-semibold mb-2")
                ui.label(f"Hostname: {ip.hostname or '—'}")
                ui.label(f"MAC: {ip.mac_address or '—'}")
                ui.label(f"Network: {ip.network.name if ip.network else '—'}")
                ui.label(f"Last Seen: {format_timestamp(ip.last_seen)}")
                ui.label(f"Created: {format_timestamp(ip.created_at)}")
                if ip.device:
                    ui.label(f"Device: {ip.device.name}")

                # Device type selector
                ui.separator().classes("my-2")
                ui.label("Device Type").classes("text-sm font-semibold")

                from app.models.device import Device, DeviceType
                from app.services.device_service import get_all_device_types

                all_types = get_all_device_types(session)
                type_options = {0: "— Not Set —"}
                type_options.update({dt.id: dt.name for dt in all_types})

                # Get current type from linked device, or None
                current_type_id = 0
                if ip.device and ip.device.device_type_id:
                    current_type_id = ip.device.device_type_id

                device_type_select = ui.select(
                    type_options, value=current_type_id, label="Type"
                ).classes("w-full")

                def save_device_type():
                    # Use a fresh session for the save operation
                    from app.database.db import get_session_direct
                    save_session = get_session_direct()

                    new_type_id = device_type_select.value if device_type_select.value != 0 else None

                    # Re-fetch the IP in this session
                    save_ip = save_session.query(IPAddress).filter(IPAddress.id == ip.id).first()
                    if not save_ip:
                        ui.notify("IP not found", type="negative")
                        save_session.close()
                        return

                    if save_ip.device_id:
                        # Update existing device's type
                        dev = save_session.query(Device).filter(Device.id == save_ip.device_id).first()
                        if dev:
                            dev.device_type_id = new_type_id
                    else:
                        # Check if a device with this MAC or hostname already exists
                        existing_dev = None
                        if save_ip.mac_address:
                            mac_norm = save_ip.mac_address.replace(":", "").replace("-", "").upper()
                            for d in save_session.query(Device).all():
                                if d.mac_address:
                                    d_mac = d.mac_address.replace(":", "").replace("-", "").upper()
                                    if d_mac == mac_norm:
                                        existing_dev = d
                                        break
                        if not existing_dev and save_ip.hostname:
                            existing_dev = save_session.query(Device).filter(
                                Device.name == save_ip.hostname
                            ).first()

                        if existing_dev:
                            existing_dev.device_type_id = new_type_id
                            save_ip.device_id = existing_dev.id
                        else:
                            new_dev = Device(
                                name=save_ip.hostname or save_ip.address,
                                device_type_id=new_type_id,
                                mac_address=save_ip.mac_address,
                            )
                            save_session.add(new_dev)
                            save_session.flush()
                            save_ip.device_id = new_dev.id

                    save_session.commit()
                    save_session.close()
                    ui.notify("Device type saved!", type="positive")

                ui.button("Save Type", on_click=save_device_type).props(
                    "color=primary size=sm"
                ).classes("mt-1")

            # Notes editor
            with ui.card().classes("flex-1 min-w-[400px]"):
                ui.label("Notes (Markdown)").classes("text-lg font-semibold mb-2")

                with ui.tabs().classes("w-full") as tabs:
                    edit_tab = ui.tab("Edit")
                    preview_tab = ui.tab("Preview")

                with ui.tab_panels(tabs, value=preview_tab).classes("w-full"):
                    with ui.tab_panel(edit_tab):
                        notes_editor = ui.textarea(
                            value=ip.notes or ""
                        ).classes("w-full").props('rows="12"')

                        def save_notes():
                            update_ip(session, ip.id, notes=notes_editor.value)
                            ui.notify("Notes saved!", type="positive")

                        ui.button("Save Notes", on_click=save_notes).props(
                            "color=primary"
                        )

                    with ui.tab_panel(preview_tab):
                        ui.markdown(ip.notes or "*No notes yet*").classes("w-full")

        # Tags
        render_tag_assignment(session, ip)

    session.close()
