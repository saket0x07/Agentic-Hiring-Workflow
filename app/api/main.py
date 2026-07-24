from fastapi import FastAPI

from app.core.settings import settings
from app.core.logger import logger
from app.api.routes.jobs import router as jobs_router
from app.api.routes.resumes import router as resumes_router
from app.api.routes.retrieval import router as retrieval_router
from app.api.routes.evaluations import router as evaluations_router



app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)
app.include_router(jobs_router)
app.include_router(resumes_router)
app.include_router(retrieval_router)
app.include_router(evaluations_router)


@app.get("/")
async def root():
    """ROOT ENDPOINTS"""
    logger.info("Root endpoint accessed")
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENV,
    }

@app.get("/version")
async def version():
    """Application version endpoint"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
