import requests
import os
from dotenv import load_dotenv

load_dotenv()


def send_google_chat_message(text):
    webhook_url = os.getenv("GOOGLE_CHAT_WEBHOOK_URL")

    if not webhook_url:
        print("GOOGLE_CHAT_WEBHOOK missing in .env")
        return False

    payload = {"text": text}

    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            print("[NOTIFY] Google Chat message sent")
            return True
        else:
            print(f"[ERROR] Google Chat failed: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Google Chat Exception: {e}")
        return False
