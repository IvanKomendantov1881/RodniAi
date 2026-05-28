"""
card_generator.py
Анализ текста + генерация структурированного ответа через LLM.

Поддерживаемые типы ответа:
  - exam       — задачи/тесты: решение с пояснениями
  - study_guide — лекции/методички: структурированный разбор тем
  - summary    — общий текст: ключевые мысли
"""

import json
import re
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

FREELLM_BASE_URL = "http://localhost:3001/v1"
FREELLM_API_KEY  = token = os.getenv('FREELLM_API_KEY')
MODEL = "auto"

_client = None

def _get_client() -> AsyncOpenAI:
    """
    Возвращает синглтон-экземпляр AsyncOpenAI, создавая его при первом вызове.

    Returns:
        Настроенный экземпляр AsyncOpenAI с base_url и api_key из конфига модуля.
    """
    global _client
    if _client is None:
        _client = AsyncOpenAI(base_url=FREELLM_BASE_URL, api_key=FREELLM_API_KEY)
    return _client


SYSTEM_PROMPT = """You are an academic content analyzer and structured learning assistant.
Analyze the input text and determine its type:
1. EXAM — tests, assignments, контрольные, exercises, questions, tasks
2. STUDY_GUIDE — lectures, методички, educational material, theory explanations
3. SUMMARY — general informational text
Follow ONLY the instructions for the detected type.
CASE 1: EXAM
If the input contains tasks, exercises, numbered questions, variants, or anything resembling a test/exam:
- Solve ALL tasks
- Explain the reasoning step-by-step
- Keep explanations concise but understandable
- Preserve the original order
- Never skip tasks
Return ONLY this JSON structure:
{
  "type": "exam",
  "tasks": [
    {
      "question": "original question",
      "solution": "step-by-step explanation",
      "answer": "final short answer"
    }
  ]
}
CASE 2: STUDY_GUIDE
If the input is educational material intended for studying or presenting:
- Extract the main concepts
- Explain what should be understood or said
- Structure the material logically
- Focus on clarity and understanding
- Remove unimportant details
Return ONLY this JSON structure:
{
  "type": "study_guide",
  "topics": [
    {
      "title": "topic name",
      "explanation": "clear explanation",
      "important_points": [
        "point 1",
        "point 2"
      ]
    }
  ]
}
CASE 3: SUMMARY
If the input is general informational text:
- Extract key ideas
- Create a concise structured summary
- Keep only important information
- Structure the summary logically
- Highlight the core meaning of the text
Return ONLY this JSON structure:
{
  "type": "summary",
  "summary": {
    "key_points": [
      "point 1",
      "point 2"
    ],
    "structured_summary": "short structured summary"
  }
}
IMPORTANT:
The response is parsed automatically by a JSON parser.
Any extra text will break the parser.
Your ENTIRE response MUST be:
- valid raw JSON
- without markdown
- without code fences
- without comments
- without explanations outside JSON
- without additional text
STRICT RULES:
- Start with {
- End with }
- Use only double quotes
- Never output invalid JSON
- Never mix formats between cases
- Never add extra fields
- Always close arrays and objects properly
If uncertain about the type, choose the closest matching type and still return valid JSON only.
IMPORTANT LANGUAGE RULE:
All generated content inside the JSON MUST be written in Russian.
This includes:
- explanations
- summaries
- answers
- flashcards
- key points
- titles
- tags may remain in English snake_case
Never switch to English unless the input explicitly requires it.
"""


async def generate_card(text: str) -> dict:
    """
    Отправляет текст в LLM и возвращает распарсенный словарь карточки.

    Тип ответа определяется моделью автоматически на основе содержания текста.

    Args:
        text: Исходный текст для анализа (транскрипт, PDF-контент или пользовательский ввод).

    Returns:
        Словарь с полем "type" и соответствующими данными:
        - "exam":        {"type": "exam", "tasks": [...]}
        - "study_guide": {"type": "study_guide", "topics": [...]}
        - "summary":     {"type": "summary", "summary": {...}}

    Raises:
        ValueError: Если ответ LLM не удалось распарсить как валидный JSON.
        openai.APIError: При сетевых ошибках или ошибках API.
    """
    client = _get_client()

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"Analyze this text:\n\n{text}"}
        ],
        temperature=0.3,
        max_tokens=1500,
    )

    raw = response.choices[0].message.content.strip()
    return _parse_json_response(raw)


def _parse_json_response(raw: str) -> dict:
    """
    Устойчиво парсит JSON из сырого ответа LLM.

    Последовательно применяет три стратегии:
    1. Удаляет markdown-обёртки (```json ... ```) и парсит напрямую.
    2. Ищет первый JSON-объект в тексте через регулярное выражение.
    3. Выбрасывает ValueError, если ни одна стратегия не сработала.

    Args:
        raw: Сырая строка из ответа LLM.

    Returns:
        Распарсенный словарь.

    Raises:
        ValueError: Если JSON не удалось извлечь ни одной из стратегий.
            Сообщение содержит исходный ответ и подсказку по устранению.
    """
    cleaned = re.sub(r"```(?:json)?\s*", "", raw)
    cleaned = re.sub(r"```", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Не удалось распарсить ответ LLM как JSON.\n"
        f"Получено:\n{raw}\n\n"
        f"Попробуй сменить модель в переменной MODEL в card_generator.py"
    )


def format_card_for_telegram(data: dict) -> str:
    """
    Форматирует словарь карточки в строку с Telegram Markdown.

    Делегирует форматирование в приватную функцию в зависимости
    от значения поля "type".

    Args:
        data: Распарсенный словарь из generate_card().

    Returns:
        Отформатированная строка, готовая для отправки через Telegram Bot API
        с parse_mode="Markdown".

    Raises:
        ValueError: Если значение поля "type" не является одним из
            "exam", "study_guide", "summary".
    """
    content_type = data.get("type")

    if content_type == "exam":
        return _format_exam(data)
    elif content_type == "study_guide":
        return _format_study_guide(data)
    elif content_type == "summary":
        return _format_summary(data)
    else:
        raise ValueError(f"Неизвестный тип ответа LLM: '{content_type}'")


def _format_exam(data: dict) -> str:
    """
    Форматирует карточку типа "exam" в Telegram Markdown.

    Args:
        data: Словарь с ключом "tasks" — списком задач, каждая из которых
              содержит поля "question", "solution", "answer".

    Returns:
        Строка с пронумерованными задачами, решениями и ответами,
        разделёнными горизонтальными линиями.
    """
    tasks = data.get("tasks", [])
    lines = ["📝 *Решение задач:*\n"]

    for i, task in enumerate(tasks, start=1):
        lines.append(f"*Задача {i}:* {task.get('question', '')}")
        lines.append(f"💡 *Решение:* {task.get('solution', '')}")
        lines.append(f"✅ *Ответ:* {task.get('answer', '')}")
        if i < len(tasks):
            lines.append("─" * 20)

    return "\n".join(lines)


def _format_study_guide(data: dict) -> str:
    """
    Форматирует карточку типа "study_guide" в Telegram Markdown.

    Args:
        data: Словарь с ключом "topics" — списком тем, каждая из которых
              содержит поля "title", "explanation" и "important_points".

    Returns:
        Строка с пронумерованными темами, пояснениями и маркированными
        ключевыми моментами.
    """
    topics = data.get("topics", [])
    lines = ["📚 *Учебный материал:*\n"]

    for i, topic in enumerate(topics, start=1):
        lines.append(f"*{i}. {topic.get('title', '')}*")
        lines.append(topic.get("explanation", ""))

        points = topic.get("important_points", [])
        if points:
            lines.append("*Ключевые моменты:*")
            for point in points:
                lines.append(f"  • {point}")

        if i < len(topics):
            lines.append("")

    return "\n".join(lines)


def _format_summary(data: dict) -> str:
    """
    Форматирует карточку типа "summary" в Telegram Markdown.

    Args:
        data: Словарь с ключом "summary", содержащим вложенные поля
              "key_points" (список строк) и "structured_summary" (строка).

    Returns:
        Строка с маркированным списком ключевых мыслей и кратким содержанием.
    """
    summary = data.get("summary", {})

    key_points = summary.get("key_points", [])
    key_points_str = "\n".join(f"  • {point}" for point in key_points)

    structured_summary = summary.get("structured_summary", "")

    return (
        f"📌 *Ключевые мысли:*\n"
        f"{key_points_str}\n\n"
        f"📋 *Краткое содержание:*\n"
        f"{structured_summary}"
    )
