import logging
import json
import os

PUNISHMENT_FILE = 'punishments.json'

def load_punishments():
    # Проверяем существование файла наказаний
    if not os.path.exists(PUNISHMENT_FILE):
        logging.warning(f"Файл {PUNISHMENT_FILE} не найден, создается новый.")
        return {}

    try:
        with open(PUNISHMENT_FILE, 'r', encoding='utf-8') as f:
            # Если файл пустой, возвращаем пустой словарь
            if os.stat(PUNISHMENT_FILE).st_size == 0:
                logging.warning(f"Файл {PUNISHMENT_FILE} пуст, создание пустой структуры.")
                return {}
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка при чтении JSON: {e}")
        return {}

def save_punishments(punishments):
    try:
        with open(PUNISHMENT_FILE, 'w', encoding='utf-8') as f:
            json.dump(punishments, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Ошибка при записи в файл наказаний: {e}")

def add_punishment(player_name, moderator_name, reason_code, duration, context):
    punishments = load_punishments()
    punishment_data = {
        "player": player_name,
        "moderator": moderator_name,
        "reason_code": reason_code,
        "duration": duration,
        "context": context
    }
    punishments[player_name] = punishment_data
    save_punishments(punishments)

def get_player_context(player_name, recent_messages):
    # Получаем последние 10 сообщений игрока для контекста
    if player_name in recent_messages:
        return recent_messages[player_name][-10:]
    else:
        logging.warning(f"Контекст для игрока {player_name} не найден.")
        return []
