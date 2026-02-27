"""SQLite veritabani baglantisi ve tablo olusturma."""

import os
import sqlite3
from contextlib import contextmanager

DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "flights.db"))


def get_db_path():
    path = os.path.abspath(DATABASE_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


@contextmanager
def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kalkis_havalimani TEXT NOT NULL,
                varis_havalimani TEXT NOT NULL,
                varis_sehir TEXT NOT NULL,
                varis_ulke TEXT NOT NULL,
                hafta_sonu TEXT NOT NULL,
                havayolu_gidis TEXT,
                kalkis_saati_gidis TEXT,
                varis_saati_gidis TEXT,
                sure_gidis TEXT,
                sure_dk_gidis INTEGER,
                aktarma_int_gidis INTEGER,
                fiyat_tl_gidis REAL,
                havayolu_donus TEXT,
                kalkis_saati_donus TEXT,
                varis_saati_donus TEXT,
                sure_donus TEXT,
                sure_dk_donus INTEGER,
                aktarma_int_donus INTEGER,
                fiyat_tl_donus REAL,
                toplam_fiyat REAL NOT NULL,
                toplam_sure INTEGER,
                max_aktarma INTEGER,
                skor REAL,
                skor_direkt REAL,
                skor_fiyat REAL,
                skor_sure REAL,
                skor_saat REAL
            );

            CREATE INDEX IF NOT EXISTS idx_trips_hafta_sonu ON trips(hafta_sonu);
            CREATE INDEX IF NOT EXISTS idx_trips_varis_sehir ON trips(varis_sehir);
            CREATE INDEX IF NOT EXISTS idx_trips_toplam_fiyat ON trips(toplam_fiyat);
            CREATE INDEX IF NOT EXISTS idx_trips_skor ON trips(skor);
            CREATE INDEX IF NOT EXISTS idx_trips_kalkis ON trips(kalkis_havalimani);
            CREATE INDEX IF NOT EXISTS idx_trips_max_aktarma ON trips(max_aktarma);

            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                name TEXT,
                rate_limit_per_minute INTEGER DEFAULT 60,
                rate_limit_per_hour INTEGER DEFAULT 500,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        conn.commit()


if __name__ == "__main__":
    init_db()
    print(f"Veritabani olusturuldu: {get_db_path()}")
