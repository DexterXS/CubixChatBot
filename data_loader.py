import logging

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
