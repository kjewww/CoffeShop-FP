import streamlit as st
import requests
from api_client import BASE_URL, get_all_menus, get_headers

def render_kasir_page():
    st.title("Kasir Point of Sale (POS)")
    menus_data = get_all_menus()

    if not menus_data:
        st.info("Belum ada menu terdaftar atau database kosong.")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Pilihan Menu")
        for m in menus_data:
            col_a, col_b, col_c = st.columns([2, 1, 1])
            col_a.write(f"**{m['name']}** \nRp {m['price']:,} (Stok: {m['stock']})")

            if m["stock"] <= 0:
                col_b.caption("Habis")
            else:
                qty_order = col_b.number_input(
                    f"Qty", min_value=0, max_value=m["stock"], key=f"input_{m['id']}"
                )
                if qty_order > 0:
                    st.session_state.cart[m["id"]] = {
                        "name": m["name"],
                        "price": m["price"],
                        "qty": qty_order,
                    }
                elif m["id"] in st.session_state.cart and qty_order == 0:
                    del st.session_state.cart[m["id"]]

    with col2:
        st.subheader("Keranjang Belanja")
        if not st.session_state.cart:
            st.caption("Keranjang belanja kosong.")
        else:
            grand_total = 0
            items_payload = []

            for m_id, item in list(st.session_state.cart.items()):
                subtotal = item["price"] * item["qty"]
                grand_total += subtotal
                st.write(f"- {item['name']} x{item['qty']} = Rp {subtotal:,}")
                items_payload.append({"menu_id": int(m_id), "qty": item["qty"]})

            st.markdown("---")
            st.subheader(f"Total: Rp {grand_total:,}")

            if st.button("Proses & Bayar Nota", type="primary"):
                tx_payload = {"items": items_payload}
                try:
                    res_tx = requests.post(f"{BASE_URL}/transactions", json=tx_payload, headers=get_headers())
                    if res_tx.status_code == 201:
                        st.success("Transaksi Sukses Tercatat!")
                        st.session_state.cart = {}
                        st.rerun()
                    else:
                        st.error(f"Gagal memproses transaksi: {res_tx.json().get('detail')}")
                except Exception as e:
                    st.error(f"Gagal terhubung ke server: {e}")