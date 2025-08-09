from flask import Flask, request, jsonify, render_template
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import datetime
from random import randint

app = Flask(__name__)
engine = create_engine("sqlite:///database.db")
Base = declarative_base()

# количество клеток
GRID_CELL_HORIZONTAL = 20
GRID_CELL_VERTICAL = 15

# границы поля
MIN_X = 0
MIN_Y = 0
MAX_X = GRID_CELL_HORIZONTAL - 1
MAX_Y = GRID_CELL_VERTICAL - 1


class Player(Base):
    """
    Модель игрока.
    """

    __tablename__ = "players"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    x = Column(Integer)
    y = Column(Integer)
    coins = Column(Integer)
    joined_at = Column(DateTime)


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


@app.route("/join", methods=["POST"])
def join_player():
    """
    Добавление нового игрока в игру со случайными начальными координатами.

    :return: JSON-ответ об успешном добавлении игрока.
    """

    data = request.json
    username = data["username"]
    session = Session()
    player = Player(
        username=username,
        x=randint(MIN_X, MAX_X),
        y=randint(MIN_Y, MAX_Y),
        coins=0,
        joined_at=datetime.datetime.now(),
    )

    session.add(player)
    session.commit()
    session.close()

    return jsonify({"status": "player_added"})


@app.route("/move", methods=["POST"])
def move_player():
    """
    Обработка перемещения игрока на игровом поле.
    Принимает POST-запрос с JSON-данными, содержащими имя пользователя и направление движения.
    Обновляет координаты игрока в БД с проверкой границ игрового поля.

    :return: Данные JSON о перемещении игрока.
    """

    data = request.json
    username = data["username"]
    direction = data["direction"]
    session = Session()
    player = session.query(Player).filter_by(username=username).first()

    if player:
        if direction == "up" and player.y > 0:
            player.y -= 1
        elif direction == "down" and player.y < MAX_Y:
            player.y += 1
        elif direction == "left" and player.x > 0:
            player.x -= 1
        elif direction == "right" and player.x < MAX_X:
            player.x += 1

        session.commit()
    session.close()

    return jsonify({"status": "moved"})


@app.route("/get_players_status", methods=["GET"])
def get_players_status():
    """
    Получения текущих статусов всех игроков: имя, позиции (x, y), кол-во монет.

    :return: Данные в JSON о статусе всех игроков.
    """

    session = Session()
    players = session.query(Player).all()
    data = [
        {
            "username": player.username,
            "x": player.x,
            "y": player.y,
            "coins": player.coins,
        }
        for player in players
    ]

    session.close()

    return jsonify(data)


@app.route("/collect_coin", methods=["POST"])
def collect_coin():
    """
    Обработка сбора монет.
    Увеличивает счетчик монет игрока на 1.

    :return: Данные в JSON со статусом "собрано".
    """

    data = request.json
    username = data["username"]
    session = Session()
    player = session.query(Player).filter_by(username=username).first()

    if player:
        player.coins += 1
        session.commit()

    session.close()

    return jsonify({"status": "collected"})


@app.route("/leaderboard")
def leaderboard():
    """
    Таблица лидеров, отсортированная по кол-ву монет.

    :return: HTML-страница с переданными данными игроков.
    """

    session = Session()
    players = session.query(Player).order_by(Player.coins.desc()).all()
    data = [
        {
            "username": player.username,
            "coins": player.coins,
            "time": (datetime.datetime.now() - player.joined_at).total_seconds(),
        }
        for player in players
    ]

    session.close()

    return render_template("leaderboard.html", players=data)
