import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])

class PasswordVerification(BaseModel):
    password: str

@router.post("/verify-admin")
async def verify_admin_password(data: PasswordVerification):
    """
    Verify admin password against environment variable.
    Returns success status if password matches.
    """
    # Get admin password from environment variable
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

    if data.password == admin_password:
        return {"success": True, "message": "Password verified"}
    else:
        raise HTTPException(status_code=401, detail="Invalid password")
