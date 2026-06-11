import streamlit as st
import requests
import jwt
from api_client import BASE_URL

# Impor komponen UI
from kasir import render_kasir_page
from riwayat import render_riwayat_page
from manajemen_menu import render_manajemen_menu_page
from dashboard import render_dashboard_page

# 1. Konfigurasi Awal
st.set_page_config(
    page_title="Coffee Shop Kasir dan Analytics", layout="wide"
)

# 2. Inisialisasi Session State
if "token" not in st.session_state:
    st.session_state.token = None
if "role" not in st.session_state:
    st.session_state.role = None
if "username" not in st.session_state:
    st.session_state.username = None
if "cart" not in st.session_state:
    st.session_state.cart = {}


# 3. KONDISI BELUM LOGIN 
if st.session_state.token is None:
    st.title("Welcome to Coffee Shop System")
    st.subheader("Silakan masuk untuk mengakses sistem POS dan Analytics")

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

# 4. KONDISI SUDAH LOGIN 
else:
    st.sidebar.title("Coffeeshop System")
    st.sidebar.write(f"Login sebagai: **{st.session_state.username}** (`{st.session_state.role.upper()}`)")

    # Proteksi Menu Berdasarkan Role Akses Pengguna
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

    # Routing Pemanggilan Fungsi Render Modul Eksternal
    if choice == "Kasir POS":
        render_kasir_page()
    elif choice == "Riwayat Transaksi":
        render_riwayat_page()
    elif choice == "Manajemen Menu" and st.session_state.role in ["owner", "admin"]:
        render_manajemen_menu_page()
    elif choice == "Dashboard Analytics" and st.session_state.role in ["owner", "admin"]:
        render_dashboard_page()