"""PSTN Export page — export phone numbers and ranges to CSV."""

import csv
import io
from nicegui import ui

from app.database.pstn_db import get_pstn_session_direct as get_session
from app.models.pstn.phone_number import PhoneNumber
from app.models.pstn.number_range import NumberRange
from app.models.pstn.customer import Customer
from app.services.pstn_service import get_all_ranges, get_all_customers
from app.pages.layout import page_layout


def render_pstn_export():
    """Render the PSTN export page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        ui.label("Export Telephony Data").classes("text-3xl font-bold")
        ui.label("Download phone numbers, ranges, or customers as CSV.").classes(
            "text-gray-500 mb-4"
        )

        ui.separator()

        with ui.row().classes("w-full gap-4 flex-wrap mt-4"):
            # Export Numbers
            with ui.card().classes("flex-1 min-w-[300px]"):
                ui.label("Export Phone Numbers").classes("text-lg font-semibold mb-2")
                ui.label("All numbers with full details.").classes("text-sm text-gray-500 mb-3")

                ranges = get_all_ranges(session)
                customers = get_all_customers(session)

                range_options = {0: "All Ranges"}
                range_options.update({r.id: r.name for r in ranges})
                customer_options = {0: "All Customers"}
                customer_options.update({c.id: c.name for c in customers})

                export_range = ui.select(range_options, value=0, label="Filter by Range").classes("w-full")
                export_customer = ui.select(customer_options, value=0, label="Filter by Customer").classes("w-full")

                def export_numbers():
                    query = session.query(PhoneNumber)
                    if export_range.value:
                        query = query.filter(PhoneNumber.range_id == export_range.value)
                    if export_customer.value:
                        query = query.filter(PhoneNumber.customer_id == export_customer.value)
                    numbers = query.order_by(PhoneNumber.number).all()

                    output = io.StringIO()
                    writer = csv.writer(output)
                    writer.writerow([
                        "number", "extension", "number_type", "status",
                        "assigned_to", "department", "location", "device_name",
                        "description", "notes", "range", "customer",
                    ])
                    for pn in numbers:
                        range_name = pn.number_range.name if pn.number_range else ""
                        customer_name = pn.customer.name if pn.customer else ""
                        writer.writerow([
                            pn.number, pn.extension or "", pn.number_type, pn.status,
                            pn.assigned_to or "", pn.department or "", pn.location or "",
                            pn.device_name or "", pn.description or "", pn.notes or "",
                            range_name, customer_name,
                        ])

                    ui.download(output.getvalue().encode("utf-8"), "phone_numbers.csv", "text/csv")
                    ui.notify(f"Exported {len(numbers)} numbers", type="positive")

                ui.button("Export Numbers (CSV)", icon="download", on_click=export_numbers).props(
                    "color=primary"
                )

            # Export Ranges
            with ui.card().classes("flex-1 min-w-[300px]"):
                ui.label("Export Number Ranges").classes("text-lg font-semibold mb-2")
                ui.label("All ranges with provider and utilization info.").classes(
                    "text-sm text-gray-500 mb-3"
                )

                def export_ranges():
                    ranges_list = session.query(NumberRange).order_by(NumberRange.name).all()

                    output = io.StringIO()
                    writer = csv.writer(output)
                    writer.writerow([
                        "name", "range_start", "range_end", "country_code",
                        "area_code", "prefix", "provider", "range_type",
                        "status", "total_numbers", "description", "customer",
                    ])
                    for nr in ranges_list:
                        customer_name = nr.customer.name if nr.customer else ""
                        writer.writerow([
                            nr.name, nr.range_start, nr.range_end,
                            nr.country_code or "", nr.area_code or "",
                            nr.prefix or "", nr.provider or "", nr.range_type,
                            nr.status, nr.total_numbers or 0,
                            nr.description or "", customer_name,
                        ])

                    ui.download(output.getvalue().encode("utf-8"), "number_ranges.csv", "text/csv")
                    ui.notify(f"Exported {len(ranges_list)} ranges", type="positive")

                ui.button("Export Ranges (CSV)", icon="download", on_click=export_ranges).props(
                    "color=primary"
                )

            # Export Customers
            with ui.card().classes("flex-1 min-w-[300px]"):
                ui.label("Export Customers").classes("text-lg font-semibold mb-2")
                ui.label("All customers with contact info.").classes(
                    "text-sm text-gray-500 mb-3"
                )

                def export_customers():
                    customers_list = session.query(Customer).order_by(Customer.name).all()

                    output = io.StringIO()
                    writer = csv.writer(output)
                    writer.writerow([
                        "name", "account_number", "contact_name",
                        "contact_email", "contact_phone", "notes",
                    ])
                    for c in customers_list:
                        writer.writerow([
                            c.name, c.account_number or "",
                            c.contact_name or "", c.contact_email or "",
                            c.contact_phone or "", c.notes or "",
                        ])

                    ui.download(output.getvalue().encode("utf-8"), "pstn_customers.csv", "text/csv")
                    ui.notify(f"Exported {len(customers_list)} customers", type="positive")

                ui.button("Export Customers (CSV)", icon="download", on_click=export_customers).props(
                    "color=primary"
                )

    session.close()
