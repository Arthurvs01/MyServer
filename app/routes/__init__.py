from .auth import router as auth_router
from .home import router as home_router
from .info import router as info_router
from .storage import router as storage_router
from .api import api_bp as api_router

__all__ = ["auth_router", "home_router", "info_router", "storage_router", "api_router"]
