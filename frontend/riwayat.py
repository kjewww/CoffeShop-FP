import streamlit as st
import pandas as pd
from datetime import datetime
from api_client import get_all_transactions, get_all_menus

def render_riwayat_page():
    st.title("Riwayat Transaksi")
    st.subheader("Semua Nota Penjualan di Database")

    transactions_data = get_all_transactions()
    menus_data = get_all_menus()

    if not transactions_data:
        st.info("Belum ada riwayat transaksi yang tercatat.")
        return

    flattened_transactions = []
    for tx in reversed(transactions_data):
        try:
            tx_time = datetime.fromisoformat(tx["created_at"].replace("Z", "")).strftime("%d %B %Y - %H:%M")
        except:
            tx_time = tx["created_at"]

        items_summary = []
        if tx.get("details"):
            for item in tx["details"]:
                menu_name = f"Menu ID {item['menu_id']}"
                if menus_data:
                    for m in menus_data:
                        if m["id"] == item["menu_id"]:
                            menu_name = m["name"]
                            break
                items_summary.append(f"{menu_name} ({item['qty']}x)")
            detail_produk = ", ".join(items_summary)
        else:
            detail_produk = "Tidak ada detail item"

        flattened_transactions.append(
            {
                "ID Nota": f"#{tx['id']}",
                "Waktu Transaksi": tx_time,
                "Detail Pembelian": detail_produk,
                "Total Pembayaran": tx["total_price"],
            }
        )

    df_history = pd.DataFrame(flattened_transactions)
    st.dataframe(
        df_history.set_index("ID Nota"),
        use_container_width=True,
        column_config={
            "Total Pembayaran": st.column_config.NumberColumn("Total Pembayaran", format="Rp %,d")
        },
    )