"""
pdf_processor.py
Извлечение текста из PDF-файлов для дальнейшей передачи в LLM.

Поддерживает:
  - Обычные PDF (с текстовым слоем) — через pdfplumber

Установка:
    pip install
"""

import asyncio
from pathlib import Path


async def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Асинхронно извлекает текст из PDF-файла.

    Если результат пустой, выбрасывает ValueError — файл может быть
    сканированным, защищённым или нечитаемым.

    Args:
        pdf_path: Путь к .pdf-файлу.

    Returns:
        Извлечённый текст всех страниц, объединённый через двойной перенос строки,
        без ведущих и хвостовых пробелов.

    Raises:
        FileNotFoundError: Если файл не найден по указанному пути.
        ValueError: Если расширение файла не .pdf или текст извлечь не удалось
            (пустой результат после обработки всех страниц).
        ImportError: Если библиотека pdfplumber не установлена.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF файл не найден: {pdf_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Ожидается .pdf файл, получен: {path.suffix}")

    text = await asyncio.to_thread(_extract_with_pdfplumber, pdf_path)

    if not text.strip():
        raise ValueError(
            "Не удалось извлечь текст из PDF. "
            "Файл может быть защищен паролем или не иметь читабельного содержания."
        )

    return text.strip()


def _extract_with_pdfplumber(pdf_path: str) -> str:
    """
    Извлекает текстовый слой из PDF через pdfplumber.

    Обходит все страницы документа и объединяет их текст через двойной
    перенос строки. Страницы без текстового слоя (например, сканы)
    пропускаются.

    Args:
        pdf_path: Путь к .pdf-файлу.

    Returns:
        Объединённый текст всех страниц. Пустая строка, если ни одна страница
        не содержит текстового слоя.

    Raises:
        ImportError: Если pdfplumber не установлен.
        pdfplumber.exceptions.PDFSyntaxError: Если файл повреждён или зашифрован.
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("Установи pdfplumber: pip install pdfplumber")

    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                pages_text.append(page_text)

    return "\n\n".join(pages_text)
