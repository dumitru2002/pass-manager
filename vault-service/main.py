import httpx
from fastapi import FastAPI, Depends, HTTPException, Header
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
    db.refresh(entry)               # ← this line was missing!
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