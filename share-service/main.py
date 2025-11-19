from fastapi import FastAPI, Depends, HTTPException, Header
from jose import jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models import SharedPassword, SessionLocal, Base, engine

app = FastAPI(title="Share Service")
SECRET_KEY = "super-secret-key-123"   # same as auth and vault

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ← THIS WAS MISSING — ADD IT!
def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "Missing token")
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]   # returns the email
    except:
        raise HTTPException(401, "Invalid token")

class ShareRequest(BaseModel):
    to_email: str
    password_id: int

@app.post("/share")
def share(req: ShareRequest, email: str = Depends(get_current_user), db: Session = Depends(get_db)):
    new_share = SharedPassword(
        from_email=email,        # ← real sender email!
        to_email=req.to_email,
        vault_entry_id=req.password_id
    )
    db.add(new_share)
    db.commit()
    return {"msg": "Password shared successfully!"}

@app.get("/shared-with-me")
def shared_with_me(to_email: str, db: Session = Depends(get_db)):
    shares = db.query(SharedPassword).filter(SharedPassword.to_email == to_email).all()
    return [{"vault_entry_id": s.vault_entry_id, "from": s.from_email or "someone"} for s in shares]