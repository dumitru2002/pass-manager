from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

engine = create_engine("sqlite:///./vault.db")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class PasswordEntry(Base):
    __tablename__ = "entries"
    id = Column(Integer, primary_key=True)
    user_email = Column(String)
    site = Column(String)
    username = Column(String)
    password_encrypted = Column(String)

Base.metadata.create_all(engine)