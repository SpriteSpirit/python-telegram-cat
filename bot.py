import telebot
from dotenv import load_dotenv
import os
import requests


load_dotenv()
bot = telebot.TeleBot(os.getenv("TOKEN"))
pending_moves = []


def get_keyboard_controller():
    """
    Создание клавиатуры управления.

    :return: Объект ReplyKeyboardMarkup с кнопками управления.
    """

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("⬆️")
    markup.row("⬅️", "➡️")
    markup.row("⬇️")

    return markup


def safe_request_json(url, payload):
    """
    Выполняет POST-запрос и безопасно возвращает JSON или None.
    Если ответ не JSON — вернёт None и сам текст ответа.
    """

    try:
        res = requests.post(url, json=payload, timeout=2)

        if res.status_code != 200:
            return None, f"Сервер вернул код {res.status_code}: {res.text}"

        if "application/json" not in res.headers.get("Content-Type", ""):
            return None, f"Сервер вернул не JSON: {res.text}"

        try:
            return res.json(), None
        except ValueError:
            return None, f"Ошибка парсинга JSON: {res.text}"

    except requests.RequestException as e:
        return None, f"Ошибка подключения: {e}"


def process_pending_moves():
    """
    Обработка ожидающих движений игрока.
    Выполняет запрос к /move, отправляет уведомления в Telegram:
    - об ошибке, если запрос неуспешен.
    - об успешном перемещении или его отказе, в зависимости от ответа сервера.

    :return: Если список pending_moves пуст, то вернет None
    """

    if not pending_moves:
        return

    move = pending_moves.pop(0)
    data, error = safe_request_json("http://localhost:5000/move", move)

    if error:
        bot.send_message(
            move["chat_id"],
            f"Ошибка: {error}",
            reply_markup=get_keyboard_controller(),
        )
        return

    if data.get("status") == "moved":
        bot.send_message(
            move["chat_id"],
            f"Ты переместился: {move['direction']}",
            reply_markup=get_keyboard_controller(),
        )
    else:
        bot.send_message(
            move["chat_id"],
            "Не удалось переместиться",
            reply_markup=get_keyboard_controller(),
        )


@bot.message_handler(commands=["join"])
def join_game(message):
    """
    Регистрация нового игрока или активация существующего.

    :param message: Объект сообщения от Telegram.
    """

    username = message.from_user.username or message.from_user.first_name
    data, error = safe_request_json(
        "http://localhost:5000/join", {"username": username}
    )

    if error:
        bot.send_message(message.chat.id, error)
        return

    status = data.get("status")
    if status == "player_already_exists":
        bot.send_message(
            message.chat.id,
            f"Привет, {username}! Ты уже в игре!",
            reply_markup=get_keyboard_controller(),
        )
    else:
        bot.send_message(
            message.chat.id,
            f"Привет, {username}! Добро пожаловать!",
            reply_markup=get_keyboard_controller(),
        )


@bot.message_handler(content_types=["text"])
def move(message):
    """
    Обработка команд движения и перемещение игрока.

    :param message: Сообщение с выбранным направлением.
    """

    username = message.from_user.username or message.from_user.first_name
    direction = {"⬅️": "left", "➡️": "right", "⬆️": "up", "⬇️": "down"}.get(message.text)

    if direction:
        data, error = safe_request_json(
            "http://localhost:5000/move", {"username": username, "direction": direction}
        )

        if error:
            bot.send_message(
                message.chat.id, error, reply_markup=get_keyboard_controller()
            )
            return

        if data.get("status") == "moved":
            bot.send_message(
                message.chat.id,
                f"Ты переместился: {direction}",
                reply_markup=get_keyboard_controller(),
            )
        else:
            bot.send_message(
                message.chat.id,
                "Не удалось переместиться",
                reply_markup=get_keyboard_controller(),
            )


print("Бот запущен...")
bot.polling(non_stop=True, timeout=60, long_polling_timeout=30)
