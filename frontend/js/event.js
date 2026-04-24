// =====================
// GLOBAL
// =====================
const role = localStorage.getItem("role");
const email = localStorage.getItem("email");

// =====================
// LOAD EVENTS
// =====================
function loadEvents() {

    // Show / Hide Admin Panel
    const adminSection = document.getElementById("adminSection");

    if (role === "admin") {
        adminSection.style.display = "flex";
    } else {
        adminSection.style.display = "none";
    }

    fetch("/events")
    .then(res => res.json())
    .then(eventsData => {

        let html = "";

        eventsData.forEach(e => {

            // Format date nicely
            const eventDate = new Date(e.date).toLocaleDateString('en-US', {
                weekday: 'short',
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });

            html += `
            <div class="event-card">
                <h3>${e.title}</h3>
                
                <div class="event-info">
                    <div class="event-info-item">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        <span>${e.location}</span>
                    </div>
                    <div class="event-info-item">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        <span>${eventDate}</span>
                    </div>
                </div>

                <div class="seats-info">
                    <div class="seat-stat">
                        <div class="seat-stat-label">Total</div>
                        <div class="seat-stat-value">${e.seats}</div>
                    </div>
                    <div class="seat-stat">
                        <div class="seat-stat-label">Booked</div>
                        <div class="seat-stat-value">${e.booked_seats}</div>
                    </div>
                    <div class="seat-stat">
                        <div class="seat-stat-label">Available</div>
                        <div class="seat-stat-value available">${e.available_seats}</div>
                    </div>
                </div>

                ${e.available_seats <= 3 && e.available_seats > 0 ? `
                    <div class="low-seats-warning">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="20" height="20">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        Only ${e.available_seats} seats left!
                    </div>
                ` : ""}

                ${e.available_seats === 0 ? `
                    <div class="sold-out-badge">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="20" height="20" style="display: inline; vertical-align: middle; margin-right: 8px;">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                        </svg>
                        Sold Out
                    </div>
                ` : ""}

                ${role === "user" && e.available_seats > 0 ? `
                    <div class="booking-section">
                        <input type="number" id="seat_${e.id}" min="1" max="${e.available_seats}" placeholder="Number of seats">
                        <button class="btn btn-primary" onclick="book(${e.id})">Book Now</button>
                    </div>
                ` : ""}

                ${role === "admin" ? `
                    <button class="btn delete-btn" onclick="deleteEvent(${e.id})">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="18" height="18">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                        Delete Event
                    </button>
                ` : ""}
            </div>`;
        });

        document.getElementById("events").innerHTML =
            html || '<p style="text-align: center; color: var(--text-muted); grid-column: 1/-1;">No events available</p>';

        // Load admin panels
        if (role === "admin") {
            loadBookingRequests();
        }

    })
    .catch(err => console.log("Error loading events:", err));
}

// =====================
// BOOKING REQUESTS (ADMIN)
// =====================
function loadBookingRequests() {

    if (role !== "admin") return;

    fetch("/bookings")
    .then(res => res.json())
    .then(data => {

        let bookingHTML = "";
        let hasData = false;

        data.forEach(b => {

            if (b.status !== "pending") return;

            hasData = true;

            bookingHTML += `
            <div class="booking-request-card">
                <div class="booking-request-info">
                    <p><strong>User:</strong> ${b.user_email}</p>
                    <p><strong>Event:</strong> ${b.event_name}</p>
                    <p><strong>Seats:</strong> ${b.seats}</p>
                </div>
                <div class="seat-decision-grid">
                    <label>
                        <span>Approve</span>
                        <input type="number" id="approve_${b.id}" min="0" max="${b.seats}" value="${b.seats}" oninput="syncSeatDecision(${b.id}, ${b.seats}, 'approve')">
                    </label>
                    <label>
                        <span>Reject</span>
                        <input type="number" id="reject_${b.id}" min="0" max="${b.seats}" value="0" oninput="syncSeatDecision(${b.id}, ${b.seats}, 'reject')">
                    </label>
                </div>
                <div class="booking-actions">
                    <button class="btn btn-success" onclick="approve(${b.id}, ${b.seats})">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="16" height="16">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        Save
                    </button>
                    <button class="btn btn-danger" onclick="reject(${b.id})">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="16" height="16">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                        Reject
                    </button>
                </div>
            </div>`;
        });

        document.getElementById("bookingBox").innerHTML =
            hasData ? bookingHTML : '<p class="no-requests">No pending requests</p>';
    });
}

// =====================
// SEAT DECISION SYNC
// =====================
function syncSeatDecision(id, requestedSeats, changedField) {
    const approveInput = document.getElementById(`approve_${id}`);
    const rejectInput = document.getElementById(`reject_${id}`);

    let changedValue = parseInt(changedField === "approve" ? approveInput.value : rejectInput.value);
    if (Number.isNaN(changedValue)) changedValue = 0;
    changedValue = Math.max(0, Math.min(requestedSeats, changedValue));

    if (changedField === "approve") {
        approveInput.value = changedValue;
        rejectInput.value = requestedSeats - changedValue;
    } else {
        rejectInput.value = changedValue;
        approveInput.value = requestedSeats - changedValue;
    }
}

// =====================
// BOOK EVENT
// =====================
function book(id) {
    let seats = document.getElementById(`seat_${id}`).value;

    if (!seats || seats <= 0) {
        alert("Please enter valid number of seats");
        return;
    }

    fetch("/book_event", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            user_email: email,
            event_id: id,
            seats: parseInt(seats)
        })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message || data.error);
        loadEvents();
    })
    .catch(err => {
        console.error(err);
        alert("Server error");
    });
}

// =====================
// ADD EVENT
// =====================
function addEvent() {

    let title = document.getElementById("title").value;
    let date = document.getElementById("date").value;
    let location = document.getElementById("location").value;
    let seats = document.getElementById("seats").value;

    if (!title || !date || !location || !seats) {
        alert("Please fill all fields");
        return;
    }

    fetch("/add_event", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            title,
            date,
            location,
            seats: parseInt(seats)
        })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
        // Clear form
        document.getElementById("title").value = "";
        document.getElementById("date").value = "";
        document.getElementById("location").value = "";
        document.getElementById("seats").value = "";
        loadEvents();
    })
    .catch(err => {
        console.error(err);
        alert("Server error");
    });
}

// =====================
// DELETE EVENT
// =====================
function deleteEvent(id) {
    if (!confirm("Are you sure you want to delete this event?")) return;

    fetch(`/delete_event/${id}`, {
        method: "DELETE"
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message || data.error);
        loadEvents();
    })
    .catch(err => {
        console.error(err);
        alert("Server error");
    });
}

// =====================
// APPROVE BOOKING
// =====================
function approve(id, requestedSeats) {
    const approvedSeats = parseInt(document.getElementById(`approve_${id}`).value);

    if (Number.isNaN(approvedSeats) || approvedSeats < 0 || approvedSeats > requestedSeats) {
        alert("Please enter a valid approved seat count");
        return;
    }

    if (approvedSeats === 0) {
        reject(id);
        return;
    }

    fetch(`/approve_booking/${id}`, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(approvedSeats)
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message || data.error);
        loadEvents();
    })
    .catch(err => {
        console.error(err);
        alert("Server error");
    });
}

// =====================
// REJECT BOOKING
// =====================
function reject(id) {
    fetch(`/reject_booking/${id}`, {
        method: "PUT"
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message || data.error);
        loadEvents();
    })
    .catch(err => {
        console.error(err);
        alert("Server error");
    });
}

// =====================
// LOGOUT
// =====================
function logout() {
    localStorage.removeItem("email");
    localStorage.removeItem("role");
    window.location.href = "/";
}

// =====================
// INIT
// =====================
document.addEventListener("DOMContentLoaded", loadEvents);
