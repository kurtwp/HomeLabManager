"""Service for tracking changes to entities."""

import json
from sqlalchemy.orm import Session

from app.models.changelog import Changelog, EntityType, ActionType


def log_change(
    session: Session,
    entity_type: EntityType,
    entity_id: int,
    action: ActionType,
    entity_name: str | None = None,
    old_values: dict | None = None,
    new_values: dict | None = None,
    comment: str | None = None,
) -> Changelog:
    """Record a change in the changelog."""
    entry = Changelog(
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        action=action,
        old_values=json.dumps(old_values) if old_values else None,
        new_values=json.dumps(new_values) if new_values else None,
        comment=comment,
    )
    session.add(entry)
    session.flush()
    return entry


def get_changelog(
    session: Session,
    entity_type: EntityType | None = None,
    entity_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Changelog]:
    """Retrieve changelog entries with optional filters."""
    query = session.query(Changelog)
    if entity_type:
        query = query.filter(Changelog.entity_type == entity_type)
    if entity_id:
        query = query.filter(Changelog.entity_id == entity_id)
    return (
        query.order_by(Changelog.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
