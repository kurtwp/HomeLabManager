"""Scheduled scans management page."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.services.network_service import get_all_networks
from app.services.scheduler import (
    get_scheduled_jobs,
    add_scan_job,
    remove_scan_job,
)
from app.pages.layout import page_layout


def render_scheduler():
    """Render the scheduled scans management page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        ui.label("Scheduled Scans").classes("text-3xl font-bold")
        ui.label(
            "Configure automatic network scanning on a recurring schedule."
        ).classes("text-gray-500 mb-4")

        ui.separator()

        # Current jobs
        with ui.card().classes("w-full mt-4"):
            ui.label("Active Schedules").classes("text-lg font-semibold mb-2")

            jobs_container = ui.column().classes("w-full gap-2")

            def refresh_jobs():
                jobs_container.clear()
                jobs = get_scheduled_jobs()
                with jobs_container:
                    if not jobs:
                        ui.label("No scheduled scans configured.").classes(
                            "text-gray-500"
                        )
                        return

                    for job in jobs:
                        with ui.row().classes("w-full items-center justify-between"):
                            with ui.column().classes("gap-0"):
                                ui.label(job["name"]).classes("font-semibold")
                                ui.label(f"Next run: {job['next_run']}").classes(
                                    "text-xs text-gray-500"
                                )
                                ui.label(f"Schedule: {job['trigger']}").classes(
                                    "text-xs text-gray-400"
                                )
                            # Extract network_id from job id
                            net_id = job["id"].replace("scan_network_", "")
                            ui.button(
                                icon="delete",
                                on_click=lambda nid=net_id: (
                                    remove_scan_job(int(nid)),
                                    refresh_jobs(),
                                    ui.notify("Schedule removed", type="warning"),
                                ),
                            ).props("flat round color=red size=sm")

            refresh_jobs()

        # Add new schedule
        ui.separator().classes("my-4")

        with ui.card().classes("w-full"):
            ui.label("Add Scheduled Scan").classes("text-lg font-semibold mb-2")

            networks = get_all_networks(session)
            net_options = {n.id: f"{n.name} ({n.cidr})" for n in networks}

            if not net_options:
                ui.label("Add networks first before scheduling scans.").classes(
                    "text-gray-500"
                )
            else:
                with ui.row().classes("w-full gap-4 items-end flex-wrap"):
                    net_select = ui.select(
                        net_options, label="Network"
                    ).classes("w-64")

                    interval_options = {
                        15: "Every 15 minutes",
                        30: "Every 30 minutes",
                        60: "Every hour",
                        120: "Every 2 hours",
                        360: "Every 6 hours",
                        720: "Every 12 hours",
                        1440: "Every 24 hours",
                    }
                    interval_select = ui.select(
                        interval_options, value=60, label="Frequency"
                    ).classes("w-48")

                    def schedule_scan():
                        if not net_select.value:
                            ui.notify("Select a network", type="warning")
                            return
                        add_scan_job(net_select.value, interval_select.value)
                        ui.notify("Scan scheduled!", type="positive")
                        refresh_jobs()

                    ui.button(
                        "Schedule", icon="schedule", on_click=schedule_scan
                    ).props("color=primary")

    session.close()
