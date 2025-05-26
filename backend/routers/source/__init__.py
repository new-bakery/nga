
from fastapi import APIRouter, Depends, HTTPException, status

from .sources import router as sources_router


router = sources_router

