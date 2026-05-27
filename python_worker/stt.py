"""
stt.py
Speech-to-Text через Vosk (полностью локально, без интернета).

Установка:
    pip install vosk

Модели:
    Маленькая (~45MB, быстрая):  https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip
    Большая  (~1.8GB, точнее):   https://alphacephei.com/vosk/models/vosk-model-ru-0.42.zip
"""

import asyncio
import json
import wave
from pathlib import Path

from vosk import Model, KaldiRecognizer

MODEL_PATH = str(Path(__file__).parent.parent / "vosk-model-small-ru-0.22")

_model = None


def _load_model() -> Model:
    """
    Загружает модель Vosk с диска и кэширует её в глобальной переменной.

    Синхронная операция: предназначена для однократного вызова через
    asyncio.to_thread, чтобы не блокировать event loop во время загрузки.

    Returns:
        Загруженный экземпляр vosk.Model.

    Raises:
        FileNotFoundError: Если директория модели не найдена по пути MODEL_PATH.
    """
    global _model
    if _model is None:
        if not Path(MODEL_PATH).exists():
            raise FileNotFoundError(
                f"Vosk модель не найдена: {MODEL_PATH}\n"
            )
        _model = Model(MODEL_PATH)
    return _model


async def _get_model() -> Model:
    """
    Возвращает экземпляр модели Vosk, загружая его при первом обращении.

    Использует asyncio.to_thread для выноса тяжёлой загрузки из event loop.
    При повторных вызовах возвращает уже закэшированный экземпляр.

    Returns:
        Загруженный экземпляр vosk.Model.
    """
    return await asyncio.to_thread(_load_model)


def _run_transcription(wav_path: str, model: Model) -> str:
    """
    Транскрибирует .wav-файл в текст с помощью KaldiRecognizer.

    Читает аудио чанками по 4000 фреймов, чтобы не загружать весь файл
    в память. Результаты промежуточных и финального распознавания
    объединяются в одну строку.

    Args:
        wav_path: Путь к .wav-файлу (16kHz, mono, 16-bit PCM).
        model: Загруженный экземпляр vosk.Model.

    Returns:
        Распознанный текст в виде одной строки.

    Raises:
        ValueError: Если WAV-файл не является mono или не имеет 16-bit глубины.
        wave.Error: Если файл повреждён или не является корректным WAV.
    """
    with wave.open(wav_path, "rb") as wf:
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
            raise ValueError("WAV должен быть mono, 16-bit. Используй audio_processor.convert_to_wav()")

        sample_rate = wf.getframerate()
        recognizer = KaldiRecognizer(model, sample_rate)
        recognizer.SetWords(True)

        results = []
        chunk_size = 4000

        while True:
            data = wf.readframes(chunk_size)
            if not data:
                break

            if recognizer.AcceptWaveform(data):
                partial = json.loads(recognizer.Result())
                if partial.get("text"):
                    results.append(partial["text"])

        final = json.loads(recognizer.FinalResult())
        if final.get("text"):
            results.append(final["text"])

    return " ".join(results).strip()


async def transcribe(wav_path: str) -> str:
    """
    Асинхронно транскрибирует .wav-файл в текст через Vosk.

    Выносит CPU-bound транскрипцию в пул потоков через asyncio.to_thread,
    чтобы не блокировать event loop на время распознавания.

    Args:
        wav_path: Путь к .wav-файлу (16kHz, mono — после audio_processor.convert_to_wav).

    Returns:
        Распознанный текст строкой. Пустая строка, если речь не обнаружена.

    Raises:
        FileNotFoundError: Если модель Vosk не найдена.
        ValueError: Если формат WAV-файла не соответствует требованиям Vosk.
    """
    model = await _get_model()
    return await asyncio.to_thread(_run_transcription, wav_path, model)
