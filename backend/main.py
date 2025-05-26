from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
import json
import logging

import uvicorn.config

import models
from config import config
from logging_config import setup_logging
from routers import router as api_router
from routers.auth import router as auth_router
from source_type_manager import setup_source_types
from util.module_discover import ModuleContext, ModuleRegistry
import database

setup_logging()

setup_source_types()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.startup(app)
    yield
    await database.shutdown(app)
    

app = FastAPI(
    title="nga",
    description="next generation analytics",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router, prefix="", tags=["auth"])
app.include_router(api_router, prefix="/api", tags=["api"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 

# uvicorn main:app --host 0.0.0.0 --port 8000

# celery -A celery_app.worker worker --loglevel=debug