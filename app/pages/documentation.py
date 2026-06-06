"""Knowledge base / documentation page."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.models.documentation import Documentation, DocCategory
from app.pages.layout import page_layout


def render_documentation():
    """Render the knowledge base page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Knowledge Base").classes("text-3xl font-bold")
            ui.button("New Article", on_click=lambda: add_dialog.open()).props(
                "color=primary icon=add"
            )

        ui.separator().classes("my-4")

        # Category filter
        with ui.row().classes("gap-2 mb-4"):
            category_filter = ui.select(
                {"all": "All", **{c.value: c.value.replace("-", " ").title() for c in DocCategory}},
                value="all",
                label="Category",
            ).classes("w-48")
            ui.button("Filter", on_click=lambda: refresh_docs()).props("flat")

        # Articles list
        docs_container = ui.column().classes("w-full gap-3")

        def refresh_docs():
            docs_container.clear()
            with docs_container:
                query = session.query(Documentation)
                if category_filter.value != "all":
                    query = query.filter(
                        Documentation.category == DocCategory(category_filter.value)
                    )
                docs = query.order_by(Documentation.updated_at.desc()).all()

                if not docs:
                    ui.label("No documentation yet. Create your first article!").classes(
                        "text-gray-500"
                    )
                    return

                for doc in docs:
                    with ui.card().classes("w-full cursor-pointer").on(
                        "click", lambda d=doc: ui.navigate.to(f"/docs/{d.id}")
                    ):
                        with ui.row().classes("items-center gap-2"):
                            cat_colors = {
                                DocCategory.HOWTO: "blue",
                                DocCategory.TROUBLESHOOTING: "orange",
                                DocCategory.RUNBOOK: "green",
                                DocCategory.GENERAL: "gray",
                            }
                            ui.badge(doc.category.value.replace("-", " ").title()).props(
                                f"color={cat_colors.get(doc.category, 'gray')}"
                            )
                            ui.label(doc.title).classes("text-lg font-semibold")
                        # Show first 150 chars of body
                        preview = doc.body[:150] + "..." if len(doc.body) > 150 else doc.body
                        ui.label(preview).classes("text-sm text-gray-500")

        refresh_docs()

    # Add article dialog
    with ui.dialog().props("maximized") as add_dialog, ui.card().classes("w-full h-full"):
        ui.label("New Article").classes("text-2xl font-bold mb-2")

        with ui.row().classes("w-full gap-4"):
            title_input = ui.input("Title *", placeholder="Article title").classes("flex-1")
            cat_select = ui.select(
                {c.value: c.value.replace("-", " ").title() for c in DocCategory},
                value=DocCategory.GENERAL.value,
                label="Category",
            ).classes("w-48")

        with ui.tabs().classes("w-full") as tabs:
            edit_tab = ui.tab("Edit")
            preview_tab = ui.tab("Preview")

        body_input = ui.textarea(placeholder="Write your article in Markdown...").classes(
            "w-full"
        ).props('rows="20"')
        markdown_preview = None

        with ui.tab_panels(tabs, value=edit_tab).classes("w-full flex-1"):
            with ui.tab_panel(edit_tab):
                body_input
            with ui.tab_panel(preview_tab):
                markdown_preview = ui.markdown("").classes("w-full")

        def update_preview():
            if markdown_preview:
                markdown_preview.set_content(body_input.value or "*Start writing...*")

        tabs.on("update:model-value", lambda: update_preview())

        def save_article():
            if not title_input.value:
                ui.notify("Title is required", type="warning")
                return
            doc = Documentation(
                title=title_input.value,
                body=body_input.value or "",
                category=DocCategory(cat_select.value),
            )
            session.add(doc)
            session.commit()
            ui.notify("Article saved!", type="positive")
            add_dialog.close()
            refresh_docs()

        with ui.row().classes("justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=add_dialog.close).props("flat")
            ui.button("Save", on_click=save_article).props("color=primary")

    session.close()


def render_doc_detail(doc_id: int):
    """Render a single documentation article with edit capability."""
    page_layout()

    session = get_session()
    doc = session.query(Documentation).filter(Documentation.id == doc_id).first()

    if not doc:
        with ui.column().classes("page-container"):
            ui.label("Article not found").classes("text-xl text-red")
        session.close()
        return

    with ui.column().classes("page-container w-full"):
        with ui.row().classes("items-center gap-4"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/docs")).props(
                "flat round"
            )
            ui.label(doc.title).classes("text-3xl font-bold")
            ui.badge(doc.category.value.replace("-", " ").title()).props("color=blue")

        ui.separator().classes("my-4")

        with ui.tabs().classes("w-full") as tabs:
            view_tab = ui.tab("View")
            edit_tab = ui.tab("Edit")

        with ui.tab_panels(tabs, value=view_tab).classes("w-full"):
            with ui.tab_panel(view_tab):
                ui.markdown(doc.body).classes("w-full")

            with ui.tab_panel(edit_tab):
                title_edit = ui.input("Title", value=doc.title).classes("w-full")
                body_edit = ui.textarea(value=doc.body).classes("w-full").props(
                    'rows="20"'
                )

                def save_changes():
                    doc.title = title_edit.value
                    doc.body = body_edit.value
                    session.commit()
                    ui.notify("Article updated!", type="positive")
                    ui.navigate.to(f"/docs/{doc.id}")

                ui.button("Save Changes", on_click=save_changes).props("color=primary")

    session.close()
