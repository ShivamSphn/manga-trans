from typing import Any, Callable, Optional, Awaitable
from PIL import Image
import io

from manga_translator import Config
from ..models.translation import TranslationResponse, ProgressUpdate
from ..services.queue import get_task_queue
from ..utils.image import image_to_bytes, bytes_to_image

class TranslationService:
    @staticmethod
    async def translate(
        image_data: bytes,
        config: Config,
        progress_callback: Optional[Callable[[ProgressUpdate], Awaitable[None]]] = None
    ) -> Any:
        """
        Handle translation request
        Returns different formats based on the original response type (json/bytes/image)
        """
        # Convert bytes to PIL Image
        image = bytes_to_image(image_data)
        
        # Process through task queue
        task_queue = get_task_queue()
        result = await task_queue.process_task(
            image=image,
            config=config,
            progress_callback=progress_callback
        )
        
        return result

    @staticmethod
    def transform_to_json(ctx: Any) -> TranslationResponse:
        """Transform translation context to JSON response"""
        # Implementation should match the original to_translation function
        # This would create a TranslationResponse object from the context
        pass

    @staticmethod
    def transform_to_bytes(ctx: Any) -> bytes:
        """Transform translation context to bytes response"""
        # Implementation should match the original to_bytes function
        return TranslationService.transform_to_json(ctx).to_bytes()

    @staticmethod
    def transform_to_image(ctx: Any) -> bytes:
        """Transform translation context to image response"""
        return image_to_bytes(ctx.result)

# Global translation service instance
_translation_service: Optional[TranslationService] = None

def get_translation_service() -> TranslationService:
    """Get the global translation service instance"""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service