"""Custom field definitions and values for user-defined metadata."""

from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database.db import Base


class FieldType(enum.Enum):
    """Supported custom field types."""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    SELECT = "select"
    CHECKBOX = "checkbox"


class EntityType(enum.Enum):
    """Entity types that can have custom fields."""
    IP = "ip"
    DEVICE = "device"
    NETWORK = "network"


class CustomFieldDefinition(Base):
    """Defines a custom field that can be attached to entities."""

    __tablename__ = "custom_field_definitions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    field_type: Mapped[str] = mapped_column(String(50), nullable=False)  # FieldType value
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # EntityType value
    options: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # For select fields
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    default_value: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    values: Mapped[list["CustomFieldValue"]] = relationship(
        back_populates="field_definition", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CustomFieldDefinition(name={self.name!r}, type={self.field_type})>"


class CustomFieldValue(Base):
    """Stores the value of a custom field for a specific entity."""

    __tablename__ = "custom_field_values"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    field_definition_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("custom_field_definitions.id"), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    field_definition: Mapped["CustomFieldDefinition"] = relationship(back_populates="values")

    def __repr__(self) -> str:
        return f"<CustomFieldValue(field={self.field_definition_id}, entity={self.entity_type}:{self.entity_id})>"
