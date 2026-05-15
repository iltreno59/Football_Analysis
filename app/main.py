"""Точка входа FastAPI."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routers import auth, catalog, players, reports, frontend

app = FastAPI(title="Football Analysis API", version="0.1.0")

# Middleware для разрешения встраивания iframe
class FrameOptionsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "ALLOWALL"
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

app.add_middleware(FrameOptionsMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(catalog.router, prefix="/api/v1")
app.include_router(players.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(frontend.router)  # Без префикса, т.к. он уже определён в роутере


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
