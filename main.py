import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone
from passlib.context import CryptContext
from jose import jwt
from database import db, create_document, get_documents
from schemas import AuthUser, KYCVerification

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-key")
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class SigninRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class KYCRequest(BaseModel):
    user_id: str
    full_name: str
    country: str
    document_type: str
    document_number: str
    address: str

@app.get("/")
def read_root():
    return {"message": "Web3Pay API running"}

@app.get("/test")
def test_database():
    status = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            status["database"] = "✅ Available"
            status["connection_status"] = "Connected"
            status["collections"] = db.list_collection_names()[:10]
        else:
            status["database"] = "❌ Not Configured"
    except Exception as e:
        status["database"] = f"❌ Error: {str(e)[:80]}"
    return status

# Utility functions

def get_user_by_email(email: str) -> Optional[dict]:
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    return db["authuser"].find_one({"email": email})


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode.update({"iat": int(datetime.now(timezone.utc).timestamp())})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Auth endpoints
@app.post("/auth/signup", response_model=TokenResponse)
def signup(payload: SignupRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    existing = get_user_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash = pwd_context.hash(payload.password)
    user = AuthUser(
        name=payload.name,
        email=payload.email,
        password_hash=password_hash,
    )
    user_id = create_document("authuser", user)

    token = create_access_token({"sub": user_id, "email": payload.email})
    return {"access_token": token, "user": {"id": user_id, "name": payload.name, "email": payload.email}}


@app.post("/auth/signin", response_model=TokenResponse)
def signin(payload: SigninRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    user = get_user_by_email(payload.email)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    if not pwd_context.verify(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.get("_id")), "email": user.get("email")})
    return {"access_token": token, "user": {"id": str(user.get("_id")), "name": user.get("name"), "email": user.get("email")}}


# KYC endpoints
@app.post("/kyc/submit")
def submit_kyc(payload: KYCRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    kyc = KYCVerification(**payload.model_dump())
    kyc_id = create_document("kycverification", kyc)
    return {"id": kyc_id, "status": "pending"}


@app.get("/kyc/status")
def kyc_status(user_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    doc = db["kycverification"].find_one({"user_id": user_id}, sort=[("created_at", -1)])
    if not doc:
        return {"status": "not_submitted"}
    return {"status": doc.get("status", "pending"), "submitted_at": doc.get("created_at")}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
