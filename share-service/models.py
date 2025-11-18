from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///./shares.db")
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class SharedPassword(Base):
    __tablename__ = "shares"
    id = Column(Integer, primary_key=True)
    from_email = Column(String)       # who shared
    to_email = Column(String)         # who receives
    vault_entry_id = Column(Integer)  # which password (id from vault)

Base.metadata.create_all(engine)