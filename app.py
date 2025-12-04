import streamlit as st
import requests
from datetime import datetime, date, time
import base64
from pathlib import Path
import re
import html

API_BASE = "https://dashboard-backend-qqmi.onrender.com"
MAKE_WEBHOOK_URL = st.secrets.get("make_webhook_url", "")


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
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.stop()
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("❌ Wrong password")
        st.stop()


# Page config
st.set_page_config(
    page_title="WhatsApp Business Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)
check_password()

# Initialize theme in session state
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# Initialize filter states
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
            @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;500;600&display=swap');
            
            * {
                font-family: 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            }
            
            .main {
                background-color: #0b141a;
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
                gap: 12px;
                border-bottom: 1px solid #2a3942;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                position: sticky;
                top: 0;
                z-index: 999;
            }
            
            .main-header h1 {
                color: #e9edef;
                margin: 0;
                font-size: 16px;
                font-weight: 500;
                flex: 1;
                letter-spacing: 0.3px;
            }
            
            .logo-img {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                object-fit: cover;
            }
            
            .filter-container {
                background-color: #111b21;
                border-radius: 0;
                padding: 0;
                margin: 0 0 8px 0;
                overflow: hidden;
                box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            }
            
            .filter-header {
                background-color: #202c33;
                padding: 12px 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: pointer;
            }
            
            .filter-header h3 {
                color: #e9edef;
                margin: 0;
                font-size: 15px;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .filter-content {
                padding: 16px;
                background: #0b141a;
            }
            
            .chat-container {
                display: flex;
                flex-direction: column;
                height: calc(100vh - 120px);
                background: #0b141a;
                margin-top: -20px;
            }
            
            .stSelectbox {
                margin-bottom: 0 !important;
            }
            
            [data-testid="stSelectbox"] {
                margin-bottom: 0 !important;
            }
            
            .chat-header {
                background: #202c33;
                padding: 10px 16px;
                border-bottom: 1px solid #2a3942;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-shrink: 0;
            }
            
            .chat-header-left {
                display: flex;
                align-items: center;
                gap: 12px;
                flex: 1;
            }
            
            .chat-avatar {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: linear-gradient(135deg, #00a884 0%, #00796b 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                color: #fff;
                font-size: 16px;
                font-weight: 500;
            }
            
            .chat-header-info {
                flex: 1;
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
            
            .chat-header-actions {
                display: flex;
                gap: 20px;
                align-items: center;
            }
            
            .icon-btn {
                color: #aebac1;
                background: none;
                border: none;
                cursor: pointer;
                font-size: 20px;
                padding: 4px;
                transition: color 0.15s ease;
            }
            
            .icon-btn:hover {
                color: #e9edef;
            }
            
            .messages-area {
                flex: 1;
                overflow-y: auto;
                padding: 12px 8% 20px 8%;
                background-image: 
                    repeating-linear-gradient(
                        45deg,
                        transparent,
                        transparent 10px,
                        rgba(255,255,255,.02) 10px,
                        rgba(255,255,255,.02) 20px
                    );
                position: relative;
            }
            
            .message-row {
                display: flex;
                margin-bottom: 8px;
                clear: both;
                animation: fadeIn 0.3s ease-in;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .message-row.incoming {
                justify-content: flex-start;
            }
            
            .message-row.outgoing {
                justify-content: flex-end;
            }
            
            .message-bubble {
                max-width: 65%;
                padding: 6px 7px 8px 9px;
                border-radius: 7.5px;
                position: relative;
                box-shadow: 0 1px 0.5px rgba(11,20,26,0.13);
                word-wrap: break-word;
            }
            
            .message-bubble.incoming {
                background-color: #202c33;
            }
            
            .message-bubble.outgoing {
                background-color: #005c4b;
            }
            
            .message-text {
                color: #e9edef;
                font-size: 14.2px;
                line-height: 19px;
                margin: 0;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            
            .message-footer {
                display: flex;
                align-items: center;
                justify-content: flex-end;
                gap: 4px;
                margin-top: 4px;
                font-size: 11px;
                color: #8696a0;
            }
            
            .message-time {
                color: #8696a0;
                font-size: 11px;
            }
            
            .message-status {
                color: #53bdeb;
                font-size: 14px;
                line-height: 1;
            }
            
            .message-meta {
                color: #8696a0;
                font-size: 11px;
                margin-top: 4px;
                display: flex;
                align-items: center;
                gap: 4px;
            }
            
            .message-input-area {
                background: #202c33;
                padding: 8px 16px;
                border-top: 1px solid #2a3942;
                flex-shrink: 0;
            }
            
            .date-divider {
                text-align: center;
                margin: 20px 0;
                position: relative;
            }
            
            .date-divider span {
                background: #202c33;
                color: #8696a0;
                padding: 5px 12px;
                border-radius: 7.5px;
                font-size: 12.5px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            }
            
            .pagination-section {
                background: #202c33;
                padding: 12px 16px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 12px;
                border-top: 1px solid #2a3942;
            }
            
            .pagination-info {
                color: #8696a0;
                font-size: 13px;
                margin: 0;
            }
            
            .update-section {
                background: #111b21;
                border-top: 1px solid #2a3942;
                padding: 16px;
                margin-top: auto;
            }
            
            .update-section h3 {
                color: #e9edef !important;
                font-size: 15px !important;
                font-weight: 500 !important;
                margin-bottom: 12px !important;
            }
            
            .stButton > button {
                background-color: #00a884 !important;
                color: white !important;
                border: none !important;
                font-weight: 500 !important;
                border-radius: 8px !important;
                padding: 8px 16px !important;
                transition: background-color 0.15s ease !important;
            }
            
            .stButton > button:hover {
                background-color: #06cf9c !important;
            }
            
            .stTextInput input, .stTextArea textarea {
                background-color: #2a3942 !important;
                color: #e9edef !important;
                border: 1px solid #3b4a54 !important;
                border-radius: 8px !important;
                font-size: 14px !important;
            }
            
            .stTextInput input:focus, .stTextArea textarea:focus {
                border-color: #00a884 !important;
                box-shadow: 0 0 0 1px #00a884 !important;
            }
            
            [data-testid="stCheckbox"] label {
                color: #e9edef !important;
                font-size: 14px !important;
            }
            
            .stSelectbox label {
                color: #e9edef !important;
                font-size: 14px !important;
            }
            
            .stRadio label {
                color: #e9edef !important;
                font-size: 14px !important;
            }
            
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
            
            ::-webkit-scrollbar-track {
                background: #0b141a;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #374045;
                border-radius: 3px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #4a5458;
            }
            
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            .highlight {
                background-color: #5c5c5c;
                padding: 0 2px;
                border-radius: 2px;
            }
            
            .empty-state {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100%;
                color: #8696a0;
                text-align: center;
                padding: 40px;
            }
            
            .empty-state-icon {
                font-size: 64px;
                margin-bottom: 16px;
                opacity: 0.5;
            }
            
            .empty-state-text {
                font-size: 20px;
                margin-bottom: 8px;
            }
            
            .empty-state-subtext {
                font-size: 14px;
            }
        </style>
        """
    else:
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;500;600&display=swap');
            
            * {
                font-family: 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            }
            
            .main {
                background-color: #f0f2f5;
                padding: 0 !important;
            }
            
            .block-container {
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                max-width: 100% !important;
            }
            
            .main-header {
                background: #ededed;
                padding: 10px 16px;
                display: flex;
                align-items: center;
                gap: 12px;
                border-bottom: 1px solid #d1d7db;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                position: sticky;
                top: 0;
                z-index: 999;
            }
            
            .main-header h1 {
                color: #111b21;
                margin: 0;
                font-size: 16px;
                font-weight: 500;
                flex: 1;
                letter-spacing: 0.3px;
            }
            
            .logo-img {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                object-fit: cover;
            }
            
            .filter-container {
                background-color: #fff;
                border-radius: 0;
                padding: 0;
                margin: 0 0 8px 0;
                overflow: hidden;
                box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            }
            
            .filter-header {
                background-color: #ededed;
                padding: 12px 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: pointer;
            }
            
            .filter-header h3 {
                color: #111b21;
                margin: 0;
                font-size: 15px;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .filter-content {
                padding: 16px;
                background: #fff;
            }
            
            .chat-container {
                display: flex;
                flex-direction: column;
                height: calc(100vh - 120px);
                background: #efeae2;
                margin-top: -20px;
            }
            
            .stSelectbox {
                margin-bottom: 0 !important;
            }
            
            [data-testid="stSelectbox"] {
                margin-bottom: 0 !important;
            }
            
            .chat-header {
                background: #ededed;
                padding: 10px 16px;
                border-bottom: 1px solid #d1d7db;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-shrink: 0;
            }
            
            .chat-header-left {
                display: flex;
                align-items: center;
                gap: 12px;
                flex: 1;
            }
            
            .chat-avatar {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: linear-gradient(135deg, #25d366 0%, #128c7e 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                color: #fff;
                font-size: 16px;
                font-weight: 500;
            }
            
            .chat-header-info {
                flex: 1;
            }
            
            .chat-header-info h3 {
                color: #111b21;
                margin: 0;
                font-size: 16px;
                font-weight: 400;
            }
            
            .chat-header-info p {
                color: #667781;
                margin: 0;
                font-size: 13px;
            }
            
            .chat-header-actions {
                display: flex;
                gap: 20px;
                align-items: center;
            }
            
            .icon-btn {
                color: #54656f;
                background: none;
                border: none;
                cursor: pointer;
                font-size: 20px;
                padding: 4px;
                transition: color 0.15s ease;
            }
            
            .icon-btn:hover {
                color: #111b21;
            }
            
            .messages-area {
                flex: 1;
                overflow-y: auto;
                padding: 12px 8% 20px 8%;
                background-image: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAKklEQVQoU2NkYGD4z4AEpgIx2ERGRJB/DAwM/0GG/wcZCNIJM3QUFAIAnI0G8S3WzXQAAAAASUVORK5CYII=');
                background-repeat: repeat;
                position: relative;
            }
            
            .message-row {
                display: flex;
                margin-bottom: 8px;
                clear: both;
                animation: fadeIn 0.3s ease-in;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .message-row.incoming {
                justify-content: flex-start;
            }
            
            .message-row.outgoing {
                justify-content: flex-end;
            }
            
            .message-bubble {
                max-width: 65%;
                padding: 6px 7px 8px 9px;
                border-radius: 7.5px;
                position: relative;
                box-shadow: 0 1px 0.5px rgba(0,0,0,0.13);
                word-wrap: break-word;
            }
            
            .message-bubble.incoming {
                background-color: #ffffff;
            }
            
            .message-bubble.outgoing {
                background-color: #d9fdd3;
            }
            
            .message-text {
                color: #111b21;
                font-size: 14.2px;
                line-height: 19px;
                margin: 0;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            
            .message-footer {
                display: flex;
                align-items: center;
                justify-content: flex-end;
                gap: 4px;
                margin-top: 4px;
                font-size: 11px;
                color: #667781;
            }
            
            .message-time {
                color: #667781;
                font-size: 11px;
            }
            
            .message-status {
                color: #53bdeb;
                font-size: 14px;
                line-height: 1;
            }
            
            .message-meta {
                color: #667781;
                font-size: 11px;
                margin-top: 4px;
                display: flex;
                align-items: center;
                gap: 4px;
            }
            
            .message-input-area {
                background: #ededed;
                padding: 8px 16px;
                border-top: 1px solid #d1d7db;
                flex-shrink: 0;
            }
            
            .date-divider {
                text-align: center;
                margin: 20px 0;
                position: relative;
            }
            
            .date-divider span {
                background: #ffffff;
                color: #54656f;
                padding: 5px 12px;
                border-radius: 7.5px;
                font-size: 12.5px;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            }
            
            .pagination-section {
                background: #ededed;
                padding: 12px 16px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 12px;
                border-top: 1px solid #d1d7db;
            }
            
            .pagination-info {
                color: #667781;
                font-size: 13px;
                margin: 0;
            }
            
            .update-section {
                background: #fff;
                border-top: 1px solid #d1d7db;
                padding: 16px;
                margin-top: auto;
            }
            
            .update-section h3 {
                color: #111b21 !important;
                font-size: 15px !important;
                font-weight: 500 !important;
                margin-bottom: 12px !important;
            }
            
            .stButton > button {
                background-color: #25d366 !important;
                color: white !important;
                border: none !important;
                font-weight: 500 !important;
                border-radius: 8px !important;
                padding: 8px 16px !important;
                transition: background-color 0.15s ease !important;
            }
            
            .stButton > button:hover {
                background-color: #20bd5a !important;
            }
            
            .stTextInput input, .stTextArea textarea {
                background-color: #ffffff !important;
                color: #111b21 !important;
                border: 1px solid #d1d7db !important;
                border-radius: 8px !important;
                font-size: 14px !important;
            }
            
            .stTextInput input:focus, .stTextArea textarea:focus {
                border-color: #25d366 !important;
                box-shadow: 0 0 0 1px #25d366 !important;
            }
            
            [data-testid="stCheckbox"] label {
                color: #111b21 !important;
                font-size: 14px !important;
            }
            
            .stSelectbox label {
                color: #111b21 !important;
                font-size: 14px !important;
            }
            
            .stRadio label {
                color: #111b21 !important;
                font-size: 14px !important;
            }
            
            .stDateInput input, .stTimeInput input {
                background-color: #ffffff !important;
                color: #111b21 !important;
                border: 1px solid #d1d7db !important;
                border-radius: 8px !important;
            }
            
            ::-webkit-scrollbar {
                width: 6px;
                height: 6px;
            }
            
            ::-webkit-scrollbar-track {
                background: #f0f2f5;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #bfc5c9;
                border-radius: 3px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #a8aeb3;
            }
            
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            .highlight {
                background-color: #ffd700;
                padding: 0 2px;
                border-radius: 2px;
            }
            
            .empty-state {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100%;
                color: #667781;
                text-align: center;
                padding: 40px;
            }
            
            .empty-state-icon {
                font-size: 64px;
                margin-bottom: 16px;
                opacity: 0.5;
            }
            
            .empty-state-text {
                font-size: 20px;
                margin-bottom: 8px;
            }
            
            .empty-state-subtext {
                font-size: 14px;
            }
        </style>
        """


# Apply CSS
st.markdown(get_css(st.session_state.theme), unsafe_allow_html=True)

# Header with logo
logo_base64 = get_base64_logo()
if logo_base64:
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="logo-img">'
else:
    logo_url = "https://drive.google.com/uc?export=view&id=1NSTzTZ_gusa-c4Sc5dZelth-Djft0Zca"
    logo_html = f'<img src="{logo_url}" class="logo-img" onerror="this.style.display=\'none\'">'

st.markdown(f"""
<div class="main-header">
    {logo_html}
    <h1>WhatsApp Business – Amirtharaj Investment</h1>
</div>
""", unsafe_allow_html=True)

# Top controls
col1, col2 = st.columns([1, 1])

with col1:
    filter_icon = "▼" if st.session_state.show_filters else "▶"
    if st.button(f"{filter_icon} Filters", key="toggle_filters", use_container_width=True):
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

# Filter section
if st.session_state.show_filters:
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    st.markdown('<div class="filter-header">', unsafe_allow_html=True)
    st.markdown('<h3>🔍 Filter Options</h3>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="filter-content">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.filter_phone = st.text_input(
            "📱 Phone Number",
            value=st.session_state.filter_phone,
            placeholder="Search by phone...",
            key="filter_phone_input"
        )
    
    with col2:
        st.session_state.filter_name = st.text_input(
            "👤 Client Name",
            value=st.session_state.filter_name,
            placeholder="Search by name...",
            key="filter_name_input"
        )
    
    st.session_state.filter_by_date = st.checkbox(
        "📅 Enable date filter",
        value=st.session_state.filter_by_date,
        key="filter_by_date_check"
    )
    
    if st.session_state.filter_by_date:
        st.session_state.filter_date = st.date_input(
            "Select date",
            value=st.session_state.filter_date,
            key="filter_date_input"
        )
    
    st.session_state.filter_by_time = st.checkbox(
        "🕐 Enable time filter",
        value=st.session_state.filter_by_time,
        key="filter_by_time_check"
    )
    
    if st.session_state.filter_by_time:
        col_time1, col_time2 = st.columns(2)
        with col_time1:
            st.session_state.filter_time_from = st.time_input(
                "From time",
                value=st.session_state.filter_time_from,
                key="filter_time_from_input"
            )
        with col_time2:
            st.session_state.filter_time_to = st.time_input(
                "To time",
                value=st.session_state.filter_time_to,
                key="filter_time_to_input"
            )
    
    st.session_state.filter_only_fu = st.checkbox(
        "🔴 Show only follow-up clients",
        value=st.session_state.filter_only_fu,
        key="filter_only_fu_check"
    )
    
    if st.button("Apply Filters", use_container_width=True, type="primary"):
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


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
    if not MAKE_WEBHOOK_URL:
        st.error("Make webhook URL not configured.")
        return False

    payload = {
        "phone": phone,
        "message": message_text,
        "type": msg_type,
    }
    if msg_type == "template" and template_name:
        payload["template_name"] = template_name

    try:
        r = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=15)
        if r.status_code in (200, 201, 202):
            log_sent_message(phone, message_text, msg_type)
            return True
        else:
            st.error(f"Send failed ({r.status_code}): {r.text}")
            return False
    except Exception as e:
        st.error(f"Send error: {e}")
        return False


def log_sent_message(phone: str, message: str, msg_type: str = "text"):
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
        st.warning(f"Message sent but not logged: {e}")
        return False


def get_initials(name):
    """Get initials from name for avatar"""
    if not name or name == "Unknown":
        return "?"
    parts = name.strip().split()
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


# Fetch and filter contacts
contacts = fetch_contacts(st.session_state.filter_only_fu)
if st.session_state.filter_phone:
    contacts = [c for c in contacts if st.session_state.filter_phone.lower() in c["phone"].lower()]
if st.session_state.filter_name:
    contacts = [c for c in contacts if c.get("client_name") and st.session_state.filter_name.lower() in c["client_name"].lower()]

# Initialize session state
if "selected_phone" not in st.session_state:
    st.session_state.selected_phone = contacts[0]["phone"] if contacts else ""

if "conv_offset" not in st.session_state:
    st.session_state.conv_offset = 0

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False

CONV_LIMIT = 50

# Contact selector dropdown
phone = st.session_state.selected_phone

if contacts:
    contact_options = {c["phone"]: f"{c['client_name'] or 'Unknown'} ({c['phone']})" for c in contacts}
    
    selected_display = st.selectbox(
        "Select Contact",
        options=list(contact_options.keys()),
        format_func=lambda x: contact_options[x],
        index=list(contact_options.keys()).index(phone) if phone in contact_options else 0,
        key="contact_selector"
    )
    
    if selected_display != phone:
        st.session_state.selected_phone = selected_display
        st.session_state.conv_offset = 0
        draft_key = f"new_msg_{selected_display}"
        if draft_key in st.session_state:
            del st.session_state[draft_key]
        st.rerun()
    
    phone = selected_display

if not phone and contacts:
    phone = contacts[0]["phone"]
    st.session_state.selected_phone = phone

selected = next((c for c in contacts if c["phone"] == phone), None) if phone else None

if not selected:
    st.markdown("""
    <div class="empty-state" style="height: calc(100vh - 120px);">
        <div class="empty-state-icon">💭</div>
        <div class="empty-state-text">No contact selected</div>
        <div class="empty-state-subtext">Choose a contact from the dropdown above</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

client_name = selected["client_name"] or phone
initials = get_initials(client_name)

# Chat header
col_h1, col_h2 = st.columns([6, 1])

with col_h1:
    st.markdown(f"""
    <div class="chat-header">
        <div class="chat-header-left">
            <div class="chat-avatar">{initials}</div>
            <div class="chat-header-info">
                <h3>{client_name}</h3>
                <p>{phone}</p>
            </div>
        </div>
        <div class="chat-header-actions">
            <button class="icon-btn">🔍</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_h2:
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        auto_refresh = st.checkbox("🔄", value=st.session_state.auto_refresh, key="auto_refresh_toggle", 
                                   help="Auto-refresh")
        st.session_state.auto_refresh = auto_refresh
    
    with col_btn2:
        if st.button("🗑️", key="del_all", help="Delete conversation"):
            if st.session_state.get('confirm_del'):
                if delete_conversation(phone):
                    st.success("Deleted!")
                    st.session_state.pop('confirm_del', None)
                    st.rerun()
            else:
                st.session_state.confirm_del = True
                st.warning("Click again")

# Auto-refresh script
if st.session_state.auto_refresh:
    st.markdown("""
    <script>
        setTimeout(function() {
            window.parent.location.reload();
        }, 5000);
    </script>
    """, unsafe_allow_html=True)

# Search bar
search_query = st.text_input(
    "Search",
    placeholder="Search messages...",
    key="search_conv",
    label_visibility="collapsed"
)

# Fetch messages
conv = fetch_conversation(phone, limit=CONV_LIMIT, offset=st.session_state.conv_offset)

# Apply filters
date_filter = st.session_state.filter_date if st.session_state.filter_by_date else None
time_from = st.session_state.filter_time_from if st.session_state.filter_by_time else None
time_to = st.session_state.filter_time_to if st.session_state.filter_by_time else None
conv = filter_messages(conv, date_filter, time_from, time_to)

# Sort messages (oldest first)
conv.sort(key=lambda x: datetime.fromisoformat(x["timestamp"]), reverse=False)

# Messages area
st.markdown('<div class="messages-area" id="chat-messages">', unsafe_allow_html=True)

if not conv:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">📭</div>
        <div class="empty-state-text">No messages yet</div>
        <div class="empty-state-subtext">Start the conversation</div>
    </div>
    """, unsafe_allow_html=True)
else:
    current_date = None
    for msg in conv:
        ts = datetime.fromisoformat(msg["timestamp"])
        msg_date = ts.date()
        
        # Date divider
        if current_date != msg_date:
            current_date = msg_date
            if msg_date == date.today():
                date_label = "TODAY"
            elif msg_date == date.today().replace(day=date.today().day - 1):
                date_label = "YESTERDAY"
            else:
                date_label = msg_date.strftime("%d/%m/%Y")
            
            st.markdown(f"""
            <div class="date-divider">
                <span>{date_label}</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Message direction
        direction = "incoming" if msg["direction"] in ["user", "incoming"] else "outgoing"
        
        raw_text = msg["message"] or ""
        
        # Escape HTML first to prevent any HTML tags from rendering
        display_text = html.escape(raw_text)
        
        # Highlight search matches (after escaping)
        if search_query:
            pattern = re.escape(search_query)
            def repl(m):
                return f"<span class='highlight'>{m.group(0)}</span>"
            display_text = re.sub(pattern, repl, display_text, flags=re.IGNORECASE)
        
        # Replace newlines with <br> (after escaping)
        display_text = display_text.replace("\n", "<br>")
        
        # Message status (for outgoing)
        status_icon = ""
        if direction == "outgoing":
            status_icon = '<span class="message-status">✓✓</span>'
        
        # Build meta info inside the bubble
        meta_html = ""
        if msg.get("follow_up_needed"):
            meta_html += '<div class="message-meta">🔴 Follow-up needed</div>'
        if msg.get("notes"):
            notes_text = html.escape(msg["notes"])
            meta_html += f'<div class="message-meta">📝 {notes_text}</div>'
        
        message_html = f"""
        <div class="message-row {direction}">
            <div class="message-bubble {direction}">
                <div class="message-text">{display_text}</div>
                <div class="message-footer">
                    <span class="message-time">{ts.strftime("%H:%M")}</span>
                    {status_icon}
                </div>
                {meta_html}
            </div>
        </div>
        """
        st.markdown(message_html, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Auto-scroll to bottom
st.markdown("""
<script>
    setTimeout(function() {
        var chatArea = document.getElementById('chat-messages');
        if (chatArea) {
            chatArea.scrollTop = chatArea.scrollHeight;
        }
    }, 100);
</script>
""", unsafe_allow_html=True)

# Pagination
st.markdown('<div class="pagination-section">', unsafe_allow_html=True)
col_p1, col_p2, col_p3 = st.columns([1, 2, 1])

with col_p1:
    prev_disabled = st.session_state.conv_offset == 0
    if st.button("⬅️ Previous", disabled=prev_disabled):
        st.session_state.conv_offset = max(0, st.session_state.conv_offset - CONV_LIMIT)
        st.rerun()

with col_p2:
    start_idx = st.session_state.conv_offset + 1 if conv else 0
    end_idx = st.session_state.conv_offset + len(conv)
    st.markdown(f'<p class="pagination-info">Messages {start_idx}–{end_idx}</p>', unsafe_allow_html=True)

with col_p3:
    if st.button("Next ➡️"):
        st.session_state.conv_offset += CONV_LIMIT
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# Message input area
st.markdown('<div class="message-input-area">', unsafe_allow_html=True)

draft_key = f"new_msg_{phone}"
type_key = f"msg_type_{phone}"
tmpl_key = f"tmpl_{phone}"

col_input1, col_input2 = st.columns([3, 1])

with col_input1:
    new_msg = st.text_area(
        "Message",
        value=st.session_state.get(draft_key, ""),
        placeholder="Type a message...",
        key=draft_key,
        height=60,
        label_visibility="collapsed"
    )

with col_input2:
    msg_type_label = st.radio(
        "Type",
        ["Text", "Template"],
        key=type_key,
        horizontal=False
    )
    
    if msg_type_label == "Template":
        template_name = st.text_input(
            "Template",
            placeholder="Template name",
            key=tmpl_key,
            label_visibility="collapsed"
        )
    else:
        template_name = None

if st.button("📤 Send", use_container_width=True, key=f"send_{phone}"):
    msg_clean = (new_msg or "").strip()
    if not msg_clean:
        st.warning("Please type a message")
    else:
        msg_type = "template" if msg_type_label == "Template" else "text"
        ok = send_whatsapp_message(phone, msg_clean, msg_type, template_name)
        if ok:
            st.success("✅ Message sent!")
            if draft_key in st.session_state:
                del st.session_state[draft_key]
            import time
            time.sleep(0.5)
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# Update section
update_msg = conv[0] if conv else None

if update_msg:
    st.markdown('<div class="update-section">', unsafe_allow_html=True)
    st.markdown("### 📝 Update Status")
    
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        fu_flag = st.checkbox("🔴 Follow-up needed", value=update_msg.get("follow_up_needed", False))
    with col_u2:
        handler = st.text_input("👤 Handled by", value=update_msg.get("handled_by") or "")
    
    notes = st.text_area("📝 Notes", value=update_msg.get("notes") or "", height=60)
    
    if st.button("💾 Save", use_container_width=True):
        resp = requests.patch(
            f"{API_BASE}/message/{update_msg['id']}",
            json={"follow_up_needed": fu_flag, "notes": notes, "handled_by": handler}
        )
        if resp.status_code == 200:
            st.success("✅ Updated!")
            st.rerun()
        else:
            st.error(f"Error: {resp.text}")
    
    st.markdown('</div>', unsafe_allow_html=True)
