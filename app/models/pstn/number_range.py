"""NumberRange model for PSTN module."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database.pstn_db import PSTNBase


class NumberRange(PSTNBase):
    """A range of telephone numbers (DID block, extension range, etc.)."""

    __tablename__ = "number_ranges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    range_start = Column(String(20), nullable=False)  # E.164 e.g. "+15550100"
    range_end = Column(String(20), nullable=False)    # E.164 e.g. "+15550199"

    country_code = Column(String(10), nullable=True)
    area_code = Column(String(10), nullable=True)
    prefix = Column(String(20), nullable=True)

    provider = Column(String(200), nullable=True)  # Telecom provider name

    range_type = Column(String(20), nullable=False, default="master")  # "master" or "sub"
    parent_range_id = Column(Integer, ForeignKey("number_ranges.id"), nullable=True)

    total_numbers = Column(Integer, nullable=True)

    status = Column(String(20), nullable=False, default="active")  # active, inactive, reserved

    customer_id = Column(Integer, ForeignKey("pstn_customers.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    parent_range = relationship("NumberRange", remote_side=[id], backref="sub_ranges")
    phone_numbers = relationship("PhoneNumber", back_populates="number_range", lazy="dynamic")
    customer = relationship("Customer", back_populates="number_ranges")

    def __repr__(self):
        return f"<NumberRange {self.name} ({self.range_start} - {self.range_end})>"
