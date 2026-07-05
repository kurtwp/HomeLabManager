"""Customer model for PSTN module — tracks ownership/allocation of numbers."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship

from app.database.pstn_db import PSTNBase


class Customer(PSTNBase):
    """A customer or client who owns/leases phone numbers."""

    __tablename__ = "pstn_customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    account_number = Column(String(100), nullable=True, unique=True)

    contact_name = Column(String(200), nullable=True)
    contact_email = Column(String(200), nullable=True)
    contact_phone = Column(String(50), nullable=True)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    phone_numbers = relationship("PhoneNumber", back_populates="customer", lazy="dynamic")
    number_ranges = relationship("NumberRange", back_populates="customer", lazy="dynamic")

    def __repr__(self):
        return f"<Customer {self.name} ({self.account_number})>"
