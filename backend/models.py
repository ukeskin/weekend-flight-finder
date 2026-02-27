"""Pydantic request/response semalari."""

from typing import Optional
from pydantic import BaseModel


class TripLeg(BaseModel):
    airline: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    duration: Optional[str] = None
    duration_minutes: Optional[int] = None
    stops: Optional[int] = None
    price: Optional[float] = None


class TripItem(BaseModel):
    id: str
    origin: str
    destination_code: str
    destination_city: str
    destination_country: str
    weekend: str
    outbound: TripLeg
    return_leg: TripLeg
    total_price: float
    total_duration_minutes: Optional[int] = None
    max_stops: Optional[int] = None
    score: Optional[float] = None


class PaginatedTrips(BaseModel):
    data: list[TripItem]
    total: int
    page: int
    per_page: int
    total_pages: int


class DestinationOption(BaseModel):
    code: str
    city: str
    country: str
    label: str
