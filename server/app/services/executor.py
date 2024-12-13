from asyncio import Event, Lock
from typing import List, Optional
from PIL.Image import Image

from ..models.translation import ExecutorInstance
from manga_translator import Config
from ..core.security import get_client_ip

class ExecutorService:
    def __init__(self):
        self._executors: List[ExecutorInstance] = []
        self._lock: Lock = Lock()
        self._event = Event()

    def register(self, instance: ExecutorInstance) -> None:
        """Register a new executor instance"""
        self._executors.append(instance)

    def free_executors(self) -> int:
        """Get the number of free executors"""
        return len([item for item in self._executors if not item.busy])

    async def _find_instance(self) -> Optional[ExecutorInstance]:
        """Find a free executor instance"""
        while True:
            instance = next((x for x in self._executors if not x.busy), None)
            if instance is not None:
                return instance
            await self._event.wait()

    async def find_executor(self) -> ExecutorInstance:
        """Find and reserve an executor instance"""
        async with self._lock:
            instance = await self._find_instance()
            instance.busy = True
            return instance

    async def free_executor(self, instance: ExecutorInstance) -> None:
        """Free an executor instance"""
        instance.free_executor()
        self._event.set()
        self._event.clear()
        # Notify queue about available executor
        from ..services.queue import get_task_queue
        await get_task_queue().update_event()

    async def send_translation_request(
        self, 
        instance: ExecutorInstance,
        image: Image, 
        config: Config,
        stream: bool = False,
        progress_callback = None
    ):
        """Send translation request to executor instance"""
        base_url = f"http://{instance.ip}:{instance.port}"
        endpoint = "/execute/translate" if stream else "/simple_execute/translate"
        
        if stream and progress_callback:
            # Implementation for streaming with progress updates
            from ..utils.streaming import fetch_data_stream
            await fetch_data_stream(f"{base_url}{endpoint}", image, config, progress_callback)
        else:
            # Implementation for simple request
            from ..utils.streaming import fetch_data
            return await fetch_data(f"{base_url}{endpoint}", image, config)

# Global executor service instance
_executor_service: Optional[ExecutorService] = None

def get_executor_service() -> ExecutorService:
    """Get the global executor service instance"""
    global _executor_service
    if _executor_service is None:
        _executor_service = ExecutorService()
    return _executor_service