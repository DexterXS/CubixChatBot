import logging
import aiohttp  # Используем для асинхронных запросов
import asyncio
import config
from data_loader import load_prompt

# Тайм-аут для нейросети (в секундах)
NEURAL_NETWORK_TIMEOUT = 30

# Флаг для отслеживания активного запроса
request_lock = asyncio.Lock()  # Глобальный lock


# Функция для отправки запроса к API нейросети
async def generate_response(user_message, chat_type):
    # Захватываем блокировку перед выполнением запроса
    async with request_lock:
        logging.info(f"Отправляем запрос к API нейросети... по сообщению: {user_message}")

        # В зависимости от chat_type, используем разные промпты
        if chat_type == 'глобальный':
            prompt = load_prompt('texts/prompt_global.txt')
        elif chat_type == 'торговый':
            prompt = load_prompt('texts/prompt_trade.txt')
        else:
            prompt = load_prompt('texts/default_prompt.txt')

        payload = {
            "model": "Meta-Llama-3.1-8B-Instruct",
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": ""}
            ],
            "repetition_penalty": 1.1,
            "temperature": 0.4,  # Влияет на креативность от 0.1 до 0.9
            "top_p": 0.9,
            "top_k": 40,
            "max_tokens": 1024,
            "stream": False
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {config.SECRET_API_TOKEN}"
        }

        # Асинхронный запрос к API
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(config.SECRET_API_URL, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    else:
                        logging.error(f"Ошибка API: {response.status} - {await response.text()}")
                        return "Ошибка при проверке сообщения на нарушение правил."
            except Exception as e:
                logging.error(f"Ошибка при запросе к API нейросети: {e}")
                return "Ошибка при подключении к нейросети."
