import streamlit as st
import requests
from datetime import datetime, date, time
import base64
from pathlib import Path
import re
from zoneinfo import ZoneInfo
import pytz

API_BASE = "https://dashboard-backend-qqmi.onrender.com"
MAKE_WEBHOOK_URL = st.secrets.get("make_webhook_url", "")

# Define IST timezone
IST = pytz.timezone('Asia/Kolkata')

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
            /* WhatsApp Web Dark Theme */
            .main {
                background: linear-gradient(180deg, #0d1418 0%, #0d1418 100%);
                padding: 0 !important;
            }
            
            /* Remove default padding */
            .block-container {
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                max-width: 100% !important;
            }
            
            /* WhatsApp Header */
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
            
            /* Filter section */
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
            
            /* WhatsApp Sidebar Contacts */
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
            
            .contact-card:hover {
                background-color: #202c33;
            }
            
            .contact-card.selected {
                background-color: #2a3942;
            }
            
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
            
            /* WhatsApp Chat Header */
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
            
            .chat-header-actions {
                display: flex;
                gap: 20px;
                align-items: center;
            }
            
            .chat-status {
                color: #00a884;
                font-size: 13px;
                font-weight: 400;
            }
            
            /* WhatsApp Chat Area */
            .chat-container {
                background: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png');
                background-size: contain;
                background-position: center;
                padding: 20px 16px;
                min-height: calc(100vh - 240px);
                position: relative;
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
            
            /* WhatsApp Message Bubbles */
            .message-row {
                display: flex;
                margin-bottom: 8px;
                position: relative;
                z-index: 1;
            }
            
            .message-row.user {
                justify-content: flex-start;
            }
            
            .message-row.bot {
                justify-content: flex-end;
            }
            
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
            
            /* WhatsApp Input Area */
            .input-area {
                background: #202c33;
                padding: 10px 16px;
                border-top: 1px solid #2a3942;
                position: sticky;
                bottom: 0;
                z-index: 100;
            }
            
            /* Update section */
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
            
            /* Send section */
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
            
            .pagination-info {
                color: #8696a0;
                font-size: 14px;
                margin: 0;
                text-align: center;
                flex: 1;
            }
            
            /* WhatsApp Buttons */
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
            
            /* Input fields */
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
            
            /* Checkbox */
            [data-testid="stCheckbox"] label {
                color: #e9edef !important;
                font-size: 14px !important;
            }
            
            /* Selectbox */
            .stSelectbox label {
                color: #e9edef !important;
            }
            
            /* Radio buttons */
            .stRadio label {
                color: #e9edef !important;
            }
            
            /* Date and time inputs */
            .stDateInput input, .stTimeInput input {
                background-color: #2a3942 !important;
                color: #e9edef !important;
                border: 1px solid #3b4a54 !important;
                border-radius: 8px !important;
            }
            
            /* Scrollbar */
            ::-webkit-scrollbar {
                width: 6px;
                height: 6px;
            }
            
            ::-webkit-scrollbar-track {
                background: #111b21;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #374045;
                border-radius: 3px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #3b4a54;
            }
            
            /* Hide streamlit elements */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* Override streamlit's default padding */
            .main .block-container {
                padding-top: 0rem !important;
            }
            
            /* Header buttons */
            .header-buttons {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            /* Filter actions */
            .filter-actions {
                display: flex;
                gap: 10px;
                margin-top: 20px;
                justify-content: flex-end;
            }
            
            /* Top buttons */
            .top-buttons-row {
                display: flex;
                gap: 10px;
                margin-bottom: 15px;
            }
            
            /* Search input */
            .search-input {
                background-color: #202c33;
                border: none;
                border-bottom: 1px solid #2a3942;
                padding: 8px 12px;
                color: #e9edef;
                font-size: 14px;
                width: 100%;
            }
            
            /* Status indicators */
            .status-online {
                color: #00a884;
                font-size: 11px;
            }
            
            .status-offline {
                color: #8696a0;
                font-size: 11px;
            }
            
            /* Avatar colors based on name */
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
        return """
        <style>
            /* WhatsApp Web Light Theme */
            .main {
                background: linear-gradient(180deg, #eae6df 0%, #eae6df 100%);
                padding: 0 !important;
            }
            
            /* Remove default padding */
            .block-container {
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                max-width: 100% !important;
            }
            
            /* WhatsApp Header */
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
            
            .logo-img {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                object-fit: cover;
                border: 1px solid #dddfe2;
            }
            
            /* Filter section */
            .filter-container {
                background-color: #ffffff;
                border: 1px solid #dddfe2;
                border-radius: 8px;
                padding: 0;
                margin-bottom: 12px;
                overflow: hidden;
                margin-top: 10px;
            }
            
            .filter-header {
                background-color: #f0f2f5;
                padding: 12px 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: pointer;
                border-bottom: 1px solid #dddfe2;
            }
            
            .filter-header h3 {
                color: #3b4a54;
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
                color: #667781;
                font-size: 12px;
                margin-bottom: 4px;
                display: block;
                font-weight: 400;
            }
            
            /* WhatsApp Sidebar Contacts */
            .contact-card {
                background-color: transparent;
                padding: 12px;
                cursor: pointer;
                border-bottom: 1px solid #f0f2f5;
                transition: background-color 0.2s;
                position: relative;
                display: flex;
                align-items: center;
                gap: 12px;
                min-height: 72px;
            }
            
            .contact-card:hover {
                background-color: #f0f2f5;
            }
            
            .contact-card.selected {
                background-color: #e4e6eb;
            }
            
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
                color: #3b4a54;
                font-size: 17px;
                font-weight: 400;
                margin-bottom: 2px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            .contact-preview {
                color: #667781;
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
                color: #667781;
                font-size: 12px;
                margin-bottom: 4px;
            }
            
            .unread-indicator {
                background-color: #00a884;
                color: white;
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
            
            /* WhatsApp Chat Header */
            .chat-header {
                background: #f0f2f5;
                padding: 10px 16px;
                margin-bottom: 1px;
                border-bottom: 1px solid #dddfe2;
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
                color: #3b4a54;
                margin: 0 0 2px 0;
                font-size: 16px;
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            .chat-header-info p {
                color: #667781;
                margin: 0;
                font-size: 13px;
                font-weight: 400;
            }
            
            .chat-header-actions {
                display: flex;
                gap: 20px;
                align-items: center;
            }
            
            .chat-status {
                color: #00a884;
                font-size: 13px;
                font-weight: 400;
            }
            
            /* WhatsApp Chat Area */
            .chat-container {
                background: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png');
                background-size: contain;
                background-position: center;
                padding: 20px 16px;
                min-height: calc(100vh - 240px);
                position: relative;
            }
            
            .chat-container::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(234, 230, 223, 0.85);
                pointer-events: none;
            }
            
            /* WhatsApp Message Bubbles */
            .message-row {
                display: flex;
                margin-bottom: 8px;
                position: relative;
                z-index: 1;
            }
            
            .message-row.user {
                justify-content: flex-start;
            }
            
            .message-row.bot {
                justify-content: flex-end;
            }
            
            .message-bubble {
                max-width: 65%;
                padding: 8px 9px;
                border-radius: 7.5px;
                position: relative;
                box-shadow: 0 1px 0.5px rgba(0,0,0,0.13);
                word-wrap: break-word;
            }
            
            .message-bubble.user {
                background-color: #ffffff;
                border-top-left-radius: 0;
                border: 1px solid #e0e0e0;
            }
            
            .message-bubble.bot {
                background-color: #dcf8c6;
                border-top-right-radius: 0;
            }
            
            .message-bubble.user::before {
                content: '';
                position: absolute;
                top: 0;
                left: -8px;
                width: 8px;
                height: 13px;
                background-color: #ffffff;
                border-bottom-right-radius: 10px;
                border-left: 1px solid #e0e0e0;
                border-bottom: 1px solid #e0e0e0;
            }
            
            .message-bubble.bot::before {
                content: '';
                position: absolute;
                top: 0;
                right: -8px;
                width: 8px;
                height: 13px;
                background-color: #dcf8c6;
                border-bottom-left-radius: 10px;
            }
            
            .message-text {
                color: #303030;
                font-size: 14.2px;
                line-height: 19px;
                margin-bottom: 4px;
                word-wrap: break-word;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            .message-time {
                color: rgba(0, 0, 0, 0.45);
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
            
            .message-status.sent { color: #667781; }
            .message-status.delivered { color: #667781; }
            .message-status.read { color: #53bdeb; }
            
            /* WhatsApp Input Area */
            .input-area {
                background: #f0f2f5;
                padding: 10px 16px;
                border-top: 1px solid #dddfe2;
                position: sticky;
                bottom: 0;
                z-index: 100;
            }
            
            /* Update section */
            .update-section {
                background-color: #ffffff;
                border-radius: 8px;
                padding: 16px;
                margin-top: 16px;
                border: 1px solid #dddfe2;
            }
            
            .update-section h3 {
                color: #3b4a54 !important;
                font-size: 16px !important;
                margin-bottom: 12px !important;
                font-weight: 500 !important;
            }
            
            /* Send section */
            .send-section {
                background-color: #ffffff;
                border-radius: 8px;
                padding: 16px;
                margin-top: 16px;
                border: 1px solid #dddfe2;
            }
            
            .send-section h3 {
                color: #3b4a54 !important;
                font-size: 16px !important;
                margin-bottom: 12px !important;
                font-weight: 500 !important;
            }
            
            .pagination-section {
                background-color: #ffffff;
                border-radius: 8px;
                padding: 12px 16px;
                margin-top: 12px;
                border: 1px solid #dddfe2;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .pagination-info {
                color: #667781;
                font-size: 14px;
                margin: 0;
                text-align: center;
                flex: 1;
            }
            
            /* WhatsApp Buttons */
            .stButton > button {
                background-color: #00a884 !important;
                color: white !important;
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
            
            /* Input fields */
            .stTextInput input, .stTextArea textarea {
                background-color: #ffffff !important;
                color: #3b4a54 !important;
                border: 1px solid #dddfe2 !important;
                border-radius: 8px !important;
                font-size: 14px !important;
                padding: 12px !important;
            }
            
            .stTextInput input:focus, .stTextArea textarea:focus {
                border-color: #00a884 !important;
                box-shadow: 0 0 0 1px #00a884 !important;
            }
            
            /* Checkbox */
            [data-testid="stCheckbox"] label {
                color: #3b4a54 !important;
                font-size: 14px !important;
            }
            
            /* Selectbox */
            .stSelectbox label {
                color: #3b4a54 !important;
            }
            
            /* Radio buttons */
            .stRadio label {
                color: #3b4a54 !important;
            }
            
            /* Date and time inputs */
            .stDateInput input, .stTimeInput input {
                background-color: #ffffff !important;
                color: #3b4a54 !important;
                border: 1px solid #dddfe2 !important;
                border-radius: 8px !important;
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
                background: #bcc0c4;
                border-radius: 3px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #a0a4a8;
            }
            
            /* Hide streamlit elements */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* Override streamlit's default padding */
            .main .block-container {
                padding-top: 0rem !important;
            }
            
            /* Header buttons */
            .header-buttons {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            /* Filter actions */
            .filter-actions {
                display: flex;
                gap: 10px;
                margin-top: 20px;
                justify-content: flex-end;
            }
            
            /* Top buttons */
            .top-buttons-row {
                display: flex;
                gap: 10px;
                margin-bottom: 15px;
            }
            
            /* Search input */
            .search-input {
                background-color: #ffffff;
                border: none;
                border-bottom: 1px solid #dddfe2;
                padding: 8px 12px;
                color: #3b4a54;
                font-size: 14px;
                width: 100%;
            }
            
            /* Status indicators */
            .status-online {
                color: #00a884;
                font-size: 11px;
            }
            
            .status-offline {
                color: #667781;
                font-size: 11px;
            }
            
            /* Avatar colors */
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

st.markdown(get_css(st.session_state.theme), unsafe_allow_html=True)

logo_base64 = get_base64_logo()
if logo_base64:
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="logo-img">'
else:
    logo_url = "https://drive.google.com/uc?export=view&id=1NSTzTZ_gusa-c4Sc5dZelth-Djft0Zca"
    logo_html = f'<img src="{logo_url}" class="logo-img" onerror="this.style.display=\'none\'">'

st.markdown(f"""
<div class="main-header">
    {logo_html}
    <h1>WhatsApp Chat Inbox</h1>
</div>
""", unsafe_allow_html=True)

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

if st.session_state.show_filters:
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    st.markdown('<div class="filter-header">', unsafe_allow_html=True)
    st.markdown('<h3><span>🔍</span> Filter Options</h3>', unsafe_allow_html=True)
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
    
    st.markdown('<div class="filter-actions">', unsafe_allow_html=True)
    if st.button("Apply Filters", use_container_width=True, type="primary"):
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def convert_to_ist(timestamp_str: str) -> datetime:
    """Convert ISO timestamp string to IST datetime object"""
    try:
        # Parse the timestamp
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        
        # If it's naive (no timezone), assume it's UTC
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        
        # Convert to IST
        ist_dt = dt.astimezone(IST)
        return ist_dt
    except Exception as e:
        st.error(f"Error converting time: {e}")
        # Return current IST time as fallback
        return datetime.now(IST)


def format_message_time(timestamp_str: str) -> str:
    """Format timestamp for display in IST timezone (HH:MM format)"""
    ist_dt = convert_to_ist(timestamp_str)
    return ist_dt.strftime("%I:%M %p").lstrip('0')


def format_contact_time(timestamp_str: str) -> str:
    """Format timestamp for contact list display"""
    ist_dt = convert_to_ist(timestamp_str)
    now = datetime.now(IST)
    
    # If today, show time
    if ist_dt.date() == now.date():
        return ist_dt.strftime("%I:%M %p").lstrip('0')
    # If yesterday
    elif ist_dt.date() == (now.date() - timedelta(days=1)):
        return "Yesterday"
    # If within last 7 days
    elif (now - ist_dt).days < 7:
        return ist_dt.strftime("%a")
    # Otherwise show date
    else:
        return ist_dt.strftime("%d/%m")


def get_avatar_color(name: str) -> int:
    """Get consistent color index for avatar based on name"""
    if not name:
        return 0
    return hash(name) % 8


def get_avatar_initials(name: str) -> str:
    """Get initials for avatar"""
    if not name or name == "Unknown":
        return "?"
    
    # Extract first letter of each word, max 2 letters
    words = name.split()
    if len(words) >= 2:
        return (words[0][0] + words[-1][0]).upper()
    elif len(name) >= 2:
        return name[:2].upper()
    else:
        return name[0].upper() if name else "?"


from datetime import timedelta


def fetch_contacts(only_follow_up: bool):
    try:
        r = requests.get(f"{API_BASE}/contacts", params={"only_follow_up": only_follow_up})
        r.raise_for_status()
        contacts_data = r.json()
        
        # Get conversation for each contact to get last message time
        for contact in contacts_data:
            phone = contact["phone"]
            try:
                conv = fetch_conversation(phone, limit=1, offset=0)
                if conv:
                    contact["last_message_time"] = conv[0]["timestamp"]
                    contact["last_message_preview"] = conv[0]["message"][:30] + "..." if len(conv[0]["message"]) > 30 else conv[0]["message"]
                else:
                    contact["last_message_time"] = None
                    contact["last_message_preview"] = "No messages yet"
            except:
                contact["last_message_time"] = None
                contact["last_message_preview"] = "No messages yet"
        
        return contacts_data
    except Exception as e:
        st.error(f"Error fetching contacts: {e}")
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
        st.error(f"Error fetching conversation: {e}")
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
        msg_dt = convert_to_ist(msg["timestamp"])
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
    """Log sent message to backend database with IST timestamp"""
    try:
        ist_now = datetime.now(IST)
        
        payload = {
            "phone": phone,
            "message": message,
            "direction": "outgoing",
            "message_type": msg_type,
            "timestamp": ist_now.isoformat(),
            "follow_up_needed": False,
            "notes": "",
            "handled_by": "Dashboard User"
        }
        response = requests.post(f"{API_BASE}/log_message", json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        st.warning(f"Message sent but not logged in database: {e}")
        return False


# Fetch contacts with improved error handling
try:
    contacts = fetch_contacts(st.session_state.filter_only_fu)
    
    # Apply filters
    if st.session_state.filter_phone:
        contacts = [c for c in contacts if st.session_state.filter_phone.lower() in c["phone"].lower()]
    if st.session_state.filter_name:
        contacts = [c for c in contacts if c.get("client_name") and st.session_state.filter_name.lower() in c["client_name"].lower()]
    
    # Sort contacts by last message time (most recent first)
    contacts.sort(key=lambda x: convert_to_ist(x.get("last_message_time") or "2000-01-01T00:00:00Z"), reverse=True)
    
except Exception as e:
    st.error(f"Error loading contacts: {e}")
    contacts = []

if not contacts:
    st.info("🔍 No contacts found")
    st.stop()

if "selected_phone" not in st.session_state:
    st.session_state.selected_phone = contacts[0]["phone"] if contacts else ""

if "conv_offset" not in st.session_state:
    st.session_state.conv_offset = 0

if "last_message_count" not in st.session_state:
    st.session_state.last_message_count = {}

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True

CONV_LIMIT = 20

col1, col2 = st.columns([1, 2.5])

with col1:
    st.markdown("### 💬 Contacts")
    
    # Search in contacts
    search_query = st.text_input(
        "Search contacts...",
        placeholder="Type to search...",
        key="search_contacts",
        label_visibility="collapsed"
    )
    
    if search_query:
        filtered_contacts = [c for c in contacts if 
                           search_query.lower() in (c.get("client_name") or "").lower() or 
                           search_query in c["phone"]]
    else:
        filtered_contacts = contacts
    
    for c in filtered_contacts:
        client_name = c["client_name"] or "Unknown"
        phone = c["phone"]
        is_selected = st.session_state.selected_phone == phone
        
        # Calculate unread messages for this contact
        unread_count = sum(1 for msg in fetch_conversation(phone, limit=50) if msg.get("follow_up_needed"))
        
        # Get avatar color and initials
        color_index = get_avatar_color(client_name)
        initials = get_avatar_initials(client_name)
        
        # Format last message time
        last_time = ""
        if c.get("last_message_time"):
            last_time = format_contact_time(c["last_message_time"])
        
        # Create contact card HTML
        contact_html = f"""
        <div class="contact-card {'selected' if is_selected else ''}" onclick="window.location.href='?phone={phone}';">
            <div class="contact-avatar avatar-color-{color_index}">{initials}</div>
            <div class="contact-info">
                <div class="contact-name">{client_name}</div>
                <div class="contact-preview">{c.get('last_message_preview', '')}</div>
            </div>
            <div class="contact-meta">
                <div class="contact-time">{last_time}</div>
                {f'<div class="unread-indicator">{unread_count}</div>' if unread_count > 0 else ''}
            </div>
        </div>
        """
        
        st.markdown(contact_html, unsafe_allow_html=True)

with col2:
    phone = st.session_state.selected_phone
    if not phone and contacts:
        phone = contacts[0]["phone"]
        st.session_state.selected_phone = phone
    
    selected = next((c for c in contacts if c["phone"] == phone), None) if phone else None
    
    if not selected:
        st.info("📭 Select a contact to view messages")
        st.stop()
    
    client_name = selected["client_name"] or phone
    
    # Get avatar color and initials
    color_index = get_avatar_color(client_name)
    initials = get_avatar_initials(client_name)
    
    col_toggle1, col_toggle2 = st.columns([3, 1])
    with col_toggle1:
        pass
    with col_toggle2:
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=st.session_state.auto_refresh, key="auto_refresh_toggle")
        st.session_state.auto_refresh = auto_refresh
    
    if st.session_state.auto_refresh:
        st.markdown("""
        <script>
            setTimeout(function() {
                window.parent.location.reload();
            }, 5000);
        </script>
        """, unsafe_allow_html=True)
    
    # WhatsApp-like chat header
    st.markdown(f"""
    <div class="chat-header">
        <div class="chat-header-left">
            <div class="chat-avatar avatar-color-{color_index}">{initials}</div>
            <div class="chat-header-info">
                <h3>{client_name}</h3>
                <p>{phone}</p>
            </div>
        </div>
        <div class="chat-header-actions">
            <span class="chat-status">Online</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Delete button
    if st.button("🗑️ Delete All", key="del_all"):
        if st.session_state.get('confirm_del'):
            if delete_conversation(phone):
                st.success("Deleted!")
                st.session_state.pop('confirm_del', None)
                st.rerun()
        else:
            st.session_state.confirm_del = True
            st.warning("Click again to confirm deletion")
    
    # Search in conversation
    search_query = st.text_input(
        "Search in this chat",
        placeholder="Type to search messages...",
        key="search_conv",
        label_visibility="collapsed"
    )
    
    # Fetch conversation
    conv = fetch_conversation(phone, limit=CONV_LIMIT, offset=st.session_state.conv_offset)
    
    # Apply filters
    date_filter = st.session_state.filter_date if st.session_state.filter_by_date else None
    time_from = st.session_state.filter_time_from if st.session_state.filter_by_time else None
    time_to = st.session_state.filter_time_to if st.session_state.filter_by_time else None
    conv = filter_messages(conv, date_filter, time_from, time_to)
    
    # Sort messages chronologically
    conv.sort(key=lambda x: convert_to_ist(x["timestamp"]), reverse=False)
    
    # Calculate unread messages
    unread_count = sum(1 for m in conv if m.get("follow_up_needed"))
    
    # WhatsApp chat container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    if not conv:
        st.info("📭 No messages yet")
    else:
        # Group messages by date
        current_date = None
        for msg in conv:
            msg_dt = convert_to_ist(msg["timestamp"])
            msg_date = msg_dt.date()
            
            # Show date separator if date changed
            if current_date != msg_date:
                current_date = msg_date
                today = datetime.now(IST).date()
                
                if msg_date == today:
                    date_label = "Today"
                elif msg_date == today - timedelta(days=1):
                    date_label = "Yesterday"
                else:
                    date_label = msg_dt.strftime("%B %d, %Y")
                
                st.markdown(f'<div style="text-align: center; margin: 16px 0; color: #8696a0; font-size: 12px;">{date_label}</div>', unsafe_allow_html=True)
            
            direction = "user" if msg["direction"] in ["user", "incoming"] else "bot"
            
            raw_text = msg["message"] or ""
            display_text = raw_text
            
            if search_query:
                pattern = re.escape(search_query)
                def repl(m):
                    return f"<span style='background-color: #ffd700; padding: 0 1px; border-radius: 2px;'>{m.group(0)}</span>"
                display_text = re.sub(pattern, repl, display_text, flags=re.IGNORECASE)
            
            display_text = display_text.replace("\n", "<br>")
            
            # Format message time
            msg_time = format_message_time(msg["timestamp"])
            
            message_html = f"""
            <div class="message-row {direction}">
                <div class="message-bubble {direction}">
                    <div class="message-text">{display_text}</div>
                    <div class="message-time">
                        {msg_time}
                        <span class="message-meta">
                            {'<span class="message-status delivered">✓✓</span>' if direction == 'bot' else ''}
                            {'🔴' if msg.get('follow_up_needed') else ''}
                        </span>
                    </div>
            """
            
            if msg.get("notes"):
                message_html += f'<div style="font-size: 11px; color: rgba(255, 255, 255, 0.6); margin-top: 4px; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 2px;">📝 {msg["notes"]}</div>'
            if msg.get("handled_by"):
                message_html += f'<div style="font-size: 11px; color: rgba(255, 255, 255, 0.6);">👤 {msg["handled_by"]}</div>'
            
            message_html += "</div></div>"
            st.markdown(message_html, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Pagination
    st.markdown('<div class="pagination-section">', unsafe_allow_html=True)
    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])

    with col_p1:
        prev_disabled = st.session_state.conv_offset == 0
        if st.button("⬅️ Prev", disabled=prev_disabled):
            st.session_state.conv_offset = max(0, st.session_state.conv_offset - CONV_LIMIT)
            st.rerun()

    with col_p2:
        start_idx = st.session_state.conv_offset + 1 if conv else 0
        end_idx = st.session_state.conv_offset + len(conv)
        st.markdown(f'<p class="pagination-info">Showing messages {start_idx}–{end_idx}</p>', unsafe_allow_html=True)

    with col_p3:
        if st.button("Next ➡️"):
            st.session_state.conv_offset += CONV_LIMIT
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
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
            height=100
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
                if draft_key in st.session_state:
                    del st.session_state[draft_key]
                import time
                time.sleep(0.5)
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Update follow-up status section
    update_msg = conv[0] if conv else None
    
    if update_msg:
        st.markdown('<div class="update-section">', unsafe_allow_html=True)
        st.markdown("### 📝 Update Follow-up Status")
        
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            fu_flag = st.checkbox("🔴 Follow-up needed", value=update_msg.get("follow_up_needed", False))
        with col_u2:
            handler = st.text_input("👤 Handled by", value=update_msg.get("handled_by") or "")
        
        notes = st.text_area("📝 Notes", value=update_msg.get("notes") or "")
        
        if st.button("💾 Save Follow-up", use_container_width=True):
            resp = requests.patch(
                f"{API_BASE}/message/{update_msg['id']}",
                json={"follow_up_needed": fu_flag, "notes": notes, "handled_by": handler}
            )
            if resp.status_code == 200:
                st.success("✅ Saved!")
                st.rerun()
            else:
                st.error(f"Error: {resp.text}")
        
        st.markdown('</div>', unsafe_allow_html=True)
