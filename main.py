from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
from datetime import datetime
from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LICENSES_FILE = Path(__file__).parent / 'licenses.json'

def load_licenses():
    try:
        with open(LICENSES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        save_licenses({})
        return {}

def save_licenses(licenses):
    with open(LICENSES_FILE, 'w') as f:
        json.dump(licenses, f, indent=4)

class LicenseRequest(BaseModel):
    license_key: str

class LicenseResponse(BaseModel):
    status: str
    message: str
    expires_at: str = None

@app.get("/")
async def root():
    return {"message": "License API Server is running"}

@app.post("/verify")
async def verify_license(request: LicenseRequest):
    licenses = load_licenses()
    if request.license_key not in licenses:
        raise HTTPException(status_code=400, detail="Invalid license key")
    license_info = licenses[request.license_key]
    # Check if license is expired
    if datetime.fromisoformat(license_info["expires_at"]) < datetime.now():
        return LicenseResponse(
            status="error",
            message="License has expired",
            expires_at=license_info["expires_at"]
        )
    # Mark as used if not already
    if not license_info.get("is_used", False):
        license_info["is_used"] = True
        save_licenses(licenses)
    return LicenseResponse(
        status="success",
        message="License is valid",
        expires_at=license_info["expires_at"]
    )

# Catch-all exception handler for debugging
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )
