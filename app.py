import streamlit as st
import requests
from datetime import datetime, date, time
import base64
from pathlib import Path
import re

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
    page_title="WhatsApp Chat Inbox",
    layout="wide",
    initial_sidebar_state="collapsed"
)
check_password()

# Initialize theme and states
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
            /* WhatsApp Dark Theme */
            .main {
                background-color: #0b141a;
                padding: 0 !important;
            }
            
            .block-container {
                padding: 0 !important;
                max-width: 100% !important;
            }
            
            /* WhatsApp Header */
            .wa-header {
                background: #202c33;
                padding: 10px 16px;
                display: flex;
                align-items: center;
                gap: 15px;
                border-bottom: 1px solid #2a3942;
                position: sticky;
                top: 0;
                z-index: 1000;
                height: 60px;
            }
            
            .wa-header-title {
                color: #e9edef;
                margin: 0;
                font-size: 16px;
                font-weight: 500;
                flex: 1;
            }
            
            .wa-logo {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                object-fit: cover;
            }
            
            .wa-header-icons {
                display: flex;
                gap: 24px;
                color: #aebac1;
                font-size: 20px;
            }
            
            /* Layout Container */
            .wa-container {
                display: flex;
                height: calc(100vh - 60px);
                overflow: hidden;
            }
            
            /* Contact List Sidebar */
            .wa-sidebar {
                width: 400px;
                background: #111b21;
                border-right: 1px solid #2a3942;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .wa-search-container {
                padding: 8px 12px;
                background: #111b21;
                border-bottom: 1px solid #2a3942;
            }
            
            .wa-contacts-list {
                overflow-y: auto;
                flex: 1;
            }
            
            /* Contact Card (WhatsApp Style) */
            .wa-contact {
                display: flex;
                align-items: center;
                padding: 12px 16px;
                cursor: pointer;
                border-bottom: 1px solid #2a3942;
                transition: background-color 0.2s;
                position: relative;
            }
            
            .wa-contact:hover {
                background-color: #202c33;
            }
            
            .wa-contact.active {
                background-color: #2a3942;
            }
            
            .wa-contact-avatar {
                width: 49px;
                height: 49px;
                border-radius: 50%;
                background: linear-gradient(135deg, #667781 0%, #8696a0 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                color: #e9edef;
                font-size: 20px;
                font-weight: 500;
                flex-shrink: 0;
                margin-right: 12px;
            }
            
            .wa-contact-info {
                flex: 1;
                min-width: 0;
                padding-right: 12px;
            }
            
            .wa-contact-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 4px;
            }
            
            .wa-contact-name {
                color: #e9edef;
                font-size: 16px;
                font-weight: 400;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .wa-contact-time {
                color: #667781;
                font-size: 12px;
                white-space: nowrap;
                margin-left: 8px;
            }
            
            .wa-contact-preview {
                color: #8696a0;
                font-size: 14px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                display: flex;
                align-items: center;
                gap: 4px;
            }
            
            .wa-unread-badge {
                background: #00a884;
                color: #111b21;
                border-radius: 12px;
                padding: 0 6px;
                font-size: 12px;
                font-weight: 500;
                min-width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                position: absolute;
                right: 16px;
                bottom: 16px;
            }
            
            .wa-fu-indicator {
                color: #ff3b30;
                font-size: 10px;
                margin-right: 2px;
            }
            
            /* Chat Area */
            .wa-chat-area {
                flex: 1;
                display: flex;
                flex-direction: column;
                background: #0b141a;
                overflow: hidden;
            }
            
            /* Chat Header */
            .wa-chat-header {
                background: #202c33;
                padding: 10px 16px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                border-bottom: 1px solid #2a3942;
                height: 60px;
            }
            
            .wa-chat-header-info {
                display: flex;
                align-items: center;
                gap: 12px;
                flex: 1;
            }
            
            .wa-chat-header-text h3 {
                color: #e9edef;
                margin: 0;
                font-size: 16px;
                font-weight: 400;
            }
            
            .wa-chat-header-text p {
                color: #8696a0;
                margin: 2px 0 0 0;
                font-size: 13px;
            }
            
            .wa-chat-header-actions {
                display: flex;
                gap: 24px;
                color: #aebac1;
                font-size: 20px;
            }
            
            /* Messages Container */
            .wa-messages {
                flex: 1;
                overflow-y: auto;
                padding: 12px 7% 12px 7%;
                background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect fill="%230b141a" width="100" height="100"/><path fill="%231a252d" opacity="0.05" d="M0 0h50v50H0z"/></svg>');
                background-size: 400px 400px;
            }
            
            /* Message Bubbles */
            .wa-message-wrapper {
                display: flex;
                margin-bottom: 8px;
                clear: both;
            }
            
            .wa-message-wrapper.incoming {
                justify-content: flex-start;
            }
            
            .wa-message-wrapper.outgoing {
                justify-content: flex-end;
            }
            
            .wa-message {
                max-width: 65%;
                padding: 6px 7px 8px 9px;
                border-radius: 7.5px;
                position: relative;
                box-shadow: 0 1px 0.5px rgba(11,20,26,.13);
            }
            
            .wa-message.incoming {
                background-color: #202c33;
            }
            
            .wa-message.outgoing {
                background-color: #005c4b;
            }
            
            .wa-message-text {
                color: #e9edef;
                font-size: 14.2px;
                line-height: 19px;
                word-wrap: break-word;
                white-space: pre-wrap;
            }
            
            .wa-message-footer {
                display: flex;
                align-items: center;
                justify-content: flex-end;
                gap: 4px;
                margin-top: 4px;
            }
            
            .wa-message-time {
                color: rgba(241,241,242,.6);
                font-size: 11px;
            }
            
            .wa-message.outgoing .wa-message-time {
                color: rgba(241,241,242,.6);
            }
            
            .wa-checkmark {
                color: #53bdeb;
                font-size: 16px;
                line-height: 1;
            }
            
            .wa-message-meta {
                background: rgba(0,0,0,0.15);
                padding: 3px 6px;
                border-radius: 4px;
                margin-top: 4px;
                font-size: 11px;
                color: #8696a0;
            }
            
            /* Message Input Area */
            .wa-input-area {
                background: #202c33;
                padding: 10px 16px;
                display: flex;
                align-items: flex-end;
                gap: 8px;
                border-top: 1px solid #2a3942;
            }
            
            .wa-input-wrapper {
                flex: 1;
                background: #2a3942;
                border-radius: 8px;
                display: flex;
                align-items: center;
                padding: 8px 12px;
                gap: 8px;
            }
            
            .wa-input-icon {
                color: #8696a0;
                font-size: 24px;
                cursor: pointer;
            }
            
            .wa-send-button {
                background: #00a884;
                border: none;
                border-radius: 50%;
                width: 48px;
                height: 48px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                color: #111b21;
                font-size: 20px;
                transition: background 0.2s;
            }
            
            .wa-send-button:hover {
                background: #06cf9c;
            }
            
            /* Filters Panel */
            .wa-filters {
                background: #111b21;
                border-bottom: 1px solid #2a3942;
                padding: 12px;
                max-height: 300px;
                overflow-y: auto;
            }
            
            /* Buttons */
            .stButton > button {
                background-color: #00a884 !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                font-weight: 500 !important;
                padding: 8px 16px !important;
            }
            
            .stButton > button:hover {
                background-color: #06cf9c !important;
            }
            
            /* Input fields */
            .stTextInput input, .stTextArea textarea {
                background-color: #2a3942 !important;
                color: #e9edef !important;
                border: 1px solid #3b4a54 !important;
                border-radius: 8px !important;
            }
            
            /* Scrollbar */
            ::-webkit-scrollbar {
                width: 6px;
            }
            
            ::-webkit-scrollbar-track {
                background: #0b141a;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #374248;
                border-radius: 3px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #4a5a63;
            }
            
            /* Hide text area label */
            .wa-input-area label {
                display: none !important;
            }
            
            /* Hide button labels in contact list */
            .wa-contacts-list button {
                position: absolute;
                opacity: 0;
                pointer-events: none;
            }
            
            /* Date picker styling */
            .stDateInput input, .stTimeInput input {
                background-color: #2a3942 !important;
                color: #e9edef !important;
                border: 1px solid #3b4a54 !important;
            }
            
            /* Checkbox styling */
            [data-testid="stCheckbox"] label {
                color: #e9edef !important;
            }
            
            /* Select box styling */
            .stSelectbox label, .stRadio label {
                color: #e9edef !important;
            }
            
            /* Empty state */
            .wa-empty-state {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100%;
                color: #667781;
                text-align: center;
                padding: 40px;
            }
            
            .wa-empty-state-icon {
                font-size: 80px;
                margin-bottom: 20px;
                opacity: 0.3;
            }
        </style>
        """
    else:  # light theme
        return """
        <style>
            /* WhatsApp Light Theme */
            .main {
                background-color: #f0f2f5;
                padding: 0 !important;
            }
            
            .block-container {
                padding: 0 !important;
                max-width: 100% !important;
            }
            
            /* WhatsApp Header */
            .wa-header {
                background: #ededed;
                padding: 10px 16px;
                display: flex;
                align-items: center;
                gap: 15px;
                border-bottom: 1px solid #d1d7db;
                position: sticky;
                top: 0;
                z-index: 1000;
                height: 60px;
            }
            
            .wa-header-title {
                color: #3b4a54;
                margin: 0;
                font-size: 16px;
                font-weight: 500;
                flex: 1;
            }
            
            .wa-logo {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                object-fit: cover;
            }
            
            .wa-header-icons {
                display: flex;
                gap: 24px;
                color: #54656f;
                font-size: 20px;
            }
            
            /* Layout Container */
            .wa-container {
                display: flex;
                height: calc(100vh - 60px);
                overflow: hidden;
            }
            
            /* Contact List Sidebar */
            .wa-sidebar {
                width: 400px;
                background: #ffffff;
                border-right: 1px solid #d1d7db;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .wa-search-container {
                padding: 8px 12px;
                background: #f0f2f5;
                border-bottom: 1px solid #d1d7db;
            }
            
            .wa-contacts-list {
                overflow-y: auto;
                flex: 1;
            }
            
            /* Contact Card */
            .wa-contact {
                display: flex;
                align-items: center;
                padding: 12px 16px;
                cursor: pointer;
                border-bottom: 1px solid #f0f2f5;
                transition: background-color 0.2s;
                position: relative;
                background: #ffffff;
            }
            
            .wa-contact:hover {
                background-color: #f5f6f6;
            }
            
            .wa-contact.active {
                background-color: #f0f2f5;
            }
            
            .wa-contact-avatar {
                width: 49px;
                height: 49px;
                border-radius: 50%;
                background: linear-gradient(135deg, #dfe5e7 0%, #c4cdd1 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                color: #667781;
                font-size: 20px;
                font-weight: 500;
                flex-shrink: 0;
                margin-right: 12px;
            }
            
            .wa-contact-info {
                flex: 1;
                min-width: 0;
                padding-right: 12px;
            }
            
            .wa-contact-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 4px;
            }
            
            .wa-contact-name {
                color: #111b21;
                font-size: 16px;
                font-weight: 400;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .wa-contact-time {
                color: #667781;
                font-size: 12px;
                white-space: nowrap;
                margin-left: 8px;
            }
            
            .wa-contact-preview {
                color: #667781;
                font-size: 14px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                display: flex;
                align-items: center;
                gap: 4px;
            }
            
            .wa-unread-badge {
                background: #25d366;
                color: #ffffff;
                border-radius: 12px;
                padding: 0 6px;
                font-size: 12px;
                font-weight: 500;
                min-width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                position: absolute;
                right: 16px;
                bottom: 16px;
            }
            
            .wa-fu-indicator {
                color: #ff3b30;
                font-size: 10px;
                margin-right: 2px;
            }
            
            /* Chat Area */
            .wa-chat-area {
                flex: 1;
                display: flex;
                flex-direction: column;
                background: #efeae2;
                overflow: hidden;
            }
            
            /* Chat Header */
            .wa-chat-header {
                background: #ededed;
                padding: 10px 16px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                border-bottom: 1px solid #d1d7db;
                height: 60px;
            }
            
            .wa-chat-header-info {
                display: flex;
                align-items: center;
                gap: 12px;
                flex: 1;
            }
            
            .wa-chat-header-text h3 {
                color: #111b21;
                margin: 0;
                font-size: 16px;
                font-weight: 400;
            }
            
            .wa-chat-header-text p {
                color: #667781;
                margin: 2px 0 0 0;
                font-size: 13px;
            }
            
            .wa-chat-header-actions {
                display: flex;
                gap: 24px;
                color: #54656f;
                font-size: 20px;
            }
            
            /* Messages Container */
            .wa-messages {
                flex: 1;
                overflow-y: auto;
                padding: 12px 7% 12px 7%;
                background-color: #efeae2;
                background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect fill="%23efeae2" width="100" height="100"/></svg>');
            }
            
            /* Message Bubbles */
            .wa-message-wrapper {
                display: flex;
                margin-bottom: 8px;
                clear: both;
            }
            
            .wa-message-wrapper.incoming {
                justify-content: flex-start;
            }
            
            .wa-message-wrapper.outgoing {
                justify-content: flex-end;
            }
            
            .wa-message {
                max-width: 65%;
                padding: 6px 7px 8px 9px;
                border-radius: 7.5px;
                position: relative;
                box-shadow: 0 1px 0.5px rgba(11,20,26,.13);
            }
            
            .wa-message.incoming {
                background-color: #ffffff;
            }
            
            .wa-message.outgoing {
                background-color: #d9fdd3;
            }
            
            .wa-message-text {
                color: #111b21;
                font-size: 14.2px;
                line-height: 19px;
                word-wrap: break-word;
                white-space: pre-wrap;
            }
            
            .wa-message-footer {
                display: flex;
                align-items: center;
                justify-content: flex-end;
                gap: 4px;
                margin-top: 4px;
            }
            
            .wa-message-time {
                color: rgba(17,27,33,.45);
                font-size: 11px;
            }
            
            .wa-checkmark {
                color: #53bdeb;
                font-size: 16px;
                line-height: 1;
            }
            
            .wa-message-meta {
                background: rgba(0,0,0,0.05);
                padding: 3px 6px;
                border-radius: 4px;
                margin-top: 4px;
                font-size: 11px;
                color: #667781;
            }
            
            /* Message Input Area */
            .wa-input-area {
                background: #ededed;
                padding: 10px 16px;
                display: flex;
                align-items: flex-end;
                gap: 8px;
                border-top: 1px solid #d1d7db;
            }
            
            .wa-input-wrapper {
                flex: 1;
                background: #ffffff;
                border-radius: 8px;
                display: flex;
                align-items: center;
                padding: 8px 12px;
                gap: 8px;
            }
            
            .wa-input-icon {
                color: #54656f;
                font-size: 24px;
                cursor: pointer;
            }
            
            .wa-send-button {
                background: #25d366;
                border: none;
                border-radius: 50%;
                width: 48px;
                height: 48px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                color: #ffffff;
                font-size: 20px;
                transition: background 0.2s;
            }
            
            .wa-send-button:hover {
                background: #20bd5f;
            }
            
            /* Filters Panel */
            .wa-filters {
                background: #ffffff;
                border-bottom: 1px solid #d1d7db;
                padding: 12px;
                max-height: 300px;
                overflow-y: auto;
            }
            
            /* Buttons */
            .stButton > button {
                background-color: #25d366 !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                font-weight: 500 !important;
                padding: 8px 16px !important;
            }
            
            .stButton > button:hover {
                background-color: #20bd5f !important;
            }
            
            /* Input fields */
            .stTextInput input, .stTextArea textarea {
                background-color: #ffffff !important;
                color: #111b21 !important;
                border: 1px solid #d1d7db !important;
                border-radius: 8px !important;
            }
            
            /* Scrollbar */
            ::-webkit-scrollbar {
                width: 6px;
            }
            
            ::-webkit-scrollbar-track {
                background: #f0f2f5;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #c4cdd1;
                border-radius: 3px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #aeb5bb;
            }
            
            /* Hide text area label */
            .wa-input-area label {
                display: none !important;
            }
            
            /* Hide button labels in contact list */
            .wa-contacts-list button {
                position: absolute;
                opacity: 0;
                pointer-events: none;
            }
            
            /* Hide Streamlit branding */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* Date picker styling */
            .stDateInput input, .stTimeInput input {
                background-color: #ffffff !important;
                color: #111b21 !important;
                border: 1px solid #d1d7db !important;
            }
            
            /* Checkbox styling */
            [data-testid="stCheckbox"] label {
                color: #111b21 !important;
            }
            
            /* Select box styling */
            .stSelectbox label, .stRadio label {
                color: #111b21 !important;
            }
            
            /* Empty state */
            .wa-empty-state {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100%;
                color: #667781;
                text-align: center;
                padding: 40px;
            }
            
            .wa-empty-state-icon {
                font-size: 80px;
                margin-bottom: 20px;
                opacity: 0.3;
            }
        </style>
        """

# Apply CSS
st.markdown(get_css(st.session_state.theme), unsafe_allow_html=True)

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
        r = requests.get(f"{API_BASE}/conversation/{phone}", params={"limit": limit, "offset": offset})
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

def send_whatsapp_message(phone: str, message_text: str, msg_type: str = "text", template_name: str | None = None) -> bool:
    if not MAKE_WEBHOOK_URL:
        st.error("Make webhook URL not configured")
        return False
    
    payload = {"phone": phone, "message": message_text, "type": msg_type}
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

def get_base64_logo():
    logo_path = Path("Logo.png")
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# Initialize session state
if "selected_phone" not in st.session_state:
    st.session_state.selected_phone = ""
if "conv_offset" not in st.session_state:
    st.session_state.conv_offset = 0
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True

CONV_LIMIT = 20

# Fetch and filter contacts
contacts = fetch_contacts(st.session_state.filter_only_fu)
if st.session_state.filter_phone:
    contacts = [c for c in contacts if st.session_state.filter_phone.lower() in c["phone"].lower()]
if st.session_state.filter_name:
    contacts = [c for c in contacts if c.get("client_name") and st.session_state.filter_name.lower() in c["client_name"].lower()]

# Main Header
logo_base64 = get_base64_logo()
if logo_base64:
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="wa-logo">'
else:
    logo_url = "https://drive.google.com/uc?export=view&id=1NSTzTZ_gusa-c4Sc5dZelth-Djft0Zca"
    logo_html = f'<img src="{logo_url}" class="wa-logo">'

theme_icon = "☀️" if st.session_state.theme == "dark" else "🌙"
st.markdown(f"""
<div class="wa-header">
    {logo_html}
    <h1 class="wa-header-title">Amirtharaj Investment – WhatsApp</h1>
    <div class="wa-header-icons">
        <span>💬</span>
        <span>⋮</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Theme toggle (outside main container)
col_theme1, col_theme2 = st.columns([6, 1])
with col_theme2:
    if st.session_state.theme == "dark":
        if st.button("☀️", key="theme_toggle"):
            st.session_state.theme = "light"
            st.rerun()
    else:
        if st.button("🌙", key="theme_toggle"):
            st.session_state.theme = "dark"
            st.rerun()

# Main container
st.markdown('<div class="wa-container">', unsafe_allow_html=True)

# Sidebar - Contact List
st.markdown('<div class="wa-sidebar">', unsafe_allow_html=True)

# Search and filters
st.markdown('<div class="wa-search-container">', unsafe_allow_html=True)
filter_icon = "▼" if st.session_state.show_filters else "▶"
if st.button(f"{filter_icon} Filters", key="toggle_filters"):
    st.session_state.show_filters = not st.session_state.show_filters
    st.rerun()

if st.session_state.show_filters:
    st.markdown('<div class="wa-filters">', unsafe_allow_html=True)
    st.session_state.filter_phone = st.text_input("📱 Phone", value=st.session_state.filter_phone, placeholder="Search...")
    st.session_state.filter_name = st.text_input("👤 Name", value=st.session_state.filter_name, placeholder="Search...")
    st.session_state.filter_only_fu = st.checkbox("🔴 Follow-ups only", value=st.session_state.filter_only_fu)
    if st.button("Apply"):
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Contacts list
st.markdown('<div class="wa-contacts-list">', unsafe_allow_html=True)

if not contacts:
    st.markdown('<div class="wa-empty-state"><div class="wa-empty-state-icon">💬</div><p>No contacts found</p></div>', unsafe_allow_html=True)
else:
    for c in contacts:
        client_name = c["client_name"] or "Unknown"
        phone = c["phone"]
        is_selected = st.session_state.selected_phone == phone
        fu_indicator = '<span class="wa-fu-indicator">●</span>' if c.get("follow_up_open") else ""
        
        # Get initials for avatar
        initials = "".join([word[0].upper() for word in client_name.split()[:2]])
        
        active_class = "active" if is_selected else ""
        
        # WhatsApp-style contact card with button
        contact_html = f"""
        <div class="wa-contact {active_class}" onclick="document.getElementById('btn_{phone}').click()">
            <div class="wa-contact-avatar">{initials}</div>
            <div class="wa-contact-info">
                <div class="wa-contact-header">
                    <span class="wa-contact-name">{fu_indicator}{client_name}</span>
                    <span class="wa-contact-time">12:45</span>
                </div>
                <div class="wa-contact-preview">
                    <span>Latest message preview...</span>
                </div>
            </div>
        </div>
        """
        st.markdown(contact_html, unsafe_allow_html=True)
        
        # Hidden button for functionality
        if st.button(" ", key=f"btn_{phone}", help=client_name):
            st.session_state.selected_phone = phone
            st.session_state.conv_offset = 0
            draft_key = f"new_msg_{phone}"
            if draft_key in st.session_state:
                del st.session_state[draft_key]
            st.rerun()

st.markdown('</div></div>', unsafe_allow_html=True)  # Close contacts-list and sidebar

# Chat Area
st.markdown('<div class="wa-chat-area">', unsafe_allow_html=True)

phone = st.session_state.selected_phone
if not phone and contacts:
    phone = contacts[0]["phone"]
    st.session_state.selected_phone = phone

selected = next((c for c in contacts if c["phone"] == phone), None) if phone else None

if not selected:
    st.markdown('<div class="wa-empty-state"><div class="wa-empty-state-icon">💬</div><p>Select a contact to start chatting</p></div>', unsafe_allow_html=True)
else:
    client_name = selected["client_name"] or phone
    initials = "".join([word[0].upper() for word in client_name.split()[:2]])
    
    # Chat header
    st.markdown(f"""
    <div class="wa-chat-header">
        <div class="wa-chat-header-info">
            <div class="wa-contact-avatar" style="width: 40px; height: 40px; font-size: 16px;">{initials}</div>
            <div class="wa-chat-header-text">
                <h3>{client_name}</h3>
                <p>{phone}</p>
            </div>
        </div>
        <div class="wa-chat-header-actions">
            <span>🔍</span>
            <span>⋮</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Fetch conversation
    conv = fetch_conversation(phone, limit=CONV_LIMIT, offset=st.session_state.conv_offset)
    date_filter = st.session_state.filter_date if st.session_state.filter_by_date else None
    time_from = st.session_state.filter_time_from if st.session_state.filter_by_time else None
    time_to = st.session_state.filter_time_to if st.session_state.filter_by_time else None
    conv = filter_messages(conv, date_filter, time_from, time_to)
    conv.sort(key=lambda x: datetime.fromisoformat(x["timestamp"]), reverse=False)
    
    # Messages area
    st.markdown('<div class="wa-messages">', unsafe_allow_html=True)
    
    if not conv:
        st.markdown('<div class="wa-empty-state"><p>No messages yet</p></div>', unsafe_allow_html=True)
    else:
        for msg in conv:
            ts = datetime.fromisoformat(msg["timestamp"])
            direction = "incoming" if msg["direction"] in ["user", "incoming"] else "outgoing"
            
            message_text = (msg["message"] or "").replace("\n", "<br>")
            
            # WhatsApp checkmark for outgoing messages
            checkmark = '<span class="wa-checkmark">✓✓</span>' if direction == "outgoing" else ""
            
            meta_html = ""
            if msg.get("follow_up_needed"):
                meta_html += '<div class="wa-message-meta">🔴 Follow-up needed</div>'
            if msg.get("notes"):
                meta_html += f'<div class="wa-message-meta">📝 {msg["notes"]}</div>'
            
            st.markdown(f"""
            <div class="wa-message-wrapper {direction}">
                <div class="wa-message {direction}">
                    <div class="wa-message-text">{message_text}</div>
                    <div class="wa-message-footer">
                        <span class="wa-message-time">{ts.strftime("%H:%M")}</span>
                        {checkmark}
                    </div>
                    {meta_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close wa-messages
    
    # Input area (WhatsApp style)
    st.markdown('<div class="wa-input-area">', unsafe_allow_html=True)
    
    draft_key = f"new_msg_{phone}"
    
    col_input, col_send = st.columns([6, 1])
    with col_input:
        new_msg = st.text_area(
            "Message",
            value=st.session_state.get(draft_key, ""),
            placeholder="Type a message",
            key=draft_key,
            height=50
        )
    
    with col_send:
        if st.button("📤", key=f"send_{phone}"):
            msg_clean = (new_msg or "").strip()
            if msg_clean:
                ok = send_whatsapp_message(phone, msg_clean, "text")
                if ok:
                    st.success("Sent!")
                    if draft_key in st.session_state:
                        del st.session_state[draft_key]
                    import time
                    time.sleep(0.5)
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close wa-input-area

st.markdown('</div>', unsafe_allow_html=True)  # Close wa-chat-area
st.markdown('</div>', unsafe_allow_html=True)  # Close wa-container

# Auto-refresh
if st.session_state.auto_refresh:
    st.markdown("""
    <script>
        setTimeout(function() {
            window.parent.location.reload();
        }, 5000);
    </script>
    """, unsafe_allow_html=True)
