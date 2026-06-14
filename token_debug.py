import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("WHATSAPP_TOKEN")

r = requests.get(
    "https://graph.facebook.com/v25.0/me",
    headers={
        "Authorization": f"Bearer {token}"
    }
)

print(r.status_code)
print(r.text)