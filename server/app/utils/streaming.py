from typing import Any, Callable, Awaitable
import aiohttp
from PIL.Image import Image
import json

from manga_translator import Config
from ..models.translation import ProgressUpdate

async def fetch_data(url: str, image: Image, config: Config) -> Any:
    """Fetch data from executor instance"""
    async with aiohttp.ClientSession() as session:
        # Prepare the image and config data
        data = aiohttp.FormData()
        image_bytes = image_to_bytes(image)
        data.add_field('image', image_bytes, filename='image.png', content_type='image/png')
        data.add_field('config', config.json(), content_type='application/json')

        async with session.post(url, data=data) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Error from executor: {error_text}")
            return await response.json()

async def fetch_data_stream(
    url: str,
    image: Image,
    config: Config,
    progress_callback: Callable[[ProgressUpdate], Awaitable[None]]
) -> None:
    """Fetch streaming data from executor instance"""
    async with aiohttp.ClientSession() as session:
        # Prepare the image and config data
        data = aiohttp.FormData()
        image_bytes = image_to_bytes(image)
        data.add_field('image', image_bytes, filename='image.png', content_type='image/png')
        data.add_field('config', config.json(), content_type='application/json')

        async with session.post(url, data=data) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Error from executor: {error_text}")

            # Process the streaming response
            async for line in response.content:
                try:
                    data = json.loads(line)
                    if 'status' in data:
                        await progress_callback(ProgressUpdate(**data))
                except json.JSONDecodeError:
                    continue