from tempfile import NamedTemporaryFile

from bot.services.openai_client import client

import aiohttp


async def get_voice_path(file_url : str) -> str:
    """
    Получает путь к аудиофайлу по URL.
    :param file_url: URL аудиофайла
    :return: Путь к аудиофайлу
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            if resp.status == 200:
                with NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
                    tmp.write(await resp.read())
                    tmp_path = tmp.name
                    return tmp_path
            else:
                raise RuntimeError(f"Ошибка получения аудиофайла: {resp.status}")

async def transcribe_audio(file_path: str) -> str:
    """
    Транскрибирует аудиофайл с помощью OpenAI Whisper API.
    :param file_path: Путь к аудиофайлу
    :return: Текстовая транскрипция аудиофайла
    """
    with open(file_path, "rb") as audio_file:
        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        return transcript.text

async def close_voice_file(file_path: str):
    """
    Закрывает файл, чтобы он был удален при выходе из контекста.
    :param file_path: Путь к файлу
    """
    with NamedTemporaryFile(delete=True) as tmp_file:
        tmp_file.name = file_path  # Устанавливаем имя временного файла
        tmp_file.close()  # Закрываем файл, чтобы он был удален при выходе из контекста
