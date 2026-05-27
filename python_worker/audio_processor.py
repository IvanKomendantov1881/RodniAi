"""
audio_processor.py
Конвертация аудио из форматов Telegram (.ogg) в формат для Vosk (.wav)
"""

import asyncio
from pathlib import Path


async def convert_to_wav(input_path: str, output_path: str) -> str:
    """
    Конвертирует аудиофайл в формат WAV (16kHz, mono, 16-bit PCM).

    Запускает ffmpeg как асинхронный подпроцесс. Требует ffmpeg,
    установленного и доступного в системном PATH.

    Args:
        input_path: Путь к исходному аудиофайлу (.ogg, .mp3, .m4a и др.).
        output_path: Путь для сохранения результирующего .wav-файла.
            Если файл существует, он будет перезаписан.

    Returns:
        output_path — путь к сконвертированному файлу.

    Raises:
        RuntimeError: Если ffmpeg завершился с ненулевым кодом возврата.
            Сообщение содержит stderr ffmpeg с описанием ошибки.
    """
    command = [
        "ffmpeg",
        "-loglevel", "error",
        "-i", input_path,
        "-ar", "16000",
        "-ac", "1",
        "-f", "wav",
        "-y",
        output_path
    ]

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg ошибка: {stderr.decode()}")

    return output_path


async def cleanup_files(*paths: str) -> None:
    """
    Удаляет указанные файлы, игнорируя отсутствующие.

    Предназначена для очистки временных файлов после обработки.
    Ошибки при удалении подавляются: если файл уже удалён или
    недоступен, функция продолжает удаление остальных путей.

    Args:
        *paths: Произвольное количество путей к файлам для удаления.
    """
    for path in paths:
        try:
            await asyncio.to_thread(Path(path).unlink, True)
        except Exception:
            pass
