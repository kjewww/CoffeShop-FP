from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# Konfigurasi Halaman Utama Streamlit
st.set_page_config(
    page_title="Coffee Shop POS & Analytics", layout="wide"
)

# URL Backend Vercel Anda
BASE_URL = "https://kjeww-coffeshop-api.vercel.app/api/v1"

# =====================================================================
# INISIALISASI SESSION STATE (Menjaga Sesi Login)
# =====================================================================
if "token" not in st.session_state:
    st.session_state.token = None
if "role" not in st.session_state:
    st.session_state.role = None
if "username" not in st.session_state:
    st.session_state.username = None
if "cart" not in st.session_state:
    st.session_state.cart = {}


# =====================================================================
# FUNGSI HELPER UNTUK REQUEST KE BACKEND (Membawa Token JWT)
# =====================================================================
def get_headers():
    """Membuat header berisi token akses jika pengguna sudah login."""
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    return headers


def get_all_menus():
    try:
        response = requests.get(f"{BASE_URL}/menus", headers=get_headers())
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.error("Sesi Anda berakhir. Silakan login kembali.")
            st.session_state.token = None
        return []
    except:
        return []


def get_all_transactions():
    try:
        response = requests.get(f"{BASE_URL}/transactions", headers=get_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []


def get_analytics_summary():
    try:
        response = requests.get(f"{BASE_URL}/analytics/summary", headers=get_headers())
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}


def get_revenue_per_day():
    try:
        response = requests.get(f"{BASE_URL}/analytics/revenue-per-day", headers=get_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []


def get_best_selling_menu():
    try:
        response = requests.get(f"{BASE_URL}/analytics/best-selling-menu", headers=get_headers())
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []


# =====================================================================
# HALAMAN LOGIN (Ditampilkan jika Belum Autentikasi)
# =====================================================================
if st.session_state.token is None:
    st.title("Welcome to Coffee Shop System")
    st.subheader("Silakan masuk untuk mengakses sistem POS dan Analytics")

    tab1 = st.tabs(["Login Kasir/Owner"])

    # ---- KODE SETELAH DIEDIT (HANYA MODUL LOGIN KASIR) ----
if st.session_state.token is None:
    st.title("☕ Welcome to Coffee Shop System")
    st.subheader("Silakan masuk untuk mengakses sistem POS dan Analytics")

    # Cukup buat satu form login tanpa menggunakan komponen st.tabs lagi
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_login = st.form_submit_button("Masuk")

        if submit_login:
            if not username or not password:
                st.warning("Username dan password wajib diisi!")
            else:
                login_payload = {"username": username, "password": password}
                try:
                    res = requests.post(f"{BASE_URL}/auth/login", data=login_payload)
                    
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.token = data["access_token"]
                        
                        import jwt
                        try:
                            decoded_token = jwt.decode(data["access_token"], options={"verify_signature": False})
                            st.session_state.role = decoded_token.get("role", "kasir").lower()
                        except:
                            st.session_state.role = data.get("role", "kasir").lower()
                        
                        st.session_state.username = username
                        st.success(f"Login Berhasil! Selamat datang, {username}.")
                        st.rerun()
                    else:
                        st.error(f"Gagal masuk: {res.json().get('detail', 'Username atau password salah')}")
                except Exception as e:
                    st.error(f"Tidak dapat terhubung ke server backend: {e}")

# =====================================================================
# APABILA SUDAH LOGIN (TAMPILAN UTAMA APLIKASI) -> Biarkan kode ke bawah tetap sama
# =====================================================================

# =====================================================================
# APABILA SUDAH LOGIN (TAMPILAN UTAMA APLIKASI)
# =====================================================================
# =====================================================================
# APABILA SUDAH LOGIN (TAMPILAN UTAMA APLIKASI)
# =====================================================================
else:
    # --- SIDEBAR NAVIGASI & INFORMASI PENGGUNA ---
    st.sidebar.title("Coffeeshop System")
    st.sidebar.write(f"Login sebagai: **{st.session_state.username}** (`{st.session_state.role.upper()}`)")

    # Pengecekan role agar mencakup kata kunci admin maupun owner
    if st.session_state.role in ["owner", "admin"]:
        menu_options = [
            "Kasir POS",
            "Riwayat Transaksi",
            "Manajemen Menu",
            "Dashboard Analytics",
        ]
    else:
        menu_options = ["Kasir POS", "Riwayat Transaksi"]

    choice = st.sidebar.radio("Navigasi Fitur:", menu_options)

    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.session_state.role = None
        st.session_state.username = None
        st.session_state.cart = {}
        st.rerun()

    # -----------------------------------------------------------------
    # 1. KASIR POS
    # -----------------------------------------------------------------
    if choice == "Kasir POS":
        st.title("Kasir Point of Sale (POS)")
        
        #PERBAIKAN: get_all_menus() baru dipanggil HANYA jika menu Kasir aktif!
        menus_data = get_all_menus()

        if not menus_data:
            st.info("Belum ada menu terdaftar atau database kosong.")
        else:
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
                        res_tx = requests.post(f"{BASE_URL}/transactions", json=tx_payload, headers=get_headers())

                        if res_tx.status_code == 201:
                            st.success("Transaksi Sukses Tercatat!")
                            st.session_state.cart = {}
                            st.rerun()
                        else:
                            st.error(f"Gagal memproses transaksi: {res_tx.json().get('detail')}")

    # -----------------------------------------------------------------
    # 2. RIWAYAT TRANSAKSI
    # -----------------------------------------------------------------
    elif choice == "Riwayat Transaksi":
        st.title("Riwayat Transaksi")
        st.subheader("Semua Nota Penjualan di Database")

        transactions_data = get_all_transactions()
        
        # Ambil data menu secara lokal di sini hanya untuk mencocokkan ID nama menu ke ID transaksi
        menus_data = get_all_menus()

        if not transactions_data:
            st.info("Belum ada riwayat transaksi yang tercatat.")
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

    # -----------------------------------------------------------------
    # 3. MANAJEMEN MENU (Owner / Admin Only)
    # -----------------------------------------------------------------
    elif choice == "Manajemen Menu" and st.session_state.role in ["owner", "admin"]:
        st.title("Manajemen Menu Restoran")
        
        #Ambil data menu khusus di dalam halaman manajemen menu saja
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

    # -----------------------------------------------------------------
    # 4. DASHBOARD ANALYTICS (Owner / Admin Only)
    # -----------------------------------------------------------------
    elif choice == "Dashboard Analytics" and st.session_state.role in ["owner", "admin"]:
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