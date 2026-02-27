"""
Streamlit Hafta Sonu Ucus Dashboard'u
Istanbul'dan Avrupa'ya en uygun hafta sonu tatili ucuslarini analiz eder.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data_processing import load_and_clean, build_weekend_trips

st.set_page_config(
    page_title="Hafta Sonu Ucus Bulucu",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .deal-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 12px;
        border-left: 4px solid #38bdf8;
    }
    .deal-card h3 { margin: 0 0 8px 0; color: #f1f5f9; }
    .deal-card p { margin: 2px 0; color: #94a3b8; font-size: 14px; }
    .deal-price { color: #4ade80; font-size: 24px; font-weight: 700; }
    .deal-score {
        display: inline-block;
        background: #38bdf8;
        color: #0f172a;
        padding: 2px 10px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 13px;
    }
    .metric-box {
        background: #1e293b;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .metric-box h2 { color: #4ade80; margin: 0; }
    .metric-box p { color: #94a3b8; margin: 4px 0 0 0; font-size: 13px; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_data():
    df = load_and_clean()
    trips = build_weekend_trips(df)
    return df, trips


def main():
    st.title("✈️ Hafta Sonu Ucus Bulucu")
    st.caption("Istanbul'dan Avrupa'ya en uygun hafta sonu tatili firsatlari")

    with st.spinner("Veriler yukleniyor..."):
        raw_df, trips = load_data()

    if trips.empty:
        st.error("Eslesen ucus bulunamadi. Once search_flights.py'yi calistirin.")
        return

    # ── Sidebar Filtreler ──────────────────────────────────────────────
    with st.sidebar:
        st.header("🔍 Filtreler")

        all_weekends = sorted(trips["hafta_sonu"].unique())
        if len(all_weekends) >= 2:
            we_start, we_end = st.select_slider(
                "Hafta sonu araligi",
                options=all_weekends,
                value=(all_weekends[0], all_weekends[-1]),
            )
        else:
            we_start = we_end = all_weekends[0]

        cities = sorted(trips["varis_sehir_gidis"].unique())
        selected_cities = st.multiselect("Destinasyon", cities, default=[])

        max_price = int(trips["toplam_fiyat"].quantile(0.95))
        price_limit = st.slider(
            "Maks. toplam fiyat (TRY)",
            min_value=1000,
            max_value=int(trips["toplam_fiyat"].max()),
            value=max_price,
            step=500,
        )

        direct_only = st.toggle("Sadece direkt ucus", value=False)

        origin_choice = st.radio(
            "Kalkis havalimani",
            ["Hepsi", "IST", "SAW"],
            horizontal=True,
        )

    # ── Filtreleme ─────────────────────────────────────────────────────
    mask = (
        (trips["hafta_sonu"] >= we_start)
        & (trips["hafta_sonu"] <= we_end)
        & (trips["toplam_fiyat"] <= price_limit)
    )
    if selected_cities:
        mask &= trips["varis_sehir_gidis"].isin(selected_cities)
    if direct_only:
        mask &= trips["max_aktarma"] == 0
    if origin_choice != "Hepsi":
        mask &= trips["kalkis_havalimani"] == origin_choice

    filtered = trips[mask].copy()

    # ── Ozet Metrikler ─────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam Firsat", f"{len(filtered):,}")
    c2.metric("En Ucuz", f"₺{int(filtered['toplam_fiyat'].min()):,}" if len(filtered) else "—")
    c3.metric("Ort. Fiyat", f"₺{int(filtered['toplam_fiyat'].mean()):,}" if len(filtered) else "—")
    c4.metric("Destinasyon", f"{filtered['varis_sehir_gidis'].nunique()}" if len(filtered) else "0")

    if filtered.empty:
        st.warning("Bu filtrelerle eslesen ucus bulunamadi. Filtreleri genisletin.")
        return

    # ── Tablar ─────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏆 En Iyi Firsatlar",
        "🗺️ Fiyat Haritasi",
        "📊 Destinasyon Karsilastirma",
        "📋 Detay Tablosu",
    ])

    # ── TAB 1: En Iyi Firsatlar ───────────────────────────────────────
    with tab1:
        st.subheader("En Iyi 20 Hafta Sonu Tatili")
        top = filtered.nlargest(20, "skor")

        for _, row in top.iterrows():
            aktarma_gidis = int(row["aktarma_int_gidis"])
            aktarma_donus = int(row["aktarma_int_donus"])
            aktarma_txt_g = "Direkt" if aktarma_gidis == 0 else f"{aktarma_gidis} aktarma"
            aktarma_txt_d = "Direkt" if aktarma_donus == 0 else f"{aktarma_donus} aktarma"

            st.markdown(f"""
            <div class="deal-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <h3>{row['varis_sehir_gidis']}, {row['varis_ulke_gidis']} 
                            <span style="color:#64748b;font-size:14px;">({row['varis_havalimani']})</span>
                        </h3>
                        <p>📅 {row['hafta_sonu']}</p>
                        <p>🛫 Gidis: {row['kalkis_saati_gidis']} → {row['varis_saati_gidis']} ({aktarma_txt_g})</p>
                        <p>🛬 Donus: {row['kalkis_saati_donus']} → {row['varis_saati_donus']} ({aktarma_txt_d})</p>
                        <p>⏱️ {row.get('sure_gidis', '')} + {row.get('sure_donus', '')}</p>
                    </div>
                    <div style="text-align:right;">
                        <div class="deal-price">₺{int(row['toplam_fiyat']):,}</div>
                        <div class="deal-score">Skor: {row['skor']}</div>
                        <p style="margin-top:6px;">{row['kalkis_havalimani']}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 2: Fiyat Haritasi (Heatmap) ───────────────────────────────
    with tab2:
        st.subheader("Destinasyon x Hafta Sonu Fiyat Haritasi")

        heatmap_data = (
            filtered
            .groupby(["varis_sehir_gidis", "hafta_sonu"])["toplam_fiyat"]
            .min()
            .reset_index()
        )
        pivot = heatmap_data.pivot(
            index="varis_sehir_gidis",
            columns="hafta_sonu",
            values="toplam_fiyat",
        )

        fig_heat = px.imshow(
            pivot,
            labels=dict(x="Hafta Sonu", y="Destinasyon", color="Min Fiyat (TRY)"),
            color_continuous_scale="YlGn_r",
            aspect="auto",
        )
        fig_heat.update_layout(height=max(400, len(pivot) * 22))
        st.plotly_chart(fig_heat, use_container_width=True)

    # ── TAB 3: Destinasyon Karsilastirma ───────────────────────────────
    with tab3:
        st.subheader("Destinasyonlara Gore Fiyat")

        dest_stats = (
            filtered
            .groupby("varis_sehir_gidis")["toplam_fiyat"]
            .agg(["min", "mean", "count"])
            .reset_index()
            .rename(columns={
                "varis_sehir_gidis": "Sehir",
                "min": "Min Fiyat",
                "mean": "Ort Fiyat",
                "count": "Secenek",
            })
            .sort_values("Min Fiyat")
        )

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=dest_stats["Sehir"],
            y=dest_stats["Min Fiyat"],
            name="En Ucuz",
            marker_color="#4ade80",
        ))
        fig_bar.add_trace(go.Bar(
            x=dest_stats["Sehir"],
            y=dest_stats["Ort Fiyat"],
            name="Ortalama",
            marker_color="#38bdf8",
            opacity=0.6,
        ))
        fig_bar.update_layout(
            barmode="group",
            xaxis_title="",
            yaxis_title="Fiyat (TRY)",
            height=500,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**En Ucuz 10 Destinasyon**")
            st.dataframe(
                dest_stats.head(10).style.format({"Min Fiyat": "₺{:,.0f}", "Ort Fiyat": "₺{:,.0f}"}),
                hide_index=True,
                use_container_width=True,
            )
        with col_b:
            st.markdown("**En Cok Secenek**")
            st.dataframe(
                dest_stats.nlargest(10, "Secenek").style.format({"Min Fiyat": "₺{:,.0f}", "Ort Fiyat": "₺{:,.0f}"}),
                hide_index=True,
                use_container_width=True,
            )

    # ── TAB 4: Detay Tablosu ──────────────────────────────────────────
    with tab4:
        st.subheader("Tum Eslesmis Ucuslar")

        display_cols = {
            "kalkis_havalimani": "Kalkis",
            "varis_sehir_gidis": "Sehir",
            "varis_ulke_gidis": "Ulke",
            "hafta_sonu": "Hafta Sonu",
            "havayolu_gidis": "Gidis Havayolu",
            "kalkis_saati_gidis": "Gidis Kalkis",
            "aktarma_int_gidis": "Gidis Aktarma",
            "fiyat_tl_gidis": "Gidis Fiyat",
            "havayolu_donus": "Donus Havayolu",
            "kalkis_saati_donus": "Donus Kalkis",
            "aktarma_int_donus": "Donus Aktarma",
            "fiyat_tl_donus": "Donus Fiyat",
            "toplam_fiyat": "Toplam Fiyat",
            "skor": "Skor",
        }

        available = {k: v for k, v in display_cols.items() if k in filtered.columns}
        display_df = filtered[list(available.keys())].rename(columns=available)

        sort_col = st.selectbox("Sirala", list(available.values()), index=list(available.values()).index("Skor"))
        ascending = sort_col not in ("Skor",)
        display_df = display_df.sort_values(sort_col, ascending=ascending)

        st.dataframe(
            display_df,
            hide_index=True,
            use_container_width=True,
            height=600,
        )
        st.caption(f"Toplam {len(display_df):,} sonuc")


if __name__ == "__main__":
    main()
