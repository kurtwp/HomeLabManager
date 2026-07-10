"""Phone Numbers page — list, add, edit, delete with filters."""

import re
from nicegui import ui

from app.database.pstn_db import get_pstn_session_direct as get_session
from app.models.pstn.phone_number import PhoneNumber
from app.models.pstn.number_range import NumberRange
from app.services.pstn_service import (
    create_phone_number,
    get_all_phone_numbers,
    get_phone_number_by_id,
    update_phone_number,
    delete_phone_number,
    get_all_ranges,
    get_all_customers,
    search_numbers,
)
from app.pages.layout import page_layout


NUMBER_TYPES = {"did": "DID", "extension": "Extension", "toll_free": "Toll-Free", "fax": "Fax", "other": "Other"}
STATUSES = {"active": "Active", "inactive": "Inactive", "reserved": "Reserved", "future_use": "Future Use"}
STATUS_COLORS = {"active": "green", "inactive": "gray", "reserved": "orange", "future_use": "blue"}


def render_numbers():
    """Render the Phone Numbers page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Phone Numbers").classes("text-3xl font-bold")
            with ui.row().classes("gap-2"):
                ui.button("Add Number", icon="add", on_click=lambda: add_dialog.open()).props(
                    "color=primary"
                )
                ui.button("Delete All", icon="delete_sweep", on_click=lambda: _confirm_delete_all_numbers()).props(
                    "color=red outline"
                )

        ui.separator().classes("my-4")

        # Filters row
        ranges = get_all_ranges(session)
        range_options = {0: "All Ranges"}
        range_options.update({r.id: r.name for r in ranges})

        customers = get_all_customers(session)
        customer_options = {0: "All Customers"}
        customer_options.update({c.id: c.name for c in customers})

        with ui.row().classes("w-full gap-3 items-end flex-wrap"):
            filter_search = ui.input("Search", placeholder="Number, name, dept...").classes("w-52")
            filter_type = ui.select(
                {"": "All Types", **NUMBER_TYPES}, value="", label="Type"
            ).classes("w-36")
            filter_status = ui.select(
                {"": "All Statuses", **STATUSES}, value="", label="Status"
            ).classes("w-36")
            filter_range = ui.select(range_options, value=0, label="Range").classes("w-44")
            filter_customer = ui.select(customer_options, value=0, label="Customer").classes("w-44")
            ui.button("Filter", icon="filter_list", on_click=lambda: refresh_numbers()).props(
                "flat color=primary"
            )

        numbers_container = ui.column().classes("w-full mt-4")

        def _confirm_delete_all_numbers():
            with ui.dialog() as dlg, ui.card():
                total = session.query(PhoneNumber).count()
                ui.label(f"Delete ALL {total} phone numbers?").classes("text-lg font-semibold")
                ui.label("This cannot be undone.").classes("text-sm text-red")
                with ui.row().classes("justify-end gap-2 mt-3"):
                    ui.button("Cancel", on_click=dlg.close).props("flat")
                    ui.button("Delete All", on_click=lambda: (
                        session.query(PhoneNumber).delete(),
                        session.commit(),
                        dlg.close(),
                        refresh_numbers(),
                        ui.notify(f"Deleted {total} numbers", type="warning"),
                    )).props("color=red")
            dlg.open()

        def refresh_numbers():
            numbers_container.clear()

            # Determine query
            if filter_search.value:
                all_numbers = search_numbers(session, filter_search.value)
            else:
                all_numbers = get_all_phone_numbers(session)

            # Apply filters
            filtered = all_numbers
            if filter_type.value:
                filtered = [n for n in filtered if n.number_type == filter_type.value]
            if filter_status.value:
                filtered = [n for n in filtered if n.status == filter_status.value]
            if filter_range.value:
                filtered = [n for n in filtered if n.range_id == filter_range.value]
            if filter_customer.value:
                filtered = [n for n in filtered if n.customer_id == filter_customer.value]

            # Natural sort
            def natural_key(pn):
                return [
                    int(c) if c.isdigit() else c.lower()
                    for c in re.split(r"(\d+)", pn.number)
                ]

            filtered.sort(key=natural_key)

            with numbers_container:
                if not filtered:
                    ui.label("No numbers found.").classes("text-gray-500 italic")
                    return

                ui.label(f"{len(filtered)} numbers").classes("text-sm text-gray-400 mb-2")

                columns = [
                    {"name": "number", "label": "Number", "field": "number", "align": "left", "sortable": True},
                    {"name": "extension", "label": "Ext", "field": "extension", "align": "left"},
                    {"name": "type", "label": "Type", "field": "type", "align": "center"},
                    {"name": "status", "label": "Status", "field": "status", "align": "center"},
                    {"name": "customer", "label": "Customer", "field": "customer", "align": "left"},
                    {"name": "assigned_to", "label": "Assigned To", "field": "assigned_to", "align": "left"},
                    {"name": "department", "label": "Department", "field": "department", "align": "left"},
                    {"name": "location", "label": "Location", "field": "location", "align": "left"},
                    {"name": "device_name", "label": "Device", "field": "device_name", "align": "left"},
                    {"name": "description", "label": "Description", "field": "description", "align": "left"},
                    {"name": "actions", "label": "Actions", "field": "actions", "align": "center"},
                ]

                # Build a customer lookup
                cust_lookup = {c.id: c.name for c in customers}

                rows = [
                    {
                        "id": pn.id,
                        "number": pn.number,
                        "extension": pn.extension or "—",
                        "type": NUMBER_TYPES.get(pn.number_type, pn.number_type),
                        "status": pn.status,
                        "customer": cust_lookup.get(pn.customer_id, "—") if pn.customer_id else "—",
                        "assigned_to": pn.assigned_to or "—",
                        "department": pn.department or "—",
                        "location": pn.location or "—",
                        "device_name": pn.device_name or "—",
                        "description": (pn.description or "—")[:40],
                    }
                    for pn in filtered
                ]

                table = ui.table(
                    columns=columns, rows=rows, row_key="id"
                ).classes("w-full").props("flat bordered dense")

                # Custom body slot for status badges and actions
                table.add_slot(
                    "body-cell-status",
                    '''
                    <q-td :props="props">
                        <q-badge :color="
                            props.value === 'active' ? 'green' :
                            props.value === 'reserved' ? 'orange' :
                            props.value === 'future_use' ? 'blue' : 'grey'
                        ">
                            {{ props.value.replace('_', ' ') }}
                        </q-badge>
                    </q-td>
                    ''',
                )

                table.add_slot(
                    "body-cell-actions",
                    '''
                    <q-td :props="props">
                        <q-btn flat round dense icon="edit" size="sm"
                            @click="$parent.$emit('edit', props.row)" />
                        <q-btn flat round dense icon="delete" size="sm" color="red"
                            @click="$parent.$emit('delete', props.row)" />
                    </q-td>
                    ''',
                )

                table.on("edit", lambda e: open_edit(e.args["id"]))
                table.on("delete", lambda e: confirm_delete(e.args["id"]))

        def open_edit(phone_id: int):
            pn = get_phone_number_by_id(session, phone_id)
            if not pn:
                return
            edit_number.value = pn.number
            edit_extension.value = pn.extension or ""
            edit_type.value = pn.number_type
            edit_status.value = pn.status
            edit_assigned.value = pn.assigned_to or ""
            edit_dept.value = pn.department or ""
            edit_location.value = pn.location or ""
            edit_device.value = pn.device_name or ""
            edit_description.value = pn.description or ""
            edit_range.value = pn.range_id or 0
            edit_customer.value = pn.customer_id or 0
            edit_notes.value = pn.notes or ""
            edit_dialog.phone_id = phone_id
            edit_dialog.open()

        def confirm_delete(phone_id: int):
            pn = get_phone_number_by_id(session, phone_id)
            if not pn:
                return
            with ui.dialog() as confirm, ui.card():
                ui.label(f"Delete number '{pn.number}'?").classes("text-lg")
                with ui.row().classes("justify-end gap-2 mt-2"):
                    ui.button("Cancel", on_click=confirm.close).props("flat")

                    def do_delete():
                        delete_phone_number(session, phone_id)
                        ui.notify("Number deleted", type="warning")
                        confirm.close()
                        refresh_numbers()

                    ui.button("Delete", on_click=do_delete).props("color=red")
            confirm.open()

        refresh_numbers()

    # ─── Add Number dialog ──────────────────────────────────────────────────────

    range_opts_add = {0: "— None —"}
    range_opts_add.update({r.id: r.name for r in ranges})

    customer_opts_add = {0: "— None —"}
    customer_opts_add.update({c.id: c.name for c in customers})

    with ui.dialog() as add_dialog, ui.card().classes("w-[500px]"):
        ui.label("New Phone Number").classes("text-xl font-bold mb-2")
        with ui.row().classes("w-full gap-2"):
            add_number = ui.input("Number *", placeholder="+15550101").classes("flex-1")
            add_extension = ui.input("Extension", placeholder="4501").classes("w-28")
        with ui.row().classes("w-full gap-2"):
            add_type = ui.select(NUMBER_TYPES, value="did", label="Type").classes("flex-1")
            add_status = ui.select(STATUSES, value="active", label="Status").classes("flex-1")
        add_assigned = ui.input("Assigned To", placeholder="Person or team").classes("w-full")
        with ui.row().classes("w-full gap-2"):
            add_dept = ui.input("Department", placeholder="IT, Sales...").classes("flex-1")
            add_location = ui.input("Location", placeholder="Floor 2, Room 4").classes("flex-1")
        add_device = ui.input("Device Name", placeholder="PBX / gateway").classes("w-full")
        add_range = ui.select(range_opts_add, value=0, label="Number Range").classes("w-full")
        add_customer = ui.select(customer_opts_add, value=0, label="Customer").classes("w-full")
        add_description = ui.input("Description", placeholder="What is this used for?").classes("w-full")
        add_notes = ui.textarea("Notes").classes("w-full").props('rows="3"')

        def save_new_number():
            if not add_number.value:
                ui.notify("Number is required", type="warning")
                return
            # Check duplicate
            existing = session.query(PhoneNumber).filter(PhoneNumber.number == add_number.value.strip()).first()
            if existing:
                ui.notify("Number already exists", type="negative")
                return
            create_phone_number(
                session,
                number=add_number.value.strip(),
                extension=add_extension.value.strip() or None,
                number_type=add_type.value,
                status=add_status.value,
                assigned_to=add_assigned.value.strip() or None,
                department=add_dept.value.strip() or None,
                location=add_location.value.strip() or None,
                device_name=add_device.value.strip() or None,
                range_id=add_range.value if add_range.value else None,
                customer_id=add_customer.value if add_customer.value else None,
                description=add_description.value.strip() or None,
                notes=add_notes.value.strip() or None,
            )
            ui.notify("Number created!", type="positive")
            add_dialog.close()
            refresh_numbers()

        with ui.row().classes("justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=add_dialog.close).props("flat")
            ui.button("Save", on_click=save_new_number).props("color=primary")

    # ─── Edit Number dialog ─────────────────────────────────────────────────────

    range_opts_edit = {0: "— None —"}
    range_opts_edit.update({r.id: r.name for r in ranges})

    customer_opts_edit = {0: "— None —"}
    customer_opts_edit.update({c.id: c.name for c in customers})

    with ui.dialog() as edit_dialog, ui.card().classes("w-[500px]"):
        edit_dialog.phone_id = None
        ui.label("Edit Phone Number").classes("text-xl font-bold mb-2")
        with ui.row().classes("w-full gap-2"):
            edit_number = ui.input("Number *").classes("flex-1")
            edit_extension = ui.input("Extension").classes("w-28")
        with ui.row().classes("w-full gap-2"):
            edit_type = ui.select(NUMBER_TYPES, value="did", label="Type").classes("flex-1")
            edit_status = ui.select(STATUSES, value="active", label="Status").classes("flex-1")
        edit_assigned = ui.input("Assigned To").classes("w-full")
        with ui.row().classes("w-full gap-2"):
            edit_dept = ui.input("Department").classes("flex-1")
            edit_location = ui.input("Location").classes("flex-1")
        edit_device = ui.input("Device Name").classes("w-full")
        edit_range = ui.select(range_opts_edit, value=0, label="Number Range").classes("w-full")
        edit_customer = ui.select(customer_opts_edit, value=0, label="Customer").classes("w-full")
        edit_description = ui.input("Description").classes("w-full")
        edit_notes = ui.textarea("Notes").classes("w-full").props('rows="3"')

        def save_edit():
            if not edit_number.value:
                ui.notify("Number is required", type="warning")
                return
            update_phone_number(
                session,
                edit_dialog.phone_id,
                number=edit_number.value.strip(),
                extension=edit_extension.value.strip() or None,
                number_type=edit_type.value,
                status=edit_status.value,
                assigned_to=edit_assigned.value.strip() or None,
                department=edit_dept.value.strip() or None,
                location=edit_location.value.strip() or None,
                device_name=edit_device.value.strip() or None,
                range_id=edit_range.value if edit_range.value else None,
                customer_id=edit_customer.value if edit_customer.value else None,
                description=edit_description.value.strip() or None,
                notes=edit_notes.value.strip() or None,
            )
            ui.notify("Number updated!", type="positive")
            edit_dialog.close()
            refresh_numbers()

        with ui.row().classes("justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=edit_dialog.close).props("flat")
            ui.button("Save", on_click=save_edit).props("color=primary")

    session.close()
