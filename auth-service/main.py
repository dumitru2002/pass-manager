from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

# Change these two lines (remove the dot!)
from models import User, SessionLocal, Base, engine

app = FastAPI(title="Auth Service")
#pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "super-secret-key-123"
ALGORITHM = "HS256"

# Create tables (in case DB is empty)
Base.metadata.create_all(bind=engine)


class RegisterForm(BaseModel):
    email: str
    password: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/register")
def register(form: RegisterForm, db: Session = Depends(get_db)):
    hashed = pwd_context.hash(form.password)
    user = User(email=form.email, hashed_password=hashed)
    db.add(user)
    db.commit()
    return {"msg": "user created"}


@app.post("/login")
def login(form: RegisterForm, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.email).first()
    if not user or not pwd_context.verify(form.password, user.hashed_password):
        raise HTTPException(401, "Bad credentials")

    token = jwt.encode({
        "sub": user.email,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }, SECRET_KEY, algorithm=ALGORITHM)

    return {"access_token": token, "token_type": "bearer"}