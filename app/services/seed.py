"""Seed default data (device types, tags) on first run."""

from sqlalchemy.orm import Session

from app.models.device import DeviceType
from app.models.tag import Tag
from app.utils.constants import DEFAULT_DEVICE_TYPES, DEFAULT_TAGS


def seed_defaults(session: Session) -> None:
    """Populate default device types and tags if they don't exist."""
    # Seed device types
    existing_types = {dt.name for dt in session.query(DeviceType).all()}
    for dt_data in DEFAULT_DEVICE_TYPES:
        if dt_data["name"] not in existing_types:
            session.add(DeviceType(name=dt_data["name"], icon=dt_data.get("icon")))

    # Seed tags
    existing_tags = {t.name for t in session.query(Tag).all()}
    for tag_data in DEFAULT_TAGS:
        if tag_data["name"] not in existing_tags:
            session.add(Tag(name=tag_data["name"], color=tag_data["color"]))

    session.commit()
