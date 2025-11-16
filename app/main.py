import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.recommendations import router as recommendations_router

app = FastAPI(title="Grocery AI Recommendations API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommendations_router)


@app.get("/")
def root():
    return {"status": "ok", "service": "recommendations"}


@app.on_event("startup")
def on_startup():
    return None
