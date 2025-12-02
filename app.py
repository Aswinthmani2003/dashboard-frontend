import streamlit as st
import requests
from datetime import datetime, date, time
import base64
from pathlib import Path

API_BASE = "https://dashboard-backend-qqmi.onrender.com"

# Page config
st.set_page_config(
    page_title="WhatsApp Chat Inbox",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to load and encode logo
def get_base64_logo():
    """Load logo.png and convert to base64 for embedding"""
    logo_path = Path("Logo.png")
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

# Custom CSS for authentic WhatsApp styling
st.markdown("""
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
    }
    
    .main-header h1 {
        color: #e9edef;
        margin: 0;
        font-size: 19px;
        font-weight: 400;
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
        margin-bottom: 20px;
        border-bottom: 1px solid #2a3942;
        display: flex;
        justify-content: space-between;
        align-items: center;
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
    
    /* Update section */
    
    .update-section h3 {
        color: #e9edef !important;
        font-size: 16px !important;
        margin-bottom: 15px !important;
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
    
    /* Hide streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

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

# Helper functions
def fetch_contacts(only_follow_up: bool):
    try:
        r = requests.get(f"{API_BASE}/contacts", params={"only_follow_up": only_follow_up})
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Error: {e}")
        return []

def fetch_conversation(phone: str):
    try:
        r = requests.get(f"{API_BASE}/conversation/{phone}")
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

# Layout
col1, col2 = st.columns([1, 2.5])

with col1:
    st.markdown("### 💬 Contacts")
    for c in contacts:
        client_name = c["client_name"] or "Unknown"
        phone = c["phone"]
        is_selected = st.session_state.selected_phone == phone
        fu_indicator = "🔴 " if c["follow_up_open"] else ""
        
        if st.button(
            f"{fu_indicator}{client_name}",
            key=phone,
            use_container_width=True,
            type="primary" if is_selected else "secondary"
        ):
            st.session_state.selected_phone = phone
            st.rerun()

with col2:
    phone = st.session_state.selected_phone
    selected = next((c for c in contacts if c["phone"] == phone), None)
    
    if not selected:
        st.stop()
    
    client_name = selected["client_name"] or phone
    
    # Chat header
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
    
    # Fetch messages
    conv = fetch_conversation(phone)
    conv = filter_messages(conv, date_filter, time_from, time_to)
    
    if not conv:
        st.info("📭 No messages")
    else:
        # Chat area
        
        for msg in conv:
            ts = datetime.fromisoformat(msg["timestamp"])
            direction = "user" if msg["direction"] in ["user", "incoming"] else "bot"
            
            message_html = f"""
            <div class="message-row {direction}">
                <div class="message-bubble {direction}">
                    <div class="message-text">{msg["message"]}</div>
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
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Update section
        last_msg = conv[-1]
        
        st.markdown("### 📝 Update Follow-up Status")
        
        col1, col2 = st.columns(2)
        with col1:
            fu_flag = st.checkbox("🔴 Follow-up needed", value=last_msg.get("follow_up_needed", False))
        with col2:
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
        
        st.markdown('</div>', unsafe_allow_html=True)