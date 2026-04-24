function register() {
    let name = document.getElementById("name").value.trim();
    let email = document.getElementById("email").value.trim().toLowerCase();
    let password = document.getElementById("password").value.trim();
    let confirmPassword = document.getElementById("confirmPassword").value.trim();

    clearRegisterErrors();
    let isValid = true;

    if (name.length < 2) {
        showRegisterError("nameError", "Enter at least 2 characters for your name.");
        isValid = false;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        showRegisterError("emailError", "Enter a valid email address.");
        isValid = false;
    }

    if (password.length < 6) {
        showRegisterError("passwordError", "Password must be at least 6 characters.");
        isValid = false;
    }

    if (password !== confirmPassword) {
        showRegisterError("confirmPasswordError", "Passwords do not match.");
        isValid = false;
    }

    if (!isValid) {
        return;
    }

    fetch("/register", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ name, email, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.message) {
            alert(data.message);
            window.location.href = "/";
        } else {
            alert(data.error || "Registration failed");
        }
    })
    .catch(err => {
        console.log("ERROR:", err);
        alert("Server error");
    });
}

function showRegisterError(id, message) {
    document.getElementById(id).textContent = message;
}

function clearRegisterErrors() {
    ["nameError", "emailError", "passwordError", "confirmPasswordError"].forEach(id => {
        document.getElementById(id).textContent = "";
    });
}
