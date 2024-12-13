from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path
import os
import signal
import subprocess
import sys
from argparse import Namespace

from .core.config import get_settings, initialize_nonce, setup_upload_cache
from .models.translation import ExecutorInstance
from .services.executor import get_executor_service
from .api.v1.endpoints import translate, executor

def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
    )

    # Set up CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(translate.router, prefix=f"{settings.API_V1_STR}/translate", tags=["translate"])
    app.include_router(executor.router, prefix=f"{settings.API_V1_STR}/executor", tags=["executor"])

    # UI Routes
    @app.get("/", response_class=HTMLResponse, tags=["ui"])
    async def index() -> HTMLResponse:
        script_directory = Path(__file__).parent.parent
        html_file = script_directory / "static" / "index.html"
        html_content = html_file.read_text()
        return HTMLResponse(content=html_content)

    @app.get("/manual", response_class=HTMLResponse, tags=["ui"])
    async def manual() -> HTMLResponse:
        script_directory = Path(__file__).parent.parent
        html_file = script_directory / "static" / "manual.html"
        html_content = html_file.read_text()
        return HTMLResponse(content=html_content)

    return app

def start_translator_client_proc(host: str, port: int, nonce: str, params: Namespace):
    """Start a translator client process"""
    cmds = [
        sys.executable,
        '-m', 'manga_translator',
        'shared',
        '--host', host,
        '--port', str(port),
        '--nonce', nonce,
    ]
    
    # Add optional flags
    if params.use_gpu:
        cmds.append('--use-gpu')
    if params.use_gpu_limited:
        cmds.append('--use-gpu-limited')
    if params.ignore_errors:
        cmds.append('--ignore-errors')
    if params.verbose:
        cmds.append('--verbose')

    # Start process
    base_path = os.path.dirname(os.path.abspath(__file__))
    parent = os.path.dirname(os.path.dirname(base_path))
    proc = subprocess.Popen(cmds, cwd=parent)
    
    # Register executor instance
    executor_service = get_executor_service()
    executor_service.register(ExecutorInstance(ip=host, port=port))

    # Handle exit signals
    def handle_exit_signals(signal, frame):
        proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit_signals)
    signal.signal(signal.SIGTERM, handle_exit_signals)

    return proc

def prepare_app(args: Namespace):
    """Prepare the application"""
    # Initialize nonce
    settings = get_settings()
    settings.NONCE = initialize_nonce(args.nonce)
    
    # Start translator client if requested
    proc = None
    if args.start_instance:
        proc = start_translator_client_proc(args.host, args.port + 1, settings.NONCE, args)
    
    # Setup upload cache
    setup_upload_cache()
    
    return proc

app = create_app()

if __name__ == '__main__':
    import uvicorn
    from manga_translator.args import parse_arguments

    args = parse_arguments()
    args.start_instance = True
    proc = prepare_app(args)
    
    try:
        uvicorn.run(app, host=args.host, port=args.port)
    except Exception:
        if proc:
            proc.terminate()