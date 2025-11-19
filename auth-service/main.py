from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import pyotp
import qrcode
from io import BytesIO
import base64
from models import User, SessionLocal, Base, engine

app = FastAPI(title="Auth Service + 2FA")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "super-secret-key-123"
ALGORITHM = "HS256"

Base.metadata.create_all(bind=engine)

class RegisterForm(BaseModel):
    email: str
    password: str

class LoginForm(BaseModel):
    email: str
    password: str
    totp_code: str = None   # optional if 2FA not enabled

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except:
        return None

@app.post("/register")
def register(form: RegisterForm, db: Session = Depends(get_db)):
    hashed = pwd_context.hash(form.password)
    user = User(email=form.email, hashed_password=hashed)
    db.add(user)
    db.commit()
    return {"msg": "user created"}

@app.post("/login")
def login(form: LoginForm, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.email).first()
    if not user or not pwd_context.verify(form.password, user.hashed_password):
        raise HTTPException(401, "Bad credentials")

    # 2FA check if enabled
    if user.totp_enabled:
        if not form.totp_code or not pyotp.TOTP(user.totp_secret).verify(form.totp_code):
            raise HTTPException(401, "Invalid 2FA code")

    token = jwt.encode({
        "sub": user.email,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }, SECRET_KEY, algorithm=ALGORITHM)

    return {"access_token": token, "token_type": "bearer", "2fa_enabled": user.totp_enabled}

# Enable 2FA + get QR code
@app.post("/enable-2fa")
def enable_2fa(authorization: str = Header(None), db: Session = Depends(get_db)):
    email = get_current_user(authorization.split(" ")[1] if authorization else "")
    if not email:
        raise HTTPException(401)

    user = db.query(User).filter(User.email == email).first()
    secret = pyotp.random_base32()
    user.totp_secret = secret
    user.totp_enabled = True
    db.commit()

    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name="MyPasswordManager")
    qr = qrcode.make(totp_uri)
    buffered = BytesIO()
    qr.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()

    return {
        "msg": "2FA enabled – scan QR code with Authenticator app",
        "qr_code": f"data:image/png;base64,{qr_base64}"
    }

# Disable 2FA
@app.post("/disable-2fa")
def disable_2fa(authorization: str = Header(None), db: Session = Depends(get_db)):
    email = get_current_user(authorization.split(" ")[1] if authorization else "")
    if not email:
        raise HTTPException(401)
    user = db.query(User).filter(User.email == email).first()
    user.totp_secret = None
    user.totp_enabled = False
    db.commit()
    return {"msg": "2FA disabled"}