from fastapi import APIRouter, Depends, HTTPException, status

from .admin import router as admin_router
from .source import router as source_router
from .conversation import router as conversation_router
from .sop import router as sop_router
from .plotly import router as plotly_router
from .tools import router as tools_router


router = APIRouter()

router.include_router(admin_router, prefix="/admin", tags=["admin"])
router.include_router(source_router, prefix="/sources", tags=["sources"])
router.include_router(conversation_router, prefix="/conversations", tags=["conversations"])
router.include_router(sop_router, prefix="/sops", tags=["sops"])
router.include_router(plotly_router, prefix="/plotly", tags=["plotly"])
router.include_router(tools_router, prefix="/tools", tags=["tools"])
