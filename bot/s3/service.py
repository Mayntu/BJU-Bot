from uuid import uuid4
from io import BytesIO

from bot.config import S3_CONFIG
from bot.s3.client import get_client


async def upload_image(image_bytes: bytes, user_id: int) -> str:
    """
    Загружает изображение на imgbb и возвращает прямую ссылку на него.

    :param image_bytes: Двоичные данные изображения
    :param user_id: id пользователя
    :return: URL загруженного изображения
    """
    print(isinstance(image_bytes, bytes))
    filename = f"user_uploads/{user_id}/image_{uuid4().hex}.jpg"
    async with get_client() as s3:
        await s3.put_object(
            Bucket=S3_CONFIG.BUCKET_NAME,
            Key=filename,
            Body=image_bytes,
            ContentType="image/jpeg",
            ACL="public-read"
        )
    return f"https://s3.twcstorage.ru/{S3_CONFIG.BUCKET_NAME}/{filename}"


async def delete_file(filename: str):
    async with get_client() as s3:
        await s3.delete_object(
            Bucket=S3_CONFIG.BUCKET_NAME,
            Key=filename
        )