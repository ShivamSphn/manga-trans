from pydantic_settings import BaseSettings
from functools import lru_cache
import os
import secrets
from typing import Optional

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Manga Translator API"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    # Security
    NONCE: Optional[str] = None
    
    # Upload Cache
    UPLOAD_CACHE_DIR: str = "upload-cache"
    
    class Config:
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

def initialize_nonce(nonce: Optional[str] = None) -> str:
    """Initialize the nonce for executor authentication"""
    if nonce:
        return nonce
    return os.getenv('MT_WEB_NONCE', secrets.token_hex(16))

def setup_upload_cache():
    """Setup the upload cache directory"""
    settings = get_settings()
    if os.path.exists(settings.UPLOAD_CACHE_DIR):
        import shutil
        shutil.rmtree(settings.UPLOAD_CACHE_DIR)
    os.makedirs(settings.UPLOAD_CACHE_DIR)