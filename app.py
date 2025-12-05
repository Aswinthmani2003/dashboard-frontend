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
MONGO_API_BASE = "https://mongodb-api-backend.onrender.com"  # Add your MongoDB API base URL

# Define IST timezone
IST = pytz.timezone('Asia/Kolkata')

def check_password():
    """Simple password gate using Streamlit secrets"""
    def password_entered():
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
if "client_automation_status" not in st.session_state:
    st.session_state.client_automation_status = {}

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
            
            .automation-status {
                font-size: 11px;
                padding: 2px 6px;
                border-radius: 4px;
                margin-top: 2px;
            }
            
            .automation-on {
                background-color: #00a884;
                color: white;
            }
            
            .automation-off {
                background-color: #dc3545;
                color: white;
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
            
            .chat-header-actions {
                display: flex;
                gap: 10px;
                align-items: center;
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
            
            .stSelectbox label {
                color: #e9edef !important;
            }
            
            .stRadio label {
                color: #e9edef !important;
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
                background: #111b21;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #374045;
                border-radius: 3px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #3b4a54;
            }
            
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            .main .block-container {
                padding-top: 0rem !important;
            }
            
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
            
            /* Toggle switch styles */
            .toggle-container {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .toggle-label {
                font-size: 12px;
                color: #8696a0;
            }
            
            .toggle-switch {
                position: relative;
                display: inline-block;
                width: 40px;
                height: 20px;
            }
            
            .toggle-switch input {
                opacity: 0;
                width: 0;
                height: 0;
            }
            
            .toggle-slider {
                position: absolute;
                cursor: pointer;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: #ccc;
                transition: .4s;
                border-radius: 20px;
            }
            
            .toggle-slider:before {
                position: absolute;
                content: "";
                height: 16px;
                width: 16px;
                left: 2px;
                bottom: 2px;
                background-color: white;
                transition: .4s;
                border-radius: 50%;
            }
            
            input:checked + .toggle-slider {
                background-color: #00a884;
            }
            
            input:checked + .toggle-slider:before {
                transform: translateX(20px);
            }
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
            
            .automation-status {
                font-size: 11px;
                padding: 2px 6px;
                border-radius: 4px;
                margin-top: 2px;
            }
            
            .automation-on {
                background-color: #00a884;
                color: white;
            }
            
            .automation-off {
                background-color: #dc3545;
                color: white;
            }
            
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
                gap: 10px;
                align-items: center;
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
                background: rgba(234, 230, 223, 0.85);
                pointer-events: none;
            }
            
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
            
            .input-area {
                background: #f0f2f5;
                padding: 10px 16px;
                border-top: 1px solid #dddfe2;
                position: sticky;
                bottom: 0;
                z-index: 100;
            }
            
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
            
            [data-testid="stCheckbox"] label {
                color: #3b4a54 !important;
                font-size: 14px !important;
            }
            
            .stSelectbox label {
                color: #3b4a54 !important;
            }
            
            .stRadio label {
                color: #3b4a54 !important;
            }
            
            .stDateInput input, .stTimeInput input {
                background-color: #ffffff !important;
                color: #3b4a54 !important;
                border: 1px solid #dddfe2 !important;
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
                background: #bcc0c4;
                border-radius: 3px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #a0a4a8;
            }
            
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            .main .block-container {
                padding-top: 0rem !important;
            }
            
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
                background-color: #ffffff;
                border: none;
                border-bottom: 1px solid #dddfe2;
                padding: 8px 12px;
                color: #3b4a54;
                font-size: 14px;
                width: 100%;
            }
            
            .status-online {
                color: #00a884;
                font-size: 11px;
            }
            
            .status-offline {
                color: #667781;
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
            
            /* Toggle switch styles for light mode */
            .toggle-container {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .toggle-label {
                font-size: 12px;
                color: #667781;
            }
            
            .toggle-switch {
                position: relative;
                display: inline-block;
                width: 40px;
                height: 20px;
            }
            
            .toggle-switch input {
                opacity: 0;
                width: 0;
                height: 0;
            }
            
            .toggle-slider {
                position: absolute;
                cursor: pointer;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: #ccc;
                transition: .4s;
                border-radius: 20px;
            }
            
            .toggle-slider:before {
                position: absolute;
                content: "";
                height: 16px;
                width: 16px;
                left: 2px;
                bottom: 2px;
                background-color: white;
                transition: .4s;
                border-radius: 50%;
            }
            
            input:checked + .toggle-slider {
                background-color: #00a884;
            }
            
            input:checked + .toggle-slider:before {
                transform: translateX(20px);
            }
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
        if not timestamp_str:
            return datetime.now(IST)
        
        timestamp_str = str(timestamp_str).replace('Z', '+00:00')
        
        try:
            dt = datetime.fromisoformat(timestamp_str)
        except:
            dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f%z")
        
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        
        ist_dt = dt.astimezone(IST)
        return ist_dt
    except Exception as e:
        return datetime.now(IST)


def format_message_time(timestamp_str: str) -> str:
    """Format timestamp for display in IST timezone (HH:MM format)"""
    ist_dt = convert_to_ist(timestamp_str)
    return ist_dt.strftime("%I:%M %p").lstrip('0')


def format_contact_time(timestamp_str: str) -> str:
    """Format timestamp for contact list display"""
    try:
        if not timestamp_str:
            return ""
        
        ist_dt = convert_to_ist(timestamp_str)
        now = datetime.now(IST)
        
        if ist_dt.date() == now.date():
            return ist_dt.strftime("%I:%M %p").lstrip('0')
        elif ist_dt.date() == (now.date() - timedelta(days=1)):
            return "Yesterday"
        elif (now - ist_dt).days < 7:
            return ist_dt.strftime("%a")
        else:
            return ist_dt.strftime("%d/%m")
    except:
        return ""


def get_avatar_color(name: str) -> int:
    """Get consistent color index for avatar based on name"""
    if not name:
        return 0
    return hash(name) % 8


def get_avatar_initials(name: str) -> str:
    """Get initials for avatar"""
    if not name or name == "Unknown":
        return "?"
    
    words = name.split()
    if len(words) >= 2:
        return (words[0][0] + words[-1][0]).upper()
    elif len(name) >= 2:
        return name[:2].upper()
    else:
        return name[0].upper() if name else "?"


def make_request_with_retry(url, method="GET", params=None, json_data=None, max_retries=3):
    """Make HTTP request with retry logic"""
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


def fetch_contacts(only_follow_up: bool):
    """Fetch contacts from backend API with retry logic"""
    try:
        response = make_request_with_retry(
            f"{API_BASE}/contacts",
            params={"only_follow_up": only_follow_up}
        )
        
        if response and response.status_code == 200:
            contacts_data = response.json()
            # Fetch automation status for each contact
            for contact in contacts_data:
                phone = contact.get("phone")
                if phone:
                    contact["automation_enabled"] = get_client_automation_status(phone)
            return contacts_data
        else:
            st.warning("Failed to fetch contacts. Please try again.")
            return []
            
    except Exception as e:
        st.warning(f"Could not fetch contacts: {str(e)}")
        return [
            {"phone": "1234567890", "client_name": "John Doe", "follow_up_open": False, "automation_enabled": True},
            {"phone": "9876543210", "client_name": "Jane Smith", "follow_up_open": True, "automation_enabled": True},
            {"phone": "5555555555", "client_name": "Test Client", "follow_up_open": False, "automation_enabled": True}
        ]


def fetch_conversation(phone: str, limit: int = 50, offset: int = 0):
    """Fetch conversation for a specific phone number from MongoDB"""
    try:
        if not phone:
            return []
        
        # Try MongoDB API first
        try:
            response = make_request_with_retry(
                f"{MONGO_API_BASE}/conversations/{phone}",
                params={"limit": limit, "offset": offset}
            )
            
            if response and response.status_code == 200:
                return response.json()
        except:
            pass
        
        # Fallback to original API
        endpoints_to_try = [
            f"{API_BASE}/conversation/{phone}",
            f"{API_BASE}/conversation?phone={phone}"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                response = make_request_with_retry(
                    endpoint,
                    params={"limit": limit, "offset": offset}
                )
                
                if response and response.status_code == 200:
                    return response.json()
                elif response and response.status_code == 404:
                    continue
                    
            except Exception:
                continue
        
        return []
        
    except Exception as e:
        st.warning(f"Could not fetch conversation: {str(e)}")
        return []


def save_conversation_to_mongo(phone: str, message: str, direction: str, 
                              message_type: str = "text", notes: str = "", 
                              handled_by: str = "", follow_up_needed: bool = False):
    """Save conversation to MongoDB"""
    try:
        ist_now = datetime.now(IST)
        
        payload = {
            "phone": phone,
            "message": message,
            "direction": direction,
            "message_type": message_type,
            "timestamp": ist_now.isoformat(),
            "follow_up_needed": follow_up_needed,
            "notes": notes,
            "handled_by": handled_by
        }
        
        # Save to MongoDB
        response = make_request_with_retry(
            f"{MONGO_API_BASE}/conversations",
            method="POST",
            json_data=payload
        )
        
        # Also save to original API for backup
        try:
            make_request_with_retry(
                f"{API_BASE}/log_message",
                method="POST",
                json_data=payload
            )
        except:
            pass
        
        return response and response.status_code == 200
    except Exception as e:
        st.warning(f"Could not save to MongoDB: {e}")
        return False


def delete_conversation(phone: str):
    """Delete conversation from both APIs"""
    try:
        # Delete from MongoDB
        response1 = make_request_with_retry(f"{MONGO_API_BASE}/conversations/{phone}", method="DELETE")
        # Delete from original API
        response2 = make_request_with_retry(f"{API_BASE}/conversation/{phone}", method="DELETE")
        return (response1 and response1.status_code == 200) or (response2 and response2.status_code == 200)
    except:
        return False


def delete_message(msg_id: int):
    try:
        # Try MongoDB first
        response1 = make_request_with_retry(f"{MONGO_API_BASE}/messages/{msg_id}", method="DELETE")
        # Try original API
        response2 = make_request_with_retry(f"{API_BASE}/message/{msg_id}", method="DELETE")
        return (response1 and response1.status_code == 200) or (response2 and response2.status_code == 200)
    except:
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
        except:
            continue
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
        response = make_request_with_retry(MAKE_WEBHOOK_URL, method="POST", json_data=payload)
        if response and response.status_code in (200, 201, 202):
            # Save to MongoDB
            save_conversation_to_mongo(
                phone=phone,
                message=message_text,
                direction="outgoing",
                message_type=msg_type,
                handled_by="Dashboard User"
            )
            return True
        else:
            st.error(f"Send failed")
            return False
    except Exception as e:
        st.error(f"Send error: {e}")
        return False


def get_client_automation_status(phone: str):
    """Get automation status for a client from MongoDB"""
    try:
        response = make_request_with_retry(f"{MONGO_API_BASE}/clients/{phone}/automation")
        if response and response.status_code == 200:
            data = response.json()
            return data.get("automation_enabled", True)
    except:
        pass
    
    # Default to True if not found
    return True


def update_client_automation_status(phone: str, enabled: bool):
    """Update automation status for a client in MongoDB"""
    try:
        payload = {
            "phone": phone,
            "automation_enabled": enabled,
            "updated_at": datetime.now(IST).isoformat()
        }
        
        response = make_request_with_retry(
            f"{MONGO_API_BASE}/clients/automation",
            method="POST",
            json_data=payload
        )
        
        if response and response.status_code == 200:
            # Update session state
            st.session_state.client_automation_status[phone] = enabled
            return True
    except Exception as e:
        st.warning(f"Could not update automation status: {e}")
    
    return False


# Fetch contacts with improved error handling
try:
    contacts = fetch_contacts(st.session_state.filter_only_fu)
    
    # Apply filters
    if st.session_state.filter_phone:
        contacts = [c for c in contacts if st.session_state.filter_phone.lower() in c.get("phone", "").lower()]
    if st.session_state.filter_name:
        contacts = [c for c in contacts if c.get("client_name") and st.session_state.filter_name.lower() in c["client_name"].lower()]
    
    # Sort contacts by client name
    def get_contact_sort_key(contact):
        name = contact.get("client_name", "").lower()
        phone = contact.get("phone", "")
        return (name, phone)
    
    contacts.sort(key=get_contact_sort_key)
    
except Exception as e:
    st.warning(f"Could not load contacts: {str(e)}")
    contacts = [
        {"phone": "1234567890", "client_name": "John Doe", "follow_up_open": False, "automation_enabled": True},
        {"phone": "9876543210", "client_name": "Jane Smith", "follow_up_open": True, "automation_enabled": True},
        {"phone": "5555555555", "client_name": "Test Client", "follow_up_open": False, "automation_enabled": True}
    ]

if not contacts:
    st.info("🔍 No contacts found")
    st.stop()

if "selected_phone" not in st.session_state:
    if contacts:
        st.session_state.selected_phone = contacts[0].get("phone", "")
    else:
        st.session_state.selected_phone = ""

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
    search_query_contacts = st.text_input(
        "Search contacts...",
        placeholder="Type to search...",
        key="search_contacts",
        label_visibility="collapsed"
    )
    
    if search_query_contacts:
        filtered_contacts = [c for c in contacts if 
                           search_query_contacts.lower() in (c.get("client_name") or "").lower() or 
                           search_query_contacts in c.get("phone", "")]
    else:
        filtered_contacts = contacts
    
    for c in filtered_contacts:
        client_name = c.get("client_name") or "Unknown"
        phone = c.get("phone", "")
        is_selected = st.session_state.selected_phone == phone
        
        # Get last message preview
        last_message_preview = "No messages yet"
        try:
            conv = fetch_conversation(phone, limit=1)
            if conv and len(conv) > 0:
                last_msg = conv[0].get("message", "")
                if last_msg:
                    last_message_preview = html.escape(last_msg[:30]) + ("..." if len(last_msg) > 30 else "")
        except:
            pass
        
        # Calculate unread messages
        try:
            conv = fetch_conversation(phone, limit=50)
            unread_count = sum(1 for msg in conv if msg.get("follow_up_needed"))
        except:
            unread_count = 0
        
        # Get avatar color and initials
        color_index = get_avatar_color(client_name)
        initials = get_avatar_initials(client_name)
        
        # Format last message time
        last_time = ""
        try:
            conv = fetch_conversation(phone, limit=1)
            if conv and len(conv) > 0:
                last_time = format_contact_time(conv[0].get("timestamp"))
        except:
            pass
        
        # Get automation status
        automation_enabled = c.get("automation_enabled", True)
        automation_status_class = "automation-on" if automation_enabled else "automation-off"
        automation_status_text = "🤖 Auto: ON" if automation_enabled else "🤖 Auto: OFF"
        
        # Create contact card HTML
        contact_html = f"""
        <div class="contact-card {'selected' if is_selected else ''}">
            <div class="contact-avatar avatar-color-{color_index}">{initials}</div>
            <div class="contact-info">
                <div class="contact-name">{html.escape(client_name)}</div>
                <div class="contact-preview">{last_message_preview}</div>
                <div class="automation-status {automation_status_class}">{automation_status_text}</div>
            </div>
            <div class="contact-meta">
                <div class="contact-time">{last_time}</div>
                {f'<div class="unread-indicator">{unread_count}</div>' if unread_count > 0 else ''}
            </div>
        </div>
        """
        
        # Create a clickable contact using button
        if st.button(f"📱 {client_name}", key=f"contact_{phone}", 
                    type="primary" if is_selected else "secondary", 
                    use_container_width=True):
            st.session_state.selected_phone = phone
            st.session_state.conv_offset = 0
            # Clear the message field when switching contacts
            draft_key = f"new_msg_{phone}"
            if draft_key in st.session_state:
                del st.session_state[draft_key]
            st.rerun()

with col2:
    phone = st.session_state.selected_phone
    if not phone and contacts:
        phone = contacts[0].get("phone", "")
        st.session_state.selected_phone = phone
    
    selected = next((c for c in contacts if c.get("phone") == phone), None) if phone else None
    
    if not selected:
        st.info("📭 Select a contact to view messages")
        st.stop()
    
    client_name = selected.get("client_name") or phone
    
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
    
    # WhatsApp-like chat header with automation toggle and delete button
    col_header_content, col_header_toggle, col_header_delete = st.columns([3, 1, 1])

    with col_header_content:
        st.markdown(f"""
        <div class="chat-header">
            <div class="chat-header-left">
                <div class="chat-avatar avatar-color-{color_index}">{initials}</div>
                <div class="chat-header-info">
                    <h3>{html.escape(client_name)}</h3>
                    <p>{phone}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_header_toggle:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        # Get current automation status
        automation_enabled = get_client_automation_status(phone)
        
        # Create toggle switch
        st.markdown("""
        <div class="toggle-container">
            <label class="toggle-label">Chatbot:</label>
            <label class="toggle-switch">
                <input type="checkbox" id="automation_toggle" %s>
                <span class="toggle-slider"></span>
            </label>
        </div>
        """ % ("checked" if automation_enabled else ""), unsafe_allow_html=True)
        
        # Add JavaScript to handle toggle
        toggle_html = f"""
        <script>
            document.getElementById('automation_toggle').addEventListener('change', function() {{
                var enabled = this.checked;
                fetch('{API_BASE}/update_automation', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{
                        phone: '{phone}',
                        automation_enabled: enabled
                    }})
                }}).then(response => {{
                    if (response.ok) {{
                        window.parent.location.reload();
                    }}
                }});
            }});
        </script>
        """
        st.markdown(toggle_html, unsafe_allow_html=True)
        
        # Also provide a fallback button for better UX
        if st.button("Toggle Automation", key=f"toggle_auto_{phone}", use_container_width=True):
            new_status = not automation_enabled
            if update_client_automation_status(phone, new_status):
                st.success(f"Automation {'enabled' if new_status else 'disabled'}!")
                time_module.sleep(0.5)
                st.rerun()

    with col_header_delete:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        if st.button("🗑️ Delete All", key="del_all", use_container_width=True):
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
    
    # Sort messages chronologically (oldest first for chat view)
    conv.sort(key=lambda x: convert_to_ist(x["timestamp"]), reverse=False)
    
    # Calculate unread messages
    unread_count = sum(1 for m in conv if m.get("follow_up_needed"))
    
    if unread_count > 0:
        st.markdown(f'<div style="color: #ff3b30; font-size: 13px; margin: 0 0 10px 20px;">🔴 {unread_count} unread messages</div>', unsafe_allow_html=True)
    
    # Create a container for the chat area
    chat_container = st.container()
    
    with chat_container:
        
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
                
                direction = "user" if msg.get("direction") in ["user", "incoming"] else "bot"
                
                raw_text = msg.get("message", "")
                raw_text = html.escape(raw_text)
                display_text = raw_text
                
                if search_query and search_query.strip():
                    pattern = re.escape(search_query.strip())
                    def repl(m):
                        return f'<span style="background-color: #ffd700; padding: 0 1px; border-radius: 2px;">{html.escape(m.group(0))}</span>'
                    try:
                        display_text = re.sub(pattern, repl, display_text, flags=re.IGNORECASE)
                    except:
                        pass
                
                display_text = display_text.replace("\n", "<br>")
                
                # Format message time
                msg_time = format_message_time(msg["timestamp"])
                
                # Build message HTML
                message_html = f"""
                <div class="message-row {direction}">
                    <div class="message-bubble {direction}">
                        <div class="message-text">{display_text}</div>
                """
                
                if msg.get("notes"):
                    notes_text = html.escape(msg["notes"])
                    message_html += f'<div style="font-size: 11px; color: rgba(255, 255, 255, 0.6); margin-top: 4px; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 2px;">📝 {notes_text}</div>'
                if msg.get("handled_by"):
                    handler_text = html.escape(msg["handled_by"])
                    message_html += f'<div class="handler-meta">👤 {handler_text}</div>'
                
                message_html += f'<div class="message-time">{msg_time}</div>'
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
        # Clear message field after sending by not persisting it in session state
        new_msg = st.text_area(
            "Message",
            value="",  # Always start empty
            placeholder="Type a WhatsApp message to send...",
            key=f"msg_input_{phone}",
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
                # Clear the message field by rerunning
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
            try:
                response = make_request_with_retry(
                    f"{API_BASE}/message/{update_msg['id']}",
                    method="PATCH",
                    json_data={"follow_up_needed": fu_flag, "notes": notes, "handled_by": handler}
                )
                if response and response.status_code == 200:
                    st.success("✅ Saved!")
                    st.rerun()
                else:
                    st.error("Error saving follow-up status")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
