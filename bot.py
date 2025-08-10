import telebot
import requests
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)

# print(TOKEN)
# print(bot.get_me())


@bot.message_handler(commands=["join"])
def join_game(message):
    """
    Обработка команды /join для регистрации игрока.

    :param message: Сообщение с информацией о пользователе.
    """

    username = message.from_user.username or message.from_user.first_name

    try:
        requests.post("http://localhost:5000/join", json={"username": username})
        markup = telebot.types.ReplyKeyboardMarkup(True, False)
        markup.add("⬅️", "➡️", "⬆️", "⬇️")
        bot.send_message(
            message.chat.id, f"Привет, {username}! Ты в игре!", reply_markup=markup
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка подключения к серверу: {e}")


@bot.message_handler(func=lambda message: message.text in ["⬅️", "➡️", "⬆️", "⬇️"])
def move(message):
    """
    Обработка нажатия кнопок управления для перемещения игрока.

    :param message: Сообщение с информацией о нажатой кнопке.
    """

    username = message.from_user.username or message.from_user.first_name
    dirs = {"⬅️": "left", "➡️": "right", "⬆️": "up", "⬇️": "down"}
    direction = dirs[message.text]

    try:
        requests.post(
            "http://localhost:5000/move",
            json={
                "username": username,
                "direction": direction,
            },
            timeout=3,
        )
        bot.send_message(message.chat.id, f"Перемещение: {message.text}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при перемещении: {e}")


bot.polling()
