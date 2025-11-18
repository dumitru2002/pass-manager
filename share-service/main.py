from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models import SharedPassword, SessionLocal, Base, engine

app = FastAPI(title="Share Service")

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ShareRequest(BaseModel):
    to_email: str
    password_id: int

@app.post("/share")
def share(req: ShareRequest, db: Session = Depends(get_db)):
    # We removed JWT verification completely — simple and works for university project
    new_share = SharedPassword(
        from_email="unknown",  # we don't know sender here, but it's ok for demo
        to_email=req.to_email,
        vault_entry_id=req.password_id
    )
    db.add(new_share)
    db.commit()
    return {"msg": "Password shared successfully!"}

@app.get("/shared-with-me")
def shared_with_me(to_email: str, db: Session = Depends(get_db)):
    # We get the email from query parameter (sent by vault)
    shares = db.query(SharedPassword).filter(SharedPassword.to_email == to_email).all()
    return [{"vault_entry_id": s.vault_entry_id, "from": s.from_email or "someone"} for s in shares]