from fastapi import BackgroundTasks, FastAPI
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
EVENT_CATEGORIES = {"movies", "music", "sports", "tech", "hackathons"}
EVENT_CATEGORY_LABELS = {
    "movies": "Movies",
    "music": "Music",
    "sports": "Sports",
    "tech": "Tech",
    "hackathons": "Hackathons",
}

# ================= DB =================
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="ROHITH@2006",
        database="event_db"
    )

def ensure_event_columns():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'events'
    """)
    columns = {row[0] for row in cursor.fetchall()}

    if "category" not in columns:
        cursor.execute(
            "ALTER TABLE events ADD COLUMN category VARCHAR(50) NOT NULL DEFAULT 'movies'"
        )
        db.commit()

    if "available_seats" not in columns:
        cursor.execute("ALTER TABLE events ADD COLUMN available_seats INT")
        db.commit()

    cursor.execute("""
        UPDATE events e
        SET available_seats = GREATEST(
            e.seats - (
                SELECT COALESCE(SUM(b.approved_seats), 0)
                FROM bookings b
                WHERE b.event_id = e.id AND b.status = 'approved'
            ),
            0
        )
    """)
    db.commit()

    db.close()

# ================= EMAIL =================
def send_email(to_email, subject, message):
    sender_email = "sqldbms7@gmail.com"
    app_password = "tazs aqsw saml fmyr"

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print("Email error:", e)
        return False

def get_event_category_label(category):
    category_id = (category or "movies").strip().lower()
    return EVENT_CATEGORY_LABELS.get(category_id, category_id.title())

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.on_event("startup")
def startup():
    ensure_event_columns()

def frontend_page(filename):
    return FileResponse(
        os.path.join(FRONTEND_DIR, filename),
        headers={"Cache-Control": "no-store"},
    )

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
    category: str

class Booking(BaseModel):
    user_email: EmailStr
    event_id: int
    seats: int

# ================= ROUTES =================
@app.get("/")
def home():
    return frontend_page("login.html")

@app.get("/register_page")
def register_page():
    return frontend_page("register.html")

@app.get("/events_page")
def events_page():
    return frontend_page("events.html")

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
    category = event.category.strip().lower()
    if category not in EVENT_CATEGORIES:
        return {"error": "Please select a valid event type"}
    if event.seats <= 0:
        return {"error": "Seats must be greater than 0"}

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO events (title, date, location, seats, category, available_seats) VALUES (%s,%s,%s,%s,%s,%s)",
        (event.title, event.date, event.location, event.seats, category, event.seats)
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
        COALESCE(e.category, 'movies') AS category,
        GREATEST(e.seats - COALESCE(e.available_seats, e.seats), 0) AS booked_seats,
        COALESCE(e.available_seats, e.seats) AS available_seats
    FROM events e
    ORDER BY e.date ASC
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

    cursor.execute("SELECT available_seats FROM events WHERE id=%s", (booking.event_id,))

    result = cursor.fetchone()
    if not result:
        db.close()
        return {"error": "Event not found"}

    available = result[0] or 0

    if booking.seats <= 0:
        db.close()
        return {"error": "Please enter valid number of seats"}

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

@app.get("/my_bookings")
def get_my_bookings(email: EmailStr):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT e.title, b.seats, b.approved_seats, b.status, b.booking_date
        FROM bookings b
        JOIN events e ON b.event_id = e.id
        WHERE b.user_email = %s
        ORDER BY b.booking_date DESC, b.id DESC
    """, (email.strip().lower(),))

    data = cursor.fetchall()
    db.close()
    return data

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
@app.get("/admin_stats")
def admin_stats():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            COUNT(*) AS total,
            COALESCE(SUM(status='approved'), 0) AS approved,
            COALESCE(SUM(status='pending'), 0) AS pending,
            COALESCE(SUM(status='rejected'), 0) AS rejected
        FROM bookings
    """)

    data = cursor.fetchone()
    db.close()
    return data

@app.put("/approve_booking/{booking_id}")
def approve_booking(booking_id: int, background_tasks: BackgroundTasks):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT b.*, e.title AS event_name, e.available_seats, COALESCE(e.category, 'movies') AS event_category
        FROM bookings b
        JOIN events e ON b.event_id = e.id
        WHERE b.id=%s
        FOR UPDATE
    """, (booking_id,))
    booking = cursor.fetchone()

    if not booking:
        db.close()
        return {"error": "Booking not found"}

    if booking["status"] != "pending":
        db.close()
        return {"error": "Booking already processed"}

    available = booking["available_seats"] or 0
    approved_seats = min(booking["seats"], available)

    rejected_seats = booking["seats"] - approved_seats
    available_after_approval = available - approved_seats
    status = "approved" if approved_seats > 0 else "rejected"

    cursor.execute(
        "UPDATE bookings SET approved_seats=%s, status=%s WHERE id=%s",
        (approved_seats, status, booking_id)
    )
    cursor.execute(
        "UPDATE events SET available_seats=%s WHERE id=%s",
        (available_after_approval, booking["event_id"])
    )

    db.commit()

    event_category_label = get_event_category_label(booking["event_category"])

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

    background_tasks.add_task(
        send_email,
        booking["user_email"],
        subject,
        f"""
Dear Guest,

Warm greetings from EventFlow.

Thank you for choosing EventFlow for your event experience. Your booking request for "{booking['event_name']}" has now been reviewed by our team.

Booking Status
--------------
Event: {booking['event_name']}
Event Type: {event_category_label}
Seats Requested: {booking['seats']}
Seats Confirmed: {approved_seats}
Seats Not Available: {rejected_seats}

{decision_note}

Please keep this confirmation for your records. Our team looks forward to giving you a smooth and well-managed event experience.

With regards,
Team Event Flow
EventFlow

Premium Event Booking Platform
"""
    )

    db.close()
    if available_after_approval == 0:
        return {"message": f"{approved_seats} approved, {rejected_seats} rejected. Event is sold out"}
    return {"message": f"{approved_seats} approved, {rejected_seats} rejected"}

@app.put("/reject_booking/{booking_id}")
def reject_booking(booking_id: int, background_tasks: BackgroundTasks):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT b.*, e.title AS event_name, COALESCE(e.category, 'movies') AS event_category
        FROM bookings b
        JOIN events e ON b.event_id = e.id
        WHERE b.id=%s
        FOR UPDATE
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
    event_category_label = get_event_category_label(booking["event_category"])

    background_tasks.add_task(
        send_email,
        booking["user_email"],
        "EventFlow - Booking Rejected",
        f"""
Dear Guest,

Warm greetings from EventFlow.

Thank you for showing interest in "{booking['event_name']}". After reviewing the current availability, we are sorry to inform you that your booking request could not be confirmed.

Booking Status
--------------
Event: {booking['event_name']}
Event Type: {event_category_label}
Seats Requested: {booking['seats']}
Seats Confirmed: 0
Seats Not Available: {booking['seats']}

This happened because the requested seats are no longer available. We appreciate your understanding and hope to welcome you to another EventFlow event soon.

With regards,
Team Event Flow
EventFlow

Premium Event Booking Platform
"""
    )

    db.close()
    return {"message": "Rejected"}
