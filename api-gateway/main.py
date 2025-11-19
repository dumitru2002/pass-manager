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

@app.post("/share")
@app.post("/share/")
async def share_password(request: Request, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "Missing token")
    return await forward("/share", request, "http://share:8000", authorization)

@app.delete("/passwords/{password_id}")
@app.delete("/passwords/{password_id}/")
async def delete_password(password_id: int, request: Request, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "Missing token")
    return await forward(f"/passwords/{password_id}", request, VAULT_SERVICE, authorization)

@app.put("/passwords/{password_id}")
@app.put("/passwords/{password_id}/")
async def update_password(password_id: int, request: Request, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "Missing token")
    return await forward(f"/passwords/{password_id}", request, VAULT_SERVICE, authorization)


@app.get("/generate-password")
@app.post("/check-strength")
async def utils_routes(request: Request, authorization: str = Header(None)):
    # No auth needed for generator
    return await forward(request.scope["path"], request, VAULT_SERVICE)

@app.post("/enable-2fa")
@app.post("/enable-2fa/")
async def enable_2fa_route(request: Request, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "Missing token")
    return await forward("/enable-2fa", request, AUTH_SERVICE, authorization)

@app.post("/disable-2fa")
@app.post("/disable-2fa/")
async def disable_2fa_route(request: Request, authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "Missing token")
    return await forward("/disable-2fa", request, AUTH_SERVICE, authorization)