from fastapi import FastAPI, Body
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from datetime import date
import mysql.connector
import os
import smtplib
from email.mime.text import MIMEText

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

# ================= DB =================
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="ROHITH@2006",
        database="event_db"
    )

# ================= EMAIL =================
def send_email(to_email, subject, message):
    sender_email = "sqldbms7@gmail.com"
    app_password = "tazs aqsw saml fmyr"

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("Email error:", e)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ================= MODELS =================
class User(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginUser(BaseModel):
    email: EmailStr
    password: str

class Event(BaseModel):
    title: str
    date: date
    location: str
    seats: int

class Booking(BaseModel):
    user_email: EmailStr
    event_id: int
    seats: int

# ================= ROUTES =================
@app.get("/")
def home():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

@app.get("/register_page")
def register_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "register.html"))

@app.get("/events_page")
def events_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "events.html"))

# ================= AUTH =================
@app.post("/register")
def register(user: User):
    db = get_db()
    cursor = db.cursor()

    name = user.name.strip()
    email = user.email.strip().lower()
    password = user.password.strip()

    cursor.execute("SELECT * FROM users WHERE LOWER(TRIM(email))=%s", (email,))
    if cursor.fetchone():
        db.close()
        return {"error": "User already exists"}

    cursor.execute(
        "INSERT INTO users (name, email, password, role, phone) VALUES (%s,%s,%s,'user','')",
        (name, email, password)
    )

    db.commit()
    db.close()

    return {"message": "User registered successfully"}

@app.post("/login")
def login(user: LoginUser):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    email = user.email.strip().lower()
    password = user.password.strip()

    cursor.execute(
        "SELECT * FROM users WHERE LOWER(TRIM(email))=%s AND TRIM(password)=%s",
        (email, password)
    )

    result = cursor.fetchone()
    db.close()

    if result:
        return {"message": "Login success", "role": result["role"]}
    else:
        return {"error": "Invalid credentials"}

# ================= EVENTS =================
@app.post("/add_event")
def add_event(event: Event):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO events (title, date, location, seats) VALUES (%s,%s,%s,%s)",
        (event.title, event.date, event.location, event.seats)
    )

    db.commit()
    db.close()

    return {"message": "Event added"}

@app.get("/events")
def get_events():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    query = """
    SELECT 
        e.id,
        e.title,
        e.date,
        e.location,
        e.seats,
        IFNULL(SUM(CASE WHEN b.status='approved' THEN b.approved_seats ELSE 0 END),0) AS booked_seats,
        (e.seats - IFNULL(SUM(CASE WHEN b.status='approved' THEN b.approved_seats ELSE 0 END),0)) AS available_seats
    FROM events e
    LEFT JOIN bookings b ON e.id = b.event_id
    GROUP BY e.id
    """

    cursor.execute(query)
    data = cursor.fetchall()
    db.close()

    return data

@app.delete("/delete_event/{event_id}")
def delete_event(event_id: int):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM bookings WHERE event_id=%s", (event_id,))
    cursor.execute("DELETE FROM events WHERE id=%s", (event_id,))

    db.commit()
    deleted = cursor.rowcount
    db.close()

    if deleted:
        return {"message": "Event deleted"}
    return {"error": "Event not found"}

# ================= BOOKINGS =================
@app.post("/book_event")
def book_event(booking: Booking):
    db = get_db()
    cursor = db.cursor()
    user_email = booking.user_email.strip().lower()

    cursor.execute("""
        SELECT 
            e.seats - IFNULL(SUM(b.approved_seats),0)
        FROM events e
        LEFT JOIN bookings b ON e.id=b.event_id AND b.status='approved'
        WHERE e.id=%s
        GROUP BY e.id
    """, (booking.event_id,))

    result = cursor.fetchone()
    available = result[0] if result else 0

    if booking.seats > available:
        db.close()
        return {"error": f"Only {available} seats available"}

    cursor.execute(
        "INSERT INTO bookings (user_email, event_id, seats, status) VALUES (%s,%s,%s,'pending')",
        (user_email, booking.event_id, booking.seats)
    )

    db.commit()
    db.close()

    return {"message": "Booking pending"}

@app.get("/bookings")
def get_bookings():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT b.*, e.title AS event_name 
        FROM bookings b
        JOIN events e ON b.event_id = e.id
    """)

    data = cursor.fetchall()
    db.close()
    return data

# ================= ADMIN =================
@app.put("/approve_booking/{booking_id}")
def approve_booking(booking_id: int, approved_seats: int = Body(...)):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT b.*, e.title AS event_name, e.seats AS event_seats
        FROM bookings b
        JOIN events e ON b.event_id = e.id
        WHERE b.id=%s
    """, (booking_id,))
    booking = cursor.fetchone()

    if not booking:
        db.close()
        return {"error": "Booking not found"}

    if booking["status"] != "pending":
        db.close()
        return {"error": "Booking already processed"}

    if approved_seats < 0 or approved_seats > booking["seats"]:
        db.close()
        return {"error": "Approved seats must be between 0 and requested seats"}

    cursor.execute("""
        SELECT IFNULL(SUM(approved_seats), 0) AS booked_seats
        FROM bookings
        WHERE event_id=%s AND status='approved' AND id<>%s
    """, (booking["event_id"], booking_id))
    booked = cursor.fetchone()["booked_seats"]
    available = booking["event_seats"] - booked

    if approved_seats > available:
        db.close()
        return {"error": f"Only {available} seats available to approve"}

    rejected_seats = booking["seats"] - approved_seats
    available_after_approval = available - approved_seats
    status = "approved" if approved_seats > 0 else "rejected"

    cursor.execute(
        "UPDATE bookings SET approved_seats=%s, status=%s WHERE id=%s",
        (approved_seats, status, booking_id)
    )

    db.commit()

    subject = "EventFlow - Booking Approved"
    if rejected_seats:
        subject = "EventFlow - Booking Partially Approved"
    if approved_seats == 0:
        subject = "EventFlow - Booking Rejected"

    decision_note = "Your requested seats have been confirmed."
    if rejected_seats:
        decision_note = "We are pleased to confirm part of your request based on current seat availability."
    if approved_seats == 0:
        decision_note = "We regret that we could not confirm seats for this request because the event is currently at capacity."

    send_email(
        booking["user_email"],
        subject,
        f"""
Dear Guest,

Warm greetings from EventFlow.

Thank you for choosing EventFlow for your event experience. Your booking request for "{booking['event_name']}" has now been reviewed by our team.

Booking Status
--------------
Event: {booking['event_name']}
Seats Requested: {booking['seats']}
Seats Confirmed: {approved_seats}
Seats Not Available: {rejected_seats}

{decision_note}

Please keep this confirmation for your records. Our team looks forward to giving you a smooth and well-managed event experience.

With regards,
Team Rohith
EventFlow

Premium Event Booking Platform
"""
    )

    if available_after_approval == 0:
        cursor.execute("DELETE FROM bookings WHERE event_id=%s", (booking["event_id"],))
        cursor.execute("DELETE FROM events WHERE id=%s", (booking["event_id"],))
        db.commit()
        db.close()
        return {"message": f"{approved_seats} approved, {rejected_seats} rejected. Event is full and was deleted"}

    db.close()
    return {"message": f"{approved_seats} approved, {rejected_seats} rejected"}

@app.put("/reject_booking/{booking_id}")
def reject_booking(booking_id: int):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT b.*, e.title AS event_name
        FROM bookings b
        JOIN events e ON b.event_id = e.id
        WHERE b.id=%s
    """, (booking_id,))
    booking = cursor.fetchone()

    if not booking:
        db.close()
        return {"error": "Booking not found"}

    if booking["status"] != "pending":
        db.close()
        return {"error": "Booking already processed"}

    cursor.execute(
        "UPDATE bookings SET approved_seats=0, status='rejected' WHERE id=%s",
        (booking_id,)
    )

    db.commit()

    send_email(
        booking["user_email"],
        "EventFlow - Booking Rejected",
        f"""
Dear Guest,

Warm greetings from EventFlow.

Thank you for showing interest in "{booking['event_name']}". After reviewing the current availability, we are sorry to inform you that your booking request could not be confirmed.

Booking Status
--------------
Event: {booking['event_name']}
Seats Requested: {booking['seats']}
Seats Confirmed: 0
Seats Not Available: {booking['seats']}

This happened because the requested seats are no longer available. We appreciate your understanding and hope to welcome you to another EventFlow event soon.

With regards,
Team Rohith
EventFlow

Premium Event Booking Platform
"""
    )

    db.close()
    return {"message": "Rejected"}
