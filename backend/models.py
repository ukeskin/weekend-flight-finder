"""Pydantic request/response semalari."""

from typing import Optional
from pydantic import BaseModel, Field


class TripFilters(BaseModel):
    weekend_start: Optional[str] = None
    weekend_end: Optional[str] = None
    cities: Optional[str] = None
    max_price: Optional[float] = None
    direct_only: bool = False
    origin: Optional[str] = None


class TripResponse(BaseModel):
    id: int
    kalkis_havalimani: str
    varis_havalimani: str
    varis_sehir: str
    varis_ulke: str
    hafta_sonu: str
    havayolu_gidis: Optional[str] = None
    kalkis_saati_gidis: Optional[str] = None
    varis_saati_gidis: Optional[str] = None
    sure_gidis: Optional[str] = None
    sure_dk_gidis: Optional[int] = None
    aktarma_int_gidis: Optional[int] = None
    fiyat_tl_gidis: Optional[float] = None
    havayolu_donus: Optional[str] = None
    kalkis_saati_donus: Optional[str] = None
    varis_saati_donus: Optional[str] = None
    sure_donus: Optional[str] = None
    sure_dk_donus: Optional[int] = None
    aktarma_int_donus: Optional[int] = None
    fiyat_tl_donus: Optional[float] = None
    toplam_fiyat: float
    toplam_sure: Optional[int] = None
    max_aktarma: Optional[int] = None
    skor: Optional[float] = None


class PaginatedTrips(BaseModel):
    data: list[TripResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class StatsResponse(BaseModel):
    total: int
    cheapest: Optional[float] = None
    average: Optional[float] = None
    destinations: int


class HeatmapCell(BaseModel):
    city: str
    weekend: str
    min_price: float


class CityCompare(BaseModel):
    city: str
    min_price: float
    avg_price: float
    count: int
