"""Ucus API endpoint'leri."""

from typing import Optional

from fastapi import APIRouter, Query

from backend.database import get_connection
from backend.models import (
    PaginatedTrips, TripResponse, StatsResponse,
    HeatmapCell, CityCompare,
)

router = APIRouter(prefix="/api", tags=["flights"])


def _build_where(
    weekend_start: Optional[str],
    weekend_end: Optional[str],
    cities: Optional[str],
    max_price: Optional[float],
    direct_only: bool,
    origin: Optional[str],
):
    clauses = []
    params = []

    if weekend_start:
        clauses.append("hafta_sonu >= ?")
        params.append(weekend_start)
    if weekend_end:
        clauses.append("hafta_sonu <= ?")
        params.append(weekend_end)
    if cities:
        city_list = [c.strip() for c in cities.split(",") if c.strip()]
        if city_list:
            placeholders = ",".join(["?"] * len(city_list))
            clauses.append(f"varis_sehir IN ({placeholders})")
            params.extend(city_list)
    if max_price is not None:
        clauses.append("toplam_fiyat <= ?")
        params.append(max_price)
    if direct_only:
        clauses.append("max_aktarma = 0")
    if origin and origin.upper() in ("IST", "SAW"):
        clauses.append("kalkis_havalimani = ?")
        params.append(origin.upper())

    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    return where, params


@router.get("/trips", response_model=PaginatedTrips)
def get_trips(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    weekend_start: Optional[str] = None,
    weekend_end: Optional[str] = None,
    cities: Optional[str] = None,
    max_price: Optional[float] = None,
    direct_only: bool = False,
    origin: Optional[str] = None,
    sort_by: str = Query("skor", pattern="^(skor|toplam_fiyat|toplam_sure|hafta_sonu)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
):
    where, params = _build_where(weekend_start, weekend_end, cities, max_price, direct_only, origin)

    with get_connection() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM trips{where}", params).fetchone()[0]

        offset = (page - 1) * per_page
        rows = conn.execute(
            f"SELECT * FROM trips{where} ORDER BY {sort_by} {sort_order} LIMIT ? OFFSET ?",
            params + [per_page, offset],
        ).fetchall()

        data = [TripResponse(**dict(row)) for row in rows]
        total_pages = (total + per_page - 1) // per_page

    return PaginatedTrips(data=data, total=total, page=page, per_page=per_page, total_pages=total_pages)


@router.get("/trips/top", response_model=list[TripResponse])
def get_top_trips(
    n: int = Query(20, ge=1, le=100),
    weekend_start: Optional[str] = None,
    weekend_end: Optional[str] = None,
    cities: Optional[str] = None,
    max_price: Optional[float] = None,
    direct_only: bool = False,
    origin: Optional[str] = None,
):
    where, params = _build_where(weekend_start, weekend_end, cities, max_price, direct_only, origin)

    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM trips{where} ORDER BY skor DESC LIMIT ?",
            params + [n],
        ).fetchall()

    return [TripResponse(**dict(row)) for row in rows]


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    weekend_start: Optional[str] = None,
    weekend_end: Optional[str] = None,
    cities: Optional[str] = None,
    max_price: Optional[float] = None,
    direct_only: bool = False,
    origin: Optional[str] = None,
):
    where, params = _build_where(weekend_start, weekend_end, cities, max_price, direct_only, origin)

    with get_connection() as conn:
        row = conn.execute(
            f"SELECT COUNT(*) as total, MIN(toplam_fiyat) as cheapest, "
            f"AVG(toplam_fiyat) as average, COUNT(DISTINCT varis_sehir) as destinations "
            f"FROM trips{where}",
            params,
        ).fetchone()

    return StatsResponse(
        total=row["total"],
        cheapest=row["cheapest"],
        average=round(row["average"], 0) if row["average"] else None,
        destinations=row["destinations"],
    )


@router.get("/destinations", response_model=list[str])
def get_destinations():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT varis_sehir FROM trips ORDER BY varis_sehir"
        ).fetchall()
    return [row["varis_sehir"] for row in rows]


@router.get("/weekends", response_model=list[str])
def get_weekends():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT hafta_sonu FROM trips ORDER BY hafta_sonu"
        ).fetchall()
    return [row["hafta_sonu"] for row in rows]


@router.get("/heatmap", response_model=list[HeatmapCell])
def get_heatmap(
    weekend_start: Optional[str] = None,
    weekend_end: Optional[str] = None,
    cities: Optional[str] = None,
    max_price: Optional[float] = None,
    direct_only: bool = False,
    origin: Optional[str] = None,
):
    where, params = _build_where(weekend_start, weekend_end, cities, max_price, direct_only, origin)

    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT varis_sehir, hafta_sonu, MIN(toplam_fiyat) as min_price "
            f"FROM trips{where} GROUP BY varis_sehir, hafta_sonu "
            f"ORDER BY varis_sehir, hafta_sonu",
            params,
        ).fetchall()

    return [HeatmapCell(city=r["varis_sehir"], weekend=r["hafta_sonu"], min_price=r["min_price"]) for r in rows]


@router.get("/city-compare", response_model=list[CityCompare])
def get_city_compare(
    weekend_start: Optional[str] = None,
    weekend_end: Optional[str] = None,
    cities: Optional[str] = None,
    max_price: Optional[float] = None,
    direct_only: bool = False,
    origin: Optional[str] = None,
):
    where, params = _build_where(weekend_start, weekend_end, cities, max_price, direct_only, origin)

    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT varis_sehir, MIN(toplam_fiyat) as min_price, "
            f"ROUND(AVG(toplam_fiyat), 0) as avg_price, COUNT(*) as count "
            f"FROM trips{where} GROUP BY varis_sehir ORDER BY min_price",
            params,
        ).fetchall()

    return [CityCompare(city=r["varis_sehir"], min_price=r["min_price"],
                        avg_price=r["avg_price"], count=r["count"]) for r in rows]
