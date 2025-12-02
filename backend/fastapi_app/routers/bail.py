import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
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

@router.get("/bail/pdf/{uuid}")
async def get_bail_pdf(uuid: str):
    """Get the generated bail PDF for a specific UUID."""
    pdf_path = os.path.join(GENERATED_BAILS_DIR, f"{uuid}.pdf")
    
    if os.path.exists(pdf_path):
        return FileResponse(
            path=pdf_path, 
            filename=f"bail_{uuid}.pdf",
            media_type="application/pdf"
        )
    else:
        # Check if HTML exists, maybe we can generate it on the fly?
        # For now, let's just return 404 if the PDF is missing
        raise HTTPException(status_code=404, detail="PDF not found")
