import pgzrun
import requests
from random import randint
import time

from pgzero.actor import Actor
from pgzero.rect import Rect

WIDTH = 640
HEIGHT = 480
TILE_SIZE = 32
GRID_WIDTH = WIDTH // TILE_SIZE
GRID_HEIGHT = HEIGHT // TILE_SIZE


class Cat:
    """
    Класс для управления анимацией и перемещение кота.
    """

    def __init__(self, username, x, y):
        self.username = username
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.coins = 0
        self.anim_frame = 0
        self.anim_speed = 0.06
        self.last_anim = time.time()
        self.direction = "idle"
        self.move_start_time = 0
        self.move_duration = 0.15
        self.actor = Actor(
            "cat_idle_1",
            (x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2),
        )

    def move_to(self, x, y):
        """
        Перемещение кота в целевую позицию.
        """

        self.target_x = x
        self.target_y = y

        dx = self.target_x - self.x
        dy = self.target_y - self.y

        if abs(dx) > 0.01:
            self.direction = "right" if dx > 0 else "left"
            self.move_start_time = time.time()
        elif abs(dy) > 0.01:
            self.direction = "idle"
            self.move_start_time = time.time()

    def animate(self):
        """
        Обновление кадра анимации в зависимости от направления движения
        """

        now = time.time()

        if now - self.last_anim < self.anim_speed:
            return

        is_moving = now - self.move_start_time < self.move_duration

        try:
            if not is_moving or self.direction == "idle":
                self.anim_frame = (self.anim_frame + 1) % 2
                self.actor.image = f"cat_idle_{self.anim_frame}"
            elif self.direction == "left":
                self.anim_frame = (self.anim_frame + 1) % 3
                self.actor.image = f"cat_move_left_{self.anim_frame}"
            elif self.direction == "right":
                self.anim_frame = (self.anim_frame + 1) % 3
                self.actor.image = f"cat_move_right_{self.anim_frame}"
        except Exception as e:
            print(f"Ошибка загрузки спрайта для {self.username}: {e}")

        self.last_anim = now

    def draw(self):
        """
        Отрисовка кота и имени игрока на экране.
        """

        try:
            self.actor.draw()
            screen.draw.text(
                self.username, (self.actor.x - 20, self.actor.y - 40), color="white"
            )
        except Exception as e:
            print(f"Ошибка при отрисовке кота {self.username}: {e}")

    def update(self):
        """
        Обновление позиции и анимации кота.
        """

        if self.x != self.target_x or self.y != self.target_y:
            dx = self.target_x - self.x
            dy = self.target_y - self.y

            speed = 0.8

            self.x += dx * speed
            self.y += dy * speed

            if abs(dx) < 0.01 and abs(dy) < 0.01:
                self.x = self.target_x
                self.y = self.target_y

            self.actor.x = self.x * TILE_SIZE + TILE_SIZE // 2
            self.actor.y = self.y * TILE_SIZE + TILE_SIZE // 2

        self.animate()


# Игровая логика
cats = []
coin_pos = (randint(0, GRID_WIDTH - 1), randint(0, GRID_HEIGHT - 1))
coin_actor = Actor(
    "coin",
    (
        coin_pos[0] * TILE_SIZE + TILE_SIZE // 2,
        coin_pos[1] * TILE_SIZE + TILE_SIZE // 2,
    ),
)
last_fetch = 0
FETCH_INTERVAL = 0.1
is_fetching = False


def fetch_state():
    """
    Запрос и обновление состояний игроков с сервера
    """

    global cats, coin_pos, coin_actor, last_fetch, is_fetching
    current_time = time.time()

    if current_time - last_fetch < FETCH_INTERVAL or is_fetching:
        return

    is_fetching = True

    try:
        response = requests.get("http://localhost:5000/get_players_status", timeout=1)
        res = response.json()
        server_usernames = {player["username"] for player in res}

        cats[:] = [cat for cat in cats if cat.username in server_usernames]

        for player in res:
            found = False

            for cat in cats:
                if cat.username == player["username"]:
                    cat.move_to(player["x"], player["y"])
                    found = True
                    break

            if not found:
                cats.append(Cat(player["username"], player["x"], player["y"]))

        last_fetch = current_time
    except Exception as e:
        print(f"Ошибка в fetch_state: {e}")
    finally:
        is_fetching = False


def update():
    """
    Основной игровой цикл: обновление состояния игроков.
    """

    global coin_pos, coin_actor
    fetch_state()

    for cat in cats:
        cat.update()

        if (int(round(cat.x)), int(round(cat.y))) == coin_pos:
            try:
                requests.post(
                    "http://localhost:5000/collect_coin",
                    json={"username": cat.username},
                    timeout=0.5,
                )
                new_coin_pos = (randint(0, GRID_WIDTH - 1), randint(0, GRID_HEIGHT - 1))
                attempts = 0

                while (
                    any(
                        (int(round(c.x)), int(round(c.y))) == new_coin_pos for c in cats
                    )
                    and attempts < 10
                ):
                    new_coin_pos = (
                        randint(0, GRID_WIDTH - 1),
                        randint(0, GRID_HEIGHT - 1),
                    )
                    attempts += 1

                coin_pos = new_coin_pos
                coin_actor.pos = (
                    coin_pos[0] * TILE_SIZE + TILE_SIZE // 2,
                    coin_pos[1] * TILE_SIZE + TILE_SIZE // 2,
                )
            except Exception as e:
                print(f"Ошибка в update: {e}")


def draw():
    """
    Отрисовка игрового поля, котов и монет.
    """

    screen.clear()
    screen.blit("grass", (0, 0))

    for x in range(0, WIDTH, TILE_SIZE):
        for y in range(0, HEIGHT, TILE_SIZE):
            screen.draw.rect(Rect((x, y), (TILE_SIZE, TILE_SIZE)), (0, 0, 0, 30))

    for cat in cats:
        cat.draw()

    coin_actor.draw()


pgzrun.go()
