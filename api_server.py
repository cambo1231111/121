from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from datetime import datetime
import uvicorn
from pathlib import Path

app = FastAPI()

# Enable CORS - Update this with your actual domains in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your actual domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the absolute path to the licenses file
LICENSES_FILE = Path(__file__).parent / 'licenses.json'

# Load licenses from file
def load_licenses():
    try:
        with open(LICENSES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Create an empty licenses file if it doesn't exist
        save_licenses({})
        return {}

# Save licenses to file
def save_licenses(licenses):
    with open(LICENSES_FILE, 'w') as f:
        json.dump(licenses, f, indent=4)

class LicenseRequest(BaseModel):
    license_key: str
    hwid: str

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
    
    # Check if HWID matches or license is unused
    if not license_info["is_used"] or license_info["hwid"] == request.hwid:
        if not license_info["is_used"]:
            license_info["is_used"] = True
            license_info["hwid"] = request.hwid
            save_licenses(licenses)
        
        return LicenseResponse(
            status="success",
            message="License is valid",
            expires_at=license_info["expires_at"]
        )
    else:
        return LicenseResponse(
            status="error",
            message="License is already in use on another device",
            expires_at=license_info["expires_at"]
        )

# Only run the server directly if this file is run directly
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 