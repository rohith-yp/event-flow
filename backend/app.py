from fastapi import BackgroundTasks, FastAPI, HTTPException, Body
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
import mysql.connector
import os
import smtplib
from email.mime.text import MIMEText
from contextlib import contextmanager
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
@contextmanager
def get_db_connection():
    """Context manager for database connections with proper error handling"""
    db = None
    try:
        db = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "ROHITH@2006"),
            database=os.getenv("DB_NAME", "event_db"),
            autocommit=False  # We'll handle transactions manually
        )
        yield db
    except mysql.connector.Error as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")
    finally:
        if db:
            db.close()

def ensure_event_columns():
    """Ensure required columns exist in events table"""
    try:
        with get_db_connection() as db:
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
                logger.info("Added category column to events table")

            if "available_seats" not in columns:
                cursor.execute("ALTER TABLE events ADD COLUMN available_seats INT")
                db.commit()
                logger.info("Added available_seats column to events table")

            # Update available seats based on approved bookings
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
            logger.info("Updated available seats for all events")

    except Exception as e:
        logger.error(f"Error ensuring event columns: {e}")
        raise

# ================= EMAIL =================
def send_email(to_email, subject, message):
    """Send email with proper error handling"""
    # Use environment variables for security (fallback to hardcoded for now)
    sender_email = os.getenv("EMAIL_USER", "sqldbms7@gmail.com")
    app_password = os.getenv("EMAIL_PASSWORD", "tazs aqsw saml fmyr")

    if not sender_email or not app_password:
        logger.error("Email credentials not configured")
        return False

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.send_message(msg)
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Email error: {e}")
        return False

def get_event_category_label(category):
    category_id = (category or "movies").strip().lower()
    return EVENT_CATEGORY_LABELS.get(category_id, category_id.title())

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# Use lifespan events instead of deprecated on_event
@app.on_event("startup")
def startup():
    """Initialize database on startup"""
    try:
        ensure_event_columns()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

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

class ApproveBookingRequest(BaseModel):
    approved_seats: Optional[int] = None

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
    """Register a new user"""
    try:
        name = user.name.strip()
        email = user.email.strip().lower()
        password = user.password.strip()

        if len(name) < 2:
            raise HTTPException(status_code=400, detail="Name must be at least 2 characters")
        if len(password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

        with get_db_connection() as db:
            cursor = db.cursor()

            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE LOWER(TRIM(email))=%s", (email,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="User already exists")

            # Insert new user
            cursor.execute(
                "INSERT INTO users (name, email, password, role, phone) VALUES (%s,%s,%s,'user','')",
                (name, email, password)
            )
            db.commit()

        logger.info(f"User registered successfully: {email}")
        return {"message": "User registered successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/login")
def login(user: LoginUser):
    """Authenticate user login"""
    try:
        email = user.email.strip().lower()
        password = user.password.strip()

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required")

        with get_db_connection() as db:
            cursor = db.cursor(dictionary=True)

            cursor.execute(
                "SELECT id, name, email, role FROM users WHERE LOWER(TRIM(email))=%s AND TRIM(password)=%s",
                (email, password)
            )

            result = cursor.fetchone()

        if result:
            logger.info(f"User logged in successfully: {email}")
            return {"message": "Login success", "role": result["role"]}
        else:
            logger.warning(f"Failed login attempt for: {email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

# ================= EVENTS =================
@app.post("/add_event")
def add_event(event: Event):
    """Add a new event"""
    try:
        category = event.category.strip().lower()
        if category not in EVENT_CATEGORIES:
            raise HTTPException(status_code=400, detail="Please select a valid event type")

        if event.seats <= 0:
            raise HTTPException(status_code=400, detail="Seats must be greater than 0")

        if len(event.title.strip()) < 3:
            raise HTTPException(status_code=400, detail="Event title must be at least 3 characters")

        if len(event.location.strip()) < 3:
            raise HTTPException(status_code=400, detail="Location must be at least 3 characters")

        if event.date <= date.today():
            raise HTTPException(status_code=400, detail="Event date must be in the future")

        with get_db_connection() as db:
            cursor = db.cursor()

            cursor.execute(
                "INSERT INTO events (title, date, location, seats, category, available_seats) VALUES (%s,%s,%s,%s,%s,%s)",
                (event.title.strip(), event.date, event.location.strip(), event.seats, category, event.seats)
            )
            db.commit()

        logger.info(f"Event added successfully: {event.title}")
        return {"message": "Event added"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add event error: {e}")
        raise HTTPException(status_code=500, detail="Failed to add event")

@app.get("/events")
def get_events():
    """Get all events with booking information"""
    try:
        with get_db_connection() as db:
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

        return data

    except Exception as e:
        logger.error(f"Get events error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load events")

@app.delete("/delete_event/{event_id}")
def delete_event(event_id: int):
    """Delete an event and all its bookings"""
    try:
        with get_db_connection() as db:
            cursor = db.cursor()

            # Delete bookings first (foreign key constraint)
            cursor.execute("DELETE FROM bookings WHERE event_id=%s", (event_id,))
            bookings_deleted = cursor.rowcount

            # Delete the event
            cursor.execute("DELETE FROM events WHERE id=%s", (event_id,))
            events_deleted = cursor.rowcount

            if events_deleted == 0:
                raise HTTPException(status_code=404, detail="Event not found")

            db.commit()

        logger.info(f"Event deleted: ID {event_id}, {bookings_deleted} bookings removed")
        return {"message": "Event deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete event error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete event")

# ================= BOOKINGS =================
@app.post("/book_event")
def book_event(booking: Booking):
    """Book seats for an event"""
    try:
        user_email = booking.user_email.strip().lower()
        event_id = booking.event_id
        seats_requested = booking.seats

        if seats_requested <= 0:
            raise HTTPException(status_code=400, detail="Please enter valid number of seats")

        if seats_requested > 100:
            raise HTTPException(status_code=400, detail="Cannot book more than 100 seats at once")

        with get_db_connection() as db:
            cursor = db.cursor()

            # Check if event exists and get available seats
            cursor.execute("SELECT available_seats, title FROM events WHERE id=%s", (event_id,))
            event_result = cursor.fetchone()

            if not event_result:
                raise HTTPException(status_code=404, detail="Event not found")

            available = event_result[0] or 0

            if seats_requested > available:
                raise HTTPException(
                    status_code=400,
                    detail=f"Only {available} seats available"
                )

            # Insert booking
            cursor.execute(
                "INSERT INTO bookings (user_email, event_id, seats, status) VALUES (%s,%s,%s,'pending')",
                (user_email, event_id, seats_requested)
            )
            db.commit()

        logger.info(f"Booking created: {user_email} booked {seats_requested} seats for event {event_id}")
        return {"message": "Booking pending"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Book event error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create booking")

@app.get("/my_bookings")
def get_my_bookings(email: EmailStr):
    """Get user's booking history"""
    try:
        user_email = email.strip().lower()

        with get_db_connection() as db:
            cursor = db.cursor(dictionary=True)

            cursor.execute("""
                SELECT e.title, b.seats, b.approved_seats, b.status, b.booking_date
                FROM bookings b
                JOIN events e ON b.event_id = e.id
                WHERE b.user_email = %s
                ORDER BY b.booking_date DESC, b.id DESC
            """, (user_email,))

            data = cursor.fetchall()

        return data

    except Exception as e:
        logger.error(f"Get my bookings error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load bookings")

@app.get("/bookings")
def get_bookings():
    """Get all bookings for admin"""
    try:
        with get_db_connection() as db:
            cursor = db.cursor(dictionary=True)

            cursor.execute("""
                SELECT b.*, e.title AS event_name, COALESCE(e.available_seats, e.seats) AS available_seats
                FROM bookings b
                JOIN events e ON b.event_id = e.id
                ORDER BY b.booking_date DESC
            """)

            data = cursor.fetchall()

        return data

    except Exception as e:
        logger.error(f"Get bookings error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load bookings")

# ================= ADMIN =================
@app.get("/admin_stats")
def admin_stats():
    """Get admin dashboard statistics"""
    try:
        with get_db_connection() as db:
            cursor = db.cursor(dictionary=True)

            cursor.execute("""
                SELECT 
                    COUNT(*) AS total,
                    COALESCE(SUM(CASE WHEN status='approved' THEN 1 END), 0) AS approved,
                    COALESCE(SUM(CASE WHEN status='pending' THEN 1 END), 0) AS pending,
                    COALESCE(SUM(CASE WHEN status='rejected' THEN 1 END), 0) AS rejected
                FROM bookings
            """)

            data = cursor.fetchone()

        return data

    except Exception as e:
        logger.error(f"Admin stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load statistics")

@app.put("/approve_booking/{booking_id}")
def approve_booking(
    booking_id: int,
    background_tasks: BackgroundTasks,
    payload: ApproveBookingRequest
):
    """Approve a booking request"""
    try:
        with get_db_connection() as db:
            cursor = db.cursor(dictionary=True)

            # Lock the booking and event for update to prevent race conditions
            cursor.execute("""
                SELECT b.*, e.title AS event_name, e.available_seats, COALESCE(e.category, 'movies') AS event_category
                FROM bookings b
                JOIN events e ON b.event_id = e.id
                WHERE b.id=%s
                FOR UPDATE
            """, (booking_id,))
            booking = cursor.fetchone()

            if not booking:
                raise HTTPException(status_code=404, detail="Booking not found")

            if booking["status"] != "pending":
                raise HTTPException(status_code=400, detail="Booking already processed")

            available = booking["available_seats"] or 0
            requested = booking["seats"]
            approved_seats = payload.approved_seats

            if approved_seats is None:
                approved_seats = min(requested, available)

            if approved_seats < 0:
                raise HTTPException(status_code=400, detail="Approved seats must be zero or greater")

            if approved_seats > requested:
                raise HTTPException(status_code=400, detail="Approved seats cannot exceed requested seats")

            if approved_seats > available:
                raise HTTPException(status_code=400, detail=f"Only {available} seats are available")

            if approved_seats == 0:
                cursor.execute(
                    "UPDATE bookings SET approved_seats=0, status='rejected' WHERE id=%s",
                    (booking_id,)
                )
                db.commit()
                return {"message": "Rejected - No seats approved"}

            rejected_seats = requested - approved_seats
            available_after_approval = available - approved_seats
            status = "approved"

            cursor.execute(
                "UPDATE bookings SET approved_seats=%s, status=%s WHERE id=%s",
                (approved_seats, status, booking_id)
            )

            cursor.execute(
                "UPDATE events SET available_seats=%s WHERE id=%s",
                (available_after_approval, booking["event_id"])
            )

            db.commit()

            # Send email in background
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

        logger.info(f"Booking {booking_id} processed: {approved_seats} approved, {rejected_seats} rejected")
        if available_after_approval == 0:
            return {"message": f"{approved_seats} approved, {rejected_seats} rejected. Event is sold out"}
        return {"message": f"{approved_seats} approved, {rejected_seats} rejected"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approve booking error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process booking")

@app.put("/reject_booking/{booking_id}")
def reject_booking(booking_id: int, background_tasks: BackgroundTasks):
    """Reject a booking request"""
    try:
        with get_db_connection() as db:
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
                raise HTTPException(status_code=404, detail="Booking not found")

            if booking["status"] != "pending":
                raise HTTPException(status_code=400, detail="Booking already processed")

            cursor.execute(
                "UPDATE bookings SET approved_seats=0, status='rejected' WHERE id=%s",
                (booking_id,)
            )
            db.commit()

            # Send rejection email
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

        logger.info(f"Booking {booking_id} rejected")
        return {"message": "Rejected"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reject booking error: {e}")
        raise HTTPException(status_code=500, detail="Failed to reject booking")
