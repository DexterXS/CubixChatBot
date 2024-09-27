import logging
from telegram import Bot
import config  # Подключаем файл с конфигурацией

bot = Bot(token=config.TELEGRAM_TOKEN)

# Отправка уведомлений о нарушениях в Telegram
async def send_telegram_notification(channel, player_name, message, rule_violation=None, detailed=False,
                                     moderator_name=None, punishment_duration=None):
    """
    Отправка уведомления о нарушении или наказании.
    :param channel: Тип чата (например, глобальный, торговый)
    :param player_name: Имя игрока
    :param message: Сообщение, отправленное игроком
    :param rule_violation: Правило, которое было нарушено (если есть)
    :param detailed: Флаг, если True — отправляем детализированное сообщение о наказании, иначе — стандартное уведомление
    :param moderator_name: Имя модератора, который выдал наказание (если есть)
    :param punishment_duration: Продолжительность наказания (если есть)
    """

    if detailed:
        # Формируем детализированное сообщение о наказании
        punishment_message = (
            f"[{datetime.now().strftime('%H:%M:%S')}] [Общий] System -> §0[§6Наказание§0] "
            f"§b§2{player_name} §cбыл замучен§3 {moderator_name} §cна §e{punishment_duration} §cпо причине: §7{rule_violation}"
        )
        text = punishment_message
    else:
        # Стандартное сообщение о нарушении
        text = f"Нарушение: {rule_violation} ({channel}) {player_name}: {message}"

    try:
        await bot.send_message(chat_id=config.CHAT_ID, text=text)
        logging.info(f"Отправлено уведомление: {text}")
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления: {e}")

# Отправка уведомлений о ключевых словах в Telegram
async def send_telegram_alert(channel, player_name, message):
    text = f"({channel}) {player_name}: {message}"
    try:
        await bot.send_message(chat_id=config.CHAT_ID, text=text)
        logging.info(f"Отправлено уведомление о сообщении игрока {player_name}")
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления: {e}")


