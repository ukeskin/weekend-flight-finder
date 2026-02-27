"""
Ucus CSV verisini temizler, hafta sonu gidis-donus ciftleri olusturur ve skorlar.
"""

import re
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

CSV_PATH = "ucuslar_ara.csv"


def parse_price(raw) -> Optional[float]:
    """'TRY\\xa012977' -> 12977.0, gecersiz -> None"""
    if not raw or not isinstance(raw, str) or raw == "0":
        return None
    digits = re.sub(r"[^\d.]", "", raw)
    if not digits:
        return None
    val = float(digits)
    return val if val > 0 else None


def parse_departure_time(raw) -> Optional[datetime]:
    """'5:35 PM on Sat, Mar 14' -> datetime(2026, 3, 14, 17, 35)"""
    if not raw or not isinstance(raw, str):
        return None
    try:
        m = re.match(r"(\d{1,2}:\d{2}\s*[AP]M)\s+on\s+\w+,\s+(\w+)\s+(\d{1,2})", raw)
        if not m:
            return None
        time_str, month_str, day_str = m.group(1), m.group(2), m.group(3)
        for year in (2026, 2027):
            try:
                return datetime.strptime(f"{time_str} {month_str} {day_str} {year}", "%I:%M %p %b %d %Y")
            except ValueError:
                continue
        return None
    except Exception:
        return None


def parse_duration_minutes(raw) -> Optional[int]:
    """'21 hr 10 min' -> 1270, '14 hr' -> 840, '' -> None"""
    if not raw or not isinstance(raw, str):
        return None
    hours = 0
    mins = 0
    h = re.search(r"(\d+)\s*hr", raw)
    m = re.search(r"(\d+)\s*min", raw)
    if h:
        hours = int(h.group(1))
    if m:
        mins = int(m.group(1))
    total = hours * 60 + mins
    return total if total > 0 else None


def load_and_clean(csv_path: str = CSV_PATH) -> pd.DataFrame:
    df = pd.read_csv(csv_path, encoding="utf-8", low_memory=False)

    df["fiyat_tl"] = df["fiyat"].apply(parse_price)
    df["kalkis_dt"] = df["kalkis_saati"].apply(parse_departure_time)
    df["varis_dt"] = df["varis_saati"].apply(parse_departure_time)
    df["sure_dk"] = df["sure"].apply(parse_duration_minutes)
    df["aktarma_int"] = pd.to_numeric(df["aktarma"], errors="coerce").fillna(99).astype(int)

    df = df.dropna(subset=["fiyat_tl", "kalkis_dt"])
    df["kalkis_saat"] = df["kalkis_dt"].apply(lambda dt: dt.hour + dt.minute / 60)
    df["tarih_dt"] = pd.to_datetime(df["tarih"])

    return df


def build_weekend_trips(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cuma aksami/Cumartesi sabahi gidis + Pazar ogleden sonra donus
    ciftlerini olusturur.
    """
    outbound_mask = (
        ((df["gun"] == "Cuma") & (df["kalkis_saat"] >= 17))
        | ((df["gun"] == "Cumartesi") & (df["kalkis_saat"] <= 12))
    )
    return_mask = (df["gun"] == "Pazar") & (df["kalkis_saat"] >= 12)

    out_df = df[outbound_mask].copy()
    ret_df = df[return_mask].copy()

    out_df["hafta_sonu"] = out_df["tarih_dt"].apply(_weekend_key)
    ret_df["hafta_sonu"] = ret_df["tarih_dt"].apply(_weekend_key)

    out_df = _keep_best_per_group(out_df, n=5)
    ret_df = _keep_best_per_group(ret_df, n=5)

    trips = out_df.merge(
        ret_df,
        on=["kalkis_havalimani", "varis_havalimani", "hafta_sonu"],
        suffixes=("_gidis", "_donus"),
    )

    trips["toplam_fiyat"] = trips["fiyat_tl_gidis"] + trips["fiyat_tl_donus"]
    trips["toplam_sure"] = trips["sure_dk_gidis"].fillna(0) + trips["sure_dk_donus"].fillna(0)
    trips["max_aktarma"] = trips[["aktarma_int_gidis", "aktarma_int_donus"]].max(axis=1)

    trips = _add_scores(trips)

    return trips.sort_values("skor", ascending=False).reset_index(drop=True)


def _weekend_key(dt) -> str:
    """Bir tarihi ait oldugu hafta sonunun Cumartesi tarihine esler."""
    if hasattr(dt, "weekday"):
        wd = dt.weekday()
        if wd == 4:  # Cuma -> sonraki Cumartesi
            sat = dt + timedelta(days=1)
        elif wd == 5:  # Cumartesi
            sat = dt
        elif wd == 6:  # Pazar -> onceki Cumartesi
            sat = dt - timedelta(days=1)
        else:
            sat = dt
        return sat.strftime("%Y-%m-%d")
    return str(dt)


def _keep_best_per_group(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Her (havalimani, destinasyon, hafta_sonu) icin en ucuz n ucusu tut."""
    return (
        df.sort_values("fiyat_tl")
        .groupby(["kalkis_havalimani", "varis_havalimani", "hafta_sonu"])
        .head(n)
    )


def _add_scores(trips: pd.DataFrame) -> pd.DataFrame:
    t = trips.copy()

    # Direkt ucus bonusu (max 40)
    t["skor_direkt"] = t["max_aktarma"].apply(lambda x: 40 if x == 0 else (20 if x == 1 else 0))

    # Fiyat skoru (max 30) - normalize: en ucuz=30, en pahali=0
    pmin, pmax = t["toplam_fiyat"].quantile(0.05), t["toplam_fiyat"].quantile(0.95)
    if pmax > pmin:
        t["skor_fiyat"] = 30 * (1 - (t["toplam_fiyat"].clip(pmin, pmax) - pmin) / (pmax - pmin))
    else:
        t["skor_fiyat"] = 15.0

    # Sure skoru (max 15)
    smin, smax = t["toplam_sure"].quantile(0.05), t["toplam_sure"].quantile(0.95)
    if smax > smin:
        t["skor_sure"] = 15 * (1 - (t["toplam_sure"].clip(smin, smax) - smin) / (smax - smin))
    else:
        t["skor_sure"] = 7.5

    # Saat uygunlugu (max 15) - gidis ideal 8-10 Cumartesi veya 18-20 Cuma
    def time_score(row):
        gh = row.get("kalkis_saat_gidis", 12)
        day = row.get("gun_gidis", "")
        if day == "Cumartesi":
            ideal = 9.0
        else:
            ideal = 18.5
        diff = abs(gh - ideal)
        return max(0, 15 - diff * 3)

    t["skor_saat"] = t.apply(time_score, axis=1)

    t["skor"] = (t["skor_direkt"] + t["skor_fiyat"] + t["skor_sure"] + t["skor_saat"]).round(1)

    return t


if __name__ == "__main__":
    print("Veri yukleniyor...")
    df = load_and_clean()
    print(f"Temiz satir: {len(df)}")
    trips = build_weekend_trips(df)
    print(f"Hafta sonu ciftleri: {len(trips)}")
    if not trips.empty:
        print("\nEn iyi 5 firsat:")
        cols = ["kalkis_havalimani", "varis_havalimani", "hafta_sonu",
                "toplam_fiyat", "max_aktarma", "skor"]
        print(trips[cols].head(5).to_string(index=False))
