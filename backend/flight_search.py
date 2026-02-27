"""Google Flights uzerinden hafta sonu aramalari."""

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable, Optional

import pandas as pd
from fast_flights import FlightData, Passengers, get_flights

from data_processing import (
    build_weekend_trips,
    parse_departure_time,
    parse_duration_minutes,
    parse_price,
)


ORIGINS = ["IST", "SAW"]

DESTINATIONS = [
    {"code": "CDG", "city": "Paris", "country": "Fransa"},
    {"code": "NCE", "city": "Nice", "country": "Fransa"},
    {"code": "AMS", "city": "Amsterdam", "country": "Hollanda"},
    {"code": "RTM", "city": "Rotterdam", "country": "Hollanda"},
    {"code": "BRU", "city": "Bruksel", "country": "Belcika"},
    {"code": "BER", "city": "Berlin", "country": "Almanya"},
    {"code": "MUC", "city": "Munih", "country": "Almanya"},
    {"code": "FRA", "city": "Frankfurt", "country": "Almanya"},
    {"code": "VIE", "city": "Viyana", "country": "Avusturya"},
    {"code": "ZRH", "city": "Zurih", "country": "Isvicre"},
    {"code": "GVA", "city": "Cenevre", "country": "Isvicre"},
    {"code": "PRG", "city": "Prag", "country": "Cekya"},
    {"code": "WAW", "city": "Varsova", "country": "Polonya"},
    {"code": "BUD", "city": "Budapeste", "country": "Macaristan"},
    {"code": "FCO", "city": "Roma", "country": "Italya"},
    {"code": "VCE", "city": "Venedik", "country": "Italya"},
    {"code": "FLR", "city": "Floransa", "country": "Italya"},
    {"code": "MXP", "city": "Milano", "country": "Italya"},
    {"code": "MAD", "city": "Madrid", "country": "Ispanya"},
    {"code": "BCN", "city": "Barselona", "country": "Ispanya"},
    {"code": "LIS", "city": "Lizbon", "country": "Portekiz"},
    {"code": "OPO", "city": "Porto", "country": "Portekiz"},
    {"code": "ATH", "city": "Atina", "country": "Yunanistan"},
    {"code": "CPH", "city": "Kopenhag", "country": "Danimarka"},
    {"code": "ARN", "city": "Stockholm", "country": "Isvec"},
    {"code": "OSL", "city": "Oslo", "country": "Norvec"},
    {"code": "HEL", "city": "Helsinki", "country": "Finlandiya"},
    {"code": "KEF", "city": "Reykjavik", "country": "Izlanda"},
]

DESTINATION_MAP = {d["code"]: d for d in DESTINATIONS}

TURKISH_DAYS = {4: "Cuma", 5: "Cumartesi", 6: "Pazar"}

WORKERS = int(os.getenv("FLIGHT_SEARCH_WORKERS", "6"))
RETRY_COUNT = int(os.getenv("FLIGHT_SEARCH_RETRY_COUNT", "2"))
RETRY_BASE_WAIT = float(os.getenv("FLIGHT_SEARCH_RETRY_BASE_WAIT", "2"))
MAX_FLIGHTS_PER_DATE = int(os.getenv("FLIGHT_MAX_FLIGHTS_PER_DATE", "8"))
MAX_WEEKENDS_PER_REQUEST = int(os.getenv("FLIGHT_MAX_WEEKENDS_PER_REQUEST", "4"))
MAX_DESTINATIONS_PER_REQUEST = int(os.getenv("FLIGHT_MAX_DESTINATIONS_PER_REQUEST", "10"))

CACHE_TTL_SECONDS = int(os.getenv("FLIGHT_CACHE_TTL_SECONDS", "600"))
_CACHE: dict[tuple, tuple[float, list[dict]]] = {}


@dataclass(frozen=True)
class SearchConfig:
    weekend_start: date
    weekend_end: date
    destinations: tuple[str, ...]
    direct_only: bool


def get_destinations() -> list[dict]:
    return [
        {
            "code": d["code"],
            "city": d["city"],
            "country": d["country"],
            "label": f'{d["city"]} ({d["code"]})',
        }
        for d in DESTINATIONS
    ]


def _next_saturday(d: date) -> date:
    days_until = (5 - d.weekday()) % 7
    return d + timedelta(days=days_until)


def get_weekends(weeks: int = 12) -> list[str]:
    start = _next_saturday(date.today())
    return [(start + timedelta(days=7 * i)).isoformat() for i in range(weeks)]


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def _weekend_span(start: date, end: date) -> list[date]:
    if start > end:
        start, end = end, start
    # Guvenli hizli adim: haftalik ilerle
    days_until = (5 - start.weekday()) % 7
    current = start + timedelta(days=days_until)
    weekends = []
    while current <= end:
        weekends.append(current)
        current += timedelta(days=7)
    return weekends


def _search_dates(weekends: Iterable[date]) -> list[date]:
    dates: set[date] = set()
    for sat in weekends:
        dates.add(sat - timedelta(days=1))  # Cuma
        dates.add(sat)
        dates.add(sat + timedelta(days=1))  # Pazar
    return sorted(dates)


def _cache_get(key: tuple) -> Optional[list[dict]]:
    now = time.time()
    entry = _CACHE.get(key)
    if not entry:
        return None
    expires_at, data = entry
    if expires_at < now:
        _CACHE.pop(key, None)
        return None
    return data


def _cache_set(key: tuple, data: list[dict]) -> None:
    _CACHE[key] = (time.time() + CACHE_TTL_SECONDS, data)


def _search_one(origin: str, dest: str, d: date, direct_only: bool) -> list[dict]:
    city = DESTINATION_MAP[dest]["city"]
    country = DESTINATION_MAP[dest]["country"]
    day_name = TURKISH_DAYS.get(d.weekday(), "")

    for attempt in range(RETRY_COUNT):
        try:
            result = get_flights(
                flight_data=[FlightData(date=d.isoformat(), from_airport=origin, to_airport=dest)],
                trip="one-way",
                seat="economy",
                passengers=Passengers(adults=1),
            )
            rows = []
            for fl in result.flights[:MAX_FLIGHTS_PER_DATE]:
                stops = int(fl.stops) if fl.stops is not None else None
                if direct_only and stops not in (0, None):
                    continue
                rows.append(
                    {
                        "kalkis_havalimani": origin,
                        "varis_havalimani": dest,
                        "varis_sehir": city,
                        "varis_ulke": country,
                        "tarih": d.isoformat(),
                        "gun": day_name,
                        "havayolu": str(getattr(fl, "name", "")),
                        "kalkis_saati": str(getattr(fl, "departure", "")),
                        "varis_saati": str(getattr(fl, "arrival", "")),
                        "sure": str(getattr(fl, "duration", "")),
                        "aktarma": stops if stops is not None else "",
                        "fiyat": str(getattr(fl, "price", "")),
                        "en_iyi": "Evet" if getattr(fl, "is_best", False) else "Hayir",
                    }
                )
            return rows
        except Exception:
            wait = RETRY_BASE_WAIT ** (attempt + 1)
            time.sleep(wait)
    return []


def _prepare_dataframe(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["fiyat_tl"] = df["fiyat"].apply(parse_price)
    df["kalkis_dt"] = df["kalkis_saati"].apply(parse_departure_time)
    df["varis_dt"] = df["varis_saati"].apply(parse_departure_time)
    df["sure_dk"] = df["sure"].apply(parse_duration_minutes)
    df["aktarma_int"] = pd.to_numeric(df["aktarma"], errors="coerce").fillna(99).astype(int)
    df = df.dropna(subset=["fiyat_tl", "kalkis_dt"])
    df["kalkis_saat"] = df["kalkis_dt"].apply(lambda dt: dt.hour + dt.minute / 60)
    df["tarih_dt"] = pd.to_datetime(df["tarih"])
    return df


def search_weekend_trips(
    weekend_start: Optional[str],
    weekend_end: Optional[str],
    destinations: Optional[list[str]],
    max_price: Optional[float],
    direct_only: bool,
) -> list[dict]:
    start = _parse_date(weekend_start) or _next_saturday(date.today())
    end = _parse_date(weekend_end) or start

    weekends = _weekend_span(start, end)
    if len(weekends) > MAX_WEEKENDS_PER_REQUEST:
        raise ValueError("Cok fazla hafta sonu secildi. Daha dar bir aralik secin.")

    dest_codes = [d for d in (destinations or []) if d in DESTINATION_MAP]
    if not dest_codes:
        dest_codes = [d["code"] for d in DESTINATIONS]
    if len(dest_codes) > MAX_DESTINATIONS_PER_REQUEST:
        raise ValueError("Cok fazla destinasyon secildi. Daha az destinasyon deneyin.")

    config = SearchConfig(
        weekend_start=weekends[0],
        weekend_end=weekends[-1],
        destinations=tuple(sorted(dest_codes)),
        direct_only=direct_only,
    )
    cache_key = (config.weekend_start.isoformat(), config.weekend_end.isoformat(), config.destinations, config.direct_only)
    cached = _cache_get(cache_key)
    if cached is not None:
        trips = cached
    else:
        dates = _search_dates(weekends)
        rows: list[dict] = []
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            futures = [
                executor.submit(_search_one, origin, dest, d, direct_only)
                for origin in ORIGINS
                for dest in dest_codes
                for d in dates
            ]
            for future in as_completed(futures):
                rows.extend(future.result())

        df = _prepare_dataframe(rows)
        if df.empty:
            trips = []
        else:
            trips_df = build_weekend_trips(df)
            trips = trips_df.to_dict(orient="records")
        _cache_set(cache_key, trips)

    if max_price is not None:
        trips = [t for t in trips if t.get("toplam_fiyat") is not None and t["toplam_fiyat"] <= max_price]

    return trips
