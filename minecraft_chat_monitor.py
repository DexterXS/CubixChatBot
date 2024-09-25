import os
import re
import asyncio
import logging
from telegram import Bot
import config  # Импортируем файл конфигурации

# === Настройки логирования ===

# Настройка логирования
LOG_FILE = "bot.log"  # Файл, в который будет записываться лог
logging.basicConfig(
    level=logging.INFO,  # Логируем только информацию, предупреждения и ошибки
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),  # Запись логов в файл
        logging.StreamHandler()  # Также вывод логов в консоль
    ]
)

# === Настройки Telegram бота ===

TELEGRAM_TOKEN = config.TELEGRAM_TOKEN
CHAT_ID = config.CHAT_ID
LOG_FILE_PATH = r'C:\Users\rootu\cubixworld\updates\HiTech\logs\fml-client-latest.log'  # Укажите путь к вашему лог-файлу

# Загрузка ключевых слов из файла
def load_keywords(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            keywords = [line.strip().lower() for line in f if line.strip()]
        logging.info(f"Загружены ключевые слова из файла {filename}")
        return keywords
    except Exception as e:
        logging.error(f"Ошибка при загрузке ключевых слов: {e}")
        return []

# Загрузка белого списка слов/фраз
def load_whitelist(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            whitelist = [line.strip().lower() for line in f if line.strip()]
        logging.info(f"Загружен белый список из файла {filename}")
        return whitelist
    except Exception as e:
        logging.error(f"Ошибка при загрузке белого списка: {e}")
        return []

# Загрузка фраз для торгового и локального чата
def load_trade_chat_phrases(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            phrases = [line.strip().lower() for line in f if line.strip()]
        logging.info(f"Загружены фразы для торгового чата из файла {filename}")
        return phrases
    except Exception as e:
        logging.error(f"Ошибка при загрузке фраз для торгового чата: {e}")
        return []

keywords = load_keywords('keywords.txt')
whitelist = load_whitelist('whitelist.txt')  # Файл с белым списком
trade_chat_phrases = load_trade_chat_phrases('trade_chat.txt')  # Фразы для торгового чата

# === Инициализация ===

async def send_telegram_notification(bot, channel, player_name, message):
    text = f"[{channel}] {player_name}:\n{message}"
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text)
        logging.info(f"Отправлено уведомление о сообщении от {player_name} в канале {channel}")
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

# Основной цикл мониторинга лог-файла
async def monitor_log(bot):
    # Проверяем, существует ли файл
    if not os.path.exists(LOG_FILE_PATH):
        logging.error(f"Лог-файл не найден: {LOG_FILE_PATH}")
        return

    logging.info(f"Начат мониторинг лог-файла: {LOG_FILE_PATH}")

    # Открываем файл для чтения
    with open(LOG_FILE_PATH, 'r', encoding='cp1251') as logfile:
        async for line in follow(logfile):
            # Регулярное выражение для поиска сообщений чата
            chat_message_pattern = re.compile(r'\[\d+:\d+:\d+\] \[.+?\] \[.+?\/\]: \[(?!System)(.+?)\] (.+?) -> .*? (.+)')

            # Ищем сообщения чата
            match = chat_message_pattern.search(line)
            if match:
                channel = match.group(1)
                player_name = match.group(2)
                message = match.group(3)
                lower_message = message.lower()

                # Игнорируем все сообщения из "Общего" чата
                if channel.lower() == 'общий':
                    continue  # Пропускаем все сообщения из Общего чата

                # Проверяем, содержится ли сообщение в белом списке
                if any(whitelist_word in lower_message for whitelist_word in whitelist):
                    logging.info(f"Сообщение от {player_name} в канале {channel} находится в белом списке. Уведомление не отправлено.")
                    continue  # Пропускаем это сообщение

                # Проверяем, содержатся ли фразы для торгового чата
                if any(trade_phrase in lower_message for trade_phrase in trade_chat_phrases):
                    # Игнорируем сообщения в локальном чате с фразами для торгового чата
                    if channel.lower() == 'локальный':
                        logging.info(f"Сообщение от {player_name} с фразой для торгового чата в Локальном чате. Игнорируем.")
                        continue

                    # Если сообщение в торговом чате, проверяем, есть ли ключевые слова
                    if channel.lower() == 'торговый':
                        if any(keyword in lower_message for keyword in keywords):
                            logging.info(f"Найдено сообщение с ключевым словом в торговом чате: {message}")
                            await send_telegram_notification(bot, channel, player_name, message)
                        else:
                            logging.info(f"Сообщение от {player_name} в торговом чате содержит фразу из торгового чата. Игнорируем.")
                        continue  # Игнорируем, если нет ключевых слов

                    # Если сообщение не в торговом или локальном чате, отправляем уведомление
                    if channel.lower() not in ['торговый', 'локальный']:
                        logging.info(f"Сообщение от {player_name} с фразой для торгового чата в неправильном канале: {channel}")
                        await send_telegram_notification(bot, channel, player_name, message)
                    continue  # Пропускаем уведомление, если сообщение в торговом/локальном чате

                # Проверяем, содержит ли сообщение ключевые слова
                if any(keyword in lower_message for keyword in keywords):
                    logging.info(f"Найдено сообщение с ключевым словом: {message}")
                    # Отправляем уведомление в Telegram
                    await send_telegram_notification(bot, channel, player_name, message)

async def main():
    # Создаем экземпляр бота
    bot = Bot(token=TELEGRAM_TOKEN)

    # Запускаем мониторинг лог-файла
    await monitor_log(bot)

if __name__ == '__main__':
    # Запускаем основную корутину
    asyncio.run(main())
