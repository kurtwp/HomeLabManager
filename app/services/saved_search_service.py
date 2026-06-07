"""Service for saved search queries."""

from sqlalchemy.orm import Session

from app.models.saved_search import SavedSearch


def create_saved_search(
    session: Session,
    name: str,
    entity_type: str,
    filters: dict,
) -> SavedSearch:
    """Create a new saved search."""
    search = SavedSearch(
        name=name,
        entity_type=entity_type,
        filters=filters,
    )
    session.add(search)
    session.commit()
    return search


def get_all_saved_searches(session: Session) -> list[SavedSearch]:
    """Get all saved searches."""
    return session.query(SavedSearch).order_by(SavedSearch.name).all()


def get_saved_search_by_id(session: Session, search_id: int) -> SavedSearch | None:
    """Get a saved search by ID."""
    return session.query(SavedSearch).filter(SavedSearch.id == search_id).first()


def delete_saved_search(session: Session, search_id: int) -> bool:
    """Delete a saved search."""
    search = get_saved_search_by_id(session, search_id)
    if not search:
        return False
    session.delete(search)
    session.commit()
    return True
