from fastapi import APIRouter

from app.api.api_v1.endpoints import login, fake_login, calendar, enroll, ping, profile, attendance, training, group

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(fake_login.router, prefix="/fake_login", tags=["fake-login"])
api_router.include_router(calendar.router, tags=["calendar"], prefix="/calendar")
api_router.include_router(enroll.router, tags=["enrollment"])
api_router.include_router(ping.router, prefix="/ping", tags=["test"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(training.router, prefix="/training", tags=["training"])
api_router.include_router(group.router, prefix="/group", tags=["group"])