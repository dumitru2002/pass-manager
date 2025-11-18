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
}

if (token) showApp();

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
    document.getElementById("auth-msg").textContent = "Login failed";
  }
};

document.getElementById("register").onclick = async () => {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  await fetch(`${API}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  document.getElementById("auth-msg").textContent = "Registered! Now login";
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
  await fetch(`${API}/passwords`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ site, username, password: pass })
  });
  document.getElementById("site").value = "";
  document.getElementById("username").value = "";
  document.getElementById("pass").value = "";
  loadPasswords();
};

async function loadPasswords() {
  const res = await fetch(`${API}/passwords`, {
    headers: { "Authorization": `Bearer ${token}` }
  });
  const passwords = await res.json();
  const list = document.getElementById("list");
  list.innerHTML = passwords.map(p => `
    <li>
      <strong>${p.site}</strong><br>
      Username: ${p.username}<br>
      Password: <span style="font-family:monospace">${p.password}</span>
    </li>
  `).join("");
}