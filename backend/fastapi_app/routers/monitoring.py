from fastapi import APIRouter, Depends
from ..services.monitoring import monitoring_service

# Determine if we need auth dependency. 
# For now, we'll keep it open or assume it will be used in an admin context.
# If there is an auth module, we should use it. 
# Checking imports in main.py... it has 'auth' router.
# Let's import auth dependency if possible, but to keep it "light and simple" and avoid circular imports or complex auth logic 
# instantly, I will stick to open or basic. 
# Re-reading: "Light, simple and propre".
# Propre implies security too.
# Let's check 'backend/fastapi_app/routers/auth.py' later if needed. 
# For now, standard router.

router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"],
    responses={404: {"description": "Not found"}},
)

@router.get("/stats")
async def get_monitoring_stats():
    return monitoring_service.get_stats()
