// Smart API URL – works on localhost AND from LAN
const API = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
  ? "http://localhost:8000"
  : `http://${window.location.hostname}:8000`;

let token = localStorage.getItem("token");

function showApp() {
  document.getElementById("auth").classList.add("hidden");
  document.getElementById("app").classList.remove("hidden");
  loadPasswords();
}

function showAuth() {
  document.getElementById("app").classList.add("hidden");
  document.getElementById("auth").classList.remove("hidden");
  document.getElementById("list").innerHTML = "";
  update2FAField();
}

function update2FAField() {
  const field = document.getElementById("totp_code");
  if (localStorage.getItem("2fa_enabled") === "true") {
    field.style.display = "block";
  } else {
    field.style.display = "none";
  }
}

// Check token on load
async function checkToken() {
  if (!token) return showAuth();
  const res = await fetch(`${API}/passwords`, {
    headers: { "Authorization": `Bearer ${token}` }
  });
  if (res.ok) {
    showApp();
  } else {
    localStorage.removeItem("token");
    token = null;
    showAuth();
  }
}
checkToken();

// LOGIN
document.getElementById("login").onclick = async () => {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const totp_code = document.getElementById("totp_code").value.trim();

  const body = { email, password };
  if (totp_code) body.totp_code = totp_code;

  const res = await fetch(`${API}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const data = await res.json();

  if (data.access_token) {
    token = data.access_token;
    localStorage.setItem("token", token);
    if (data["2fa_enabled"] === true) {
      localStorage.setItem("2fa_enabled", "true");
    } else {
      localStorage.removeItem("2fa_enabled");
    }
    showApp();
  } else {
    document.getElementById("auth-msg").textContent = "Wrong credentials or 2FA code";
  }
};

// REGISTER
document.getElementById("register").onclick = async () => {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const res = await fetch(`${API}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  if (res.ok) {
    document.getElementById("auth-msg").textContent = "Registered! Now login";
  }
};

// LOGOUT
document.getElementById("logout").onclick = () => {
  localStorage.removeItem("token");
  token = null;
  showAuth();
};

// ADD PASSWORD
document.getElementById("add").onclick = async () => {
  const site = document.getElementById("site").value.trim();
  const username = document.getElementById("username").value.trim();
  const pass = document.getElementById("pass").value;
  if (!site || !username || !pass) return alert("All fields required");

  const res = await fetch(`${API}/passwords`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ site, username, password: pass })
  });
  if (res.ok) {
    document.getElementById("site").value = "";
    document.getElementById("username").value = "";
    document.getElementById("pass").value = "";
    loadPasswords();
  } else {
    alert("Error – session expired");
    showAuth();
  }
};

// LOAD PASSWORDS
async function loadPasswords() {
  const res = await fetch(`${API}/passwords`, {
    headers: { "Authorization": `Bearer ${token}` }
  });
  if (!res.ok) {
    localStorage.removeItem("token");
    token = null;
    showAuth();
    return;
  }
  const passwords = await res.json();
  const list = document.getElementById("list");
  list.innerHTML = passwords.map(p => `
    <li id="pw-${p.id}">
      <strong>${p.site}</strong> ${p.note ? `<span style="color:#28a745">(${p.note})</span>` : ''}
      <br>Username: ${p.username}
      <br>Password: <span style="background:#f0f0f0;padding:2px 6px;">${p.password}</span>
      ${p.note ? '' : `
        <div style="margin-top:8px;">
          <button onclick="editPassword(${p.id})" style="background:#007bff;color:white;">Edit</button>
          <button onclick="sharePassword(${p.id})" style="background:#ffc107;color:black;margin-left:5px;">Share</button>
          <button onclick="deletePassword(${p.id})" style="background:#dc3545;color:white;margin-left:5px;">Delete</button>
        </div>
      `}
    </li>
  `).join("");
}

// DELETE
function deletePassword(id) {
  if (confirm("Delete forever?")) {
    fetch(`${API}/passwords/${id}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${token}` }
    }).then(() => loadPasswords());
  }
}

// EDIT
function editPassword(id) {
  fetch(`${API}/passwords`, { headers: { "Authorization": `Bearer ${token}` } })
    .then(r => r.json())
    .then(all => {
      const pw = all.find(x => x.id === id);
      const newSite = prompt("Site:", pw.site) || pw.site;
      const newUser = prompt("Username:", pw.username) || pw.username;
      const newPass = prompt("Password:", pw.password) || pw.password;
      fetch(`${API}/passwords/${id}`, {
        method: "PUT",
        headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ site: newSite, username: newUser, password: newPass })
      }).then(() => loadPasswords());
    });
}

// SHARE
function sharePassword(id) {
  const email = prompt("Share with (email):");
  if (email && email.includes("@")) {
    fetch(`${API}/share`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ to_email: email, password_id: id })
    }).then(() => alert("Shared!"));
  }
}

// ENABLE 2FA
document.getElementById("toggle-2fa").onclick = async () => {
  const res = await fetch(`${API}/enable-2fa`, {
    method: "POST",
    headers: { "Authorization": `Bearer ${token}` }
  });
  const data = await res.json();
  if (data.qr_code) {
    document.getElementById("qr-img").src = data.qr_code;
    document.getElementById("qr-code").style.display = "block";
    localStorage.setItem("2fa_enabled", "true");
    alert("2FA enabled! Next login will ask for code");
  }
};

// GENERATE PASSWORD (optional – keep if you have it)
document.getElementById("generate").onclick = () => {
  const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*";
  let pass = "";
  for (let i = 0; i < 18; i++) pass += chars[Math.floor(Math.random() * chars.length)];
  document.getElementById("pass").value = pass;
};

// Init
update2FAField();

// Live password strength meter
document.getElementById("pass").addEventListener("input", () => {
  const pass = document.getElementById("pass").value;
  const bar = document.getElementById("strength-bar");
  const text = document.getElementById("strength-text");

  if (pass.length === 0) {
    bar.style.width = "0%";
    bar.style.backgroundColor = "#ddd";
    text.textContent = "Enter password";
    return;
  }

  let score = 0;
  if (pass.length >= 8) score++;
  if (pass.length >= 12) score++;
  if (/[a-z]/.test(pass)) score++;
  if (/[A-Z]/.test(pass)) score++;
  if (/\d/.test(pass)) score++;
  if (/[^A-Za-z0-9]/.test(pass)) score++;

  const colors = ["#d9534f", "#f0ad4e", "#f0ad4e", "#5cb85c", "#5cb85c", "#4caf50"];
  const labels = ["Very Weak", "Weak", "Fair", "Good", "Strong", "Very Strong"];

  bar.style.width = (score * 16.67) + "%";
  bar.style.backgroundColor = colors[score] || "#4caf50";
  text.textContent = labels[score] || "Very Strong";
});

// LIVE PASSWORD STRENGTH METER – updates on every change
function updateStrengthMeter() {
  const pass = document.getElementById("pass").value;
  const bar = document.getElementById("strength-bar");
  const text = document.getElementById("strength-text");

  if (pass.length === 0) {
    bar.style.width = "0%";
    bar.style.backgroundColor = "#ddd";
    text.textContent = "Enter password";
    return;
  }

  let score = 0;
  if (pass.length >= 8) score++;
  if (pass.length >= 12) score++;
  if (pass.length >= 16) score++;
  if (/[a-z]/.test(pass)) score++;
  if (/[A-Z]/.test(pass)) score++;
  if (/\d/.test(pass)) score++;
  if (/[^A-Za-z0-9]/.test(pass)) score++;

  const colors = ["#d9534f", "#f0ad4e", "#ffa500", "#ffdb4d", "#5cb85c", "#4caf50", "#28a745"];
  const labels = ["Very Weak", "Weak", "Fair", "Good", "Strong", "Very Strong", "Excellent"];

  bar.style.width = (score * 14.28) + "%";
  bar.style.backgroundColor = colors[score] || "#28a745";
  text.textContent = labels[score] || "Excellent";
}

// Update meter when clicking Generate
document.getElementById("generate").onclick = () => {
  const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=";
  let password = "";
  for (let i = 0; i < 18; i++) {
    password += chars[Math.floor(Math.random() * chars.length)];
  }
  document.getElementById("pass").value = password;
  updateStrengthMeter();   // ← THIS LINE FIXES THE GENERATE BUTTON
};

// Clear meter after adding password
const oldAddButton = document.getElementById("add").onclick;
document.getElementById("add").onclick = async () => {
  await oldAddButton();
  updateStrengthMeter();   // ← clears meter after adding
};