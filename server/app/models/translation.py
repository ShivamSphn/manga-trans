from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from PIL.Image import Image
from manga_translator import Config

class TranslateRequest(BaseModel):
    config: Config
    image: bytes

    class Config:
        arbitrary_types_allowed = True

class TranslationText(BaseModel):
    text: str
    translation: str
    box: List[int]  # [x, y, width, height]

class TranslationResponse(BaseModel):
    texts: List[TranslationText]
    image_data: Optional[bytes] = None
    
    def to_bytes(self) -> bytes:
        """Convert the response to a custom byte format"""
        # Implementation for byte serialization
        # This should match the existing byte format from the original code
        pass

class ExecutorInstance(BaseModel):
    ip: str
    port: int
    busy: bool = False

    def free_executor(self):
        self.busy = False

class ProgressUpdate(BaseModel):
    status: str
    progress: float
    message: Optional[str] = None

class QueueStatus(BaseModel):
    position: int
    total: int