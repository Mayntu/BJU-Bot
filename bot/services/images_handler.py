from bot.config import IMGUR_CLIENT_ID

import aiohttp
import base64


async def upload_to_imgur(image_bytes: bytes) -> str:
    """
    Загружает изображение в Imgur и возвращает ссылку на него.
    :param image_bytes: Двоичные данные изображения
    :return: URL загруженного изображения
    :raises RuntimeError: Если загрузка не удалась
    """
    
    url = "https://api.imgur.com/3/image"
    headers = {
        "Authorization": f"Client-ID {IMGUR_CLIENT_ID}"
    }
    data = {
        "image": base64.b64encode(image_bytes).decode("utf-8"),
        "type": "base64"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=data) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"Ошибка загрузки в Imgur: статус {resp.status}, ответ: {text}")
            res = await resp.json()
            if not res.get("success"):
                raise RuntimeError(f"Ошибка загрузки в Imgur: {res}")
            return res["data"]["link"]
