"""PhoneNumber model for PSTN module."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database.pstn_db import PSTNBase


class PhoneNumber(PSTNBase):
    """An individual telephone number with assignment and status tracking."""

    __tablename__ = "phone_numbers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(String(20), nullable=False, unique=True)  # Full E.164 e.g. "+15550101"
    extension = Column(String(20), nullable=True)  # Internal extension e.g. "4501"

    number_type = Column(String(20), nullable=False, default="did")
    # Types: "did", "extension", "toll_free", "fax", "other"

    status = Column(String(20), nullable=False, default="active")
    # Status: "active", "inactive", "reserved", "future_use"

    description = Column(Text, nullable=True)  # What it's used for
    assigned_to = Column(String(200), nullable=True)  # Person/team name
    department = Column(String(200), nullable=True)
    location = Column(String(200), nullable=True)  # Physical location
    device_name = Column(String(200), nullable=True)  # PBX/gateway name

    range_id = Column(Integer, ForeignKey("number_ranges.id"), nullable=True)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    number_range = relationship("NumberRange", back_populates="phone_numbers")

    def __repr__(self):
        return f"<PhoneNumber {self.number} ({self.status})>"
