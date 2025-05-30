from bot.config import IMGBB_API_KEY

import aiohttp

async def get_image_bytes(image_url: str) -> bytes:
    """
    Получает двоичные данные изображения по URL.

    :param image_url: URL изображения
    :return: Двоичные данные изображения
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Ошибка получения изображения: {resp.status}")
            return await resp.read()


async def upload_to_imgbb(image_bytes: bytes) -> str:
    """
    Загружает изображение на imgbb и возвращает прямую ссылку на него.

    :param image_bytes: Двоичные данные изображения
    :return: URL загруженного изображения
    """
    upload_url = "https://api.imgbb.com/1/upload"

    data = {
        "key": IMGBB_API_KEY,
        "image": image_bytes.encode("base64") if isinstance(image_bytes, str) else image_bytes,
    }

    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field("key", IMGBB_API_KEY)
        data.add_field("image", image_bytes, filename="image.jpg", content_type="image/jpeg")

        async with session.post(upload_url, data=data) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Ошибка загрузки изображения: {resp.status}")
            json_resp = await resp.json()
            return json_resp["data"]["url"]