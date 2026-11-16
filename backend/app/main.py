from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.rate_limit import RateLimitMiddleware

app = FastAPI(title=settings.APP_NAME, version="1.0.0")


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    # Never leak raw database errors to the client.
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error"},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Avoid exposing internals in production.
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Rate limiting: tighter on auth endpoints, general limit elsewhere.
app.add_middleware(
    RateLimitMiddleware,
    limit=120,
    window_seconds=60,
    path_limits={
        "/api/v1/auth/profile": (10, 60),
        "/api/v1/auth/logout": (10, 60),
        "/api/v1/sensors/": (30, 60),
        "/api/v1/fields/": (30, 60),
    },
)

cors_origins = settings.cors_origin_list
allow_credentials = "*" not in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}
