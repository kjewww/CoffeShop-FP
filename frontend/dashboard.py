import streamlit as st
import pandas as pd
from api_client import get_analytics_summary, get_revenue_per_day, get_best_selling_menu

def render_dashboard_page():
    st.title("Dashboard Analytics & Ringkasan")

    summary = get_analytics_summary()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Pendapatan", f"Rp {summary.get('total_revenue', 0):,}")
    c2.metric("Total Transaksi Nota", f"{summary.get('total_transactions', 0)} Nota")
    c3.metric("Varian Menu Aktif", f"{summary.get('total_menus', 0)} Menu")

    st.markdown("---")
    st.subheader("Grafik Pendapatan Harian")
    rev_day = get_revenue_per_day()
    if rev_day:
        df_rev = pd.DataFrame(rev_day)
        df_rev.columns = ["Tanggal", "Pendapatan (Rp)"]
        st.line_chart(df_rev.set_index("Tanggal"))
    else:
        st.info("Data grafik harian belum tersedia (Belum ada transaksi di database Vercel Anda).")

    st.subheader("5 Menu Paling Laris")
    best_menu = get_best_selling_menu()
    if best_menu:
        df_best = pd.DataFrame(best_menu)
        df_best.columns = ["Nama Menu", "Jumlah Terjual"]
        st.bar_chart(df_best.set_index("Nama Menu"))
    else:
        st.info("Data menu terlaris belum tersedia.")