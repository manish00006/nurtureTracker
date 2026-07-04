"""
Services for communications: WhatsApp Cloud API integration.
"""

import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Wrapper for Meta's WhatsApp Cloud API.
    """
    def __init__(self):
        self.token = getattr(settings, 'WHATSAPP_API_TOKEN', '')
        self.phone_id = getattr(settings, 'WHATSAPP_PHONE_ID', '')
        self.api_url = f"https://graph.facebook.com/v19.0/{self.phone_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def _is_configured(self):
        return bool(self.token and self.phone_id)

    def _format_phone(self, phone):
        """Ensure phone number is in correct format (digits only, e.g., 919876543210)."""
        if not phone:
            return ""
        clean = ''.join(filter(str.isdigit, str(phone)))
        if len(clean) == 10:
            return f"91{clean}"  # Default to India if no country code
        return clean

    def send_text_message(self, to_phone, message):
        """
        Send a plain text message.
        """
        phone = self._format_phone(to_phone)
        if not phone:
            logger.error("WhatsApp: No phone number provided.")
            return False
            
        if not self._is_configured():
            # For development without active API keys
            print("\n" + "="*50)
            print(f"🟢 [DEV] WHATSAPP MESSAGE INTERCEPTED")
            print(f"To: {phone}")
            print(f"Message:\n{message}")
            print("="*50 + "\n")
            return True

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"WhatsApp sent successfully to {phone}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"WhatsApp API error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response data: {e.response.text}")
            return False

    def send_attendance_alert(self, student_name, parent_phone, status, date_str):
        """
        Send formatted attendance alert.
        """
        emoji = "✅" if status == 'present' else "❌" if status == 'absent' else "⏰"
        msg = (
            f"*Nurture Coaching Class*\n\n"
            f"Hello, this is an attendance update for {student_name}.\n"
            f"Date: {date_str}\n"
            f"Status: {emoji} *{status.title()}*\n\n"
            f"Log in to the app for more details."
        )
        return self.send_text_message(parent_phone, msg)
        
    def send_score_alert(self, student_name, parent_phone, test_name, subject, marks, total):
        """
        Send formatted test score alert.
        """
        pct = round((marks / total) * 100)
        emoji = "🌟" if pct >= 75 else "⚠️" if pct < 50 else "📊"
        msg = (
            f"*Nurture Coaching Class*\n\n"
            f"New test score for {student_name}!\n"
            f"Subject: {subject}\n"
            f"Test: {test_name}\n"
            f"Score: {marks}/{total} ({pct}%)\n"
            f"Performance: {emoji}\n\n"
            f"Check the app to see detailed concept mastery."
        )
        return self.send_text_message(parent_phone, msg)
