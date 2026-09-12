import os
import bcrypt
import urllib.parse
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import engine, SessionLocal, Base, get_db
from models import User, PlantCare
from schemas import (
    UserRegister,
    UserLogin,
    ApiResponse,
    AssistantRequest
)
from services.plant_identifier import identify_plant
from services.seed_identifier import identify_seed
from services.health_checker import check_health
from services.plant_assistant import ask_assistant
from services.plant_care_service import get_plant_care_with_fallback

# Load environment configuration
load_dotenv(override=True)

# Initialize Database Schema safely
try:
    Base.metadata.create_all(bind=engine)
except Exception as db_init_err:
    print("Database initial sync note (will retry on query):", db_init_err)


# Create FastAPI app
app = FastAPI(
    title="PlantAI API",
    description="AI-Based Plant Identification, Health Assessment, Seed Recognition & Smart Care Assistant",
    version="2.0.0"
)

# Configure CORS
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000")
allowed_origins = [orig.strip() for orig in allowed_origins_env.split(",") if orig.strip()]
if "*" not in allowed_origins:
    allowed_origins.extend(["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler to prevent raw stack trace exposure
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print("Unhandled error on", request.url.path, ":", exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "status": "error",
            "message": "An unexpected error occurred while processing your request. Please try again.",
            "data": None
        }
    )

# -------------------------------------------------------------
# 1. System Health Endpoint
# -------------------------------------------------------------
@app.get("/")
def home():
    return {
        "success": True,
        "status": "online",
        "message": "PlantAI Backend API is running successfully!",
        "version": "2.0.0"
    }

# -------------------------------------------------------------
# 2. Authentication Endpoints
# -------------------------------------------------------------
@app.post("/register")
def register_user(user_in: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        return {
            "success": False,
            "status": "error",
            "message": "An account with this email already exists."
        }

    hashed_pw = bcrypt.hashpw(user_in.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    new_user = User(name=user_in.name, email=user_in.email, password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "success": True,
        "status": "created",
        "message": "User registered successfully!",
        "data": {
            "user_id": new_user.id,
            "name": new_user.name,
            "email": new_user.email
        }
    }

@app.post("/login")
def login_user(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user:
        return {
            "success": False,
            "status": "error",
            "message": "Invalid email or password."
        }

    if not bcrypt.checkpw(user_in.password.encode("utf-8"), user.password.encode("utf-8")):
        return {
            "success": False,
            "status": "error",
            "message": "Invalid email or password."
        }

    return {
        "success": True,
        "status": "authenticated",
        "message": "Login successful!",
        "data": {
            "user_id": user.id,
            "name": user.name,
            "email": user.email
        }
    }

# -------------------------------------------------------------
# 3. Plant Identification Endpoint
# -------------------------------------------------------------
@app.post("/upload-image")
async def scan_plant(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        filename = file.filename or "image.jpg"
        content_type = file.content_type or "image/jpeg"

        result = identify_plant(image_bytes, filename, content_type)
        return result
    except Exception as e:
        print("scan_plant error:", e)
        return {
            "success": False,
            "status": "error",
            "message": "Could not identify plant. Please check your image and try again.",
            "data": None
        }

# -------------------------------------------------------------
# 4. Seed Identification Endpoint
# -------------------------------------------------------------
@app.post("/seed-identify")
@app.post("/identify-seed")
async def scan_seed(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        filename = file.filename or "seed.jpg"
        content_type = file.content_type or "image/jpeg"

        result = identify_seed(image_bytes, filename, content_type)
        return result
    except Exception as e:
        print("scan_seed error:", e)
        return {
            "success": False,
            "status": "error",
            "message": "Could not identify seed. Please try again.",
            "data": None
        }

# -------------------------------------------------------------
# 5. Plant Health & Disease Assessment Endpoint
# -------------------------------------------------------------
@app.post("/health-check")
async def plant_health(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        filename = file.filename or "health.jpg"
        content_type = file.content_type or "image/jpeg"

        result = check_health(image_bytes, filename, content_type)
        return result
    except Exception as e:
        print("plant_health error:", e)
        return {
            "success": False,
            "status": "error",
            "message": "Plant health analysis could not be completed. Please try again.",
            "data": None
        }

# -------------------------------------------------------------
# 6. Plant Care Retrieval (MySQL Primary + AI/API Fallback)
# -------------------------------------------------------------
@app.get("/plant-care/{plant_name}")
def get_plant_care(plant_name: str, db: Session = Depends(get_db)):
    try:
        result = get_plant_care_with_fallback(plant_name, db)
        return result
    except Exception as e:
        print("get_plant_care error:", e)
        return {
            "success": False,
            "status": "error",
            "message": "Plant care information is temporarily unavailable.",
            "data": None
        }

# -------------------------------------------------------------
# 7. AI Plant Assistant Endpoint
# -------------------------------------------------------------
@app.post("/assistant")
def assistant_chat(
    payload: AssistantRequest = None,
    question: str = None,
    plant_name: str = "",
    db: Session = Depends(get_db)
):
    try:
        # Support both JSON payload and query/form parameters
        q = ""
        p_name = ""
        if payload:
            q = payload.question
            p_name = payload.plant_name or ""
        elif question:
            q = question
            p_name = plant_name or ""

        result = ask_assistant(q, p_name, db)
        return result
    except Exception as e:
        print("assistant error:", e)
        return {
            "success": False,
            "status": "error",
            "message": "AI Assistant is temporarily unavailable. Please try again.",
            "answer": "AI Assistant is temporarily unavailable. Please try again.",
            "plant_name": plant_name or ""
        }
