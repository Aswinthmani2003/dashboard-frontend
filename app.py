def toggle_automation(phone: str, enable: bool) -> bool:
    """Toggle automation on/off for a specific contact"""
    try:
        payload = {"phone": phone, "automation_enabled": enable}
        r = requests.post(f"{API_BASE}/toggle_automation", json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        st.error(f"Toggle automation error: {e}")
        return False


def get_automation_status(phone: str) -> bool:
    """Get current automation status for a contact"""
    try:
        r = requests.get(f"{API_BASE}/automation_status/{phone}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data.get("automation_enabled", True)
        return True  # Default to enabled
    except:
        return True


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
        "source": "dashboard"  # Mark as dashboard message
    }
    if msg_type == "template" and template_name:
        payload["template_name"] = template_name

    try:
        r = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=15)
        if r.status_code in (200, 201, 202):
            # Log the sent message to the backend database
            log_sent_message(phone, message_text, msg_type, source="dashboard")
            return True
        else:
            st.error(f"Send failed ({r.status_code}): {r.text}")
            return False
    except Exception as e:
        st.error(f"Send error: {e}")
        return False


def log_sent_message(phone: str, message: str, msg_type: str = "text", source: str = "dashboard"):
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
            "handled_by": "Dashboard User" if source == "dashboard" else "AI Chatbot",
            "source": source  # 'dashboard' or 'chatbot'
        }
        response = requests.post(f"{API_BASE}/log_message", json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        # Silently fail - don't disrupt the UI if logging fails
        st.warning(f"Message sent but not logged in database: {e}")
        return False
