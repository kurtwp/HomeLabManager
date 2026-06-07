"""Reusable tag assignment component for entity detail pages."""

from nicegui import ui
from sqlalchemy.orm import Session

from app.models.tag import Tag


def render_tag_assignment(
    session: Session,
    entity,
    entity_tags_attr: str = "tags",
):
    """
    Render a tag assignment widget for any entity (IP, device, network).

    Args:
        session: Active SQLAlchemy session
        entity: The SQLAlchemy model instance (must have a 'tags' relationship)
        entity_tags_attr: Name of the tags relationship attribute
    """
    all_tags = session.query(Tag).order_by(Tag.name).all()
    current_tags: list[Tag] = getattr(entity, entity_tags_attr, [])
    current_tag_ids = {t.id for t in current_tags}

    with ui.card().classes("w-full"):
        ui.label("Tags").classes("text-lg font-semibold mb-2")

        # Display current tags
        tags_display = ui.row().classes("flex-wrap gap-1 mb-3")

        def refresh_display():
            tags_display.clear()
            entity_tags = getattr(entity, entity_tags_attr, [])
            with tags_display:
                if not entity_tags:
                    ui.label("No tags assigned").classes("text-sm text-gray-400 italic")
                else:
                    for tag in entity_tags:
                        with ui.row().classes("items-center gap-0"):
                            ui.html(
                                f'<span style="display:inline-flex; align-items:center; '
                                f"padding:2px 10px; border-radius:12px; font-size:0.75rem; "
                                f"font-weight:500; background:{tag.color}20; "
                                f'color:{tag.color}; border:1px solid {tag.color}40;">'
                                f"{tag.name}</span>"
                            )
                            ui.button(
                                icon="close",
                                on_click=lambda t=tag: remove_tag(t),
                            ).props("flat round size=xs").classes("ml-0")

        def remove_tag(tag: Tag):
            entity_tags = getattr(entity, entity_tags_attr)
            if tag in entity_tags:
                entity_tags.remove(tag)
                session.commit()
                ui.notify(f"Removed tag '{tag.name}'", type="info")
                refresh_display()

        refresh_display()

        # Add tag selector
        available_tags = {
            t.id: t.name for t in all_tags if t.id not in current_tag_ids
        }

        if available_tags:
            with ui.row().classes("items-center gap-2"):
                tag_select = ui.select(
                    available_tags, label="Add tag", with_input=True
                ).classes("w-48")

                def add_tag():
                    if not tag_select.value:
                        return
                    tag = session.query(Tag).filter(Tag.id == tag_select.value).first()
                    if tag:
                        entity_tags = getattr(entity, entity_tags_attr)
                        if tag not in entity_tags:
                            entity_tags.append(tag)
                            session.commit()
                            ui.notify(f"Added tag '{tag.name}'", type="positive")
                            # Update available options
                            new_options = {
                                k: v
                                for k, v in available_tags.items()
                                if k != tag_select.value
                            }
                            tag_select.options = new_options
                            tag_select.value = None
                            tag_select.update()
                            refresh_display()

                ui.button("Add", on_click=add_tag).props("flat color=primary size=sm")
        else:
            ui.label("All tags assigned").classes("text-xs text-gray-400")
