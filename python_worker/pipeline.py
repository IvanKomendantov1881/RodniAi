"""
pipeline.py
Главный пайплайн: аудио/текст/PDF → карточка.

Использование:
    from pipeline import process_voice, process_text, process_pdf

    card, transcript = await process_voice("voice.ogg")
    card = await process_text("Митохондрия — это органелла клетки...")
    card, text = await process_pdf("lecture.pdf")

Все функции возвращают dict с полем "type": "exam" | "study_guide" | "summary".
Для форматирования используй format_card_for_telegram(card) из card_generator.
"""

import asyncio
import uuid

import audio_processor
import stt
import pdf_processor
from card_generator import generate_card, format_card_for_telegram


async def process_voice(ogg_path: str) -> tuple[dict, str]:
    """
    Выполняет полный пайплайн обработки голосового сообщения.

    Конвертирует .ogg-файл в .wav, транскрибирует речь через Vosk
    и передаёт текст в LLM для генерации карточки.
    Временный .wav-файл удаляется после завершения независимо от результата.

    Args:
        ogg_path: Путь к .ogg-файлу, полученному от Telegram.

    Returns:
        Кортеж (card, transcript), где card — словарь карточки,
        transcript — распознанный текст.

    Raises:
        ValueError: Если Vosk не смог распознать речь в аудиофайле.
        RuntimeError: Если ffmpeg вернул ненулевой код завершения.
        FileNotFoundError: Если модель Vosk не найдена по указанному пути.
    """
    wav_path = ogg_path.replace(".ogg", f"_{uuid.uuid4().hex[:8]}.wav")

    try:
        await audio_processor.convert_to_wav(ogg_path, wav_path)

        transcript = await stt.transcribe(wav_path)
        if not transcript:
            raise ValueError("Vosk не смог распознать речь. Попробуй говорить чётче или тише.")

        card = await generate_card(transcript)
        return card, transcript

    finally:
        await audio_processor.cleanup_files(wav_path)


async def process_text(text: str) -> dict:
    """
    Выполняет пайплайн обработки текстового сообщения.

    Проверяет минимальную длину текста и передаёт его в LLM
    для генерации структурированной карточки.

    Args:
        text: Текст от пользователя.

    Returns:
        Словарь карточки с полем "type": "exam" | "study_guide" | "summary".

    Raises:
        ValueError: Если длина текста после strip() меньше 10 символов.
    """
    if len(text.strip()) < 10:
        raise ValueError("Текст слишком короткий для создания карточки.")

    return await generate_card(text)


async def process_pdf(pdf_path: str) -> tuple[dict, str]:
    """
    Выполняет пайплайн обработки PDF-файла.

    Извлекает текст из PDF через pdfplumber (с OCR-fallback для сканов)
    и передаёт его в LLM для генерации структурированной карточки.

    Args:
        pdf_path: Путь к .pdf-файлу.

    Returns:
        Кортеж (card, extracted_text), где card — словарь карточки,
        extracted_text — извлечённый из PDF текст.

    Raises:
        FileNotFoundError: Если файл не найден по указанному пути.
        ValueError: Если текст извлечь не удалось (пустой или защищённый PDF).
        ImportError: Если не установлены библиотеки pdfplumber или pdf2image.
    """
    extracted_text = await pdf_processor.extract_text_from_pdf(pdf_path)
    card = await generate_card(extracted_text)
    return card, extracted_text
