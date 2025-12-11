from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import conversations, chat, bail, auth
# Import config to ensure sys.path is set up
from . import config
import time
from fastapi import Request
from .services.monitoring import monitoring_service
from .routers import monitoring

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
app.include_router(monitoring.router)

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Extract endpoint - this is a simplification
    # ideally we match against routes, but for "simple" monitoring path is ok
    monitoring_service.log_request(
        endpoint=request.url.path,
        method=request.method,
        processing_time=process_time,
        status_code=response.status_code
    )
    
    return response

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
