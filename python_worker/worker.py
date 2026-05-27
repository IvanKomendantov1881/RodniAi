import asyncio
import json
import aio_pika
from sqlalchemy import select, delete

from database import init_db, async_session, UserWord
from llm_service import get_word_data_from_api

RABBITMQ_URL = "amqp://guest:guest@localhost/"
QUEUE_IN = "python_tasks"
QUEUE_OUT = "go_results"

async def process_task(message_body: dict) -> dict:
    action = message_body.get("action")
    user_id = message_body.get("user_id")

    response = {"action": action, "user_id": user_id, "status": "error", "data": None}

    if not isinstance(action, str):
        response["data"] = "invalid_action"
        return response

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        response["data"] = "invalid_user_id"
        return response

    if action == "add_word":
        word_raw = message_body.get("word", "")
        if not isinstance(word_raw, str) or not word_raw.strip():
            response["status"] = "invalid_args"
            response["data"] = "missing_or_invalid_word"
            return response

        word = word_raw.lower().strip()

        try:
            definition, example = await get_word_data_from_api(word)
        except Exception as e:
            response["status"] = "error"
            response["data"] = f"dictionary_error: {e}"
            return response

        if definition == "Definition not found.":
            response["status"] = "not_found"
            return response

        try:
            async with async_session() as session:
                new_word = UserWord(
                    telegram_id=user_id,
                    word=word,
                    definition=definition,
                    example=example,
                )
                session.add(new_word)
                await session.commit()

            response["status"] = "success"
            response["data"] = {"word": word, "definition": definition, "example": example}
        except Exception as e:
            response["data"] = str(e)

    elif action == "get_dictionary":
        try:
            async with async_session() as session:
                stmt = select(UserWord).where(UserWord.telegram_id == user_id).order_by(UserWord.id)
                result = await session.execute(stmt)
                words = result.scalars().all()
                
            response["status"] = "success"
            response["data"] = [
                {"id": i + 1, "word": w.word, "definition": w.definition, "example": w.example}
                for i, w in enumerate(words)
            ]
        except Exception as e:
            response["data"] = str(e)

    elif action == "delete_word":
        word_number = message_body.get("word_number")
        
        try:
            word_number = int(word_number)
            if word_number < 1:
                raise ValueError
        except (TypeError, ValueError):
            response["status"] = "invalid_args"
            response["data"] = "word_number must be a positive integer"
            return response

        try:
            async with async_session() as session:
                # Получаем слова в том же порядке, что и при get_dictionary
                stmt = select(UserWord).where(UserWord.telegram_id == user_id).order_by(UserWord.id)
                result = await session.execute(stmt)
                words = result.scalars().all()

                if word_number > len(words):
                    response["status"] = "not_found"
                    response["data"] = f"Word number {word_number} does not exist in the dictionary."
                    return response

                # Находим слово по индексу
                word_to_delete = words[word_number - 1]
                deleted_word_text = word_to_delete.word

                # Удаляем и коммитим
                await session.delete(word_to_delete)
                await session.commit()

            response["status"] = "success"
            response["data"] = {"deleted_word": deleted_word_text}
        except Exception as e:
            response["data"] = str(e)

    elif action == "delete_all":
        try:
            async with async_session() as session:
                # Массовое удаление
                stmt = delete(UserWord).where(UserWord.telegram_id == user_id)
                await session.execute(stmt)
                await session.commit()

            response["status"] = "success"
            response["data"] = "dictionary_cleared"
        except Exception as e:
            response["data"] = str(e)

    return response

async def main():
    print("Инициализация базы данных...")
    await init_db()
    
    print("Подключение к RabbitMQ...")
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    
    async with connection:
        channel = await connection.channel()
        
        await channel.declare_queue(QUEUE_IN, durable=True)
        await channel.declare_queue(QUEUE_OUT, durable=True)
        
        print(f"Воркер запущен! Ожидание задач в очереди '{QUEUE_IN}'...")
        
        async with channel.default_exchange.connection:
            queue = await channel.get_queue(QUEUE_IN)
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            incoming_data = json.loads(message.body.decode())
                        except Exception as e:
                            print(f"Invalid JSON received: {e}")
                            error_resp = {"action": None, "user_id": None, "status": "invalid_json", "data": str(e)}
                            await channel.default_exchange.publish(
                                aio_pika.Message(body=json.dumps(error_resp).encode()),
                                routing_key=QUEUE_OUT,
                            )
                            continue

                        print(f"Получена задача: {incoming_data}")

                        try:
                            result_data = await process_task(incoming_data)
                        except Exception as e:
                            print(f"Error processing task: {e}")
                            result_data = {
                                "action": incoming_data.get("action"),
                                "user_id": incoming_data.get("user_id"),
                                "status": "processing_error",
                                "data": str(e),
                            }
                        
                        await channel.default_exchange.publish(
                            aio_pika.Message(body=json.dumps(result_data).encode()),
                            routing_key=QUEUE_OUT,
                        )
                        print(f"Отправлен результат: {result_data}")

if __name__ == "__main__":
    asyncio.run(main())