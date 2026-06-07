"""Service for custom field definitions and values."""

from sqlalchemy.orm import Session

from app.models.custom_field import CustomFieldDefinition, CustomFieldValue


# --- Field Definitions ---

def create_field_definition(
    session: Session,
    name: str,
    field_type: str,
    entity_type: str,
    options: dict | None = None,
    required: bool = False,
    default_value: str | None = None,
) -> CustomFieldDefinition:
    """Create a new custom field definition."""
    field_def = CustomFieldDefinition(
        name=name,
        field_type=field_type,
        entity_type=entity_type,
        options=options,
        required=required,
        default_value=default_value,
    )
    session.add(field_def)
    session.commit()
    return field_def


def get_all_field_definitions(session: Session) -> list[CustomFieldDefinition]:
    """Get all custom field definitions."""
    return session.query(CustomFieldDefinition).order_by(CustomFieldDefinition.name).all()


def get_field_definitions_for_entity(
    session: Session, entity_type: str
) -> list[CustomFieldDefinition]:
    """Get field definitions for a specific entity type."""
    return (
        session.query(CustomFieldDefinition)
        .filter(CustomFieldDefinition.entity_type == entity_type)
        .order_by(CustomFieldDefinition.name)
        .all()
    )


def get_field_definition_by_id(
    session: Session, field_id: int
) -> CustomFieldDefinition | None:
    """Get a field definition by ID."""
    return session.query(CustomFieldDefinition).filter(CustomFieldDefinition.id == field_id).first()


def update_field_definition(
    session: Session, field_id: int, **kwargs
) -> CustomFieldDefinition | None:
    """Update a field definition."""
    field_def = get_field_definition_by_id(session, field_id)
    if not field_def:
        return None
    for key, value in kwargs.items():
        if hasattr(field_def, key):
            setattr(field_def, key, value)
    session.commit()
    return field_def


def delete_field_definition(session: Session, field_id: int) -> bool:
    """Delete a field definition and all its values."""
    field_def = get_field_definition_by_id(session, field_id)
    if not field_def:
        return False
    session.delete(field_def)
    session.commit()
    return True


# --- Field Values ---

def get_field_values_for_entity(
    session: Session, entity_type: str, entity_id: int
) -> list[CustomFieldValue]:
    """Get all custom field values for a specific entity."""
    return (
        session.query(CustomFieldValue)
        .filter(
            CustomFieldValue.entity_type == entity_type,
            CustomFieldValue.entity_id == entity_id,
        )
        .all()
    )


def set_field_value(
    session: Session,
    field_definition_id: int,
    entity_type: str,
    entity_id: int,
    value: str | None,
) -> CustomFieldValue:
    """Set or update a custom field value for an entity."""
    existing = (
        session.query(CustomFieldValue)
        .filter(
            CustomFieldValue.field_definition_id == field_definition_id,
            CustomFieldValue.entity_type == entity_type,
            CustomFieldValue.entity_id == entity_id,
        )
        .first()
    )

    if existing:
        existing.value = value
        session.commit()
        return existing

    field_value = CustomFieldValue(
        field_definition_id=field_definition_id,
        entity_type=entity_type,
        entity_id=entity_id,
        value=value,
    )
    session.add(field_value)
    session.commit()
    return field_value


def delete_field_value(session: Session, value_id: int) -> bool:
    """Delete a custom field value."""
    value = session.query(CustomFieldValue).filter(CustomFieldValue.id == value_id).first()
    if not value:
        return False
    session.delete(value)
    session.commit()
    return True
