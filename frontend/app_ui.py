import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(
    page_title="CoffeeShop Kelompok 7",
    layout="wide",
    initial_sidebar_state="expanded"
)

# BASE_URL = "https://kjeww-coffeshop-api.vercel.app/api/v1"
BASE_URL = "http://127.0.0.1:8000/api/v1"

def get_all_menus():
    try:
        response = requests.get(f"{BASE_URL}/menus")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.ConnectionError:
        return None

def create_new_menu(name, price, stock):
    payload = {"name": name, "price": int(price), "stock": int(stock)}
    return requests.post(f"{BASE_URL}/menus", json=payload)

def update_menu_api(menu_id, name, price, stock):
    payload = {"name": name, "price": int(price), "stock": int(stock)}
    return requests.patch(f"{BASE_URL}/menus/{menu_id}", json=payload)

def delete_menu_api(menu_id):
    return requests.delete(f"{BASE_URL}/menus/{menu_id}")

def create_transaction_api(items_list):
    payload = {"items": items_list}
    return requests.post(f"{BASE_URL}/transactions", json=payload)

def get_all_transactions():
    try:
        response = requests.get(f"{BASE_URL}/transactions")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return None


if "cart" not in st.session_state:
    st.session_state.cart = []

menus_data = get_all_menus()

if menus_data is None:
    st.error("Gagal terhubung ke Server API Coffee Shop. Pastikan server backend Anda di cloud aktif atau periksa koneksi internet Anda.")
    st.stop()


st.sidebar.title("CofeeShop K7")
st.sidebar.markdown("---")
menu_options = ["Dashboard Analytics", "Transaksi Baru", "Manajemen Menu", "Riwayat Transaksi"]
choice = st.sidebar.radio("Navigasi Halaman:", menu_options)
st.sidebar.markdown("---")
st.sidebar.caption("Connected to Cloud FastAPI Backend")


if choice == "Dashboard Analytics":
    st.title("Dashboard Analytics")
    st.subheader("Ringkasan Performa Bisnis")
    
    try:
        summary = requests.get(f"{BASE_URL}/analytics/summary").json()
        revenue_day = requests.get(f"{BASE_URL}/analytics/revenue-per-day").json()
        best_selling = requests.get(f"{BASE_URL}/analytics/best-selling-menu").json()
    except Exception as e:
        st.error("Gagal memuat data analitik dari server.")
        st.stop()
        
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Pendapatan", f"Rp {summary.get('total_revenue', 0):,}")
    col2.metric("Total Transaksi", f"{summary.get('total_transactions', 0)} Pesanan")
    col3.metric("Varian Menu", f"{summary.get('total_menus', 0)} Item")
    
    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Pendapatan per Hari")
        if revenue_day:
            df_rev = pd.DataFrame(revenue_day)
            df_rev.columns = ["Tanggal", "Pendapatan (Rp)"]
            st.line_chart(df_rev.set_index("Tanggal"))
        else:
            st.info("Belum ada data transaksi harian.")
            
    with col_chart2:
        st.subheader("Top 5 Produk Terlaris")
        if best_selling:
            df_sold = pd.DataFrame(best_selling)
            df_sold.columns = ["Nama Menu", "Jumlah Terjual"]
            st.bar_chart(df_sold.set_index("Nama Menu"))
        else:
            st.info("Belum ada data penjualan item.")


elif choice == "Transaksi Baru":
    st.title("Transaksi Kasir Baru")
    
    col_menu, col_cart = st.columns([3, 2])
    
    with col_menu:
        st.subheader("Pilih Menu")
        if not menus_data:
            st.info("Tidak ada menu yang tersedia di database.")
        
        for menu in menus_data:
            with st.container():
                c1, c2, c3 = st.columns([3, 2, 2])
                c1.markdown(f"**{menu['name']}** \nRp {menu['price']:,}")
                c2.markdown(f"Stok: `{menu['stock']}`")
                
                if menu['stock'] > 0:
                    if c3.button(f"Tambah", key=f"add_{menu['id']}"):
                        found = False
                        for item in st.session_state.cart:
                            if item['id'] == menu['id']:
                                if item['qty'] < menu['stock']:
                                    item['qty'] += 1
                                    item['subtotal'] = item['qty'] * menu['price']
                                else:
                                    st.error("Stok di database tidak mencukupi!")
                                found = True
                                break
                        if not found:
                            st.session_state.cart.append({
                                "id": menu['id'],
                                "name": menu['name'],
                                "price": menu['price'],
                                "qty": 1,
                                "subtotal": menu['price']
                            })
                        st.rerun()
                else:
                    c3.error("Habis")
            st.markdown("---")

    with col_cart:
        st.subheader("Keranjang Belanja")
        if not st.session_state.cart:
            st.info("Keranjang masih kosong.")
        else:
            df_cart = pd.DataFrame(st.session_state.cart)
            st.table(df_cart[["name", "qty", "subtotal"]].rename(columns={"name": "Menu", "qty": "Qty", "subtotal": "Subtotal (Rp)"}))
            
            total_bayar = df_cart["subtotal"].sum()
            st.markdown(f"### **Total: Rp {total_bayar:,}**")
            
            c_clear, c_checkout = st.columns(2)
            if c_clear.button("Kosongkan"):
                st.session_state.cart = []
                st.rerun()
                
            if c_checkout.button("Simpan Transaksi", type="primary"):
                items_payload = [{"menu_id": item["id"], "qty": item["qty"]} for item in st.session_state.cart]
                
                response = create_transaction_api(items_payload)
                
                if response.status_code == 201:
                    st.success(f"Transaksi Berhasil Disimpan di Database!")
                    st.session_state.cart = [] 
                    st.rerun()
                else:
                    error_msg = response.json().get("detail", "Terjadi kesalahan sistem.")
                    st.error(f"Gagal memproses transaksi: {error_msg}")


elif choice == "Manajemen Menu":
    st.title("Manajemen Data Menu")
    
    with st.expander("Tambah Menu Baru"):
        with st.form("add_menu_form", clear_on_submit=True):
            new_name = st.text_input("Nama Menu")
            new_price = st.number_input("Harga (Rp)", min_value=0, step=500)
            new_stock = st.number_input("Stok Awal", min_value=0, step=1)
            submitted = st.form_submit_button("Simpan Menu")
            
            if submitted:
                if new_name:
                    res = create_new_menu(new_name, new_price, new_stock)
                    if res.status_code == 201:
                        st.success(f"Menu '{new_name}' berhasil disimpan ke database!")
                        st.rerun()
                    else:
                        st.error(f"Gagal: {res.json().get('detail')}")
                else:
                    st.warning("Nama menu tidak boleh kosong!")

    st.subheader("Daftar Menu Saat Ini")
    if menus_data:
        df_menus = pd.DataFrame(menus_data)
        st.dataframe(df_menus[["id", "name", "price", "stock"]].rename(
            columns={"id": "ID", "name": "Nama Menu", "price": "Harga", "stock": "Stok"}
        ), use_container_width=True)
    else:
        st.info("Belum ada menu terdaftar di database.")
        
    st.markdown("---")
    
    if menus_data:
        st.subheader("Aksi Menu")
        menu_options_dict = {m["name"]: m for m in menus_data}
        selected_menu_name = st.selectbox("Pilih menu yang ingin dikelola:", list(menu_options_dict.keys()))
        
        selected_menu = menu_options_dict[selected_menu_name]
        
        col_edit, col_del = st.columns(2)
        
        with col_edit:
            st.markdown("**Update Informasi Menu**")
            edit_name = st.text_input("Ubah Nama", value=selected_menu["name"])
            edit_price = st.number_input("Ubah Harga (Rp)", value=selected_menu["price"], min_value=0, step=500)
            edit_stock = st.number_input("Ubah Stok", value=selected_menu["stock"], min_value=0, step=1)
            
            if st.button("Perbarui Menu"):
                res_update = update_menu_api(selected_menu["id"], edit_name, edit_price, edit_stock)
                if res_update.status_code == 200:
                    st.success("Menu berhasil diperbarui di database!")
                    st.rerun()
                else:
                    st.error("Gagal memperbarui menu.")
                
        with col_del:
            st.markdown("**Zona Bahaya**")
            st.write(f"Menghapus menu akan menghilangkannya secara permanen dari sistem database.")
            if st.button(f"Hapus '{selected_menu['name']}' 🗑️", type="primary"):
                res_delete = delete_menu_api(selected_menu["id"])
                if res_delete.status_code == 200:
                    st.warning(f"Menu '{selected_menu['name']}' telah dihapus.")
                    st.rerun()
                else:
                    st.error("Gagal menghapus menu.")


elif choice == "Riwayat Transaksi":
    st.title("Riwayat Transaksi")
    st.subheader("Semua Nota Penjualan di Database")

    transactions_data = get_all_transactions()

    if transactions_data is None:
        st.error("Gagal mengambil data transaksi dari server.")
    elif not transactions_data:
        st.info("Belum ada riwayat transaksi yang tercatat di database.")
    else:
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

            flattened_transactions.append({
                "ID Nota": f"#{tx['id']}",
                "Waktu Transaksi": tx_time,
                "Detail Pembelian": detail_produk,
                "Total Pembayaran": tx["total_price"]
            })

        df_history = pd.DataFrame(flattened_transactions)

        st.dataframe(
            df_history.set_index("ID Nota"), 
            use_container_width=True,
            column_config={
                "Total Pembayaran": st.column_config.NumberColumn(
                    "Total Pembayaran",
                    format="Rp %,d"
                )
            }
        )
        
        st.caption(f"Menampilkan {len(df_history)} transaksi terakhir. Anda dapat mengurutkan data dengan mengklik judul kolom di atas.")