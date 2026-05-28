# RodniAi
RodnenkAI — AI Telegram Learning Bot
📌 Описание проекта

RodnenkAI — это интеллектуальный Telegram-бот для обучения и обработки учебных материалов с использованием микросервисной архитектуры.

Проект сочетает:

Go backend
Python AI workers
RabbitMQ
PostgreSQL
Telegram Bot API
AI/NLP сервисы
🚀 Основные возможности
📚 1. Learning Assistant

Пользователь может:

отправить тему для изучения
получить краткое объяснение
получать повторные вопросы по системе интервального повторения:
через 15 минут
через 1 час
через 6 часов
через 1 день
🎤 2. Audio Processing

Бот умеет:

принимать voice messages
принимать mp3/m4a/wav файлы
распознавать речь
выделять ключевые мысли
делать summary лекций

Планируемые технологии:

Whisper
Vosk
SpeechRecognition
ffmpeg
📄 3. PDF Processing

Бот умеет:

принимать PDF-файлы
извлекать текст
выделять главные идеи
использовать PDF как учебный материал

Планируемые библиотеки:

PyPDF2
pdfplumber
pymupdf (fitz)
🇬🇧 4. English Learning System

Пользователь может:

ввести английское слово
получить определение на английском
получить пример предложения
сохранить слово в словарь
просматривать словарь
удалять слова
очищать словарь
🧠 Архитектура проекта

Проект построен на event-driven микросервисной архитектуре.

📦 Общая схема
Telegram
   ↓
Go Bot Gateway
   ↓
Dispatcher
   ↓
RabbitMQ Queue
   ↓
Python Workers
   ↓
AI/NLP Processing
   ↓
RabbitMQ Results Queue
   ↓
Go Bot
   ↓
Telegram Response
🏗 Архитектурные принципы
✅ Разделение ответственности
Go отвечает за:
Telegram API
маршрутизацию сообщений
загрузку файлов
очереди
orchestration
Python отвечает за:
AI/NLP
обработку аудио
обработку PDF
работу со словарем
интеграцию с LLM API
✅ Асинхронная обработка

Все тяжёлые задачи выполняются через RabbitMQ:

аудио
PDF
NLP
AI processing

Это позволяет:

не блокировать Telegram bot
масштабировать workers
распределять нагрузку
📁 Структура проекта
project/
│
├── go-bot/
│   │
│   ├── cmd/
│   │    └── main.go
│   │
│   ├── internal/
│   │    ├── dispatcher/
│   │    ├── queue/
│   │    ├── storage/
│   │    └── telegram/
│   │
│   ├── storage/
│   ├── .env
│   └── go.mod
│
├── python-services/
│   │
│   ├── english_worker/
│   ├── audio_worker/
│   ├── pdf_worker/
│   │
│   ├── database.py
│   ├── worker.py
│   ├── llm_service.py
│   └── requirements.txt
│
├── docker-compose.yml
│
└── README.md
⚙️ Используемые технологии
Backend
Go
Python
Message Broker
RabbitMQ
Database
PostgreSQL
SQLAlchemy ORM
Telegram
go-telegram-bot-api
AI/NLP
Whisper
Vosk
OpenAI API
Gemini API
FreeLLMAPI
PDF
PyPDF2
pdfplumber
pymupdf
Infrastructure
Docker
Docker Compose
Linux VPS
🧩 RabbitMQ Architecture
Queue: python_tasks

Go отправляет задачи:

{
  "type": "english",
  "user_id": 123,
  "payload": {
    "action": "add_word",
    "word": "hello"
  }
}
Queue: go_results

Python возвращает результаты:

{
  "action": "add_word",
  "user_id": 123,
  "status": "success",
  "data": {
    "word": "hello",
    "definition": "...",
    "example": "..."
  }
}
🗄 База данных
PostgreSQL

Используется для:

хранения словаря пользователя
хранения учебных материалов
хранения расписания повторений
Таблица словаря
CREATE TABLE user_words (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    word TEXT NOT NULL,
    definition TEXT,
    example TEXT
);
🤖 Telegram Commands
/english <word>

Добавить слово в словарь.

Пример:
/english hello
/teach <topic>

Начать изучение темы.

Пример:
/teach linear algebra
🎧 Поддерживаемые форматы
Audio
ogg
mp3
wav
m4a
Documents
pdf
🔄 Workflow Examples
Audio Pipeline
User sends audio
        ↓
Go downloads file
        ↓
RabbitMQ task
        ↓
Python audio worker
        ↓
Speech-to-text
        ↓
Summary generation
        ↓
Result queue
        ↓
Go sends Telegram message
English Learning Pipeline
/english hello
        ↓
Go dispatcher
        ↓
RabbitMQ
        ↓
Python NLP worker
        ↓
Dictionary API
        ↓
PostgreSQL
        ↓
Result queue
        ↓
Telegram response
🐳 Docker Deployment
Запуск RabbitMQ
docker run -d \
  --hostname rabbit \
  --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3-management
Docker Compose
version: '3'

services:

  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"

  postgres:
    image: postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres

  go-bot:
    build: ./go-bot

  python-worker:
    build: ./python-services
🌍 Deployment

Проект планируется размещать на Linux VPS в Европе:

Германия
Нидерланды
Финляндия

Это необходимо для:

стабильной работы AI API
уменьшения ограничений
постоянной доступности бота
🔒 Безопасность
Все токены хранятся в .env
API ключи не коммитятся в Git
Используется .gitignore
👨‍💻 Команда проекта
Go Backend Developer
Telegram bot
Dispatcher
RabbitMQ integration
File handling
Infrastructure
Python AI Developer
Audio processing
Speech-to-text
Summarization
AI integrations
Python NLP Developer
English learning system
PDF extraction
Dictionary logic
Database logic
📈 Возможности масштабирования

Проект поддерживает:

multiple workers
distributed processing
horizontal scaling
cloud deployment
🔥 Почему выбрана микросервисная архитектура

Преимущества:

независимость сервисов
масштабируемость
устойчивость
асинхронная обработка
возможность замены компонентов
🎯 Цель проекта

Создать интеллектуального Telegram-ассистента для:

обучения
изучения английского языка
обработки лекций
анализа учебных материалов
автоматизации обучения
🚀 Будущие улучшения

Планируется добавить:

Web dashboard
User authentication
Progress analytics
AI-generated quizzes
Flashcards
Voice responses
Docker deployment pipeline
CI/CD
Kubernetes support
