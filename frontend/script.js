const API = "http://localhost:8000";
let token = localStorage.getItem("token");

function showApp() {
  document.getElementById("auth").classList.add("hidden");
  document.getElementById("app").classList.remove("hidden");
  loadPasswords();
}

function showAuth() {
  document.getElementById("app").classList.add("hidden");
  document.getElementById("auth").classList.remove("hidden");
  document.getElementById("list").innerHTML = ""; // clear old passwords
}

// Check if token is valid on page load
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
checkToken(); // ← THIS IS THE KEY LINE

document.getElementById("login").onclick = async () => {
  const email = document.getElementById("email").value;
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

document.getElementById("register").onclick = async () => {
  const email = document.getElementById("email").value;
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

document.getElementById("logout").onclick = () => {
  localStorage.removeItem("token");
  token = null;
  showAuth();
};

document.getElementById("add").onclick = async () => {
  const site = document.getElementById("site").value;
  const username = document.getElementById("username").value;
  const pass = document.getElementById("pass").value;
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
    alert("Session expired – please login again");
    showAuth();
  }
};

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
    <li>
      <strong>${p.site}</strong> 
      ${p.note ? '<span style="color:#28a745;font-size:0.9em">(' + p.note + ')</span>' : ''}
      <br>Username: ${p.username}
      <br>Password: <span style="font-family:monospace;background:#f0f0f0;padding:2px 6px;border-radius:4px">${p.password}</span>
      ${p.note ? '' : `<button onclick="sharePassword(${p.id})" style="float:right;background:#ffc107;color:black;padding:5px 10px;border:none;border-radius:4px;cursor:pointer;margin-top:8px">Share</button>`}
    </li>
  `).join("");
}

function sharePassword(id) {
  const email = prompt("Enter email to share with:");
  if (email && email.includes("@")) {
    fetch(`${API}/share`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ to_email: email, password_id: id })
    }).then(r => r.json()).then(d => alert(d.msg || "Shared!")).catch(() => alert("Error – login again"));
  }
}