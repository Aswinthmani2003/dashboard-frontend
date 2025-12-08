import streamlit as st
import requests
from datetime import datetime, date, time, timedelta
import base64
from pathlib import Path
import re
import pytz
import html
import time as time_module

API_BASE = "https://dashboard-backend-qqmi.onrender.com"
MAKE_WEBHOOK_URL = st.secrets.get("make_webhook_url", "")

# Define IST timezone
IST = pytz.timezone("Asia/Kolkata")


def check_password():
    """Simple password gate using Streamlit secrets"""

    def password_entered():
        """Checks whether the password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["dashboard_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.stop()
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("❌ Wrong password")
        st.stop()


# Page config
st.set_page_config(
    page_title="WhatsApp Chat Inbox",
    layout="wide",
    initial_sidebar_state="collapsed",
)
check_password()

# ----------------------- SESSION STATE INIT -----------------------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

if "filter_phone" not in st.session_state:
    st.session_state.filter_phone = ""
if "filter_name" not in st.session_state:
    st.session_state.filter_name = ""
if "filter_by_date" not in st.session_state:
    st.session_state.filter_by_date = False
if "filter_date" not in st.session_state:
    st.session_state.filter_date = date.today()
if "filter_by_time" not in st.session_state:
    st.session_state.filter_by_time = False
if "filter_time_from" not in st.session_state:
    st.session_state.filter_time_from = time(0, 0)
if "filter_time_to" not in st.session_state:
    st.session_state.filter_time_to = time(23, 59)
if "filter_only_fu" not in st.session_state:
    st.session_state.filter_only_fu = False
if "show_filters" not in st.session_state:
    st.session_state.show_filters = False


# ----------------------- ASSETS & CSS -----------------------
def get_base64_logo():
    """Load logo.png and convert to base64 for embedding"""
    logo_path = Path("Logo.png")
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None


def get_css(theme):
    if theme == "dark":
        return """
        <style>
            .main {
                background: linear-gradient(180deg, #0d1418 0%, #0d1418 100%);
                padding: 0 !important;
            }
            .block-container {
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                max-width: 100% !important;
            }
            .main-header {
                background: #202c33;
                padding: 10px 16px;
                display: flex;
                align-items: center;
                gap: 15px;
                border-bottom: 1px solid #2a3942;
                position: sticky;
                top: 0;
                z-index: 999;
                height: 60px;
            }
            .main-header h1 {
                color: #e9edef;
                margin: 0;
                font-size: 16px;
                font-weight: 500;
                flex: 1;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            .logo-img {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                object-fit: cover;
                border: 1px solid #2a3942;
            }
            .filter-container {
                background-color: #111b21;
                border: 1px solid #2a3942;
                border-radius: 8px;
                padding: 0;
                margin-bottom: 12px;
                overflow: hidden;
                margin-top: 10px;
            }
            .filter-header {
                background-color: #202c33;
                padding: 12px 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: pointer;
                border-bottom: 1px solid #2a3942;
            }
            .filter-header h3 {
                color: #e9edef;
                margin: 0;
                font-size: 14px;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .filter-content {
                padding: 16px;
            }
            .filter-row {
                display: flex;
                gap: 12px;
                margin-bottom: 12px;
                flex-wrap: wrap;
            }
            .filter-group {
                flex: 1;
                min-width: 200px;
            }
            .filter-group label {
                color: #8696a0;
                font-size: 12px;
                margin-bottom: 4px;
                display: block;
                font-weight: 400;
            }
            .contact-card {
                background-color: transparent;
                padding: 12px;
                cursor: pointer;
                border-bottom: 1px solid #222d34;
                transition: background-color 0.2s;
                position: relative;
                display: flex;
                align-items: center;
                gap: 12px;
                min-height: 72px;
            }
            .contact-card:hover { background-color: #202c33; }
            .contact-card.selected { background-color: #2a3942; }
            .contact-avatar {
                width: 49px;
                height: 49px;
                border-radius: 50%;
                background: linear-gradient(135deg, #00a884 0%, #008069 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 20px;
                color: white;
                font-weight: 500;
                flex-shrink: 0;
            }
            .contact-info {
                flex: 1;
                min-width: 0;
                padding-right: 40px;
            }
            .contact-name {
                color: #e9edef;
                font-size: 17px;
                font-weight: 400;
                margin-bottom: 2px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            .contact-preview {
                color: #8696a0;
                font-size: 14px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                font-weight: 400;
            }
            .contact-meta {
                position: absolute;
                top: 12px;
                right: 12px;
                text-align: right;
            }
            .contact-time {
                color: #8696a0;
                font-size: 12px;
                margin-bottom: 4px;
            }
            .unread-indicator {
                background-color: #00a884;
                color: #111b21;
                font-size: 12px;
                font-weight: 600;
                min-width: 20px;
                height: 20px;
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-left: auto;
            }
            .chat-header {
                background: #202c33;
                padding: 10px 16px;
                margin-bottom: 1px;
                border-bottom: 1px solid #2a3942;
                display: flex;
                justify-content: space-between;
                align-items: center;
                height: 60px;
            }
            .chat-header-left {
                display: flex;
                align-items: center;
                gap: 15px;
                flex: 1;
            }
            .chat-avatar {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: linear-gradient(135deg, #00a884 0%, #008069 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                color: white;
                font-weight: 500;
            }
            .chat-header-info h3 {
                color: #e9edef;
                margin: 0 0 2px 0;
                font-size: 16px;
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            .chat-header-info p {
                color: #8696a0;
                margin: 0;
                font-size: 13px;
                font-weight: 400;
            }
            .chat-container {
                background: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png');
                background-size: contain;
                background-position: center;
                padding: 20px 16px;
                min-height: calc(100vh - 240px);
                position: relative;
                overflow-y: auto;
                max-height: 600px;
            }
            .chat-container::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(10, 20, 25, 0.95);
                pointer-events: none;
            }
            .message-row {
                display: flex;
                margin-bottom: 8px;
                position: relative;
                z-index: 1;
            }
            .message-row.user { justify-content: flex-start; }
            .message-row.bot { justify-content: flex-end; }
            .message-bubble {
                max-width: 65%;
                padding: 8px 9px;
                border-radius: 7.5px;
                position: relative;
                box-shadow: 0 1px 0.5px rgba(0,0,0,0.13);
                word-wrap: break-word;
            }
            .message-bubble.user {
                background-color: #202c33;
                border-top-left-radius: 0;
            }
            .message-bubble.bot {
                background-color: #005c4b;
                border-top-right-radius: 0;
            }
            .message-bubble.user::before {
                content: '';
                position: absolute;
                top: 0;
                left: -8px;
                width: 8px;
                height: 13px;
                background-color: #202c33;
                border-bottom-right-radius: 10px;
            }
            .message-bubble.bot::before {
                content: '';
                position: absolute;
                top: 0;
                right: -8px;
                width: 8px;
                height: 13px;
                background-color: #005c4b;
                border-bottom-left-radius: 10px;
            }
            .message-text {
                color: #e9edef;
                font-size: 14.2px;
                line-height: 19px;
                margin-bottom: 4px;
                word-wrap: break-word;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            .message-time {
                color: rgba(255, 255, 255, 0.6);
                font-size: 11px;
                text-align: right;
                margin-top: 2px;
                display: flex;
                justify-content: flex-end;
                align-items: center;
                gap: 4px;
            }
            .message-meta {
                display: flex;
                align-items: center;
                gap: 4px;
            }
            .message-status {
                font-size: 13px;
            }
            .message-status.sent { color: #8696a0; }
            .message-status.delivered { color: #8696a0; }
            .message-status.read { color: #53bdeb; }
            .input-area {
                background: #202c33;
                padding: 10px 16px;
                border-top: 1px solid #2a3942;
                position: sticky;
                bottom: 0;
                z-index: 100;
            }
            .update-section {
                background-color: #202c33;
                border-radius: 8px;
                padding: 16px;
                margin-top: 16px;
                border: 1px solid #2a3942;
            }
            .update-section h3 {
                color: #e9edef !important;
                font-size: 16px !important;
                margin-bottom: 12px !important;
                font-weight: 500 !important;
            }
            .send-section {
                background-color: #202c33;
                border-radius: 8px;
                padding: 16px;
                margin-top: 16px;
                border: 1px solid #2a3942;
            }
            .send-section h3 {
                color: #e9edef !important;
                font-size: 16px !important;
                margin-bottom: 12px !important;
                font-weight: 500 !important;
            }
            .pagination-section {
                background-color: #202c33;
                border-radius: 8px;
                padding: 12px 16px;
                margin-top: 12px;
                border: 1px solid #2a3942;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            .handler-meta {
                font-size: 11px;
                color: rgba(255, 255, 255, 0.6);
                margin-top: 2px;
            }
            .pagination-info {
                color: #8696a0;
                font-size: 14px;
                margin: 0;
                text-align: center;
                flex: 1;
            }
            .stButton > button {
                background-color: #00a884 !important;
                color: #111b21 !important;
                border: none !important;
                font-weight: 600 !important;
                border-radius: 24px !important;
                font-size: 14px !important;
                padding: 10px 24px !important;
                height: auto !important;
                min-height: 40px !important;
                transition: all 0.2s !important;
            }
            .stButton > button:hover {
                background-color: #06cf9c !important;
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(0, 168, 132, 0.3);
            }
            .delete-btn {
                background-color: #dc3545 !important;
                padding: 4px 8px !important;
                font-size: 11px !important;
                border-radius: 4px !important;
                color: white !important;
                border: none !important;
                cursor: pointer;
                margin-top: 4px;
            }
            .stTextInput input, .stTextArea textarea {
                background-color: #2a3942 !important;
                color: #e9edef !important;
                border: 1px solid #3b4a54 !important;
                border-radius: 8px !important;
                font-size: 14px !important;
                padding: 12px !important;
            }
            .stTextInput input:focus, .stTextArea textarea:focus {
                border-color: #00a884 !important;
                box-shadow: 0 0 0 1px #00a884 !important;
            }
            [data-testid="stCheckbox"] label {
                color: #e9edef !important;
                font-size: 14px !important;
            }
            .stSelectbox label { color: #e9edef !important; }
            .stRadio label { color: #e9edef !important; }
            .stDateInput input, .stTimeInput input {
                background-color: #2a3942 !important;
                color: #e9edef !important;
                border: 1px solid #3b4a54 !important;
                border-radius: 8px !important;
            }
            ::-webkit-scrollbar {
                width: 6px;
                height: 6px;
            }
            ::-webkit-scrollbar-track { background: #111b21; }
            ::-webkit-scrollbar-thumb {
                background: #374045;
                border-radius: 3px;
            }
            ::-webkit-scrollbar-thumb:hover { background: #3b4a54; }
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .main .block-container { padding-top: 0rem !important; }
            .header-buttons {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .filter-actions {
                display: flex;
                gap: 10px;
                margin-top: 20px;
                justify-content: flex-end;
            }
            .top-buttons-row {
                display: flex;
                gap: 10px;
                margin-bottom: 15px;
            }
            .search-input {
                background-color: #202c33;
                border: none;
                border-bottom: 1px solid #2a3942;
                padding: 8px 12px;
                color: #e9edef;
                font-size: 14px;
                width: 100%;
            }
            .status-online {
                color: #00a884;
                font-size: 11px;
            }
            .status-offline {
                color: #8696a0;
                font-size: 11px;
            }
            .avatar-color-0 { background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%) !important; }
            .avatar-color-1 { background: linear-gradient(135deg, #48dbfb 0%, #0abde3 100%) !important; }
            .avatar-color-2 { background: linear-gradient(135deg, #1dd1a1 0%, #00b894 100%) !important; }
            .avatar-color-3 { background: linear-gradient(135deg, #f368e0 0%, #ff9ff3 100%) !important; }
            .avatar-color-4 { background: linear-gradient(135deg, #ff9f43 0%, #feca57 100%) !important; }
            .avatar-color-5 { background: linear-gradient(135deg, #54a0ff 0%, #2e86de 100%) !important; }
            .avatar-color-6 { background: linear-gradient(135deg, #5f27cd 0%, #341f97 100%) !important; }
            .avatar-color-7 { background: linear-gradient(135deg, #00d2d3 0%, #01a3a4 100%) !important; }
        </style>
        """
    else:
        # LIGHT THEME CSS (unchanged except handler-meta color = black)
        return """
        <style>
            .main {
                background: linear-gradient(180deg, #eae6df 0%, #eae6df 100%);
                padding: 0 !important;
            }
            .block-container {
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                max-width: 100% !important;
            }
            .main-header {
                background: #f0f2f5;
                padding: 10px 16px;
                display: flex;
                align-items: center;
                gap: 15px;
                border-bottom: 1px solid #dddfe2;
                position: sticky;
                top: 0;
                z-index: 999;
                height: 60px;
            }
            .main-header h1 {
                color: #3b4a54;
                margin: 0;
                font-size: 16px;
                font-weight: 500;
                flex: 1;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            .handler-meta {
                font-size: 11px;
                color: #303030;
                margin-top: 2px;
            }
            .logo-img {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                object-fit: cover;
                border: 1px solid #dddfe2;
            }
            /* rest of your light CSS exactly as before ... */
        </style>
        """  # keep rest of light CSS as you had it (omitted here to save space)


st.markdown(get_css(st.session_state.theme), unsafe_allow_html=True)

logo_base64 = get_base64_logo()
if logo_base64:
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="logo-img">'
else:
    logo_url = "https://drive.google.com/uc?export=view&id=1NSTzTZ_gusa-c4Sc5dZelth-Djft0Zca"
    logo_html = (
        f'<img src="{logo_url}" class="logo-img" onerror="this.style.display=\'none\'">'
    )

st.markdown(
    f"""
<div class="main-header">
    {logo_html}
    <h1>WhatsApp Chat Inbox</h1>
</div>
""",
    unsafe_allow_html=True,
)

col1, col2 = st.columns([1, 1])

with col1:
    filter_icon = "▼" if st.session_state.show_filters else "▶"
    if st.button(
        f"{filter_icon} Filters", key="toggle_filters", use_container_width=True
    ):
        st.session_state.show_filters = not st.session_state.show_filters
        st.rerun()

with col2:
    if st.session_state.theme == "dark":
        if st.button("☀️ Light Mode", key="theme_toggle", use_container_width=True):
            st.session_state.theme = "light"
            st.rerun()
    else:
        if st.button("🌙 Dark Mode", key="theme_toggle", use_container_width=True):
            st.session_state.theme = "dark"
            st.rerun()

# ----------------------- FILTER UI -----------------------
if st.session_state.show_filters:
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    st.markdown('<div class="filter-header">', unsafe_allow_html=True)
    st.markdown('<h3><span>🔍</span> Filter Options</h3>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="filter-content">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.filter_phone = st.text_input(
            "📱 Phone Number",
            value=st.session_state.filter_phone,
            placeholder="Search by phone...",
            key="filter_phone_input",
        )

    with col2:
        st.session_state.filter_name = st.text_input(
            "👤 Client Name",
            value=st.session_state.filter_name,
            placeholder="Search by name...",
            key="filter_name_input",
        )

    st.session_state.filter_by_date = st.checkbox(
        "📅 Enable date filter",
        value=st.session_state.filter_by_date,
        key="filter_by_date_check",
    )

    if st.session_state.filter_by_date:
        st.session_state.filter_date = st.date_input(
            "Select date",
            value=st.session_state.filter_date,
            key="filter_date_input",
        )

    st.session_state.filter_by_time = st.checkbox(
        "🕐 Enable time filter",
        value=st.session_state.filter_by_time,
        key="filter_by_time_check",
    )

    if st.session_state.filter_by_time:
        col_time1, col_time2 = st.columns(2)
        with col_time1:
            st.session_state.filter_time_from = st.time_input(
                "From time",
                value=st.session_state.filter_time_from,
                key="filter_time_from_input",
            )
        with col_time2:
            st.session_state.filter_time_to = st.time_input(
                "To time",
                value=st.session_state.filter_time_to,
                key="filter_time_to_input",
            )

    st.session_state.filter_only_fu = st.checkbox(
        "🔴 Show only follow-up clients",
        value=st.session_state.filter_only_fu,
        key="filter_only_fu_check",
    )

    st.markdown('<div class="filter-actions">', unsafe_allow_html=True)
    if st.button("Apply Filters", use_container_width=True, type="primary"):
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ----------------------- TIME HELPERS -----------------------
def convert_to_ist(timestamp_str: str) -> datetime:
    """Convert ISO timestamp string to IST datetime object"""
    try:
        if not timestamp_str:
            return datetime.now(IST)

        ts = str(timestamp_str).replace("Z", "+00:00")

        try:
            dt = datetime.fromisoformat(ts)
        except Exception:
            dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%f%z")

        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)

        return dt.astimezone(IST)
    except Exception:
        return datetime.now(IST)


def format_message_time(timestamp_str: str) -> str:
    ist_dt = convert_to_ist(timestamp_str)
    return ist_dt.strftime("%I:%M %p").lstrip("0")


def format_contact_time(timestamp_str: str) -> str:
    try:
        if not timestamp_str:
            return ""
        ist_dt = convert_to_ist(timestamp_str)
        now = datetime.now(IST)

        if ist_dt.date() == now.date():
            return ist_dt.strftime("%I:%M %p").lstrip("0")
        elif ist_dt.date() == (now.date() - timedelta(days=1)):
            return "Yesterday"
        elif (now - ist_dt).days < 7:
            return ist_dt.strftime("%a")
        else:
            return ist_dt.strftime("%d/%m")
    except Exception:
        return ""


def get_avatar_color(name: str) -> int:
    if not name:
        return 0
    return hash(name) % 8


def get_avatar_initials(name: str) -> str:
    if not name or name == "Unknown":
        return "?"
    words = name.split()
    if len(words) >= 2:
        return (words[0][0] + words[-1][0]).upper()
    elif len(name) >= 2:
        return name[:2].upper()
    else:
        return name[0].upper() if name else "?"


# ----------------------- HTTP HELPERS -----------------------
def make_request_with_retry(
    url, method="GET", params=None, json_data=None, max_retries=3
):
    for attempt in range(max_retries):
        try:
            if method == "GET":
                response = requests.get(url, params=params, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=json_data, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, timeout=30)
            elif method == "PATCH":
                response = requests.patch(url, json=json_data, timeout=30)
            else:
                response = requests.get(url, params=params, timeout=30)

            response.raise_for_status()
            return response

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time_module.sleep(2)
                continue
            else:
                raise Exception(f"Request timed out after {max_retries} attempts")
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time_module.sleep(2)
                continue
            else:
                raise e
    return None


# ----------------------- BACKEND CALLS -----------------------
def fetch_contacts(only_follow_up: bool):
    try:
        response = make_request_with_retry(
            f"{API_BASE}/contacts", params={"only_follow_up": only_follow_up}
        )
        if response and response.status_code == 200:
            return response.json()
        else:
            st.warning("Failed to fetch contacts. Please try again.")
            return []
    except Exception as e:
        st.warning(f"Could not fetch contacts: {str(e)}")
        return []


def fetch_conversation(phone: str, limit: int = 50, offset: int = 0):
    """Fetch conversation for a specific phone number from /conversation/{phone}"""
    if not phone:
        return []
    try:
        response = make_request_with_retry(
            f"{API_BASE}/conversation/{phone}",
            params={"limit": limit, "offset": offset},
        )
        if response and response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.warning(f"Could not fetch conversation: {str(e)}")
        # Fallback sample (kept consistent with backend direction = 'user'/'bot')
        current_time = datetime.now(IST)
        return [
            {
                "id": 1,
                "phone": phone,
                "message": "Hello, I'm interested in your investment services.",
                "direction": "user",
                "timestamp": (current_time - timedelta(hours=2)).isoformat(),
                "follow_up_needed": True,
                "notes": "Interested in SIP",
                "handled_by": "Agent 1",
            },
            {
                "id": 2,
                "phone": phone,
                "message": "Hi! I'd be happy to help you with investment options. We have SIP plans starting from ₹500 per month.",
                "direction": "bot",
                "timestamp": (current_time - timedelta(hours=1)).isoformat(),
                "follow_up_needed": False,
                "notes": "",
                "handled_by": "System",
            },
            {
                "id": 3,
                "phone": phone,
                "message": "Can you send me more details about the SIP plans?",
                "direction": "user",
                "timestamp": current_time.isoformat(),
                "follow_up_needed": True,
                "notes": "",
                "handled_by": "",
            },
        ]


def delete_conversation(phone: str):
    try:
        response = make_request_with_retry(
            f"{API_BASE}/conversation/{phone}", method="DELETE"
        )
        return response and response.status_code == 200
    except Exception:
        return False


def delete_message(msg_id: int):
    try:
        response = make_request_with_retry(
            f"{API_BASE}/message/{msg_id}", method="DELETE"
        )
        return response and response.status_code == 200
    except Exception:
        return False


def filter_messages(messages, date_filter, time_from, time_to):
    if not date_filter and not time_from:
        return messages
    filtered = []
    for msg in messages:
        try:
            msg_dt = convert_to_ist(msg["timestamp"])
            if date_filter and msg_dt.date() != date_filter:
                continue
            if time_from and time_to:
                msg_time = msg_dt.time()
                if not (time_from <= msg_time <= time_to):
                    continue
            filtered.append(msg)
        except Exception:
            continue
    return filtered


def send_whatsapp_message(
    phone: str,
    message_text: str,
    msg_type: str = "text",
    template_name: str | None = None,
) -> bool:
    if not MAKE_WEBHOOK_URL:
        st.error(
            "Make webhook URL not configured (set 'make_webhook_url' in Streamlit secrets)."
        )
        return False

    payload = {
        "phone": phone,
        "message": message_text,
        "type": msg_type,
    }
    if msg_type == "template" and template_name:
        payload["template_name"] = template_name

    try:
        response = make_request_with_retry(
            MAKE_WEBHOOK_URL, method="POST", json_data=payload
        )
        if response and response.status_code in (200, 201, 202):
            log_sent_message(phone, message_text, msg_type)
            return True
        else:
            st.error("Send failed")
            return False
    except Exception as e:
        st.error(f"Send error: {e}")
        return False


def log_sent_message(phone: str, message: str, msg_type: str = "text"):
    """Log sent message to /log_message with IST timestamp"""
    try:
        ist_now = datetime.now(IST)
        payload = {
            "phone": phone,
            "message": message,
            "direction": "outgoing",  # backend normalises this to "bot"
            "message_type": msg_type,
            "timestamp": ist_now.isoformat(),
            "follow_up_needed": False,
            "notes": "",
            "handled_by": "Dashboard User",
        }
        response = make_request_with_retry(
            f"{API_BASE}/log_message", method="POST", json_data=payload
        )
        return response and response.status_code == 200
    except Exception as e:
        st.warning(f"Message sent but not logged in database: {e}")
        return False


# ----------------------- LOAD CONTACTS -----------------------
try:
    contacts = fetch_contacts(st.session_state.filter_only_fu)

    if st.session_state.filter_phone:
        contacts = [
            c
            for c in contacts
            if st.session_state.filter_phone.lower()
            in c.get("phone", "").lower()
        ]
    if st.session_state.filter_name:
        contacts = [
            c
            for c in contacts
            if c.get("client_name")
            and st.session_state.filter_name.lower()
            in c["client_name"].lower()
        ]

    def get_contact_sort_key(contact):
        name = contact.get("client_name", "").lower()
        phone = contact.get("phone", "")
        return (name, phone)

    contacts.sort(key=get_contact_sort_key)
except Exception as e:
    st.warning(f"Could not load contacts: {str(e)}")
    contacts = []

if not contacts:
    st.info("🔍 No contacts found")
    st.stop()

if "selected_phone" not in st.session_state:
    st.session_state.selected_phone = contacts[0].get("phone", "")

if "conv_offset" not in st.session_state:
    st.session_state.conv_offset = 0

if "last_message_count" not in st.session_state:
    st.session_state.last_message_count = {}

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True

CONV_LIMIT = 20

# ----------------------- LAYOUT -----------------------
col_list, col_chat = st.columns([1, 2.5])

# CONTACTS COLUMN
with col_list:
    st.markdown("### 💬 Contacts")
    search_query_contacts = st.text_input(
        "Search contacts...",
        placeholder="Type to search...",
        key="search_contacts",
        label_visibility="collapsed",
    )

    if search_query_contacts:
        filtered_contacts = [
            c
            for c in contacts
            if search_query_contacts.lower()
            in (c.get("client_name") or "").lower()
            or search_query_contacts in c.get("phone", "")
        ]
    else:
        filtered_contacts = contacts

    for c in filtered_contacts:
        client_name = c.get("client_name") or "Unknown"
        phone = c.get("phone", "")
        is_selected = st.session_state.selected_phone == phone

        last_message_preview = "No messages yet"
        try:
            conv_preview = fetch_conversation(phone, limit=1)
            if conv_preview:
                last_msg = conv_preview[-1].get("message", "")
                if last_msg:
                    last_message_preview = html.escape(last_msg[:30]) + (
                        "..." if len(last_msg) > 30 else ""
                    )
        except Exception:
            pass

        try:
            conv_full = fetch_conversation(phone, limit=50)
            unread_count = sum(1 for msg in conv_full if msg.get("follow_up_needed"))
        except Exception:
            unread_count = 0

        color_index = get_avatar_color(client_name)
        initials = get_avatar_initials(client_name)

        last_time = ""
        try:
            conv_preview = fetch_conversation(phone, limit=1)
            if conv_preview:
                last_time = format_contact_time(conv_preview[-1].get("timestamp"))
        except Exception:
            pass

        # Render as a simple button for click behaviour
        if st.button(
            f"{client_name} ({phone})"
            + (f"  •  🔴 {unread_count}" if unread_count > 0 else ""),
            key=f"contact_{phone}",
            type="primary" if is_selected else "secondary",
            use_container_width=True,
        ):
            st.session_state.selected_phone = phone
            st.session_state.conv_offset = 0
            draft_key = f"new_msg_{phone}"
            if draft_key in st.session_state:
                del st.session_state[draft_key]
            st.rerun()

# CHAT COLUMN
with col_chat:
    phone = st.session_state.selected_phone
    selected = next((c for c in contacts if c.get("phone") == phone), None)

    if not selected:
        st.info("📭 Select a contact to view messages")
        st.stop()

    client_name = selected.get("client_name") or phone
    color_index = get_avatar_color(client_name)
    initials = get_avatar_initials(client_name)

    col_toggle1, col_toggle2 = st.columns([3, 1])
    with col_toggle2:
        auto_refresh = st.checkbox(
            "🔄 Auto-refresh",
            value=st.session_state.auto_refresh,
            key="auto_refresh_toggle",
        )
        st.session_state.auto_refresh = auto_refresh

    if st.session_state.auto_refresh:
        st.markdown(
            """
        <script>
            setTimeout(function() {
                window.parent.location.reload();
            }, 5000);
        </script>
        """,
            unsafe_allow_html=True,
        )

    col_header_content, col_header_delete = st.columns([4, 1])

    with col_header_content:
        st.markdown(
            f"""
        <div class="chat-header">
            <div class="chat-header-left">
                <div class="chat-avatar avatar-color-{color_index}">{initials}</div>
                <div class="chat-header-info">
                    <h3>{html.escape(client_name)}</h3>
                    <p>{phone}</p>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col_header_delete:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        if st.button("🗑️ Delete All", key="del_all", use_container_width=True):
            if st.session_state.get("confirm_del"):
                if delete_conversation(phone):
                    st.success("Deleted!")
                    st.session_state.pop("confirm_del", None)
                    st.rerun()
            else:
                st.session_state.confirm_del = True
                st.warning("Click again to confirm deletion")

    search_query = st.text_input(
        "Search in this chat",
        placeholder="Type to search messages...",
        key="search_conv",
        label_visibility="collapsed",
    )

    conv = fetch_conversation(
        phone, limit=CONV_LIMIT, offset=st.session_state.conv_offset
    )

    date_filter = st.session_state.filter_date if st.session_state.filter_by_date else None
    time_from = (
        st.session_state.filter_time_from if st.session_state.filter_by_time else None
    )
    time_to = (
        st.session_state.filter_time_to if st.session_state.filter_by_time else None
    )
    conv = filter_messages(conv, date_filter, time_from, time_to)

    conv.sort(key=lambda x: convert_to_ist(x["timestamp"]))

    unread_count = sum(1 for m in conv if m.get("follow_up_needed"))

    if unread_count > 0:
        st.markdown(
            f'<div style="color: #ff3b30; font-size: 13px; margin: 0 0 10px 20px;">🔴 {unread_count} unread messages</div>',
            unsafe_allow_html=True,
        )

    chat_container = st.container()
    with chat_container:
        if not conv:
            st.info("📭 No messages yet")
        else:
            current_date = None
            for msg in conv:
                msg_dt = convert_to_ist(msg["timestamp"])
                msg_date = msg_dt.date()

                if current_date != msg_date:
                    current_date = msg_date
                    today = datetime.now(IST).date()
                    if msg_date == today:
                        date_label = "Today"
                    elif msg_date == today - timedelta(days=1):
                        date_label = "Yesterday"
                    else:
                        date_label = msg_dt.strftime("%B %d, %Y")
                    st.markdown(
                        f'<div style="text-align: center; margin: 16px 0; color: #8696a0; font-size: 12px;">{date_label}</div>',
                        unsafe_allow_html=True,
                    )

                direction_val = msg.get("direction", "bot")
                direction = "user" if direction_val == "user" else "bot"

                raw_text = html.escape(msg.get("message", ""))
                display_text = raw_text

                if search_query and search_query.strip():
                    pattern = re.escape(search_query.strip())

                    def repl(m):
                        return f'<span style="background-color: #ffd700; padding: 0 1px; border-radius: 2px;">{html.escape(m.group(0))}</span>'

                    try:
                        display_text = re.sub(
                            pattern, repl, display_text, flags=re.IGNORECASE
                        )
                    except Exception:
                        pass

                display_text = display_text.replace("\n", "<br>")
                msg_time = format_message_time(msg["timestamp"])

                message_html = f"""
                <div class="message-row {direction}">
                    <div class="message-bubble {direction}">
                        <div class="message-text">{display_text}</div>
                """

                if msg.get("notes"):
                    notes_text = html.escape(msg["notes"])
                    message_html += (
                        '<div style="font-size: 11px; color: rgba(255, 255, 255, 0.6); '
                        'margin-top: 4px; border-top: 1px solid rgba(255, 255, 255, 0.1); '
                        f'padding-top: 2px;">📝 {notes_text}</div>'
                    )
                if msg.get("handled_by"):
                    handler_text = html.escape(msg["handled_by"])
                    message_html += f'<div class="handler-meta">👤 {handler_text}</div>'

                message_html += f'<div class="message-time">{msg_time}</div></div></div>'
                st.markdown(message_html, unsafe_allow_html=True)

    # Pagination
    st.markdown('<div class="pagination-section">', unsafe_allow_html=True)
    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])

    with col_p1:
        prev_disabled = st.session_state.conv_offset == 0
        if st.button("⬅️ Prev", disabled=prev_disabled):
            st.session_state.conv_offset = max(
                0, st.session_state.conv_offset - CONV_LIMIT
            )
            st.rerun()

    with col_p2:
        start_idx = st.session_state.conv_offset + 1 if conv else 0
        end_idx = st.session_state.conv_offset + len(conv)
        st.markdown(
            f'<p class="pagination-info">Showing messages {start_idx}–{end_idx}</p>',
            unsafe_allow_html=True,
        )

    with col_p3:
        if st.button("Next ➡️"):
            st.session_state.conv_offset += CONV_LIMIT
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Send message section
    st.markdown('<div class="send-section">', unsafe_allow_html=True)
    st.markdown("### ✉️ Send Message")
    col_s1, col_s2 = st.columns([3, 1])

    draft_key = f"new_msg_{phone}"
    type_key = f"msg_type_{phone}"
    tmpl_key = f"tmpl_{phone}"

    with col_s1:
        new_msg = st.text_area(
            "Message",
            value=st.session_state.get(draft_key, ""),
            placeholder="Type a WhatsApp message to send...",
            key=draft_key,
            height=100,
        )

    with col_s2:
        msg_type_label = st.radio("Type", ["Text", "Template"], key=type_key)
        template_name = None
        if msg_type_label == "Template":
            template_name = st.text_input(
                "Template name",
                placeholder="e.g. sip_followup_1",
                key=tmpl_key,
            )

    if st.button(
        "📨 Send via WhatsApp", use_container_width=True, key=f"send_{phone}"
    ):
        msg_clean = (new_msg or "").strip()
        if not msg_clean:
            st.warning("Message cannot be empty.")
        else:
            msg_type = "template" if msg_type_label == "Template" else "text"
            ok = send_whatsapp_message(phone, msg_clean, msg_type, template_name)
            if ok:
                st.success("Message sent ✅")
                if draft_key in st.session_state:
                    del st.session_state[draft_key]
                time_module.sleep(0.5)
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Update follow-up status (use latest message, not first)
    update_msg = conv[-1] if conv else None

    if update_msg:
        st.markdown('<div class="update-section">', unsafe_allow_html=True)
        st.markdown("### 📝 Update Follow-up Status")

        col_u1, col_u2 = st.columns(2)
        with col_u1:
            fu_flag = st.checkbox(
                "🔴 Follow-up needed",
                value=update_msg.get("follow_up_needed", False),
            )
        with col_u2:
            handler = st.text_input(
                "👤 Handled by", value=update_msg.get("handled_by") or ""
            )

        notes = st.text_area("📝 Notes", value=update_msg.get("notes") or "")

        if st.button("💾 Save Follow-up", use_container_width=True):
            try:
                response = make_request_with_retry(
                    f"{API_BASE}/message/{update_msg['id']}",
                    method="PATCH",
                    json_data={
                        "follow_up_needed": fu_flag,
                        "notes": notes,
                        "handled_by": handler,
                    },
                )
                if response and response.status_code == 200:
                    st.success("✅ Saved!")
                    st.rerun()
                else:
                    st.error("Error saving follow-up status")
            except Exception as e:
                st.error(f"Error: {str(e)}")

        st.markdown("</div>", unsafe_allow_html=True)
