#!/usr/bin/env python3
"""
Istanbul -> Avrupa hafta sonu ucuslari arama scripti.
fast-flights kutuphanesi ile Google Flights'tan veri ceker, CSV'ye yazar.
ThreadPoolExecutor ile paralel arama yapar.
Cuma (aksam gidis) + Cumartesi + Pazar ucuslarini arar.
"""

import csv
import json
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

import pandas as pd
from tqdm import tqdm

from fast_flights import FlightData, Passengers, get_flights

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("search_flights.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

WORKERS = 8
RETRY_COUNT = 2
RETRY_BASE_WAIT = 2

DATE_START = date(2026, 3, 20)
DATE_END = date(2026, 7, 15)

ORIGINS = ["IST", "SAW"]

EUROPEAN_AIRPORTS: dict[str, tuple[str, str]] = {
    "CDG": ("Paris", "Fransa"),
    "AMS": ("Amsterdam", "Hollanda"),
    "BRU": ("Bruksel", "Belcika"),
    "BER": ("Berlin", "Almanya"),
    "FRA": ("Frankfurt", "Almanya"),
    "MUC": ("Munih", "Almanya"),
    "VIE": ("Viyana", "Avusturya"),
    "ZRH": ("Zurih", "Isvicre"),
    "PRG": ("Prag", "Cekya"),
    "WAW": ("Varsova", "Polonya"),
    "BUD": ("Budapeste", "Macaristan"),
    "FCO": ("Roma", "Italya"),
    "MXP": ("Milano", "Italya"),
    "MAD": ("Madrid", "Ispanya"),
    "BCN": ("Barselona", "Ispanya"),
    "LIS": ("Lizbon", "Portekiz"),
    "ATH": ("Atina", "Yunanistan"),
    "ARN": ("Stockholm", "Isvec"),
    "CPH": ("Kopenhag", "Danimarka"),
    "OSL": ("Oslo", "Norvec"),
    "HEL": ("Helsinki", "Finlandiya"),
}

TURKISH_DAYS = {4: "Cuma", 5: "Cumartesi", 6: "Pazar"}

CHECKPOINT_FILE = "checkpoint.json"
INTERMEDIATE_CSV = "ucuslar_ara.csv"
OUTPUT_EXCEL = "ucuslar.xlsx"

CSV_COLUMNS = [
    "kalkis_havalimani", "varis_havalimani", "varis_sehir", "varis_ulke",
    "tarih", "gun", "havayolu", "kalkis_saati", "varis_saati",
    "sure", "aktarma", "fiyat", "en_iyi",
]

_lock = threading.Lock()


def get_search_dates(start: date, end: date) -> list[date]:
    """Cuma (4), Cumartesi (5), Pazar (6) gunlerini dondurur."""
    current = start
    days: list[date] = []
    while current <= end:
        if current.weekday() in (4, 5, 6):
            days.append(current)
        current += timedelta(days=1)
    return days


def load_checkpoint() -> set[str]:
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_checkpoint(done: set[str]) -> None:
    with _lock:
        with open(CHECKPOINT_FILE, "w") as f:
            json.dump(sorted(done), f)


def make_key(origin: str, dest: str, d: date) -> str:
    return f"{origin}|{dest}|{d.isoformat()}"


def append_rows_to_csv(rows: list[dict]) -> None:
    if not rows:
        return
    with _lock:
        file_exists = os.path.exists(INTERMEDIATE_CSV) and os.path.getsize(INTERMEDIATE_CSV) > 0
        with open(INTERMEDIATE_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            if not file_exists:
                writer.writeheader()
            writer.writerows(rows)


def search_single(origin: str, dest: str, d: date) -> tuple[str, list[dict]]:
    city, country = EUROPEAN_AIRPORTS[dest]
    day_name = TURKISH_DAYS.get(d.weekday(), "")
    key = make_key(origin, dest, d)

    for attempt in range(RETRY_COUNT):
        try:
            result = get_flights(
                flight_data=[
                    FlightData(date=d.isoformat(), from_airport=origin, to_airport=dest)
                ],
                trip="one-way",
                seat="economy",
                passengers=Passengers(adults=1),
            )
            rows = []
            for fl in result.flights:
                rows.append({
                    "kalkis_havalimani": origin,
                    "varis_havalimani": dest,
                    "varis_sehir": city,
                    "varis_ulke": country,
                    "tarih": d.isoformat(),
                    "gun": day_name,
                    "havayolu": fl.name,
                    "kalkis_saati": fl.departure,
                    "varis_saati": fl.arrival,
                    "sure": fl.duration,
                    "aktarma": fl.stops,
                    "fiyat": fl.price,
                    "en_iyi": "Evet" if fl.is_best else "Hayir",
                })
            return key, rows

        except Exception as e:
            wait = RETRY_BASE_WAIT ** (attempt + 1)
            log.warning("%s->%s %s | Hata (%d/%d): %s", origin, dest, d.isoformat(), attempt + 1, RETRY_COUNT, e)
            time.sleep(wait)

    log.error("%s->%s %s | Basarisiz", origin, dest, d.isoformat())
    return key, []


def export_to_excel(csv_path: str, excel_path: str) -> None:
    if not os.path.exists(csv_path):
        log.error("CSV bulunamadi: %s", csv_path)
        return

    df = pd.read_csv(csv_path, encoding="utf-8")
    if df.empty:
        log.warning("Veri yok, Excel olusturulmuyor.")
        return

    df.rename(columns={
        "kalkis_havalimani": "Kalkis Havalimani",
        "varis_havalimani": "Varis Havalimani",
        "varis_sehir": "Varis Sehir",
        "varis_ulke": "Varis Ulke",
        "tarih": "Tarih",
        "gun": "Gun",
        "havayolu": "Havayolu",
        "kalkis_saati": "Kalkis Saati",
        "varis_saati": "Varis Saati",
        "sure": "Sure",
        "aktarma": "Aktarma Sayisi",
        "fiyat": "Fiyat",
        "en_iyi": "En Iyi",
    }, inplace=True)

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Ucuslar")
        ws = writer.sheets["Ucuslar"]
        for col_cells in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col_cells) + 2
            ws.column_dimensions[col_cells[0].column_letter].width = min(max_len, 30)
        ws.auto_filter.ref = ws.dimensions

    log.info("Excel olusturuldu: %s (%d satir)", excel_path, len(df))


def main() -> None:
    search_days = get_search_dates(DATE_START, DATE_END)
    destinations = list(EUROPEAN_AIRPORTS.keys())
    total_searches = len(ORIGINS) * len(destinations) * len(search_days)

    log.info("Tarih: %s — %s (%d gun)", search_days[0], search_days[-1], len(search_days))
    log.info("Kalkis: %s | Varis: %d | Toplam: %d | Workers: %d",
             ", ".join(ORIGINS), len(destinations), total_searches, WORKERS)

    done = load_checkpoint()
    if done:
        log.info("Checkpoint: %d arama onceden tamamlanmis", len(done))

    tasks: list[tuple[str, str, date]] = []
    for d in search_days:
        for origin in ORIGINS:
            for dest in destinations:
                if make_key(origin, dest, d) not in done:
                    tasks.append((origin, dest, d))

    log.info("Yapilacak arama: %d (atlanacak: %d)", len(tasks), total_searches - len(tasks))

    progress = tqdm(total=total_searches, initial=total_searches - len(tasks), desc="Ucus arama", unit="q")
    flush_every = 100
    pending_rows: list[dict] = []
    completed_since_flush = 0

    def flush():
        nonlocal pending_rows, completed_since_flush
        if pending_rows:
            append_rows_to_csv(pending_rows)
            pending_rows = []
        save_checkpoint(done)
        completed_since_flush = 0

    try:
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futures = {pool.submit(search_single, o, d, dt): (o, d, dt) for o, d, dt in tasks}

            for future in as_completed(futures):
                key, rows = future.result()
                with _lock:
                    done.add(key)
                    pending_rows.extend(rows)
                    completed_since_flush += 1
                progress.update(1)

                if completed_since_flush >= flush_every:
                    flush()

    except KeyboardInterrupt:
        log.info("Durduruldu. Ara sonuclar kaydediliyor...")
    finally:
        flush()
        progress.close()

    log.info("Arama bitti. %d / %d tamamlandi.", len(done), total_searches)
    export_to_excel(INTERMEDIATE_CSV, OUTPUT_EXCEL)
    log.info("Sonuclar: %s", OUTPUT_EXCEL)


if __name__ == "__main__":
    main()
