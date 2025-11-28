import os
from fastapi import APIRouter, HTTPException
from ..config import GENERATED_BAILS_DIR

router = APIRouter()

@router.get("/bail/{uuid}")
async def get_bail(uuid: str):
    """Get the generated bail HTML for a specific UUID."""
    bail_path = os.path.join(GENERATED_BAILS_DIR, f"{uuid}.html")
    if os.path.exists(bail_path):
        with open(bail_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"html": content}
    else:
        raise HTTPException(status_code=404, detail="Bail not found")
