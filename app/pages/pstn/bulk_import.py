"""PSTN Bulk Import page — import phone numbers from CSV."""

import csv
import io
from nicegui import ui, events

from app.database.pstn_db import get_pstn_session_direct as get_session
from app.models.pstn.phone_number import PhoneNumber
from app.models.pstn.number_range import NumberRange
from app.models.pstn.customer import Customer
from app.services.pstn_service import (
    create_phone_number,
    get_all_ranges,
    get_all_customers,
    log_pstn_audit,
)
from app.pages.layout import page_layout


def render_bulk_import():
    """Render the PSTN bulk import page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        ui.label("Bulk Import Phone Numbers").classes("text-3xl font-bold")
        ui.label("Import phone numbers from a CSV file.").classes("text-gray-500 mb-4")

        ui.separator()

        # Instructions
        with ui.card().classes("w-full mt-4"):
            ui.label("CSV Format").classes("text-lg font-semibold mb-2")
            ui.label("Upload a CSV with the following columns (header row required):").classes(
                "text-sm text-gray-500 mb-2"
            )
            ui.code(
                "number,extension,number_type,status,assigned_to,department,location,device_name,description,notes",
                language="text",
            ).classes("w-full text-xs")

            with ui.expansion("Column Details", icon="info").classes("w-full mt-2"):
                details = [
                    ("number *", "Full phone number (e.g. +15550101 or 5550101)"),
                    ("extension", "Internal extension (e.g. 4501)"),
                    ("number_type", "did, extension, toll_free, fax, or other (default: did)"),
                    ("status", "active, inactive, reserved, or future_use (default: active)"),
                    ("assigned_to", "Person or team name"),
                    ("department", "Department name"),
                    ("location", "Physical location"),
                    ("device_name", "PBX or gateway name"),
                    ("description", "What the number is used for"),
                    ("notes", "Additional notes"),
                ]
                for col, desc in details:
                    ui.label(f"• **{col}** — {desc}").classes("text-sm")

            ui.label("Download a template:").classes("text-sm mt-3")

            def download_template():
                template = "number,extension,number_type,status,assigned_to,department,location,device_name,description,notes\n"
                template += "+15550101,4501,did,active,John Doe,IT,Floor 2,Main PBX,Reception line,\n"
                template += "+15550102,4502,did,active,Jane Smith,Sales,Floor 3,Main PBX,Sales hotline,\n"
                template += "+18005551234,,toll_free,active,Support Team,Support,,IVR,Customer support,\n"
                ui.download(template.encode("utf-8"), "phone_numbers_template.csv", "text/csv")

            ui.button("Download Template", icon="download", on_click=download_template).props(
                "flat color=primary size=sm"
            )

        # Import options
        with ui.card().classes("w-full mt-4"):
            ui.label("Import Options").classes("text-lg font-semibold mb-2")

            ranges = get_all_ranges(session)
            customers = get_all_customers(session)

            range_options = {0: "— None (no range) —"}
            range_options.update({r.id: r.name for r in ranges})

            customer_options = {0: "— None (no customer) —"}
            customer_options.update({c.id: c.name for c in customers})

            with ui.row().classes("gap-4 items-end flex-wrap"):
                import_range = ui.select(
                    range_options, value=0, label="Assign to Range"
                ).classes("w-56")
                import_customer = ui.select(
                    customer_options, value=0, label="Assign to Customer"
                ).classes("w-56")
                skip_duplicates = ui.checkbox("Skip duplicates", value=True)

        # Upload and results
        with ui.card().classes("w-full mt-4"):
            ui.label("Upload CSV").classes("text-lg font-semibold mb-2")

            import_result = ui.column().classes("w-full mt-4")

            async def handle_upload(e: events.UploadEventArguments):
                content = e.content.read().decode("utf-8")
                _process_csv(
                    session, content,
                    range_id=import_range.value if import_range.value != 0 else None,
                    customer_id=import_customer.value if import_customer.value != 0 else None,
                    skip_dupes=skip_duplicates.value,
                    results_container=import_result,
                )

            ui.upload(
                label="Upload CSV File",
                on_upload=handle_upload,
                auto_upload=True,
            ).props('accept=".csv" max-file-size="10485760"').classes("w-full")

    session.close()


def _process_csv(
    session, csv_content: str,
    range_id: int | None,
    customer_id: int | None,
    skip_dupes: bool,
    results_container,
):
    """Process the uploaded CSV and import numbers."""
    results_container.clear()

    valid_types = {"did", "extension", "toll_free", "fax", "other"}
    valid_statuses = {"active", "inactive", "reserved", "future_use"}

    added = 0
    skipped = 0
    errors = []

    try:
        reader = csv.DictReader(io.StringIO(csv_content))

        if not reader.fieldnames or "number" not in reader.fieldnames:
            with results_container:
                ui.label("❌ CSV must have a 'number' column in the header row.").classes("text-red")
            return

        for row_num, row in enumerate(reader, start=2):
            number = (row.get("number") or "").strip()
            if not number:
                skipped += 1
                continue

            # Check duplicate
            if skip_dupes:
                existing = session.query(PhoneNumber).filter(PhoneNumber.number == number).first()
                if existing:
                    skipped += 1
                    continue

            # Validate type
            number_type = (row.get("number_type") or "did").strip().lower()
            if number_type not in valid_types:
                number_type = "did"

            # Validate status
            status = (row.get("status") or "active").strip().lower()
            if status not in valid_statuses:
                status = "active"

            try:
                pn = PhoneNumber(
                    number=number,
                    extension=(row.get("extension") or "").strip() or None,
                    number_type=number_type,
                    status=status,
                    assigned_to=(row.get("assigned_to") or "").strip() or None,
                    department=(row.get("department") or "").strip() or None,
                    location=(row.get("location") or "").strip() or None,
                    device_name=(row.get("device_name") or "").strip() or None,
                    description=(row.get("description") or "").strip() or None,
                    notes=(row.get("notes") or "").strip() or None,
                    range_id=range_id,
                    customer_id=customer_id,
                )
                session.add(pn)
                added += 1
            except Exception as e:
                errors.append(f"Row {row_num} ({number}): {e}")

        session.commit()

        # Log audit
        if added > 0:
            log_pstn_audit(
                session, "number", 0, "bulk_import",
                f"Imported {added} numbers from CSV (skipped {skipped})",
            )

    except Exception as e:
        errors.append(f"CSV parsing error: {e}")

    # Display results
    with results_container:
        if added or skipped:
            with ui.card().classes("w-full"):
                with ui.row().classes("gap-4 items-center"):
                    if added:
                        ui.badge(f"{added} imported").props("color=green")
                    if skipped:
                        ui.badge(f"{skipped} skipped").props("color=orange")
                    if errors:
                        ui.badge(f"{len(errors)} errors").props("color=red")

                ui.notify(
                    f"Import complete: {added} added, {skipped} skipped",
                    type="positive" if not errors else "warning",
                )

                if errors:
                    with ui.expansion(f"Errors ({len(errors)})", icon="error").classes("w-full mt-2"):
                        for err in errors[:20]:
                            ui.label(f"• {err}").classes("text-xs text-red")
                        if len(errors) > 20:
                            ui.label(f"... and {len(errors) - 20} more").classes("text-xs text-gray-500")
        elif errors:
            for err in errors:
                ui.label(f"❌ {err}").classes("text-red")
        else:
            ui.label("No numbers found in CSV.").classes("text-gray-500")
