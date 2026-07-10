"""Help page — displays documentation files from the docs/ folder."""

import os
from pathlib import Path

from nicegui import ui

from app.pages.layout import page_layout

DOCS_DIR = Path(__file__).parent.parent.parent / "docs"


def _get_doc_files() -> list[dict]:
    """Scan the docs/ folder and return a list of doc metadata."""
    docs = []
    if not DOCS_DIR.exists():
        return docs
    for f in sorted(DOCS_DIR.iterdir()):
        if f.suffix == ".md":
            # Convert filename to a readable title
            title = f.stem.replace("-", " ").replace("_", " ").title()
            docs.append({"filename": f.name, "title": title, "path": f})
    return docs


def render_help(selected_file: str = ""):
    """Render the help page with a sidebar menu and content area."""
    page_layout()

    docs = _get_doc_files()

    with ui.column().classes("page-container w-full"):
        ui.label("Help & Documentation").classes("text-3xl font-bold mb-4")

        with ui.row().classes("w-full gap-4"):
            # Sidebar menu
            with ui.card().classes("w-64 shrink-0"):
                ui.label("Topics").classes("text-lg font-semibold mb-2")
                if not docs:
                    ui.label("No documentation files found.").classes(
                        "text-gray-500 italic"
                    )
                else:
                    for doc in docs:
                        slug = doc["filename"].replace(".md", "")
                        is_active = slug == selected_file
                        btn = ui.button(
                            doc["title"],
                            on_click=lambda s=slug: ui.navigate.to(f"/help/{s}"),
                        ).props("flat no-caps align=left").classes("w-full justify-start")
                        if is_active:
                            btn.props("color=primary")

            # Content area
            with ui.card().classes("flex-1 min-w-0"):
                if selected_file:
                    # Find and render the selected doc
                    target = DOCS_DIR / f"{selected_file}.md"
                    if target.exists():
                        content = target.read_text(encoding="utf-8")
                        ui.markdown(content).classes("w-full")
                    else:
                        ui.label("Document not found.").classes("text-red text-lg")
                else:
                    # Landing — show overview
                    ui.label("Welcome to the Help section").classes(
                        "text-xl font-semibold mb-2"
                    )
                    ui.label(
                        "Select a topic from the menu on the left to view documentation."
                    ).classes("text-gray-500 mb-4")

                    # Quick links
                    ui.label("Available Topics:").classes("font-semibold mt-2")
                    for doc in docs:
                        slug = doc["filename"].replace(".md", "")
                        ui.link(doc["title"], f"/help/{slug}").classes("block ml-2 my-1")
