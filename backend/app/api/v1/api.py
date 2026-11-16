from fastapi import APIRouter
from app.api.v1.endpoints import auth, fields, sensors, weather, dashboard, guidance
from app.api.v1.endpoints import irrigation, analytics, ml

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(fields.router, prefix="/fields", tags=["fields"])
api_router.include_router(sensors.router, prefix="/sensors", tags=["sensors"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(guidance.router, prefix="/guidance", tags=["guidance"])
api_router.include_router(irrigation.router, prefix="/irrigation", tags=["irrigation"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(ml.router, prefix="/ml", tags=["ml"])
