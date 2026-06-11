import streamlit as st
import requests

BASE_URL = "https://kjeww-coffeshop-api.vercel.app/api/v1"

def get_headers():
    """Membuat header berisi token akses jika pengguna sudah login."""
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    return headers

def check_unauthorized(status_code):
    """Menangani jika sesi kedaluwarsa secara terpusat."""
    if status_code == 401:
        st.error("Sesi Anda berakhir. Silakan login kembali.")
        st.session_state.token = None
        st.session_state.role = None
        st.session_state.username = None
        st.session_state.cart = {}
        st.rerun()

def get_all_menus():
    try:
        response = requests.get(f"{BASE_URL}/menus", headers=get_headers())
        check_unauthorized(response.status_code)
        return response.json() if response.status_code == 200 else []
    except:
        return []

def get_all_transactions():
    try:
        response = requests.get(f"{BASE_URL}/transactions", headers=get_headers())
        check_unauthorized(response.status_code)
        return response.json() if response.status_code == 200 else []
    except:
        return []

def get_analytics_summary():
    try:
        response = requests.get(f"{BASE_URL}/analytics/summary", headers=get_headers())
        check_unauthorized(response.status_code)
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

def get_revenue_per_day():
    try:
        response = requests.get(f"{BASE_URL}/analytics/revenue-per-day", headers=get_headers())
        check_unauthorized(response.status_code)
        return response.json() if response.status_code == 200 else []
    except:
        return []

def get_best_selling_menu():
    try:
        response = requests.get(f"{BASE_URL}/analytics/best-selling-menu", headers=get_headers())
        check_unauthorized(response.status_code)
        return response.json() if response.status_code == 200 else []
    except:
        return []