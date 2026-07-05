"""PSTN Customers page — list, add, edit, delete, view detail."""

from nicegui import ui

from app.database.pstn_db import get_pstn_session_direct as get_session
from app.models.pstn.customer import Customer
from app.services.pstn_service import (
    create_customer,
    get_all_customers,
    get_customer_by_id,
    update_customer,
    delete_customer,
    get_numbers_by_customer,
    get_ranges_by_customer,
)
from app.pages.layout import page_layout


def render_customers():
    """Render the Customers list page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Customers").classes("text-3xl font-bold")
            ui.button("Add Customer", icon="add", on_click=lambda: add_dialog.open()).props(
                "color=primary"
            )

        ui.separator().classes("my-4")

        customers_container = ui.column().classes("w-full gap-3")

        def refresh_customers():
            customers_container.clear()
            customers = get_all_customers(session)
            with customers_container:
                if not customers:
                    ui.label("No customers yet.").classes("text-gray-500 italic")
                    return

                columns = [
                    {"name": "name", "label": "Name", "field": "name", "align": "left", "sortable": True},
                    {"name": "account_number", "label": "Account #", "field": "account_number", "align": "left"},
                    {"name": "contact_name", "label": "Contact", "field": "contact_name", "align": "left"},
                    {"name": "contact_email", "label": "Email", "field": "contact_email", "align": "left"},
                    {"name": "contact_phone", "label": "Phone", "field": "contact_phone", "align": "left"},
                    {"name": "numbers", "label": "Numbers", "field": "numbers", "align": "center"},
                    {"name": "ranges", "label": "Ranges", "field": "ranges", "align": "center"},
                    {"name": "actions", "label": "Actions", "field": "actions", "align": "center"},
                ]
                rows = []
                for c in customers:
                    num_count = session.query(Customer).filter(Customer.id == c.id).first()
                    numbers_count = get_numbers_by_customer(session, c.id)
                    ranges_count = get_ranges_by_customer(session, c.id)
                    rows.append({
                        "id": c.id,
                        "name": c.name,
                        "account_number": c.account_number or "—",
                        "contact_name": c.contact_name or "—",
                        "contact_email": c.contact_email or "—",
                        "contact_phone": c.contact_phone or "—",
                        "numbers": len(numbers_count),
                        "ranges": len(ranges_count),
                    })

                table = ui.table(
                    columns=columns, rows=rows, row_key="id"
                ).classes("w-full").props("flat bordered dense")

                table.add_slot(
                    "body-cell-name",
                    '''
                    <q-td :props="props">
                        <a :href="'/pstn/customers/' + props.row.id"
                           class="text-primary" style="text-decoration:none; font-weight:500;">
                            {{ props.value }}
                        </a>
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

        def open_edit(customer_id: int):
            c = get_customer_by_id(session, customer_id)
            if not c:
                return
            edit_name.value = c.name
            edit_account.value = c.account_number or ""
            edit_contact_name.value = c.contact_name or ""
            edit_contact_email.value = c.contact_email or ""
            edit_contact_phone.value = c.contact_phone or ""
            edit_notes.value = c.notes or ""
            edit_dialog.customer_id = customer_id
            edit_dialog.open()

        def confirm_delete(customer_id: int):
            c = get_customer_by_id(session, customer_id)
            if not c:
                return
            with ui.dialog() as confirm, ui.card():
                ui.label(f"Delete customer '{c.name}'?").classes("text-lg")
                ui.label(
                    "Numbers and ranges will be unlinked (not deleted)."
                ).classes("text-sm text-gray-500")
                with ui.row().classes("justify-end gap-2 mt-2"):
                    ui.button("Cancel", on_click=confirm.close).props("flat")

                    def do_delete():
                        # Unlink numbers and ranges
                        for pn in get_numbers_by_customer(session, customer_id):
                            pn.customer_id = None
                        for nr in get_ranges_by_customer(session, customer_id):
                            nr.customer_id = None
                        session.commit()
                        delete_customer(session, customer_id)
                        ui.notify("Customer deleted", type="warning")
                        confirm.close()
                        refresh_customers()

                    ui.button("Delete", on_click=do_delete).props("color=red")
            confirm.open()

        refresh_customers()

    # ─── Add Customer dialog ────────────────────────────────────────────────────

    with ui.dialog() as add_dialog, ui.card().classes("w-[500px]"):
        ui.label("New Customer").classes("text-xl font-bold mb-2")
        add_name = ui.input("Name *", placeholder="Company or person name").classes("w-full")
        add_account = ui.input("Account Number", placeholder="Optional unique ID").classes("w-full")
        with ui.row().classes("w-full gap-2"):
            add_contact_name = ui.input("Contact Name").classes("flex-1")
            add_contact_phone = ui.input("Contact Phone").classes("flex-1")
        add_contact_email = ui.input("Contact Email", placeholder="email@example.com").classes("w-full")
        add_notes = ui.textarea("Notes").classes("w-full").props('rows="3"')

        def save_new_customer():
            if not add_name.value:
                ui.notify("Name is required", type="warning")
                return
            create_customer(
                session,
                name=add_name.value.strip(),
                account_number=add_account.value.strip() or None,
                contact_name=add_contact_name.value.strip() or None,
                contact_email=add_contact_email.value.strip() or None,
                contact_phone=add_contact_phone.value.strip() or None,
                notes=add_notes.value.strip() or None,
            )
            ui.notify("Customer created!", type="positive")
            add_dialog.close()
            refresh_customers()

        with ui.row().classes("justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=add_dialog.close).props("flat")
            ui.button("Save", on_click=save_new_customer).props("color=primary")

    # ─── Edit Customer dialog ───────────────────────────────────────────────────

    with ui.dialog() as edit_dialog, ui.card().classes("w-[500px]"):
        edit_dialog.customer_id = None
        ui.label("Edit Customer").classes("text-xl font-bold mb-2")
        edit_name = ui.input("Name *").classes("w-full")
        edit_account = ui.input("Account Number").classes("w-full")
        with ui.row().classes("w-full gap-2"):
            edit_contact_name = ui.input("Contact Name").classes("flex-1")
            edit_contact_phone = ui.input("Contact Phone").classes("flex-1")
        edit_contact_email = ui.input("Contact Email").classes("w-full")
        edit_notes = ui.textarea("Notes").classes("w-full").props('rows="3"')

        def save_edit_customer():
            if not edit_name.value:
                ui.notify("Name is required", type="warning")
                return
            update_customer(
                session,
                edit_dialog.customer_id,
                name=edit_name.value.strip(),
                account_number=edit_account.value.strip() or None,
                contact_name=edit_contact_name.value.strip() or None,
                contact_email=edit_contact_email.value.strip() or None,
                contact_phone=edit_contact_phone.value.strip() or None,
                notes=edit_notes.value.strip() or None,
            )
            ui.notify("Customer updated!", type="positive")
            edit_dialog.close()
            refresh_customers()

        with ui.row().classes("justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=edit_dialog.close).props("flat")
            ui.button("Save", on_click=save_edit_customer).props("color=primary")

    session.close()


def render_customer_detail(customer_id: int):
    """Render the detail view for a single customer — their ranges and numbers."""
    page_layout()

    session = get_session()
    customer = get_customer_by_id(session, customer_id)

    if not customer:
        with ui.column().classes("page-container"):
            ui.label("Customer not found").classes("text-xl text-red")
        session.close()
        return

    numbers = get_numbers_by_customer(session, customer_id)
    ranges = get_ranges_by_customer(session, customer_id)

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("items-center gap-4"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/pstn/customers")).props(
                "flat round"
            )
            ui.label(customer.name).classes("text-3xl font-bold")
            if customer.account_number:
                ui.badge(f"#{customer.account_number}").props("color=blue outline")

        ui.separator().classes("my-4")

        # Customer info card
        with ui.card().classes("w-full"):
            with ui.row().classes("gap-8 flex-wrap"):
                with ui.column().classes("gap-1"):
                    ui.label("Contact Name").classes("text-xs text-gray-400")
                    ui.label(customer.contact_name or "—")
                with ui.column().classes("gap-1"):
                    ui.label("Email").classes("text-xs text-gray-400")
                    ui.label(customer.contact_email or "—")
                with ui.column().classes("gap-1"):
                    ui.label("Phone").classes("text-xs text-gray-400")
                    ui.label(customer.contact_phone or "—")
            if customer.notes:
                ui.separator().classes("my-2")
                ui.label("Notes").classes("text-xs text-gray-400")
                ui.label(customer.notes).classes("text-sm")

        # Ranges
        ui.label(f"Number Ranges ({len(ranges)})").classes("text-xl font-semibold mt-6")
        if ranges:
            range_columns = [
                {"name": "name", "label": "Name", "field": "name", "align": "left"},
                {"name": "range", "label": "Range", "field": "range", "align": "left"},
                {"name": "provider", "label": "Provider", "field": "provider", "align": "left"},
                {"name": "status", "label": "Status", "field": "status", "align": "center"},
            ]
            range_rows = [
                {
                    "id": r.id,
                    "name": r.name,
                    "range": f"{r.range_start} → {r.range_end}",
                    "provider": r.provider or "—",
                    "status": r.status,
                }
                for r in ranges
            ]
            ui.table(columns=range_columns, rows=range_rows, row_key="id").classes("w-full").props(
                "flat bordered dense"
            )
        else:
            ui.label("No ranges assigned.").classes("text-gray-500 italic")

        # Numbers
        ui.label(f"Phone Numbers ({len(numbers)})").classes("text-xl font-semibold mt-6")
        if numbers:
            import re

            def natural_key(pn):
                return [
                    int(c) if c.isdigit() else c.lower()
                    for c in re.split(r"(\d+)", pn.number)
                ]

            numbers_sorted = sorted(numbers, key=natural_key)

            num_columns = [
                {"name": "number", "label": "Number", "field": "number", "align": "left"},
                {"name": "extension", "label": "Ext", "field": "extension", "align": "left"},
                {"name": "type", "label": "Type", "field": "type", "align": "center"},
                {"name": "status", "label": "Status", "field": "status", "align": "center"},
                {"name": "assigned_to", "label": "Assigned To", "field": "assigned_to", "align": "left"},
                {"name": "department", "label": "Department", "field": "department", "align": "left"},
            ]
            num_rows = [
                {
                    "id": pn.id,
                    "number": pn.number,
                    "extension": pn.extension or "—",
                    "type": pn.number_type,
                    "status": pn.status,
                    "assigned_to": pn.assigned_to or "—",
                    "department": pn.department or "—",
                }
                for pn in numbers_sorted
            ]
            ui.table(columns=num_columns, rows=num_rows, row_key="id").classes("w-full").props(
                "flat bordered dense"
            )
        else:
            ui.label("No numbers assigned.").classes("text-gray-500 italic")

    session.close()
