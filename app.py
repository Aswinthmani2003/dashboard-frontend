import streamlit as st
import requests
from datetime import datetime, date, time
import base64
from pathlib import Path
import re

API_BASE = "https://dashboard-backend-qqmi.onrender.com"
MAKE_WEBHOOK_URL = st.secrets.get("make_webhook_url", "")  # set this in secrets.toml


def check_password():
    """Simple password gate using Streamlit secrets"""

    def password_entered():
        """Checks whether the password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["dashboard_password"]:
            st.session_state["password_correct"] = True
            # Don't store the password
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.stop()

    elif not st.session_state["password_correct"]:
        # Wrong password, show input + error
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("❌ Wrong password")
        st.stop()


# Page config
st.set_page_config(
    page_title="WhatsApp Chat Inbox",
    layout="wide",
    initial_sidebar_state="expanded"
)
check_password()

# Initialize theme in session state
if "theme" not in st.session_state:
    st.session_state.theme = "dark"  # default to dark mode

# Function to load and encode logo
def get_base64_logo():
    """Load logo.png and convert to base64 for embedding"""
    logo_path = Path("Logo.png")
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

# Function to get CSS based on theme
def get_css(theme):
    if theme == "dark":
        return """
        <style>
            /* Global dark theme */
            .main {
                background-color: #0d1418;
                padding: 0 !important;
            }
            
            /* Remove default padding */
            .block-container {
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                max-width: 100% !important;
            }
            
            /* Sidebar styling */
            [data-testid="stSidebar"] {
                background-color: #111b21;
                border-right: 1px solid #2a3942;
            }
            
            [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, 
            [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 {
                color: #e9edef !important;
            }
            
            [data-testid="stSidebar"] label {
                color: #8696a0 !important;
            }
            
            [data-testid="stSidebar"] input {
                background-color: #2a3942 !important;
                color: #e9edef !important;
                border: 1px solid #3b4a54 !important;
            }
            
            /* Header */
            .main-header {
                background: #202c33;
                padding: 15px 20px;
                display: flex;
                align-items: center;
                gap: 15px;
                border-bottom: 1px solid #2a3942;
                margin-bottom: 0;
                position: sticky;
                top: 0;
                z-index: 999;
            }
            
            .main-header h1 {
                color: #e9edef;
                margin: 0;
                font-size: 19px;
                font-weight: 400;
                flex: 1;
            }
            
            .logo-img {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                object-fit: cover;
            }
            
            /* Contact list */
            .contact-card {
                background-color: #111b21;
                padding: 12px 16px;
                cursor: pointer;
                border-bottom: 1px solid #2a3942;
                transition: background-color 0.2s;
                position: relative;
            }
            
            .contact-card:hover {
                background-color: #202c33;
            }
            
            .contact-card.selected {
                background-color: #2a3942;
            }
            
            .contact-name {
                color: #e9edef;
                font-size: 16px;
                font-weight: 400;
                margin-bottom: 2px;
            }
            
            .contact-phone {
                color: #667781;
                font-size: 13px;
                margin-bottom: 3px;
            }
            
            .contact-preview {
                color: #8696a0;
                font-size: 14px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .contact-time {
                position: absolute;
                top: 12px;
                right: 16px;
                color: #8696a0;
                font-size: 12px;
            }
            
            .follow-up-dot {
                color: #ff3b30;
                font-weight: bold;
                margin-right: 5px;
            }
            
            /* Chat header */
            .chat-header {
                background: #202c33;
                padding: 10px 20px;
                margin-bottom: 10px;
                border-bottom: 1px solid #2a3942;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border: 1px solid #3b4a54;
                border-radius: 8px;
            }
            
            .chat-header-info h3 {
                color: #e9edef;
                margin: 0;
                font-size: 16px;
                font-weight: 400;
            }
            
            .chat-header-info p {
                color: #8696a0;
                margin: 0;
                font-size: 13px;
            }
            
            .unread-badge {
                color: #ff3b30;
                font-size: 13px;
                margin: 0 0 10px 20px;
            }
            
            /* Message container */
            .message-row {
                display: flex;
                margin-bottom: 12px;
                clear: both;
            }
            
            .message-row.user {
                justify-content: flex-start;
            }
            
            .message-row.bot {
                justify-content: flex-end;
            }
            
            /* Message bubble */
            .message-bubble {
                max-width: 65%;
                padding: 8px 12px 8px 12px;
                border-radius: 8px;
                position: relative;
                box-shadow: 0 1px 0.5px rgba(0,0,0,0.13);
            }
            
            .message-bubble.user {
                background-color: #202c33;
            }
            
            .message-bubble.bot {
                background-color: #005c4b;
            }
            
            .message-text {
                color: #e9edef;
                font-size: 14.2px;
                line-height: 19px;
                margin-bottom: 4px;
                word-wrap: break-word;
            }
            
            .message-time {
                color: #8696a0;
                font-size: 11px;
                text-align: right;
                margin-top: 4px;
            }
            
            .message-meta {
                color: #8696a0;
                font-size: 11px;
                margin-top: 4px;
            }
            
            /* Highlight for search matches */
            .highlight {
                background-color: #86745f;
                padding: 0 1px;
                border-radius: 2px;
            }
            
            /* Update section */
            .update-section {
                border: 1px solid #3b4a54;
                border-radius: 8px;
                padding: 15px;
                margin-top: 20px;
                background-color: #111b21;
            }
            
            .update-section h3 {
                color: #e9edef !important;
                font-size: 16px !important;
                margin-bottom: 15px !important;
            }
            
            .send-section {
                border: 1px solid #3b4a54;
                border-radius: 8px;
                padding: 15px;
                margin-top: 20px;
                margin-bottom: 20px;
                background-color: #111b21;
            }
            
            .send-section h3 {
                color: #e9edef !important;
                font-size: 16px !important;
                margin-bottom: 15px !important;
            }
            
            .chat-area {
                border: 1px solid #3b4a54;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                background-color: #0d1418;
                min-height: 1px;
            }
            
            .pagination-section {
                border: 1px solid #3b4a54;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                background-color: #111b21;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .pagination-info {
                color: #8696a0;
                font-size: 14px;
                margin: 0;
                text-align: center;
                flex: 1;
            }
            
            /* Buttons */
            .stButton > button {
                background-color: #00a884 !important;
                color: white !important;
                border: none !important;
                font-weight: 500 !important;
            }
            
            .stButton > button:hover {
                background-color: #06cf9c !important;
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
            
            /* Input fields */
            .stTextInput input, .stTextArea textarea {
                background-color: #2a3942 !important;
                color: #e9edef !important;
                border: 1px solid #3b4a54 !important;
            }
            
            /* Checkbox */
            [data-testid="stCheckbox"] label {
                color: #e9edef !important;
            }
            
            /* Selectbox */
            .stSelectbox label {
                color: #e9edef !important;
            }
            
            /* Radio buttons */
            .stRadio label {
                color: #e9edef !important;
            }
            
            /* Scrollbar */
            ::-webkit-scrollbar {
                width: 6px;
                height: 6px;
            }
            
            ::-webkit-scrollbar-track {
                background: #0d1418;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #2a3942;
                border-radius: 3px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #3b4a54;
            }
            
            /* Hide streamlit menu/footer and header */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* Override streamlit's default padding for header */
            .main .block-container {
                padding-top: 0rem !important;
            }
        </style>
        """
    else:  # light theme
        return """
        <style>
            /* Global light theme */
            .main {
                background-color: #ffffff;
                padding: 0 !important;
            }
            
            /* Remove default padding */
            .block-container {
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                max-width: 100% !important;
            }
            
            /* Sidebar styling */
            [data-testid="stSidebar"] {
                background-color: #f8f9fa;
                border-right: 1px solid #dddfe2;
            }
            
            [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, 
            [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 {
                color: #1c1e21 !important;
            }
            
            [data-testid="stSidebar"] label {
                color: #65676b !important;
            }
            
            [data-testid="stSidebar"] input {
                background-color: #ffffff !important;
                color: #1c1e21 !important;
                border: 1px solid #ccd0d5 !important;
            }
            
            /* Header */
            .main-header {
                background: #f0f2f5;
                padding: 15px 20px;
                display: flex;
                align-items: center;
                gap: 15px;
                border-bottom: 1px solid #dddfe2;
                margin-bottom: 0;
                position: sticky;
                top: 0;
                z-index: 999;
            }
            
            .main-header h1 {
                color: #1c1e21;
                margin: 0;
                font-size: 19px;
                font-weight: 400;
                flex: 1;
            }
            
            .logo-img {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                object-fit: cover;
            }
            
            /* Contact list */
            .contact-card {
                background-color: #ffffff;
                padding: 12px 16px;
                cursor: pointer;
                border-bottom: 1px solid #dddfe2;
                transition: background-color 0.2s;
                position: relative;
            }
            
            .contact-card:hover {
                background-color: #f0f2f5;
            }
            
            .contact-card.selected {
                background-color: #e4e6eb;
            }
            
            .contact-name {
                color: #1c1e21;
                font-size: 16px;
                font-weight: 400;
                margin-bottom: 2px;
            }
            
            .contact-phone {
                color: #65676b;
                font-size: 13px;
                margin-bottom: 3px;
            }
            
            .contact-preview {
                color: #65676b;
                font-size: 14px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .contact-time {
                position: absolute;
                top: 12px;
                right: 16px;
                color: #65676b;
                font-size: 12px;
            }
            
            .follow-up-dot {
                color: #ff3b30;
                font-weight: bold;
                margin-right: 5px;
            }
            
            /* Chat header */
            .chat-header {
                background: #f0f2f5;
                padding: 10px 20px;
                margin-bottom: 10px;
                border-bottom: 1px solid #dddfe2;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border: 1px solid #ccd0d5;
                border-radius: 8px;
            }
            
            .chat-header-info h3 {
                color: #1c1e21;
                margin: 0;
                font-size: 16px;
                font-weight: 400;
            }
            
            .chat-header-info p {
                color: #65676b;
                margin: 0;
                font-size: 13px;
            }
            
            .unread-badge {
                color: #ff3b30;
                font-size: 13px;
                margin: 0 0 10px 20px;
            }
            
            /* Message container */
            .message-row {
                display: flex;
                margin-bottom: 12px;
                clear: both;
            }
            
            .message-row.user {
                justify-content: flex-start;
            }
            
            .message-row.bot {
                justify-content: flex-end;
            }
            
            /* Message bubble */
            .message-bubble {
                max-width: 65%;
                padding: 8px 12px 8px 12px;
                border-radius: 8px;
                position: relative;
                box-shadow: 0 1px 0.5px rgba(0,0,0,0.13);
            }
            
            .message-bubble.user {
                background-color: #f0f2f5;
            }
            
            .message-bubble.bot {
                background-color: #0084ff;
            }
            
            .message-text {
                color: #1c1e21;
                font-size: 14.2px;
                line-height: 19px;
                margin-bottom: 4px;
                word-wrap: break-word;
            }
            
            .message-time {
                color: #65676b;
                font-size: 11px;
                text-align: right;
                margin-top: 4px;
            }
            
            .message-meta {
                color: #65676b;
                font-size: 11px;
                margin-top: 4px;
            }
            
            /* Highlight for search matches */
            .highlight {
                background-color: #ffd700;
                padding: 0 1px;
                border-radius: 2px;
            }
            
            /* Update section */
            .update-section {
                border: 1px solid #ccd0d5;
                border-radius: 8px;
                padding: 15px;
                margin-top: 20px;
                background-color: #ffffff;
            }
            
            .update-section h3 {
                color: #1c1e21 !important;
                font-size: 16px !important;
                margin-bottom: 15px !important;
            }
            
            .send-section {
                border: 1px solid #ccd0d5;
                border-radius: 8px;
                padding: 15px;
                margin-top: 20px;
                margin-bottom: 20px;
                background-color: #ffffff;
            }
            
            .send-section h3 {
                color: #1c1e21 !important;
                font-size: 16px !important;
                margin-bottom: 15px !important;
            }
            
            .chat-area {
                border: 1px solid #ccd0d5;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                background-color: #ffffff;
                min-height: 1px;
            }
            
            .pagination-section {
                border: 1px solid #ccd0d5;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                background-color: #ffffff;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .pagination-info {
                color: #65676b;
                font-size: 14px;
                margin: 0;
                text-align: center;
                flex: 1;
            }
            
            /* Buttons */
            .stButton > button {
                background-color: #0084ff !important;
                color: white !important;
                border: none !important;
                font-weight: 500 !important;
            }
            
            .stButton > button:hover {
                background-color: #0073e6 !important;
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
            
            /* Input fields */
            .stTextInput input, .stTextArea textarea {
                background-color: #ffffff !important;
                color: #1c1e21 !important;
                border: 1px solid #ccd0d5 !important;
            }
            
            /* Checkbox */
            [data-testid="stCheckbox"] label {
                color: #1c1e21 !important;
            }
            
            /* Selectbox */
            .stSelectbox label {
                color: #1c1e21 !important;
            }
            
            /* Radio buttons */
            .stRadio label {
                color: #1c1e21 !important;
            }
            
            /* Scrollbar */
            ::-webkit-scrollbar {
                width: 6px;
                height: 6px;
            }
            
            ::-webkit-scrollbar-track {
                background: #f0f2f5;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #aeb5bb;
                border-radius: 3px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #ccd0d5;
            }
            
            /* Hide streamlit menu/footer and header */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* Override streamlit's default padding for header */
            .main .block-container {
                padding-top: 0rem !important;
            }
        </style>
        """

# Apply CSS based on current theme
st.markdown(get_css(st.session_state.theme), unsafe_allow_html=True)

# Header with logo
logo_base64 = get_base64_logo()
if logo_base64:
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="logo-img">'
else:
    # Fallback to external URL if Logo.png not found
    logo_url = "https://drive.google.com/uc?export=view&id=1NSTzTZ_gusa-c4Sc5dZelth-Djft0Zca"
    logo_html = f'<img src="{logo_url}" class="logo-img" onerror="this.style.display=\'none\'">'

st.markdown(f"""
<div class="main-header">
    {logo_html}
    <h1>WhatsApp Chat Inbox – Amirtharaj Investment</h1>
</div>
""", unsafe_allow_html=True)

# Sidebar Filters
st.sidebar.title("🔍 Filters")

st.sidebar.subheader("📱 Phone Number")
search_phone = st.sidebar.text_input("Phone Search", placeholder="Search by phone...", label_visibility="collapsed", key="phone")

st.sidebar.subheader("👤 Client Name")
search_name = st.sidebar.text_input("Name Search", placeholder="Search by name...", label_visibility="collapsed", key="name")

st.sidebar.subheader("📅 Date")
filter_by_date = st.sidebar.checkbox("Enable date filter")
date_filter = st.sidebar.date_input("Select date", value=date.today()) if filter_by_date else None

st.sidebar.subheader("🕐 Time Range")
filter_by_time = st.sidebar.checkbox("Enable time filter")
if filter_by_time:
    time_from = st.sidebar.time_input("From", value=time(0, 0))
    time_to = st.sidebar.time_input("To", value=time(23, 59))
else:
    time_from = time_to = None

st.sidebar.subheader("🔴 Follow-up")
only_fu = st.sidebar.checkbox("Show only follow-up clients")

# Theme toggle button in sidebar
st.sidebar.divider()
st.sidebar.subheader("🎨 Theme")

# Simple toggle button
if st.session_state.theme == "dark":
    if st.sidebar.button("☀️ Switch to Light Mode", use_container_width=True, key="theme_toggle"):
        st.session_state.theme = "light"
        st.rerun()
else:
    if st.sidebar.button("🌙 Switch to Dark Mode", use_container_width=True, key="theme_toggle"):
        st.session_state.theme = "dark"
        st.rerun()

# Helper functions
def fetch_contacts(only_follow_up: bool):
    try:
        r = requests.get(f"{API_BASE}/contacts", params={"only_follow_up": only_follow_up})
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Error: {e}")
        return []


def fetch_conversation(phone: str, limit: int = 50, offset: int = 0):
    try:
        r = requests.get(
            f"{API_BASE}/conversation/{phone}",
            params={"limit": limit, "offset": offset}
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Error: {e}")
        return []


def delete_conversation(phone: str):
    try:
        r = requests.delete(f"{API_BASE}/conversation/{phone}")
        return r.status_code == 200
    except:
        return False


def delete_message(msg_id: int):
    try:
        r = requests.delete(f"{API_BASE}/message/{msg_id}")
        return r.status_code == 200
    except:
        return False


def filter_messages(messages, date_filter, time_from, time_to):
    if not date_filter and not time_from:
        return messages
    filtered = []
    for msg in messages:
        msg_dt = datetime.fromisoformat(msg["timestamp"])
        if date_filter and msg_dt.date() != date_filter:
            continue
        if time_from and time_to:
            msg_time = msg_dt.time()
            if not (time_from <= msg_time <= time_to):
                continue
        filtered.append(msg)
    return filtered


def send_whatsapp_message(phone: str, message_text: str,
                          msg_type: str = "text",
                          template_name: str | None = None) -> bool:
    """Send message to Make.com webhook which will handle WhatsApp API."""
    if not MAKE_WEBHOOK_URL:
        st.error("Make webhook URL not configured (set 'make_webhook_url' in Streamlit secrets).")
        return False

    payload = {
        "phone": phone,
        "message": message_text,
        "type": msg_type,  # 'text' or 'template'
    }
    if msg_type == "template" and template_name:
        payload["template_name"] = template_name

    try:
        r = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=15)
        if r.status_code in (200, 201, 202):
            # Log the sent message to the backend database
            log_sent_message(phone, message_text, msg_type)
            return True
        else:
            st.error(f"Send failed ({r.status_code}): {r.text}")
            return False
    except Exception as e:
        st.error(f"Send error: {e}")
        return False


def log_sent_message(phone: str, message: str, msg_type: str = "text"):
    """Log sent message to backend database"""
    try:
        payload = {
            "phone": phone,
            "message": message,
            "direction": "outgoing",
            "message_type": msg_type,
            "timestamp": datetime.now().isoformat(),
            "follow_up_needed": False,
            "notes": "",
            "handled_by": "Dashboard User"
        }
        response = requests.post(f"{API_BASE}/log_message", json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        # Silently fail - don't disrupt the UI if logging fails
        st.warning(f"Message sent but not logged in database: {e}")
        return False


# Fetch and filter contacts
contacts = fetch_contacts(only_fu)
if search_phone:
    contacts = [c for c in contacts if search_phone.lower() in c["phone"].lower()]
if search_name:
    contacts = [c for c in contacts if c.get("client_name") and search_name.lower() in c["client_name"].lower()]

if not contacts:
    st.info("🔍 No contacts found")
    st.stop()

# Initialize session state
if "selected_phone" not in st.session_state:
    st.session_state.selected_phone = contacts[0]["phone"]

if "conv_offset" not in st.session_state:
    st.session_state.conv_offset = 0

if "last_message_count" not in st.session_state:
    st.session_state.last_message_count = {}

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True

CONV_LIMIT = 20  # recommended


# Layout
col1, col2 = st.columns([1, 2.5])

with col1:
    st.markdown("### 💬 Contacts")
    for c in contacts:
        client_name = c["client_name"] or "Unknown"
        phone = c["phone"]
        is_selected = st.session_state.selected_phone == phone
        fu_indicator = "🔴 " if c.get("follow_up_open") else ""
        
        if st.button(
            f"{fu_indicator}{client_name}",
            key=phone,
            use_container_width=True,
            type="primary" if is_selected else "secondary"
        ):
            # When switching contact, reset pagination and draft
            st.session_state.selected_phone = phone
            st.session_state.conv_offset = 0
            draft_key = f"new_msg_{phone}"
            if draft_key in st.session_state:
                # Delete the key instead of setting to empty string
                del st.session_state[draft_key]
            st.rerun()

with col2:
    phone = st.session_state.selected_phone
    selected = next((c for c in contacts if c["phone"] == phone), None)
    
    if not selected:
        st.stop()
    
    client_name = selected["client_name"] or phone
    
    # Auto-refresh toggle and logic
    col_toggle1, col_toggle2 = st.columns([3, 1])
    with col_toggle1:
        pass
    with col_toggle2:
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=st.session_state.auto_refresh, key="auto_refresh_toggle")
        st.session_state.auto_refresh = auto_refresh
    
    # Auto-refresh script - checks for new messages every 5 seconds
    if st.session_state.auto_refresh:
        st.markdown("""
        <script>
            setTimeout(function() {
                window.parent.location.reload();
            }, 5000);
        </script>
        """, unsafe_allow_html=True)
    
    # Chat header + delete
    col_h1, col_h2 = st.columns([6, 1])
    with col_h1:
        st.markdown(f"""
        <div class="chat-header">
            <div class="chat-header-info">
                <h3>{client_name}</h3>
                <p>{phone}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_h2:
        if st.button("🗑️ Delete All", key="del_all"):
            if st.session_state.get('confirm_del'):
                if delete_conversation(phone):
                    st.success("Deleted!")
                    st.session_state.pop('confirm_del', None)
                    st.rerun()
            else:
                st.session_state.confirm_del = True
                st.warning("Click again")
    
    # Search inside conversation
    search_query = st.text_input(
        "Search in this chat",
        placeholder="Type to search messages...",
        key="search_conv"
    )
    
    # Fetch messages with pagination
    conv = fetch_conversation(phone, limit=CONV_LIMIT, offset=st.session_state.conv_offset)
    conv = filter_messages(conv, date_filter, time_from, time_to)
    
    # Unread badge (based on follow_up_needed in current page)
    unread_count = sum(1 for m in conv if m.get("follow_up_needed"))
    if unread_count > 0:
        st.markdown(f"<p class='unread-badge'>🔴 {unread_count} unread messages</p>", unsafe_allow_html=True)
    
    if not conv:
        st.info("📭 No messages")
    else:
        # Chat area with border
        st.markdown('<div class="chat-area">', unsafe_allow_html=True)
        
        for msg in conv:
            ts = datetime.fromisoformat(msg["timestamp"])
            direction = "user" if msg["direction"] in ["user", "incoming"] else "bot"
            
            raw_text = msg["message"] or ""
            display_text = raw_text
            
            # Highlight search matches
            if search_query:
                pattern = re.escape(search_query)
                def repl(m):
                    return f"<span class='highlight'>{m.group(0)}</span>"
                display_text = re.sub(pattern, repl, display_text, flags=re.IGNORECASE)
            
            # Replace newlines with <br>
            display_text = display_text.replace("\n", "<br>")
            
            message_html = f"""
            <div class="message-row {direction}">
                <div class="message-bubble {direction}">
                    <div class="message-text">{display_text}</div>
                    <div class="message-time">{ts.strftime("%H:%M")}</div>
            """
            
            if msg.get("follow_up_needed"):
                message_html += '<div class="message-meta">🔴 Follow-up needed</div>'
            if msg.get("notes"):
                message_html += f'<div class="message-meta">📝 {msg["notes"]}</div>'
            if msg.get("handled_by"):
                message_html += f'<div class="message-meta">👤 {msg["handled_by"]}</div>'
            
            message_html += "</div></div>"
            st.markdown(message_html, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close chat-area
        
        # Pagination controls with centered info
        st.markdown('<div class="pagination-section">', unsafe_allow_html=True)
        col_p1, col_p2, col_p3 = st.columns([1, 2, 1])

        # Prev button – only disabled on first page
        with col_p1:
            prev_disabled = st.session_state.conv_offset == 0
            if st.button("⬅️ Prev", disabled=prev_disabled):
                st.session_state.conv_offset = max(0, st.session_state.conv_offset - CONV_LIMIT)
                st.rerun()

        # Info text in center
        with col_p2:
            start_idx = st.session_state.conv_offset + 1 if conv else 0
            end_idx = st.session_state.conv_offset + len(conv)
            st.markdown(f'<p class="pagination-info">Showing messages {start_idx}–{end_idx}</p>', unsafe_allow_html=True)

        # Next button – always allowed, backend decides if more exist
        with col_p3:
            if st.button("Next ➡️"):
                st.session_state.conv_offset += CONV_LIMIT
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close pagination-section
        
        # --- Send Message section ---
        st.markdown('<div class="send-section">', unsafe_allow_html=True)
        st.markdown("### ✉️ Send Message")
        col_s1, col_s2 = st.columns([3, 1])

        draft_key = f"new_msg_{phone}"
        type_key = f"msg_type_{phone}"
        tmpl_key = f"tmpl_{phone}"

        with col_s1:
            # Use value parameter with get() to handle missing key gracefully
            new_msg = st.text_area(
                "Message",
                value=st.session_state.get(draft_key, ""),
                placeholder="Type a WhatsApp message to send...",
                key=draft_key,
                height=80
            )

        with col_s2:
            msg_type_label = st.radio(
                "Type",
                ["Text", "Template"],
                key=type_key
            )
            template_name = None
            if msg_type_label == "Template":
                template_name = st.text_input(
                    "Template name",
                    placeholder="e.g. sip_followup_1",
                    key=tmpl_key
                )

        if st.button("📨 Send via WhatsApp", use_container_width=True, key=f"send_{phone}"):
            msg_clean = (new_msg or "").strip()
            if not msg_clean:
                st.warning("Message cannot be empty.")
            else:
                msg_type = "template" if msg_type_label == "Template" else "text"
                ok = send_whatsapp_message(phone, msg_clean, msg_type, template_name)
                if ok:
                    st.success("Message sent ✅")
                    # Clear draft by deleting the key instead of setting to empty string
                    if draft_key in st.session_state:
                        del st.session_state[draft_key]
                    # Wait a moment for the message to be logged
                    import time
                    time.sleep(0.5)
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close send-section
        
        # Update section
        last_msg = conv[-1]
        
        st.markdown('<div class="update-section">', unsafe_allow_html=True)
        st.markdown("### 📝 Update Follow-up Status")
        
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            fu_flag = st.checkbox("🔴 Follow-up needed", value=last_msg.get("follow_up_needed", False))
        with col_u2:
            handler = st.text_input("👤 Handled by", value=last_msg.get("handled_by") or "")
        
        notes = st.text_area("📝 Notes", value=last_msg.get("notes") or "")
        
        if st.button("💾 Save Follow-up", use_container_width=True):
            resp = requests.patch(
                f"{API_BASE}/message/{last_msg['id']}",
                json={"follow_up_needed": fu_flag, "notes": notes, "handled_by": handler}
            )
            if resp.status_code == 200:
                st.success("✅ Saved!")
                st.rerun()
            else:
                st.error(f"Error: {resp.text}")
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close update-section
