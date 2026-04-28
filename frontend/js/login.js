function login() {
    let email = document.getElementById("email").value.trim();
    let password = document.getElementById("password").value;

    // =====================
    // VALIDATION
    // =====================
    if (!email.includes("@")) {
        alert("Invalid email");
        return;
    }

    if (password.length < 4) {
        alert("Password too short");
        return;
    }

    email = email.toLowerCase();

    // =====================
    // LOGIN REQUEST
    // =====================
    fetch("/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ email, password })
    })
    .then(res => res.json())
    .then(data => {


        if (data.message) {
            localStorage.setItem("email", email);
            localStorage.setItem("role", data.role);

            window.location.href = "/events_page";
        } else {
            alert(data.error);
        }
    })
    .catch(err => {
        console.log(err);
        alert("Server error");
    });
}

function clearLoginFields() {
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");

    if (emailInput) emailInput.value = "";
    if (passwordInput) passwordInput.value = "";
}

window.addEventListener("DOMContentLoaded", () => {
    clearLoginFields();
    setTimeout(clearLoginFields, 100);
});
