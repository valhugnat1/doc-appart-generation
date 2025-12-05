from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import conversations, chat, bail, auth
# Import config to ensure sys.path is set up
from . import config

app = FastAPI(title="Agent Recup Info API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(bail.router)
app.include_router(auth.router)

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
