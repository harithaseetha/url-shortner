import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from . import models 

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./urlshortener.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# Import models so they are registered on Base.metadata
def init_db():
    Base.metadata.create_all(bind=engine)
