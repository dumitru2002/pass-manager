from fastapi import FastAPI, Header, HTTPException, Request
import httpx
from starlette.middleware.cors import CORSMiddleware

app = FastAPI(title="Password Manager - API Gateway")



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],              # In production change to ["http://localhost:8080"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUTH_SERVICE = "http://auth:8000"
VAULT_SERVICE = "http://vault:8000"

async def forward(path: str, request: Request, service_url: str, auth_token: str = None):
    url = f"{service_url}{path}"
    headers = {}
    if auth_token:
        headers["Authorization"] = auth_token

    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers={**request.headers, **headers},
            content=await request.body(),
            params=request.query_params,
        )
        try:
            return response.json()
        except:
            return response.text if response.text else {"detail": "success"}

@app.get("/health")
async def health():
    return {"status": "ok"}

# ======================
# Auth routes
# ======================
@app.post("/register")
@app.post("/register/")
@app.post("/login")
@app.post("/login/")
async def auth_routes(request: Request):
    path = "/register" if "register" in request.url.path else "/login"
    return await forward(path, request, AUTH_SERVICE)

# ======================
# Vault routes – FINAL WORKING VERSION
# ======================
@app.post("/passwords")
@app.post("/passwords/")
async def add_password(request: Request, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "Missing token")
    return await forward("/passwords", request, VAULT_SERVICE, authorization)

@app.get("/passwords")
@app.get("/passwords/")
async def list_passwords(request: Request, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "Missing token")
    return await forward("/passwords", request, VAULT_SERVICE, authorization)