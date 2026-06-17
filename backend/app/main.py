from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, collections, health, upload
from app.config import settings
from app.db import fts, history

fts.init_db()
history.init_db()

app = FastAPI(title="DocuMind API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(collections.router)
app.include_router(upload.router)
app.include_router(chat.router)
