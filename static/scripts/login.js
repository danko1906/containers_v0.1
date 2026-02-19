const BASE_URL = window.APP_CONFIG?.BASE_URL || "http://127.0.0.1:5001";

// Utility function to get the current access token
function getAccessToken() {
    return localStorage.getItem("access_token");
}

// Utility function to get the current refresh token
function getRefreshToken() {
    return localStorage.getItem("refresh_token");
}

// Function to refresh the access token using the refresh token
async function refreshAccessToken() {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
        return null;
    }

    const response = await fetch(`${BASE_URL}/api/auth/refresh`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            refresh_token: refreshToken,
        }),
    });

    if (response.ok) {
        const data = await response.json();
        const newAccessToken = data.access_token;
        localStorage.setItem("access_token", newAccessToken); // Store new access token
        return newAccessToken;
    } else {
        console.error("Failed to refresh access token");
        return null;
    }
}

// Function to handle authorization (login)
document.getElementById("loginForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    const login = document.getElementById("login").value;
    const password = document.getElementById("password").value;

    const response = await fetch(`${BASE_URL}/api/auth/token`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            login: login,
            password: password,
        }),
    });

    if (response.ok) {
        const data = await response.json();
        const token = data.access_token;
        const refreshToken = data.refresh_token;

        // Store the access and refresh tokens in localStorage
        localStorage.setItem("access_token", token);
        localStorage.setItem("refresh_token", refreshToken);

        // Redirect to the containers page after successful login
        window.location.href = "/containers/container.html";
    } else {
        const error = await response.json();
        document.getElementById("loginErrorMessage").innerText = error.detail || "Ошибка авторизации";
    }
});

// Function to handle registration
document.getElementById("registerForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    const login = document.getElementById("registerLogin").value;
    const password = document.getElementById("registerPassword").value;

    const response = await fetch(`${BASE_URL}/api/auth/register`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            login: login,
            password: password,
        }),
    });

    if (response.ok) {
        // Redirect to the login page after successful registration
        window.location.href = "/login.html";
    } else {
        const error = await response.json();
        document.getElementById("registerErrorMessage").innerText = error.detail || "Ошибка регистрации";
    }
});

// Function to check if the access token is still valid
async function checkTokenValidity() {
    const accessToken = getAccessToken();

    if (!accessToken) {
        return false;
    }

    // Try to make a request with the current access token
    const response = await fetch(`${BASE_URL}/api/protected`, {
        method: "GET",
        headers: {
            "Authorization": `Bearer ${accessToken}`,
        },
    });

    if (response.ok) {
        return true; // Token is valid
    } else if (response.status === 401) {
        // Token is expired, try refreshing it
        const newAccessToken = await refreshAccessToken();
        return newAccessToken !== null;
    }

    return false; // Any other error
}

// Example usage of checkTokenValidity to refresh token if expired
async function secureRequest() {
    const isValid = await checkTokenValidity();
    if (isValid) {
        const accessToken = getAccessToken();
        // Proceed with the API call using the valid access token
        console.log("Access token is valid, proceed with the request");
    } else {
        console.error("Access token is invalid or expired");
    }
}
