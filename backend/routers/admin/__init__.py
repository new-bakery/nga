from fastapi import APIRouter
from .users import router as users_router
from .sources import router as sources_router

router = APIRouter()

router.include_router(users_router , prefix="/users", tags=["users"])
router.include_router(sources_router , prefix="/sources", tags=["sources"])

