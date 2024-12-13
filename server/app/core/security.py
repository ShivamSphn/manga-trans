from fastapi import HTTPException, Header, Request
from typing import Optional

from .config import get_settings

async def verify_nonce(
    request: Request,
    nonce: Optional[str] = Header(None, alias="X-Nonce")
) -> None:
    """Verify the nonce for executor authentication"""
    settings = get_settings()
    if not nonce or nonce != settings.NONCE:
        raise HTTPException(
            status_code=401,
            detail="Invalid nonce"
        )

def get_client_ip(request: Request) -> str:
    """Get the client IP address from the request"""
    return request.client.host