import os
import re
import asyncio
import logging
from data_loader import load_data
from telegram_notifier import send_telegram_notification, send_telegram_alert
from ai_request import generate_response
from punishment_handler import add_punishment, get_player_context

# Хранение последних сообщений для контекста
recent_messages = {}

# Настройки логирования
LOG_FILE = "bot.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)

# Загрузка данных из файлов
keywords = load_data('texts/banned_words.txt')  # Ключевые слова для нарушений
notification_keywords = load_data('texts/notification_keywords.txt')  # Ключевые слова для уведомлений
whitelist = load_data('texts/whitelist.txt')  # Слова, которые не будут уведомляться
trade_chat_phrases = load_data('texts/trade_chat.txt')  # Слова, которые разрешены только в торговом чате


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
async def process_message(channel, player_name, message, log_type):
    lower_message = message.lower()

    # Игнорируем все сообщения из "Общего" чата
    if channel.lower() == 'общий':
        if player_name != "System":
            logging.info(f"({log_type} Общий) {player_name}: {lower_message}")
        return

    # Проверка на наличие в белом списке
    if any(whitelist_word in lower_message for whitelist_word in whitelist):
        logging.info(f"Сообщение от {player_name} в канале {channel} находится в белом списке. Уведомление не отправлено.")
        return

    # Проверка на ключевые слова для уведомлений
    for notify_keyword in notification_keywords:
        if notify_keyword in lower_message:
            logging.info(f"Оповещение от {player_name}: {notify_keyword}")
            await send_telegram_alert(channel, player_name, message)
            return  # Останавливаем обработку после отправки уведомления

    # Проверка на ключевые слова для нарушений
    if any(keyword in lower_message for keyword in keywords):
        logging.info(f"Сообщение с ключевым словом: {message}")
        await send_telegram_notification(channel, player_name, message, "Нарушение по ключевому слову")
        return

    # Проверка через нейросеть только для глобального и торгового чатов
    if channel.lower() in ['глобальный', 'торговый']:
        logging.info(f"Отправляем запрос к нейросети для {player_name}.")
        rule_violation = await generate_response(message, channel.lower())  # Передаем тип чата
        if "нарушение" in rule_violation.lower() or "мут" in rule_violation.lower():
            logging.info(f"Нарушение обнаружено: {rule_violation}")
            await send_telegram_notification(channel, player_name, message, rule_violation)
        else:
            logging.info(f"Сообщение от {player_name}: нарушений не обнаружено.")



# Функция для обновления списка сообщений игрока
def update_player_messages(player_name, message):
    if player_name not in recent_messages:
        recent_messages[player_name] = []
    recent_messages[player_name].append(message)

    # Ограничиваем до 10 сообщений
    if len(recent_messages[player_name]) > 10:
        recent_messages[player_name] = recent_messages[player_name][-10:]


# Основной цикл мониторинга лог-файла
async def monitor_log(log_path, log_type):
    if not os.path.exists(log_path):
        logging.error(f"Лог-файл не найден: {log_path}")
        return

    logging.info(f"Начат мониторинг лог-файла: {log_path}")

    with open(log_path, 'r', encoding='cp1251') as logfile:
        async for line in follow(logfile):
            chat_message_pattern = re.compile(
                r'\[\d+:\d+:\d+\] \[.+?\] \[.+?\/\]: \[(?!System)(.+?)\] (.+?) -> .*? (.+)')
            match = chat_message_pattern.search(line)

            if match:
                channel = match.group(1)
                player_name = match.group(2)
                message = match.group(3)

                # Параллельно запускаем обработку каждого сообщения, передавая тип лога (HiTech или Mobile)
                asyncio.create_task(process_message(channel, player_name, message, log_type))
