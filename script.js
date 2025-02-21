document.addEventListener("DOMContentLoaded", function () {
    console.log("Page Loaded!");

    // Smooth scrolling for navigation
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener("click", function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute("href")).scrollIntoView({
                behavior: "smooth"
            });
        });
    });

    // Handle Login Form
    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        loginForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            let email = document.getElementById("loginEmail").value;
            let password = document.getElementById("loginPassword").value;

            if (!email || !password) {
                alert("Please enter all fields!");
                return;
            }

            // Send login request to backend
            try {
                let response = await fetch("/api/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password })
                });

                let data = await response.json();
                if (data.success) {
                    localStorage.setItem("token", data.token); // Store token
                    alert("Login successful!");
                    window.location.href = "dashboard.html";
                } else {
                    alert(data.message);
                }
            } catch (error) {
                console.error("Login Error:", error);
                alert("Something went wrong. Try again!");
            }
        });
    }

    // Handle Signup Form
    const signupForm = document.getElementById("signupForm");
    if (signupForm) {
        signupForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            let name = document.getElementById("signupName").value;
            let email = document.getElementById("signupEmail").value;
            let password = document.getElementById("signupPassword").value;

            if (!name || !email || !password) {
                alert("Please fill in all fields!");
                return;
            }

            // Send signup request to backend
            try {
                let response = await fetch("/api/signup", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ name, email, password })
                });

                let data = await response.json();
                if (data.success) {
                    alert("Signup successful! You can now log in.");
                    window.location.href = "login.html"; // Redirect to login
                } else {
                    alert(data.message);
                }
            } catch (error) {
                console.error("Signup Error:", error);
                alert("Something went wrong. Try again!");
            }
        });
    }
});
