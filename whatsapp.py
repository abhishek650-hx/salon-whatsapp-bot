
import requests
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
print("TOKEN EXISTS:", TOKEN is not None)
print("TOKEN START:", TOKEN[:15] if TOKEN else "NONE")
print("TOKEN END:", TOKEN[-15:] if TOKEN else "NONE")
print("PHONE_NUMBER_ID:", PHONE_NUMBER_ID)




def send_text_message(phone, message):

    url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": str(phone),
        "type": "text",
        "text": {
            "body": message
        }
    }

    try:

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as e:

        print("WhatsApp Send Error:", str(e))

        try:
            print("Response:", response.text)
        except:
            pass

        return {
            "status": "error",
            "message": str(e)
        }
