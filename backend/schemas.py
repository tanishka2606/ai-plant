from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class CandidateMatch(BaseModel):
    scientific_name: str
    common_name: Optional[str] = None
    confidence: float
    confidence_percent: float

class PlantIdentificationData(BaseModel):
    plant_name: str
    common_name: Optional[str] = None
    scientific_name: str
    species: Optional[str] = None
    genus: Optional[str] = None
    family: Optional[str] = None
    confidence: float
    confidence_percent: float
    candidates: List[CandidateMatch] = []
    assessment: Optional[str] = None
    image_quality: Optional[str] = None

class SeedIdentificationData(BaseModel):
    seed_name: str
    common_name: Optional[str] = None
    scientific_name: str
    confidence: float
    confidence_percent: float
    candidates: List[CandidateMatch] = []
    assessment: Optional[str] = None

class HealthIssue(BaseModel):
    name: str
    probability: float
    probability_percent: float
    description: Optional[str] = None
    symptoms: List[str] = []
    causes: List[str] = []
    treatment: Optional[Dict[str, Any]] = None

class HealthCheckData(BaseModel):
    plant_name: Optional[str] = "Plant"
    is_healthy: bool
    health_status: str
    confidence: float
    confidence_percent: float
    diseases: List[HealthIssue] = []
    symptoms: List[str] = []
    causes: List[str] = []
    treatments: List[str] = []
    prevention: List[str] = []
    disclaimer: str = "AI health analysis provides guidance only and is not a confirmed professional diagnosis."

class PlantCareData(BaseModel):
    id: Optional[int] = None
    plant_name: str
    common_name: Optional[str] = None
    sunlight: Optional[str] = None
    water: Optional[str] = None
    soil: Optional[str] = None
    container: Optional[str] = None
    location: Optional[str] = None
    fertilizer: Optional[str] = None
    care: Optional[str] = None
    source: str = "MySQL"

class AssistantRequest(BaseModel):
    question: str
    plant_name: Optional[str] = ""
    history: Optional[List[Dict[str, Any]]] = None

class ApiResponse(BaseModel):
    success: bool
    status: str
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
