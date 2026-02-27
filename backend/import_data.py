"""CSV verisini isle ve SQLite'a aktar."""

import os
import sys
import secrets

# data_processing.py projenin kok dizininde
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_processing import load_and_clean, build_weekend_trips
from database import get_connection, init_db

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "ucuslar_ara.csv")


def import_trips(csv_path: str = CSV_PATH):
    print("Veri yukleniyor ve isleniyor...")
    df = load_and_clean(csv_path)
    print(f"Temiz satir: {len(df)}")

    trips = build_weekend_trips(df)
    print(f"Hafta sonu ciftleri: {len(trips)}")

    if trips.empty:
        print("Eslesen ucus bulunamadi!")
        return

    columns = [
        "kalkis_havalimani", "varis_havalimani", "varis_sehir_gidis", "varis_ulke_gidis",
        "hafta_sonu", "havayolu_gidis", "kalkis_saati_gidis", "varis_saati_gidis",
        "sure_gidis", "sure_dk_gidis", "aktarma_int_gidis", "fiyat_tl_gidis",
        "havayolu_donus", "kalkis_saati_donus", "varis_saati_donus",
        "sure_donus", "sure_dk_donus", "aktarma_int_donus", "fiyat_tl_donus",
        "toplam_fiyat", "toplam_sure", "max_aktarma",
        "skor", "skor_direkt", "skor_fiyat", "skor_sure", "skor_saat",
    ]

    db_columns = [
        "kalkis_havalimani", "varis_havalimani", "varis_sehir", "varis_ulke",
        "hafta_sonu", "havayolu_gidis", "kalkis_saati_gidis", "varis_saati_gidis",
        "sure_gidis", "sure_dk_gidis", "aktarma_int_gidis", "fiyat_tl_gidis",
        "havayolu_donus", "kalkis_saati_donus", "varis_saati_donus",
        "sure_donus", "sure_dk_donus", "aktarma_int_donus", "fiyat_tl_donus",
        "toplam_fiyat", "toplam_sure", "max_aktarma",
        "skor", "skor_direkt", "skor_fiyat", "skor_sure", "skor_saat",
    ]

    # CSV'deki sure_gidis/sure_donus kolonlari yoksa orijinal sure kolonlarindan al
    for col in columns:
        if col not in trips.columns:
            trips[col] = None

    init_db()

    with get_connection() as conn:
        conn.execute("DELETE FROM trips")

        placeholders = ", ".join(["?"] * len(db_columns))
        col_names = ", ".join(db_columns)
        sql = f"INSERT INTO trips ({col_names}) VALUES ({placeholders})"

        batch = []
        for _, row in trips.iterrows():
            values = []
            for src_col in columns:
                val = row.get(src_col)
                if hasattr(val, 'item'):
                    val = val.item()
                if val is None or (isinstance(val, float) and val != val):
                    val = None
                values.append(val)
            batch.append(tuple(values))

            if len(batch) >= 5000:
                conn.executemany(sql, batch)
                batch.clear()

        if batch:
            conn.executemany(sql, batch)

        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
        print(f"SQLite'a {count:,} kayit aktarildi.")


def create_default_api_key():
    key = os.getenv("API_KEY_PUBLIC", secrets.token_urlsafe(32))
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM api_keys WHERE key = ?", (key,)).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO api_keys (key, name, rate_limit_per_minute, rate_limit_per_hour) VALUES (?, ?, ?, ?)",
                (key, "public-frontend", 60, 500),
            )
            conn.commit()
            print(f"API key olusturuldu: {key}")
        else:
            print(f"API key zaten mevcut: {key}")


if __name__ == "__main__":
    import_trips()
    create_default_api_key()
