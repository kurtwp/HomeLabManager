"""PSTN Audit Trail model — tracks all changes to PSTN entities."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text

from app.database.pstn_db import PSTNBase


class PSTNAudit(PSTNBase):
    """Audit log entry for PSTN module changes."""

    __tablename__ = "pstn_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)  # "range", "number", "customer"
    entity_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)  # "created", "updated", "deleted"
    details = Column(Text, nullable=True)  # JSON string of what changed
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<PSTNAudit {self.action} {self.entity_type}:{self.entity_id}>"
