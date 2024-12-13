from asyncio import Queue, Event
from typing import Optional, Any, Callable, Awaitable
from PIL.Image import Image

from manga_translator import Config
from ..models.translation import ProgressUpdate
from ..services.executor import get_executor_service

class TaskQueue:
    def __init__(self):
        self.queue: Queue = Queue()
        self.event = Event()

    async def add_task(self, task: dict) -> None:
        """Add a task to the queue"""
        await self.queue.put(task)
        self.event.set()
        self.event.clear()

    async def get_task(self) -> dict:
        """Get the next task from the queue"""
        return await self.queue.get()

    def task_done(self) -> None:
        """Mark a task as done"""
        self.queue.task_done()

    async def update_event(self) -> None:
        """Update the queue event"""
        self.event.set()
        self.event.clear()

    def get_queue_size(self) -> int:
        """Get the current queue size"""
        return self.queue.qsize()

    async def process_task(
        self,
        image: Image,
        config: Config,
        progress_callback: Optional[Callable[[ProgressUpdate], Awaitable[None]]] = None
    ) -> Any:
        """Process a translation task"""
        # Get an executor
        if progress_callback:
            await progress_callback(ProgressUpdate(
                status="waiting",
                progress=0.0,
                message="Waiting for available translator instance"
            ))

        executor_service = get_executor_service()
        instance = await executor_service.find_executor()

        try:
            # Send the translation request
            result = await executor_service.send_translation_request(
                instance=instance,
                image=image,
                config=config,
                stream=progress_callback is not None,
                progress_callback=progress_callback
            )
            return result
        finally:
            # Free the executor
            await executor_service.free_executor(instance)

# Global task queue instance
_task_queue: Optional[TaskQueue] = None

def get_task_queue() -> TaskQueue:
    """Get the global task queue instance"""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue