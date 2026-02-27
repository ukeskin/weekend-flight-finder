"""Ucus API endpoint'leri (canli arama)."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.flight_search import get_destinations, get_weekends, search_weekend_trips
from backend.models import DestinationOption, PaginatedTrips, TripItem

router = APIRouter(prefix="/api", tags=["flights"])


def _parse_destinations(destinations: Optional[str]) -> Optional[list[str]]:
    if not destinations:
        return None
    return [d.strip().upper() for d in destinations.split(",") if d.strip()]


def _map_trip(row: dict) -> TripItem:
    outbound = {
        "airline": row.get("havayolu_gidis"),
        "departure_time": row.get("kalkis_saati_gidis"),
        "arrival_time": row.get("varis_saati_gidis"),
        "duration": row.get("sure_gidis"),
        "duration_minutes": row.get("sure_dk_gidis"),
        "stops": row.get("aktarma_int_gidis"),
        "price": row.get("fiyat_tl_gidis"),
    }
    return_leg = {
        "airline": row.get("havayolu_donus"),
        "departure_time": row.get("kalkis_saati_donus"),
        "arrival_time": row.get("varis_saati_donus"),
        "duration": row.get("sure_donus"),
        "duration_minutes": row.get("sure_dk_donus"),
        "stops": row.get("aktarma_int_donus"),
        "price": row.get("fiyat_tl_donus"),
    }
    trip_id = f"{row.get('kalkis_havalimani')}-{row.get('varis_havalimani')}-{row.get('hafta_sonu')}-{row.get('kalkis_saati_gidis')}-{row.get('kalkis_saati_donus')}"

    return TripItem(
        id=trip_id,
        origin=row.get("kalkis_havalimani", ""),
        destination_code=row.get("varis_havalimani", ""),
        destination_city=row.get("varis_sehir", ""),
        destination_country=row.get("varis_ulke", ""),
        weekend=row.get("hafta_sonu", ""),
        outbound=outbound,
        return_leg=return_leg,
        total_price=row.get("toplam_fiyat") or 0,
        total_duration_minutes=row.get("toplam_sure"),
        max_stops=row.get("max_aktarma"),
        score=row.get("skor"),
    )


@router.get("/destinations", response_model=list[DestinationOption])
def list_destinations():
    return get_destinations()


@router.get("/weekends", response_model=list[str])
def list_weekends():
    return get_weekends()


@router.get("/trips", response_model=PaginatedTrips)
def get_trips(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    weekend_start: Optional[str] = None,
    weekend_end: Optional[str] = None,
    destinations: Optional[str] = None,
    max_price: Optional[float] = None,
    direct_only: bool = False,
    sort_by: str = Query("score", pattern="^(score|total_price|total_duration_minutes|weekend)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
):
    dest_list = _parse_destinations(destinations)
    try:
        raw_trips = search_weekend_trips(
            weekend_start=weekend_start,
            weekend_end=weekend_end,
            destinations=dest_list,
            max_price=max_price,
            direct_only=direct_only,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    trips = [_map_trip(row) for row in raw_trips]

    def sort_key(item: TripItem):
        if sort_by == "total_price":
            return item.total_price or 0
        if sort_by == "total_duration_minutes":
            return item.total_duration_minutes or 0
        if sort_by == "weekend":
            return item.weekend or ""
        return item.score or 0

    reverse = sort_order == "desc"
    trips = sorted(trips, key=sort_key, reverse=reverse)

    total = len(trips)
    offset = (page - 1) * per_page
    data = trips[offset: offset + per_page]
    total_pages = (total + per_page - 1) // per_page if total else 1

    return PaginatedTrips(
        data=data,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )
