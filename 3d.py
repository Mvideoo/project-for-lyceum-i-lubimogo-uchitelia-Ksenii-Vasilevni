import pygame
import random
import sqlite3
import time
import os

"""
тута регали Антон и Виктория
Антон - архитектура проекта (классы, функции, методы и тп) что и с чем должно взаимодействовать, крч логика
Виктория - начиночка всех спроектированных объектов, 
"""
# Инициализация
pygame.init()

# Настройки экрана
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Drone Shkebede")

# бд
conn = sqlite3.connect("../players.db")
cursor = conn.cursor()
# Создание таблицы, если её нет
cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT UNIQUE,
        level INTEGER DEFAULT 1,
        score INTEGER DEFAULT 0
    )
""")
conn.commit()

cursor = conn.cursor()
conn.commit()

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)


def load_image(filename, width, height):
    path = os.path.join("assets", filename)  # Если файлы в папке assets
    image = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(image, (width, height))


# Функция получения топа игроков
def get_leaderboard():
    cursor.execute("SELECT nickname, score FROM players ORDER BY score DESC LIMIT 5")
    return cursor.fetchall()


# Шрифт
font = pygame.font.SysFont(None, 36)

clock = pygame.time.Clock()

FOV = 500  # Поле зрения
VIEW_DISTANCE = 800  # Дальность обзора


# Классы дронов и препятствий
class Drone(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.z = 100  # Начальная высота
        self.base_width = 30  # Базовый размер дрона
        self.base_height = 30  # Базовый размер дрона
        self.color = GREEN
        self.vel_x = 0
        self.vel_y = 0
        self.vel_z = 0
        self.acceleration = 0.5  # Увеличиваем ускорение для вертикального движения
        self.deceleration = 0.98
        self.max_speed = 5
        self.score = 0
        self.image = load_image("drone.png", 60, 60)
        self.rect = self.image.get_rect()
        self.rect.topleft = (0, 0)
        self.vertical_stability = 20

        # Переменная для плавного изменения размера
        self.size_factor = 1.0
        self.size_lerp_speed = 0.05  # Скорость интерполяции размера

    # отрисовка (типо был просто квадрат, вместо пнгшки, поэтому где-то могли остаться строки с методом rect)
    def draw_with_camera(self, camera_x, camera_y):
        size = int(self.base_width * self.size_factor)
        draw_x = int(self.x - size / 2 - camera_x)
        draw_y = int(self.y - size / 2 - camera_y)
        self.rect.x = int(self.x - size / 2 - camera_x)
        self.rect.y = int(self.y - size / 2 - camera_y)

    def update(self):
        # перемещение по клавишам
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.vel_x -= self.acceleration
        if keys[pygame.K_RIGHT]:
            self.vel_x += self.acceleration
        if keys[pygame.K_UP]:
            self.vel_y -= self.acceleration
        if keys[pygame.K_DOWN]:
            self.vel_y += self.acceleration
        if keys[pygame.K_s]:
            self.vel_z -= self.acceleration
        if keys[pygame.K_w]:
            self.vel_z += self.acceleration

        self.vel_x *= self.deceleration
        self.vel_y *= self.deceleration
        self.vel_z *= self.deceleration

        self.vel_x = max(min(self.vel_x, self.max_speed), -self.max_speed)
        self.vel_y = max(min(self.vel_y, self.max_speed), -self.max_speed)
        self.vel_z = max(min(self.vel_z, self.max_speed), -self.max_speed)

        self.x += self.vel_x
        self.y += self.vel_y
        self.z = max(0, self.z + self.vel_z)
        size = int(self.base_width * self.size_factor)
        self.x = max(0, min(1500, self.x))
        self.y = max(0, min(500, self.y))

        # Интерполяция для плавного изменения размера дрона
        target_size_factor = 1 + (self.z / VIEW_DISTANCE) * 2
        self.size_factor += (target_size_factor - self.size_factor) * self.size_lerp_speed

        if self.y < HEIGHT // 4:
            self.score += 2
        else:
            self.score += 0.5

    # старый метод отрисовки, хотели где-нибудь использовать
    def draw(self):
        # Используем плавно изменяющийся размер
        size = int(self.base_width * self.size_factor)
        draw_x = int(self.x - size / 2)
        draw_y = int(self.y - size / 2)
        pygame.draw.rect(screen, self.color, (draw_x, draw_y, size, size))

    def get_hitbox(self):
        # хитбокс дрона
        size = int(self.base_width * self.size_factor)
        return pygame.Rect(self.x - size / 2, self.y - size / 2, size, size)


# препятствие, если врезаться в него, то будет бум крах бдыщ уошщаотмвлтмв
class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, z_max, width, height):
        super().__init__()
        self.x = x
        self.y = y
        self.z_max = z_max
        self.width = width
        self.height = height

        # Рассчитываем размер объекта с учетом FOV
        self.size = int(FOV / (self.z_max + 1) * self.width)

        # Загружаем изображение с нужным размером
        self.image = load_image("obstacle.png", self.size, self.size)

        # Корректируем позицию центра объекта
        self.rect = self.image.get_rect(center=(self.x + self.size // 2, self.y + self.size // 2))

    # вообще этот метод на всякий случай, думали использовать в других штуках
    def draw(self):
        size = int(FOV / (self.z_max + 1) * self.width)
        draw_x = int(self.x - size / 2)
        draw_y = int(self.y - size / 2)
        text = font.render(str(self.z_max), True, BLACK)
        screen.blit(text, (draw_x, draw_y - 20))

    # основной метод отрисовки
    def draw_with_camera(self, camera_x, camera_y):
        size = int(FOV / (self.z_max + 1) * self.width)
        draw_x = int(self.x - size / 2 - camera_x)
        draw_y = int(self.y - size / 2 - camera_y)
        self.rect.x = int(self.x - size / 2 - camera_x)
        self.rect.y = int(self.y - size / 2 - camera_y)
        text = font.render(str(self.z_max), True, BLACK)
        screen.blit(text, (draw_x, draw_y - 20))

    def check_collision(self, drone):
        drone_hitbox = drone.get_hitbox()
        obstacle_hitbox = self.get_hitbox()

        # Проверка пересечения хитбоксов дрона и препятствия
        if drone_hitbox.colliderect(obstacle_hitbox):
            # Дрон может пересекать препятствие только если он ниже
            if drone.z < self.z_max:
                return True
        return False

    def get_hitbox(self):
        size = int(FOV / (self.z_max + 1) * self.width)
        return pygame.Rect(self.x - size / 2, self.y - size / 2, size, size)


# чекпоинт, если врезаться в него, то будет ураа эщкере плюс вайб о ес
# крч как препятствие, но хорошее
class CheckPoint:
    def __init__(self, x, y, z_max, width, height):
        self.x = x
        self.y = y
        self.z_max = z_max
        self.width = width
        self.height = height

    # вообще этот метод на всякий случай, думали использовать в других штуках №2
    def draw(self):
        size = int(FOV / self.height * self.width)
        draw_x = int(self.x - size / 2)
        draw_y = int(self.y - size / 2)
        pygame.draw.rect(screen, BLUE, (draw_x, draw_y, size, size))
        text = font.render(str(self.z_max), True, BLACK)
        screen.blit(text, (draw_x, draw_y - 20))

    # отрисовка с камерой
    def draw_with_camera(self, camera_x, camera_y):
        size = int(FOV / (self.z_max + 1) * self.width)
        draw_x = int(self.x - size / 2 - camera_x)
        draw_y = int(self.y - size / 2 - camera_y)
        pygame.draw.rect(screen, BLUE, (draw_x, draw_y, size, size))
        text = font.render(str(self.z_max), True, BLACK)
        screen.blit(text, (draw_x, draw_y - 20))

    def check_collision(self, drone):
        drone_hitbox = drone.get_hitbox()
        obstacle_hitbox = self.get_hitbox()

        # Проверка пересечения хитбоксов дрона и препятствия
        if drone_hitbox.colliderect(obstacle_hitbox):
            # Дрон может пересекать препятствие только если он ниже
            if drone.z <= self.z_max:
                checkpoint_sound.play()
                return True
        return False

    def get_hitbox(self):
        size = int(FOV / (self.z_max + 1) * self.width)
        return pygame.Rect(self.x - size / 2, self.y - size / 2, size, size)


# турбулентность
class Turbulence:
    def __init__(self, x, y, width, height, strength):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.strength = strength

    # накидываем эффект на дрона, если их хитбоксы пересекаются
    def apply_effect(self, drone):
        drone_hitbox = drone.get_hitbox()
        obstacle_hitbox = self.get_hitbox()

        # Проверка пересечения хитбоксов дрона и препятствия
        if drone_hitbox.colliderect(obstacle_hitbox):
            drone.vel_x += random.uniform(-self.strength, self.strength)
            drone.vel_y += random.uniform(-self.strength, self.strength)

    def get_hitbox(self):
        # хитбокс препятствия
        size = self.width * self.strength
        return pygame.Rect(self.x - size / 2, self.y - size / 2, size, size)


# ник игрока в начале игры
def get_player_nickname():
    nickname = ""
    input_active = True
    while input_active:
        screen.fill((50, 50, 50))
        text_surf = font.render("Введите ваш ник: " + nickname, True, (255, 255, 255))
        screen.blit(text_surf, (WIDTH // 2 - 200, HEIGHT // 2 - 20))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and nickname:
                    input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    nickname = nickname[:-1]
                else:
                    nickname += event.unicode

        pygame.display.flip()
        clock.tick(30)

    return nickname


# Получение ника
player_nickname = get_player_nickname()

# Проверка игрока в базе
cursor.execute("SELECT * FROM players WHERE nickname = ?", (player_nickname,))
player_data = cursor.fetchone()

if player_data:
    player_level = player_data[2]
else:
    cursor.execute("INSERT INTO players (nickname) VALUES (?)", (player_nickname,))
    conn.commit()
    player_level = 1
# максимальное время на уровнях
level_time = 20
# звук, если наедем на чекпоинт
checkpoint_sound = pygame.mixer.Sound(os.path.join("assets", "checkpoint_sound.wav"))


# лидерборд
def show_leaderboard():
    running = True

    # Подключаемся к БД
    conn = sqlite3.connect("../game.db")
    cursor = conn.cursor()
    leaderboard = get_leaderboard()

    conn.close()

    while running:
        screen.fill(WHITE)

        title_text = font.render("Лидерборд", True, BLACK)
        screen.blit(title_text, (300, 50))

        # Отображаем топ-10 игроков
        y_offset = 100
        for i, (nickname, highscore) in enumerate(leaderboard):
            entry_text = font.render(f"{i + 1}. {nickname}: {highscore}", True, BLACK)
            screen.blit(entry_text, (250, y_offset))
            y_offset += 40  # Смещаем каждую строку вниз

        # Кнопка "Назад"
        back_button = pygame.draw.rect(screen, BLUE, (300, 500, 200, 50))
        back_text = font.render("Назад", True, WHITE)
        screen.blit(back_text, (back_button.x + 70, back_button.y + 10))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    running = False  # Закрываем экран лидерборда

        pygame.display.update()
        clock.tick(60)


# Главное меню
def main_menu():
    running = True
    while running:
        screen.fill(WHITE)

        # Рисуем кнопки
        levels_button = draw_button(screen, "Уровни", 300, 150, 200, 50, BLUE, WHITE, font)
        free_mode_button = draw_button(screen, "Свободный режим", 300, 250, 200, 50, BLUE, WHITE, font)
        leaderboard_button = draw_button(screen, "Лидерборд", 300, 350, 200, 50, BLUE, WHITE, font)
        quit_button = draw_button(screen, "Выйти", 300, 450, 200, 50, BLUE, WHITE, font)
        # обработка ивентов
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if levels_button.collidepoint(event.pos):
                    levels_menu()
                elif free_mode_button.collidepoint(event.pos):
                    free_mode()
                elif leaderboard_button.collidepoint(event.pos):
                    show_leaderboard()
                elif quit_button.collidepoint(event.pos):
                    running = False

        pygame.display.update()
        clock.tick(60)


# кнопочки
def draw_button(surface, text, x, y, width, height, color, text_color, font, shadow_offset=3):
    shadow_color = (50, 50, 50)  # Серый (который не инженер)
    pygame.draw.rect(surface, shadow_color, (x + shadow_offset, y + shadow_offset, width, height), border_radius=10)
    pygame.draw.rect(surface, color, (x, y, width, height), border_radius=10)

    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))

    surface.blit(text_surface, text_rect)
    return pygame.Rect(x, y, width, height)


# уровни игры
def levels_menu():
    running = True
    while running:
        screen.fill(WHITE)

        # Рисуем кнопки
        level_1_button = draw_button(screen, "Уровень 1", 300, 150, 200, 50, BLUE, WHITE, font)
        level_2_button = draw_button(screen, "Уровень 2", 300, 250, 200, 50, BLUE, WHITE, font)
        back_button = draw_button(screen, "Назад", 300, 350, 200, 50, BLUE, WHITE, font)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if level_1_button.collidepoint(event.pos):
                    play_game(1)
                elif level_2_button.collidepoint(event.pos):
                    # попасть на 2 уровень можно, если пройти 1 уровень
                    cursor.execute("SELECT level FROM players WHERE nickname = ?", (player_nickname,))
                    lev = cursor.fetchone()
                    if lev and 2 in lev:
                        play_game(2)
                elif back_button.collidepoint(event.pos):
                    running = False

        pygame.display.update()
        clock.tick(60)


def check_drone_spawn(drone, obstacles):
    # Проверяет, не находится ли дрон в препятствии, и если находится, перемещает его
    while any(obs.check_collision(drone) for obs in obstacles):
        # Перемещаем дрон в случайную позицию, если он находится в препятствии
        drone.x = random.randint(0, WIDTH)
        drone.y = random.randint(0, HEIGHT)
        drone.z = random.randint(50, 300)


# камера, которая будет следовать за дроном
class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0

    def update(self, drone):
        # Камера следует за дроном, но ограничивает его на экране
        self.x = max(0, min(drone.x - self.width // 2, WIDTH - self.width))
        self.y = max(0, min(drone.y - self.height // 2, HEIGHT - self.height))

    def apply(self, entity):
        # Применяет смещение камеры к объектам
        return entity.x - self.x, entity.y - self.y


# генерация препятствий для уровней
def generate_obstacles(level):
    obstacles = []
    checkpoint = None

    # можно сделать рандом, но как будто не
    if level == 1:
        obstacles = [
            Obstacle(200, 300, 150, 50, 50),
            Obstacle(400, 300, 200, 50, 50),
            Obstacle(600, 300, 100, 50, 50),
            Obstacle(800, 300, 100, 50, 50),
            Obstacle(1000, 300, 250, 50, 50),
            Obstacle(1200, 300, 300, 50, 50)
        ]

        checkpoint = CheckPoint(1300, 100, 250, 50, 50)

    elif level == 2:
        obstacles = [
            Obstacle(150, 200, 100, 50, 50),
            Obstacle(300, 250, 150, 50, 50),
            Obstacle(450, 200, 200, 50, 50),
            Obstacle(600, 150, 120, 50, 50),
            Obstacle(750, 200, 180, 50, 50),
            Obstacle(950, 250, 220, 50, 50),
            Obstacle(1150, 300, 100, 50, 50)
        ]
        # Генерация чекпоинта в случайном месте
        checkpoint = CheckPoint(1300, 100, 250, 50, 50)

    return obstacles, checkpoint


# Метод для обновления состояния игры
def game_loop(level=None):
    # инициализируем все
    running = True
    drone = Drone()
    obstacles, checkpoint = generate_obstacles(level if level else random.randint(1, 2))
    check_drone_spawn(drone, obstacles)
    check_drone_spawn(drone, [checkpoint])
    paused = False

    camera_x, camera_y = drone.x - WIDTH // 2, drone.y - HEIGHT // 2
    start_time = time.time()
    turbulences = [Turbulence(random.randint(0, WIDTH), random.randint(0, HEIGHT), 300, 150, 1) for _ in range(3)]
    obstacles_group = pygame.sprite.Group(obstacles)
    sprites_group = pygame.sprite.Group(drone)

    while running:
        if not paused:
            screen.fill(WHITE)
            drone.update()
            # считаем время
            elapsed_time = time.time() - start_time
            remaining_time = max(0, level_time - elapsed_time)

            if remaining_time == 0:
                main_menu()
                start_time = time.time()
            # отрисовка от камеры
            camera_x = max(0, min(drone.x - WIDTH // 2, WIDTH * 2 - WIDTH))
            camera_y = max(0, min(drone.y - HEIGHT // 2, HEIGHT * 2 - HEIGHT))
            checkpoint.draw_with_camera(camera_x, camera_y)

            for obs in obstacles:
                obs.draw_with_camera(camera_x, camera_y)
                if abs(drone.x - obs.x) < 100 and abs(drone.y - obs.y) < 100:
                    # начисляем доп баллы за "безумный трюк"
                    drone.score += 3
                if obs.check_collision(drone):
                    running = False

            for turb in turbulences:
                turb.apply_effect(drone)

            drone.draw_with_camera(camera_x, camera_y)
            # если попали на чекпоинт, то +вайб, обновляем бд с игроком
            if checkpoint.check_collision(drone):
                cursor.execute("UPDATE players SET level = 2, score = ? WHERE nickname = ?",
                               (max(drone.score, cursor.execute("SELECT score FROM players WHERE nickname = ?",
                                                                (player_nickname,)).fetchone()[0]), player_nickname))
                conn.commit()
                running = False
            # рисовашки
            sprites_group.update()
            obstacles_group.draw(screen)
            sprites_group.draw(screen)
            screen.blit(font.render(f"Height: {int(drone.z)}", True, BLACK), (10, 10))
            screen.blit(font.render(f"Время: {int(remaining_time)} сек", True, BLACK), (10, 100))
            screen.blit(font.render(f"Очки: {drone.score}", True, BLACK), (10, 50))
        pause_button = pygame.draw.rect(screen, BLUE, (WIDTH - 110, 10, 100, 50))
        quit_button = pygame.draw.rect(screen, BLUE, (WIDTH - 110, 70, 100, 50))
        screen.blit(font.render("Пауза", True, WHITE), (pause_button.x + 20, pause_button.y + 10))
        screen.blit(font.render("Выйти", True, WHITE), (quit_button.x + 20, quit_button.y + 10))
        # обработка ивентов
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if pause_button.collidepoint(event.pos):
                    paused = not paused
                elif quit_button.collidepoint(event.pos):
                    running = False

        pygame.display.update()
        clock.tick(60)


# тупо вызов игр, типо 2 почти одинаковых функции, поэтому вот так поделено
def play_game(level):
    game_loop(level)


def free_mode():
    game_loop()


# Запуск игры
if __name__ == "__main__":
    main_menu()

conn.close()