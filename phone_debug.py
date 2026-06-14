import requests
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}"

response = requests.get(
    url,
    headers={
        "Authorization": f"Bearer {TOKEN}"
    }
)

print(response.status_code)
print(response.text)