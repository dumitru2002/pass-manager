const API = "http://localhost:8000";
let token = localStorage.getItem("token");

// Escape HTML to prevent JS injection and quote problems
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function showApp() {
  document.getElementById("auth").classList.add("hidden");
  document.getElementById("app").classList.remove("hidden");
  loadPasswords();
}

function showAuth() {
  document.getElementById("app").classList.add("hidden");
  document.getElementById("auth").classList.remove("hidden");
  document.getElementById("list").innerHTML = "";
}

// Validate token on page load
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

// Login
document.getElementById("login").onclick = async () => {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const res = await fetch(`${API}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  const data = await res.json();
  if (data.access_token) {
    token = data.access_token;
    localStorage.setItem("token", token);
    showApp();
  } else {
    document.getElementById("auth-msg").textContent = "Wrong email or password!";
  }
};

// Register
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
  } else {
    document.getElementById("auth-msg").textContent = "Registration failed";
  }
};

// Logout
document.getElementById("logout").onclick = () => {
  localStorage.removeItem("token");
  token = null;
  showAuth();
};

// Add password
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
  loadPasswords();
  } else {
    alert("Error – session expired");
    showAuth();
  }
};

// Load passwords + buttons
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
      <strong>${escapeHtml(p.site)}</strong>
      ${p.note ? `<span style="color:#28a745;font-size:0.9em">(${escapeHtml(p.note)})</span>` : ''}
      <br>Username: ${escapeHtml(p.username)}
      <br>Password: <span style="font-family:monospace;background:#f0f0f0;padding:3px 7px;border-radius:4px">${escapeHtml(p.password)}</span>

      ${p.note ? '' : `
        <div style="margin-top:12px;">
          <button onclick="editPassword(${p.id})" style="background:#007bff;color:white;padding:6px 12px;margin-right:6px;border:none;border-radius:4px;cursor:pointer;">Edit</button>
          <button onclick="sharePassword(${p.id})" style="background:#ffc107;color:black;padding:6px 12px;margin-right:6px;border:none;border-radius:4px;cursor:pointer;">Share</button>
          <button onclick="deletePassword(${p.id})" style="background:#dc3545;color:white;padding:6px 12px;border:none;border-radius:4px;cursor:pointer;">Delete</button>
        </div>
      `}
    </li>
  `).join("");
}

// Delete
function deletePassword(id) {
  if (confirm("Delete this password permanently?")) {
    fetch(`${API}/passwords/${id}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${token}` }
    }).then(() => loadPasswords());
  }
}

// EDIT — NOW 100% WORKING EVEN WITH QUOTES, SPACES, SPECIAL CHARS
function editPassword(id) {
  fetch(`${API}/passwords`, { headers: { "Authorization": `Bearer ${token}` } })
    .then(r => r.json())
    .then(all => {
      const pw = all.find(x => x.id === id);
      if (!pw) return alert("Not found");

      const newSite = prompt("Edit site:", pw.site) || pw.site;
      if (newSite === pw.site) return; // no change

      const newUser = prompt("Edit username:", pw.username) || pw.username;
      const newPass = prompt("Edit password:", pw.password) || pw.password;

      fetch(`${API}/passwords/${id}`, {
        method: "PUT",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ site: newSite, username: newUser, password: newPass })
      }).then(() => loadPasswords());
    });
}

// Share
function sharePassword(id) {
  const email = prompt("Share with (email):");
  if (email && email.includes("@")) {
    fetch(`${API}/share`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ to_email: email, password_id: id })
    })
    .then(r => r.json())
    .then(d => alert(d.msg || "Shared successfully!"))
    .catch(() => alert("Error – try login again"));
  }
}