import httpx
from fastapi import FastAPI, Depends, HTTPException, Header, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from jose import jwt, JWTError

# Change these lines too (remove the dot!)
from models import PasswordEntry, SessionLocal, Base, engine
from crypto import encrypt, decrypt

app = FastAPI(title="Vault Service")
SECRET_KEY = "super-secret-key-123"  # same as auth!

# Create tables
Base.metadata.create_all(bind=engine)

def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "No token")
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except:
        raise HTTPException(401, "Invalid token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PasswordIn(BaseModel):
    site: str
    username: str
    password: str

@app.post("/passwords")
def add(pw: PasswordIn, email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    encrypted = encrypt(pw.password)
    entry = PasswordEntry(
        user_email=email,
        site=pw.site,
        username=pw.username,
        password_encrypted=encrypted
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {
        "id": entry.id,
        "site": pw.site,
        "username": pw.username,
        "message": "password saved successfully"
    }


@app.get("/passwords")
def list_all(email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    # My own passwords
    my_entries = db.query(PasswordEntry).filter(PasswordEntry.user_email == email).all()

    # Shared with me — call share service with my email as query param
    # Shared with me
    import httpx
    try:
        shared_resp = httpx.get(f"http://share:8000/shared-with-me?to_email={email}")
        shared_list = shared_resp.json() if shared_resp.status_code == 200 else []
    except:
        shared_list = []

    result = []
    for e in my_entries:
        result.append({
            "id": e.id,
            "site": e.site,
            "username": e.username,
            "password": decrypt(e.password_encrypted),
            "note": ""
        })

    for shared in shared_list:
        entry = db.query(PasswordEntry).filter(PasswordEntry.id == shared["vault_entry_id"]).first()
        if entry:
            result.append({
                "id": entry.id,
                "site": entry.site,
                "username": entry.username,
                "password": decrypt(entry.password_encrypted),
                "note": f"Shared by {shared.get('from', 'someone')}"
            })

    return result


@app.delete("/passwords/{password_id}")
def delete_password(password_id: int, email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    entry = db.query(PasswordEntry).filter(PasswordEntry.id == password_id, PasswordEntry.user_email == email).first()
    if not entry:
        raise HTTPException(404, "Password not found or not yours")
    db.delete(entry)
    db.commit()
    return {"msg": "Password deleted"}


@app.put("/passwords/{password_id}")
def update_password(password_id: int, pw: PasswordIn, email: str = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    entry = db.query(PasswordEntry).filter(PasswordEntry.id == password_id, PasswordEntry.user_email == email).first()
    if not entry:
        raise HTTPException(404, "Password not found or not yours")

    entry.site = pw.site
    entry.username = pw.username
    entry.password_encrypted = encrypt(pw.password)
    db.commit()
    return {"msg": "Password updated", "id": entry.id}

from utils import PasswordUtils

@app.get("/generate-password")
def generate_password(length: int = 16):
    if length < 8 or length > 128:
        raise HTTPException(400, "Length must be 8-128")
    password = PasswordUtils.generate(length)
    strength = PasswordUtils.strength(password)
    return {
        "password": password,
        "strength": strength
    }

@app.post("/check-strength")
def check_strength(password: str = Body(..., embed=True)):
    if not password:
        raise HTTPException(400, "Password required")
    strength = PasswordUtils.strength(password)
    return {"strength": strength}