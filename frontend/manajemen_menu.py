import streamlit as st
import requests
from api_client import BASE_URL, get_all_menus, get_headers

def render_manajemen_menu_page():
    st.title("Manajemen Menu Restoran")
    menus_data = get_all_menus()

    tab_view, tab_add = st.tabs(["Lihat & Ubah Menu", "Tambah Menu Baru"])

    with tab_view:
        if not menus_data:
            st.info("Belum ada menu di database.")
        else:
            for m in menus_data:
                with st.expander(f"{m['name']} (Rp {m['price']:,})"):
                    edit_name = st.text_input("Nama Menu", m["name"], key=f"name_{m['id']}")
                    edit_price = st.number_input("Harga", value=m["price"], key=f"price_{m['id']}")
                    edit_stock = st.number_input("Stok", value=m["stock"], key=f"stock_{m['id']}")
                    
                    col_e1, col_e2, _ = st.columns([1, 1, 4])
                    if col_e1.button("Simpan Perubahan", key=f"save_{m['id']}"):
                        patch_payload = {"name": edit_name, "price": edit_price, "stock": edit_stock}
                        res = requests.patch(f"{BASE_URL}/menus/{m['id']}", json=patch_payload, headers=get_headers())
                        if res.status_code == 200:
                            st.success("Menu berhasil diubah!")
                            st.rerun()
                            
                    if col_e2.button("Hapus Menu", key=f"del_{m['id']}", type="secondary"):
                        res = requests.delete(f"{BASE_URL}/menus/{m['id']}", headers=get_headers())
                        if res.status_code == 200:
                            st.success("Menu berhasil dihapus!")
                            st.rerun()

    with tab_add:
        with st.form("form_add_menu"):
            new_name = st.text_input("Nama Menu Baru")
            new_price = st.number_input("Harga Jual", min_value=0, value=15000)
            new_stock = st.number_input("Stok Awal", min_value=0, value=20)
            submit_add = st.form_submit_button("Tambah Menu")

            if submit_add:
                if not new_name:
                    st.error("Nama menu wajib diisi!")
                else:
                    add_payload = {"name": new_name, "price": new_price, "stock": new_stock}
                    res = requests.post(f"{BASE_URL}/menus", json=add_payload, headers=get_headers())
                    if res.status_code == 201:
                        st.success("Menu baru sukses ditambahkan!")
                        st.rerun()