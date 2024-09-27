import os
import re
import asyncio
import logging
import requests
import json
from telegram import Bot
import config  # Импортируем файл конфигурации

# === Настройки логирования ===

LOG_FILE = "../../bot.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)

# === Настройки Telegram бота ===

TELEGRAM_TOKEN = config.TELEGRAM_TOKEN
CHAT_ID = config.CHAT_ID
LOG_FILE_PATH = r'C:\Users\rootu\cubixworld\updates\HiTech-Mobile\logs\fml-client-latest.log'

# URL и токен API для подключения нейросети
API_URL = config.SECRET_API_URL
API_TOKEN = config.SECRET_API_TOKEN


# Функция для чтения данных из файлов
def load_data(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip().lower() for line in f if line.strip()]
    except Exception as e:
        logging.error(f"Ошибка при загрузке данных из {filename}: {e}")
        return []


# Загрузка системного сообщения (prompt) из файла
def load_prompt(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        logging.error(f"Ошибка при загрузке prompt: {e}")
        return ""


# Функция для отправки запроса к API нейросети
def generate_response(user_message):
    prompt = load_prompt('../../texts/prompt_global.txt')

    payload = {
        "model": "Meta-Llama-3.1-8B-Instruct",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": ""}
        ],
        "repetition_penalty": 1.1,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "max_tokens": 1024,
        "stream": False
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {API_TOKEN}"
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            logging.error(f"Ошибка API: {response.status_code} - {response.text}")
            return "Ошибка при проверке сообщения на нарушение правил."
    except Exception as e:
        logging.error(f"Ошибка при запросе к API нейросети: {e}")
        return "Ошибка при подключении к нейросети."


# Загрузка данных из файлов
keywords = load_data('../../texts/banned_words.txt')  # Ключевые слова для нарушений
notification_keywords = load_data('../../texts/notification_keywords.txt')  # Ключевые слова для уведомлений
whitelist = load_data('../../texts/whitelist.txt')
trade_chat_phrases = load_data('../../texts/trade_chat.txt')


# === Инициализация ===

async def send_telegram_notification(bot, channel, player_name, message, rule_violation):
    text = f"Нарушение: {rule_violation} ({channel}) {player_name}: {message}"
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text)
        logging.info(f"Отправлено уведомление о нарушении игроком {player_name}")
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления: {e}")


async def send_telegram_alert(bot, channel, player_name, message):
    text = f"({channel}) {player_name}: {message}"
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text)
        logging.info(f"Отправлено уведомление о сообщении игрока {player_name}")
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления: {e}")


# Асинхронная функция для непрерывного чтения лог-файла
async def follow(file):
    file.seek(0, os.SEEK_END)
    while True:
        line = file.readline()
        if not line:
            await asyncio.sleep(0.1)
            continue
        yield line


# Функция для обработки сообщения
async def process_message(bot, channel, player_name, message):
    lower_message = message.lower()

    # Игнорируем все сообщения из "Общего" чата
    if channel.lower() == 'общий':
        logging.info(f"Сообщение из Общего чата от {player_name} проигнорировано.")
        return

    # Проверка на наличие в белом списке
    if any(whitelist_word in lower_message for whitelist_word in whitelist):
        logging.info(
            f"Сообщение от {player_name} в канале {channel} находится в белом списке. Уведомление не отправлено.")
        return

    # Проверка на ключевые слова для уведомлений
    for notify_keyword in notification_keywords:
        if notify_keyword in lower_message:
            logging.info(f"Сообщение от {player_name} содержит ключевое слово для уведомления: {notify_keyword}")
            await send_telegram_alert(bot, channel, player_name, message)
            break  # Отправляем только одно уведомление по первому найденному слову

    # Проверка на торговый чат
    if channel.lower() == 'торговый' and any(trade_phrase in lower_message for trade_phrase in trade_chat_phrases):
        logging.info(f"Сообщение от {player_name} в торговом чате.")
        # Проверяем, содержит ли сообщение ключевые слова для нарушений
        if any(keyword in lower_message for keyword in keywords):
            logging.info(f"Найдено сообщение с ключевым словом в торговом чате: {message}")
            await send_telegram_notification(bot, channel, player_name, message, "Нарушение в торговом чате.")
        return

    # Проверка на ключевые слова для нарушений (если есть ключевые слова в сообщении)
    if any(keyword in lower_message for keyword in keywords):
        logging.info(f"Сообщение с ключевым словом: {message}")
        await send_telegram_notification(bot, channel, player_name, message, "Нарушение по ключевому слову")
        return

    # Проверка через нейросеть только для глобального и торгового чатов
    if channel.lower() in ['глобальный', 'торговый']:
        rule_violation = generate_response(message)

        # Если нейросеть вернула указание на нарушение, отправляем уведомление
        if "нарушение" in rule_violation.lower() or "мут" in rule_violation.lower():
            logging.info(f"Нарушение обнаружено: {rule_violation}")
            await send_telegram_notification(bot, channel, player_name, message, rule_violation)
        else:
            logging.info(f"Сообщение от {player_name}: нарушений не обнаружено.")
    else:
        logging.info(f"Сообщение из канала {channel} не отправлено на проверку нейросетью.")


# Основной цикл мониторинга лог-файла
async def monitor_log(bot):
    if not os.path.exists(LOG_FILE_PATH):
        logging.error(f"Лог-файл не найден: {LOG_FILE_PATH}")
        return

    logging.info(f"Начат мониторинг лог-файла: {LOG_FILE_PATH}")

    with open(LOG_FILE_PATH, 'r', encoding='cp1251') as logfile:
        async for line in follow(logfile):
            chat_message_pattern = re.compile(
                r'\[\d+:\d+:\d+\] \[.+?\] \[.+?\/\]: \[(?!System)(.+?)\] (.+?) -> .*? (.+)')
            match = chat_message_pattern.search(line)

            if match:
                channel = match.group(1)
                player_name = match.group(2)
                message = match.group(3)

                # Обрабатываем сообщение
                await process_message(bot, channel, player_name, message)


async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    await monitor_log(bot)


if __name__ == '__main__':
    asyncio.run(main())
