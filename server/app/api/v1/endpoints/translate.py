from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse, Response
from typing import Callable, Any
import json

from ....models.translation import TranslateRequest, TranslationResponse
from ....services.translation import get_translation_service
from ....core.config import get_settings
from manga_translator import Config

router = APIRouter()

def create_streaming_response(
    transform_func: Callable[[Any], bytes],
    request: Request,
    config: Config,
    image_data: bytes
) -> StreamingResponse:
    """Create a streaming response for translation results"""
    async def stream_generator():
        translation_service = get_translation_service()
        
        async def progress_callback(progress):
            # Convert progress to bytes format with status code
            status_code = {
                "waiting": 4,
                "processing": 1,
                "error": 2,
                "complete": 0
            }.get(progress.status, 1)
            
            data = json.dumps(progress.dict()).encode('utf-8')
            yield bytes([status_code]) + len(data).to_bytes(4, 'big') + data

        ctx = await translation_service.translate(
            image_data=image_data,
            config=config,
            progress_callback=progress_callback
        )
        
        # Send final result
        result = transform_func(ctx)
        yield bytes([0]) + len(result).to_bytes(4, 'big') + result

    return StreamingResponse(stream_generator())

# JSON endpoints
@router.post("/json", response_model=TranslationResponse, tags=["api", "json"])
async def translate_json(request: Request, data: TranslateRequest):
    """Translate and return JSON response"""
    translation_service = get_translation_service()
    ctx = await translation_service.translate(data.image, data.config)
    return translation_service.transform_to_json(ctx)

@router.post("/json/stream", response_class=StreamingResponse, tags=["api", "json"])
async def translate_json_stream(request: Request, data: TranslateRequest):
    """Stream translation results as JSON"""
    return create_streaming_response(
        get_translation_service().transform_to_json,
        request,
        data.config,
        data.image
    )

# Bytes endpoints
@router.post("/bytes", response_class=StreamingResponse, tags=["api", "bytes"])
async def translate_bytes(request: Request, data: TranslateRequest):
    """Translate and return bytes response"""
    translation_service = get_translation_service()
    ctx = await translation_service.translate(data.image, data.config)
    return Response(content=translation_service.transform_to_bytes(ctx))

@router.post("/bytes/stream", response_class=StreamingResponse, tags=["api", "bytes"])
async def translate_bytes_stream(request: Request, data: TranslateRequest):
    """Stream translation results as bytes"""
    return create_streaming_response(
        get_translation_service().transform_to_bytes,
        request,
        data.config,
        data.image
    )

# Image endpoints
@router.post("/image", response_class=StreamingResponse, tags=["api", "image"])
async def translate_image(request: Request, data: TranslateRequest):
    """Translate and return image response"""
    translation_service = get_translation_service()
    ctx = await translation_service.translate(data.image, data.config)
    return Response(
        content=translation_service.transform_to_image(ctx),
        media_type="image/png"
    )

@router.post("/image/stream", response_class=StreamingResponse, tags=["api", "image"])
async def translate_image_stream(request: Request, data: TranslateRequest):
    """Stream translation results as image"""
    return create_streaming_response(
        get_translation_service().transform_to_image,
        request,
        data.config,
        data.image
    )

# Form-based endpoints
@router.post("/with-form/json", response_model=TranslationResponse, tags=["api", "form"])
async def translate_json_form(
    request: Request,
    image: UploadFile = File(...),
    config: str = Form("{}")
):
    """Translate using form data and return JSON response"""
    translation_service = get_translation_service()
    image_data = await image.read()
    ctx = await translation_service.translate(
        image_data=image_data,
        config=Config.parse_raw(config)
    )
    return translation_service.transform_to_json(ctx)

# Add remaining form-based endpoints following the same pattern...