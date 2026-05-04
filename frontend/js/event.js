// =====================
// GLOBAL
// =====================
const role = localStorage.getItem("role");
const email = localStorage.getItem("email");
let activeCategory = "all";

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    }[char]));
}

const eventCategories = [
    {
        id: "all",
        label: "All",
        icon: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" /></svg>`
    },
    {
        id: "movies",
        label: "Movies",
        icon: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4v16m10-16v16M3 8h18M3 16h18M5 4h14a2 2 0 012 2v12a2 2 0 01-2 2H5a2 2 0 01-2-2V6a2 2 0 012-2z" /></svg>`
    },
    {
        id: "music",
        label: "Music",
        icon: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-2v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-2c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z" /></svg>`
    },
    {
        id: "sports",
        label: "Sports",
        icon: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><circle cx="12" cy="12" r="9" stroke-width="2" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 9c4 1 10 1 14 0M5 15c4-1 10-1 14 0M12 3c2 4 2 14 0 18" /></svg>`
    },
    {
        id: "tech",
        label: "Tech",
        icon: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><rect x="5" y="4" width="14" height="16" rx="2" stroke-width="2" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 9h6M9 13h6M12 17h.01" /></svg>`
    },
    {
        id: "hackathons",
        label: "Hackathons",
        icon: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l-3 3 3 3M16 9l3 3-3 3M14 5l-4 14" /></svg>`
    }
];

function getCategory(categoryId) {
    return eventCategories.find(category => category.id === categoryId) || eventCategories[1];
}

function renderCategoryFilter() {
    const filter = document.getElementById("categoryFilter");
    if (!filter) return;

    filter.innerHTML = eventCategories.map(category => `
        <button class="category-chip ${activeCategory === category.id ? "active" : ""}" onclick="setCategory('${category.id}')">
            ${category.icon}
            <span>${category.label}</span>
        </button>
    `).join("");
}

function setCategory(categoryId) {
    activeCategory = categoryId;
    renderCategoryFilter();
    loadEvents();
}

// =====================
// LOAD EVENTS
// =====================
function loadEvents() {
    if (!role || !email) {
        window.location.href = "/";
        return;
    }

    // Show / Hide Admin Panel
    const adminSection = document.getElementById("adminSection");
    const userBookingsSection = document.getElementById("userBookingsSection");

    if (role === "admin") {
        adminSection.style.display = "flex";
        userBookingsSection.style.display = "none";
    } else {
        adminSection.style.display = "none";
        userBookingsSection.style.display = "block";
    }

    fetch("/events")
    .then(res => res.json())
    .then(eventsData => {

        let html = "";
        const visibleEvents = activeCategory === "all"
            ? eventsData
            : eventsData.filter(e => (e.category || "movies") === activeCategory);

        visibleEvents.forEach(e => {
            const category = getCategory(e.category || "movies");

            // Format date nicely
            const eventDate = new Date(e.date).toLocaleDateString('en-US', {
                weekday: 'short',
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });

            html += `
            <div class="event-card">
                <div class="event-category-badge">
                    ${category.icon}
                    <span>${category.label}</span>
                </div>
                <h3>${escapeHtml(e.title)}</h3>
                
                <div class="event-info">
                    <div class="event-info-item">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        <span>${escapeHtml(e.location)}</span>
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
                        Only few seats left
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
            html || '<p style="text-align: center; color: var(--text-muted); grid-column: 1/-1;">No events available in this section</p>';

        // Load admin panels
        if (role === "admin") {
            loadAdminStats();
            loadBookingRequests();
        } else {
            loadMyBookings();
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

            const seatsToApproveMax = Math.min(b.seats, Number(b.available_seats || 0));
            const approvePlaceholder = seatsToApproveMax > 0 ? `0 - ${seatsToApproveMax}` : "0";

            bookingHTML += `
            <div class="booking-request-card">
                <div class="booking-request-info">
                    <p><strong>User:</strong> ${escapeHtml(b.user_email)}</p>
                    <p><strong>Event:</strong> ${escapeHtml(b.event_name)}</p>
                    <p><strong>Seats Requested:</strong> ${b.seats}</p>
                    <p><strong>Available Seats:</strong> ${b.available_seats ?? 0}</p>
                    <p><strong>Approval:</strong> Enter how many seats to confirm; remaining seats will be rejected automatically.</p>
                </div>
                <div class="seat-decision-grid">
                    <label for="approve_${b.id}">Seats to approve</label>
                    <input type="number" id="approve_${b.id}" min="0" max="${seatsToApproveMax}" placeholder="${approvePlaceholder}">
                </div>
                <div class="booking-actions">
                    <button class="btn btn-success" onclick="approve(${b.id})">
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
// ADMIN STATS
// =====================
function loadAdminStats() {
    if (role !== "admin") return;

    fetch("/admin_stats")
    .then(res => res.json())
    .then(stats => {
        const adminStats = document.getElementById("adminStats");
        if (!adminStats) return;

        adminStats.innerHTML = `
            <div class="stat-box"><span>Total</span><strong>${stats.total || 0}</strong></div>
            <div class="stat-box approved"><span>Approved</span><strong>${stats.approved || 0}</strong></div>
            <div class="stat-box pending"><span>Pending</span><strong>${stats.pending || 0}</strong></div>
            <div class="stat-box rejected"><span>Rejected</span><strong>${stats.rejected || 0}</strong></div>
        `;
    })
    .catch(err => console.log("Error loading admin stats:", err));
}

// =====================
// MY BOOKINGS (USER)
// =====================
function loadMyBookings() {
    if (role !== "user" || !email) return;

    fetch(`/my_bookings?email=${encodeURIComponent(email)}`)
    .then(res => res.json())
    .then(bookings => {
        const myBookings = document.getElementById("myBookings");
        if (!myBookings) return;

        if (!bookings.length) {
            myBookings.innerHTML = '<p class="no-requests">No bookings yet</p>';
            return;
        }

        myBookings.innerHTML = bookings.map(booking => {
            const bookingDate = booking.booking_date
                ? new Date(booking.booking_date).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                })
                : "Not available";

            return `
                <div class="booking-history-card">
                    <div>
                        <h3>${escapeHtml(booking.title)}</h3>
                        <p>Date: ${bookingDate}</p>
                    </div>
                    <div class="booking-history-details">
                        <span>Requested: <strong>${booking.seats}</strong></span>
                        <span>Approved: <strong>${booking.approved_seats || 0}</strong></span>
                        <span class="status-pill ${booking.status}">${booking.status}</span>
                    </div>
                </div>
            `;
        }).join("");
    })
    .catch(err => console.log("Error loading booking history:", err));
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
        loadMyBookings();
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
    let category = document.getElementById("category").value;

    if (!category || !title || !date || !location || !seats) {
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
            seats: parseInt(seats),
            category
        })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message || data.error);
        if (data.error) return;
        // Clear form
        document.getElementById("title").value = "";
        document.getElementById("date").value = "";
        document.getElementById("location").value = "";
        document.getElementById("seats").value = "";
        document.getElementById("category").value = "";
        loadEvents();
        loadAdminStats();
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
        loadAdminStats();
    })
    .catch(err => {
        console.error(err);
        alert("Server error");
    });
}

// =====================
// APPROVE BOOKING
// =====================
function approve(id) {
    const input = document.getElementById(`approve_${id}`);
    let body = {};

    if (input && input.value !== "") {
        const approvedSeats = parseInt(input.value, 10);
        if (Number.isNaN(approvedSeats) || approvedSeats < 0) {
            alert("Please enter a valid number of seats to approve.");
            return;
        }
        body.approved_seats = approvedSeats;
    }

    fetch(`/approve_booking/${id}`, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body)
    })
    .then(async res => {
        const data = await res.json();
        if (!res.ok) {
            const errorDetail = data.detail ? (Array.isArray(data.detail) ? data.detail.map(d => d.msg).join('; ') : data.detail) : data.message || data.error;
            throw new Error(errorDetail || 'Approval failed');
        }
        return data;
    })
    .then(data => {
        alert(data.message || 'Booking processed');
        loadEvents();
        loadAdminStats();
    })
    .catch(err => {
        console.error(err);
        alert(err.message || 'Server error');
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
        loadAdminStats();
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
document.addEventListener("DOMContentLoaded", () => {
    renderCategoryFilter();
    loadEvents();
});
