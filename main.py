from fastapi import FastAPI, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import date
import os
import json

from database import SessionLocal
from models import Appointment
from whatsapp import send_text_message

load_dotenv()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

app = FastAPI()

AVAILABLE_SLOTS = [
    "10:00",
    "11:00",
    "12:00",
    "13:00",
    "14:00",
    "15:00",
    "16:00",
    "17:00",
    "18:00"
]


class ChatRequest(BaseModel):
    message: str


# =====================================
# HOME
# =====================================

@app.get("/")
def home():
    return {"message": "Salon Assistant Running"}


# =====================================
# WHATSAPP VERIFICATION
# =====================================

@app.get("/webhook")
async def verify_webhook(request: Request):

    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    print("VERIFY REQUEST")
    print("MODE:", mode)
    print("TOKEN:", token)
    print("CHALLENGE:", challenge)

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)

    return {"error": "Verification failed"}


# =====================================
# RECEIVE WHATSAPP MESSAGE
# =====================================

@app.post("/webhook")
async def receive_webhook(request: Request):

    data = await request.json()

    print("\n========== WEBHOOK ==========")
    print(json.dumps(data, indent=2))

    try:

        value = data["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            return {"status": "ignored"}

        phone = value["messages"][0]["from"]
        user_message = value["messages"][0]["text"]["body"].lower().strip()

        print("PHONE:", phone)
        print("MESSAGE:", user_message)

        with open("salon_data.json", "r") as file:
            salon_data = json.load(file)

        db = SessionLocal()

        try:

            if "timing" in user_message:

                reply = f"Salon timings are {salon_data['timings']}"

            elif user_message in salon_data["services"]:

                price = salon_data["services"][user_message]

                reply = f"{user_message.title()} costs ₹{price}"

            elif user_message == "show appointments":

                appointments = db.query(Appointment).all()

                if not appointments:
                    reply = "No appointments found"

                else:

                    reply = "Appointments:\n\n"

                    for a in appointments:
                        reply += (
                            f"ID: {a.id}\n"
                            f"Name: {a.name}\n"
                            f"Service: {a.service}\n"
                            f"Date: {a.date}\n"
                            f"Time: {a.time}\n\n"
                        )

            elif user_message.startswith("book"):

                parts = user_message.split()

                if len(parts) != 6:

                    reply = (
                        "Use:\n"
                        "book haircut abhishek "
                        "9876543210 2026-06-20 15:00"
                    )

                else:

                    service = parts[1]
                    name = parts[2]
                    customer_phone = parts[3]
                    booking_date = parts[4]
                    booking_time = parts[5]

                    existing = db.query(Appointment).filter(
                        Appointment.date == booking_date,
                        Appointment.time == booking_time
                    ).first()

                    if existing:

                        reply = f"Slot {booking_time} already booked"

                    else:

                        appointment = Appointment(
                            name=name,
                            phone=customer_phone,
                            service=service,
                            date=booking_date,
                            time=booking_time,
                            status="confirmed"
                        )

                        db.add(appointment)
                        db.commit()

                        reply = (
                            f"✅ Appointment Booked\n\n"
                            f"Service: {service}\n"
                            f"Name: {name}\n"
                            f"Date: {booking_date}\n"
                            f"Time: {booking_time}"
                        )

            else:

                reply = (
                    "💈 Salon Assistant\n\n"
                    "Commands:\n"
                    "• timing\n"
                    "• haircut\n"
                    "• beard\n"
                    "• facial\n"
                    "• show appointments\n\n"
                    "Booking:\n"
                    "book haircut abhishek "
                    "9876543210 2026-06-20 15:00"
                )

            send_text_message(phone, reply)

            return {"status": "success"}

        finally:
            db.close()

    except Exception as e:

        print("WEBHOOK ERROR:", str(e))

        return {
            "status": "error",
            "message": str(e)
        }


# =====================================
# APPOINTMENTS
# =====================================

@app.get("/appointments")
def get_appointments():

    db = SessionLocal()

    appointments = db.query(Appointment).all()

    result = []

    for a in appointments:
        result.append({
            "id": a.id,
            "name": a.name,
            "phone": a.phone,
            "service": a.service,
            "date": a.date,
            "time": a.time,
            "status": a.status
        })

    db.close()

    return result


# =====================================
# TODAY
# =====================================

@app.get("/today")
def today_appointments():

    db = SessionLocal()

    today_date = str(date.today())

    appointments = db.query(Appointment).filter(
        Appointment.date == today_date
    ).all()

    result = []

    for a in appointments:
        result.append({
            "id": a.id,
            "name": a.name,
            "service": a.service,
            "time": a.time
        })

    db.close()

    return result
