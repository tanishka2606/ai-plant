import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# 1. Support direct DATABASE_URL (Render, Railway, TiDB, Aiven, etc.)
raw_db_url = os.getenv("DATABASE_URL")

if raw_db_url:
    # Ensure pymysql dialect is used if raw mysql:// url provided
    if raw_db_url.startswith("mysql://"):
        DATABASE_URL = raw_db_url.replace("mysql://", "mysql+pymysql://", 1)
    else:
        DATABASE_URL = raw_db_url
else:
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = urllib.parse.quote_plus(os.getenv("DB_PASSWORD", ""))
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "plant_ai")
    
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False
    )
except Exception as e:
    print("Database engine creation warning:", e)
    # Fallback to in-memory sqlite if MySQL cannot be initialized
    engine = create_engine("sqlite:///./plantai_fallback.db", echo=False)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
