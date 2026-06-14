from fastapi import FastAPI, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from user_state import user_states
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
# WHATSAPP WEBHOOK VERIFICATION
# =====================================

@app.post("/webhook")
async def receive_webhook(request: Request):

    data = await request.json()

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

            # TIMINGS
            if "timing" in user_message:

                reply = f"Salon timings are {salon_data['timings']}"

            # SERVICE PRICES
            elif user_message in salon_data["services"]:

                price = salon_data["services"][user_message]

                reply = f"{user_message.title()} costs ₹{price}"

            # SHOW APPOINTMENTS
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

            # SIMPLE BOOKING
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

            response = send_text_message(
                phone,
                reply
            )

            print(response)

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
# HOME
# =====================================

@app.get("/")
def home():
    return {"message": "Salon Assistant Running"}


# =====================================
# ALL APPOINTMENTS
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

    return result


# =====================================
# TODAY APPOINTMENTS
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

    return result


# =====================================
# REVENUE
# =====================================

@app.get("/revenue")
def revenue():

    db = SessionLocal()

    with open("salon_data.json", "r") as file:
        salon_data = json.load(file)

    appointments = db.query(Appointment).all()

    total = 0

    for appointment in appointments:

        service = appointment.service

        if service in salon_data["services"]:
            total += salon_data["services"][service]

    return {
        "total_revenue": total
    }


# =====================================
# CHATBOT
# =====================================

@app.post("/chat")
def chat(request: ChatRequest):

    db = SessionLocal()

    with open("salon_data.json", "r") as file:
        salon_data = json.load(file)

    message = request.message.lower()

    if message == "show appointments":

        appointments = db.query(Appointment).all()

        if not appointments:
            return {"reply": "No appointments found"}

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

        return result

    if message.startswith("find"):

        parts = message.split()

        if len(parts) != 2:
            return {"reply": "Use format: find abhishek"}

        customer_name = parts[1]

        appointments = db.query(Appointment).filter(
            Appointment.name == customer_name
        ).all()

        if not appointments:
            return {"reply": "Customer not found"}

        result = []

        for a in appointments:
            result.append({
                "id": a.id,
                "service": a.service,
                "date": a.date,
                "time": a.time,
                "status": a.status
            })

        return result

    if message.startswith("available slots"):

        parts = message.split()

        if len(parts) != 3:
            return {"reply": "Use format: available slots 2026-06-20"}

        selected_date = parts[2]

        appointments = db.query(Appointment).filter(
            Appointment.date == selected_date
        ).all()

        booked_slots = [a.time for a in appointments]

        free_slots = []

        for slot in AVAILABLE_SLOTS:
            if slot not in booked_slots:
                free_slots.append(slot)

        return {
            "date": selected_date,
            "available_slots": free_slots
        }

    if message.startswith("cancel"):

        parts = message.split()

        if len(parts) != 2:
            return {"reply": "Use format: cancel 1"}

        appointment_id = int(parts[1])

        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()

        if not appointment:
            return {"reply": "Appointment not found"}

        db.delete(appointment)
        db.commit()

        return {
            "reply": f"Appointment {appointment_id} cancelled"
        }

    if message.startswith("reschedule"):

        parts = message.split()

        if len(parts) != 3:
            return {"reply": "Use format: reschedule 1 17:00"}

        appointment_id = int(parts[1])
        new_time = parts[2]

        if new_time not in AVAILABLE_SLOTS:
            return {
                "reply": f"Available slots are {AVAILABLE_SLOTS}"
            }

        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()

        if not appointment:
            return {"reply": "Appointment not found"}

        appointment.time = new_time
        db.commit()

        return {
            "reply": f"Appointment {appointment_id} moved to {new_time}"
        }

    if "timing" in message:
        return {
            "reply": f"Salon timings are {salon_data['timings']}"
        }

    for service, price in salon_data["services"].items():

        if service in message and "book" not in message:

            return {
                "reply": f"{service.title()} costs ₹{price}"
            }

    if message.startswith("book"):

        parts = message.split()

        if len(parts) != 6:
            return {
                "reply": "Use format: book haircut abhishek 9876543210 2026-06-20 15:00"
            }

        service = parts[1]
        name = parts[2]
        phone = parts[3]
        booking_date = parts[4]
        booking_time = parts[5]

        if service not in salon_data["services"]:
            return {"reply": "Service not found"}

        if booking_time not in AVAILABLE_SLOTS:
            return {
                "reply": f"Available slots are {AVAILABLE_SLOTS}"
            }

        existing = db.query(Appointment).filter(
            Appointment.date == booking_date,
            Appointment.time == booking_time
        ).first()

        if existing:
            return {
                "reply": f"Slot {booking_time} is already booked"
            }

        new_appointment = Appointment(
            name=name,
            phone=phone,
            service=service,
            date=booking_date,
            time=booking_time,
            status="confirmed"
        )

        db.add(new_appointment)
        db.commit()

        return {
            "reply": f"{service.title()} booked successfully for {name} on {booking_date} at {booking_time}"
        }

    return {
        "reply": "Sorry, I don't understand."
    }