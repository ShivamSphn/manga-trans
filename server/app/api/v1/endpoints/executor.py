from fastapi import APIRouter, Request, Header
from typing import Optional

from ....models.translation import ExecutorInstance
from ....services.executor import get_executor_service
from ....core.security import verify_nonce, get_client_ip

router = APIRouter()

@router.post("/register", response_description="Register executor instance", tags=["internal-api"])
async def register_instance(
    instance: ExecutorInstance,
    request: Request,
    nonce: Optional[str] = Header(None, alias="X-Nonce")
):
    """Register a new executor instance"""
    # Verify nonce
    await verify_nonce(request, nonce)
    
    # Update instance IP with actual client IP
    instance.ip = get_client_ip(request)
    
    # Register instance
    executor_service = get_executor_service()
    executor_service.register(instance)
    
    return {"status": "registered"}

@router.get("/free-count", response_description="Get number of free executors", tags=["api"])
async def get_free_executors():
    """Get the number of available executor instances"""
    executor_service = get_executor_service()
    return executor_service.free_executors()