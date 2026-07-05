"""PSTN/Telephony models."""

from app.models.pstn.number_range import NumberRange
from app.models.pstn.phone_number import PhoneNumber

__all__ = [
    "NumberRange",
    "PhoneNumber",
]
