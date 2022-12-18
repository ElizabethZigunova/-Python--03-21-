import pygame
from Maze import Maze
import sys
from random import randint
from svgpathtools import svg2paths


# Класс позиции персонажа или моба на карте
class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y


# Вектор (R2). Точка на карте
class Vec2:
    def __init__(self, x, y):
        self.x = x
        self.y = y


# Класс игровой карты
class Map:
    # Инициализация карты (создание)
    # Принимает размеры карты и позицию входа в лабиринт(откуда начинает игру плеер)
    def __init__(self, x_size, y_size, x_start, y_start):
        # Генерация карты (с помощью алгоритма дейкстры (поиск в глубину))
        maze = Maze(x_size, y_size, x_start, y_start)
        maze.make_maze()
        # Сохранение карты в свг (векторную) картинку. Она появляется там же где файлы проекта
        maze.write_svg('maze.svg')
        map = []
        # Достаем из свг картинки все прямые (стены) и сохраняем их в map (в будущем будем их рисовать)
        paths, attributes = svg2paths('maze.svg')
        # Находим максимальную координату по икс и y для дальнейшего растяжения карты под размер игрового окна
        max_x_coordinate = 0
        max_y_coordinate = 0
        for k, v in enumerate(attributes):
            map.append({"x1": float(v["x1"]), "y1": float(v["y1"]), "x2": float(v["x2"]), "y2": float(v["y2"])})
            max_x_coordinate = max(max_x_coordinate, map[-1]["x1"], map[-1]["x2"])
            max_y_coordinate = max(max_y_coordinate, map[-1]["y1"], map[-1]["y2"])
        # Ко-ты растяжения
        x_kf = (WIDTH - 2 * INDENT) / max_x_coordinate
        y_kf = (HEIGHT - 9 * INDENT) / max_y_coordinate
        # Изменяем карту под нужный размер
        for i in map:
            i["x1"] = INDENT + i["x1"] * x_kf
            i["x2"] = INDENT + i["x2"] * x_kf
            i["y1"] = INDENT + i["y1"] * y_kf
            i["y2"] = INDENT + i["y2"] * y_kf
        self.map = map
        self.finish_position = Position(0, 0)
        self.points = []  # Все "перекрестки" на карте
        self.segments = []  # Точки между которыми есть дорога
        for x in range(x_size):
            for y in range(y_size):
                self.points.append((
                    INDENT + 0.5 * ((WIDTH - 2 * INDENT) / x_size) + ((WIDTH - 2 * INDENT) / x_size) * x,
                    INDENT + 0.5 * ((HEIGHT - 9 * INDENT) / y_size) +
                    ((HEIGHT - 9 * INDENT) / y_size) * y))
        # Заполняем массив сегментов (все отрезки (дороги) которые есть на карте). Дороги между точками на карте
        for i in range(len(self.points)):
            if (float(str(100 * i / len(self.points)))) % 10 == 0:
                print(str(100 * i / len(self.points))[:2:] + "%", "is ready!")  # Вывод процента готовности игры
            for j in range(i + 1, len(self.points)):
                if (abs(self.points[i][0] - self.points[j][0]) <= ((WIDTH - INDENT) / x_size) * 1.25) and (
                        abs(self.points[i][1] - self.points[j][1]) <= ((HEIGHT - 9 * INDENT) / y_size) * 1.25):
                    if self.intersection(self.points[i][0], self.points[i][1], self.points[j][0], self.points[j][1]):
                        self.segments.append(
                            ((self.points[i][0], self.points[i][1]), (self.points[j][0], self.points[j][1])))

        self.all_points = {}  # Все точки на карте, где может стоять моб или плеер (словарь используется для высокой скорости поиска)
        self.game_map = {}  # Словарь формата {Точка: {Направление.вправо: -1, Направление.влево: -1, Направление.вправо: Точка, Направление.вправо: -1}} -1 - нет пути, Точка - есть!
        # Разделяем все сегменты на много точке (все точки зажаты между концами этого сегмента)
        for s in self.segments:
            if s[0][0] == s[1][0]:
                n_y = int(abs(s[0][1] - s[1][1]) / STEP)  # кол-во целых шагов между точками
                self.step_y = abs(s[0][1] - s[1][1]) / n_y
                for j in range(n_y + 1):
                    self.all_points[Position(s[0][0], min(s[0][1], s[1][1]) + self.step_y * j)] = 1
                    # Ищем финиш (самая отдаленная точка от старта (0, 0) )
                    if s[0][0] >= self.finish_position.x and min(s[0][1],
                                                                 s[1][1]) + self.step_y * j >= self.finish_position.y:
                        self.finish_position = Position(s[0][0], min(s[0][1], s[1][1]) + self.step_y * j)

                    try:
                        list_keys = list(self.all_points.keys())
                        # Для плеера по x

                        if list_keys[-1] not in self.game_map:
                            self.game_map[(list_keys[-1].x, list_keys[-1].y)] = {(1, 0): -1,
                                                                                 (-1, 0): -1,
                                                                                 (0, 1): -1,
                                                                                 (0, -1): -1,
                                                                                 }

                        if j >= 1:
                            self.game_map[(list_keys[-1].x, list_keys[-1].y)][(0, 1)] = list_keys[-2]
                            self.game_map[(list_keys[-2].x, list_keys[-2].y)][(0, -1)] = list_keys[-1]
                        # Для пули по x
                        if j >= BULLET_KF:
                            self.game_map[(list_keys[-1].x, list_keys[-1].y)][(0, BULLET_KF)] = list_keys[
                                -1 - BULLET_KF]
                            self.game_map[(list_keys[-1 - BULLET_KF].x, list_keys[-1 - BULLET_KF].y)][(0, -BULLET_KF)] = \
                                list_keys[-1]
                    except:
                        pass


            else:
                n_x = int(abs(s[0][0] - s[1][0]) / STEP)
                self.step_x = abs(s[0][0] - s[1][0]) / n_x
                for j in range(n_x + 1):
                    self.all_points[Position(min(s[0][0], s[1][0]) + self.step_x * j, s[0][1])] = 1

                    # Ищем финиш (самая отдаленная точка от старта (0, 0) )
                    if min(s[0][0], s[1][0]) + self.step_x >= self.finish_position.x and s[0][
                        1] >= self.finish_position.y:
                        self.finish_position = Position(min(s[0][0], s[1][0]) + self.step_x * j, s[0][1])

                    try:
                        list_keys = list(self.all_points.keys())
                        # Для плеера по x
                        if list_keys[-1] not in self.game_map:
                            self.game_map[(list_keys[-1].x, list_keys[-1].y)] = {(1, 0): -1,
                                                                                 (-1, 0): -1,
                                                                                 (0, 1): -1,
                                                                                 (0, -1): -1
                                                                                 }
                        if j >= 1:
                            self.game_map[(list_keys[-1].x, list_keys[-1].y)][(-1, 0)] = list_keys[-2]
                            self.game_map[(list_keys[-2].x, list_keys[-2].y)][(1, 0)] = list_keys[-1]
                        # Для пули по x
                        if j >= BULLET_KF:
                            self.game_map[(list_keys[-1].x, list_keys[-1].y)][(-BULLET_KF, 0)] = list_keys[
                                -1 - BULLET_KF]
                            self.game_map[(list_keys[-1 - BULLET_KF].x, list_keys[-1 - BULLET_KF].y)][(BULLET_KF, 0)] = \
                                list_keys[-1]
                    except:
                        pass
        # Так же для перекрестков находим куда из них можно пойти
        for s in self.segments:
            for ind in 0, 1:
                self.game_map[(s[ind][0], s[ind][1])] = {
                    (1, 0): self.can_go_from_to_slow(Position(s[ind][0], s[ind][1]), Vec2(1, 0)),
                    (-1, 0): self.can_go_from_to_slow(Position(s[ind][0], s[ind][1]), Vec2(-1, 0)),
                    (0, 1): self.can_go_from_to_slow(Position(s[ind][0], s[ind][1]), Vec2(0, 1)),
                    (0, -1): self.can_go_from_to_slow(Position(s[ind][0], s[ind][1]), Vec2(0, -1)),
                }

    # Следующие 3 функции нужны для определения есть ли путь из одной точки в другую (грубо говоря мы имеем:
    # 1) Прямая соединяющая две случайные точки на карте
    # 2) Все стены (тоже прямые)
    # Если никакая из "стен" не пересекается с (1), то дорогоа есть
    def intersection(self, x1, y1, x2, y2):
        if x1 != x2 and y1 != y2:
            return 0

        for line in self.map:
            if self.intersect((x1, y1), (x2, y2), (line["x1"], line["y1"]),
                              (line["x2"], line["y2"])):  # Пересикаются ли прямые
                return 0
        if y1 - y2 == 0 or x1 - x2 == 0:
            return 1
        return 0

    def ccw(self, A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    # Return true if line segments AB and CD intersect
    def intersect(self, A, B, C, D):
        return self.ccw(A, C, D) != self.ccw(B, C, D) and self.ccw(A, B, C) != self.ccw(A, B, D)

    # Медленный поиск есть ли дорога из данной точки по данному направлению
    # Нужна для обработки перекрестков
    def can_go_from_to_slow(self, pos1, vec):
        pos2 = -1
        if vec.x > 0 and vec.y == 0:
            for i in self.all_points:
                if i.y == pos1.y and self.step_x * (vec.x - 0.2) < i.x - pos1.x <= self.step_x * (vec.x + 0.2):
                    pos2 = i
        elif vec.x < 0 and vec.y == 0:
            for i in self.all_points:
                if i.y == pos1.y and self.step_x * (-vec.x - 0.2) < pos1.x - i.x <= self.step_x * (-vec.x + 0.2):
                    pos2 = i
        elif vec.x == 0 and vec.y > 0:
            for i in self.all_points:
                if i.x == pos1.x and self.step_y * (vec.y - 0.2) < pos1.y - i.y <= self.step_y * (vec.y + 0.2):
                    pos2 = i

        elif vec.x == 0 and vec.y < 0:
            for i in self.all_points:
                if i.x == pos1.x and self.step_y * (-vec.y - 0.2) < i.y - pos1.y <= self.step_y * (-vec.y + 0.2):
                    pos2 = i
        return pos2

    # Быстрый поиск есть ли дорога из данной точки по данному направлению (просто смотрим куда мы можем пойти из данной точки с помощью game_map)
    def can_go_from_to(self, pos1, vec):
        # Так как пуля может двигаться быстрее плеера и иметь вектор направления не (1, 0),(0, -1)..., а (2, 0) к примеру
        # То находим единичный вектор перемещения
        # А дальше перемещаемся либо 1 раз (для плеера), либо k раз для пули
        # Это сделано чтобы пуля проходила весь путь от точки А до точки Б и не пропускала препятствия
        try:
            if (vec.x == 0):
                vec2 = Vec2(0, vec.y // abs(vec.y))
                k = abs(vec.y)
            else:
                vec2 = Vec2(vec.x // abs(vec.x), 0)
                k = abs(vec.x)
            pos2 = pos1
            for i in range(k):
                pos2 = self.game_map[(pos2.x, pos2.y)][(vec2.x, vec2.y)]
                if pos2 == -1:
                    return -1
            return pos2
        except:
            pass
        return -1


# Класс плеера
class Player:
    # Создание плеера
    def __init__(self):
        self.hp = 100
        self.color = [255, 255, 204]  # Будет меняться после получения урона
        self.position = Position(list(map.all_points.keys())[0].x,
                                 list(map.all_points.keys())[0].y)  # Изначальная позиция
        self.draw()

    # Передвижение плеера по вектору
    def move(self, vec):
        new_position = map.can_go_from_to(self.position, vec)
        if new_position != -1:
            self.delete()
            self.position = new_position
            return 1
        return 0

    # Получение урона
    def get_damage(self):
        self.hp -= DAMAGE_TO_PLAYER_BY_MOB
        # Изменение цвета (становится тусклее)
        self.color[0] -= 10
        self.color[1] -= 10
        self.color[2] -= 8
        if self.hp <= 0:
            self.delete()
            return 0
        return 1

    # Закрашиваем черным место, где стоит плеер
    def delete(self):
        pygame.draw.line(screen, pygame.color.Color(0, 0, 0),
                         [self.position.x - PLAYER_SIZE * 2, self.position.y - PLAYER_SIZE * 1.5], [
                             self.position.x - PLAYER_SIZE * 2 + PLAYER_SIZE * 4 / (
                                     100 / (self.hp + DAMAGE_TO_PLAYER_BY_MOB)),
                             self.position.y - PLAYER_SIZE * 1.5], 2)
        pygame.draw.circle(screen, pygame.color.Color(0, 0, 0),
                           (self.position.x, self.position.y), PLAYER_SIZE)

    # Рисуем плеера
    def draw(self):
        pygame.draw.circle(screen, pygame.color.Color(self.color[0], self.color[1], self.color[2]),
                           (self.position.x, self.position.y), PLAYER_SIZE)
        kf = 100 / self.hp
        pygame.draw.line(screen, pygame.color.Color(0, 255, 0),
                         [self.position.x - PLAYER_SIZE * 2, self.position.y - PLAYER_SIZE * 1.5],
                         [self.position.x - PLAYER_SIZE * 2 + PLAYER_SIZE * 4 / kf,
                          self.position.y - PLAYER_SIZE * 1.5], 2)


# Класс моба, аналогичен классу плеера
class Mob:
    def __init__(self, start_position):
        self.hp = 100
        self.color = [255, 0, 255]
        self.position = start_position
        self.vector = vectors[randint(0, 3)]
        pygame.draw.circle(screen, pygame.color.Color(self.color[0], self.color[1], self.color[2]),
                           (self.position.x, self.position.y), 8)

    # Мобы идут в заданном направлении пока не врежутся в стену
    # Если врезались выбирают дальше рандомное направление
    def move(self):
        new_position = map.can_go_from_to(self.position, self.vector)
        if new_position != -1:
            pygame.draw.circle(screen, pygame.color.Color(0, 0, 0),
                               (self.position.x, self.position.y), 8)
            self.position = new_position
            pygame.draw.circle(screen, pygame.color.Color(self.color[0], self.color[1], self.color[2]),
                               (self.position.x, self.position.y), 8)
            return 1
        self.vector = vectors[randint(0, 3)]
        return 0

    def get_damage(self):
        self.hp -= 25
        self.color[0] -= 50
        self.color[2] -= 50
        if self.hp <= 0:
            self.delete()
            return 0
        return 1

    def delete(self):
        pygame.draw.circle(screen, pygame.color.Color(0, 0, 0),
                           (self.position.x, self.position.y), 8)


# Класс пуля
class Bullet:
    # Создание пули, с её изначальной позицией и направлением
    def __init__(self, start_position, vector):
        self.position = start_position
        self.vector = vector
        pygame.draw.circle(screen, pygame.color.Color(0, 0, 255),
                           (self.position.x, self.position.y), 5)

    def move(self, vec):
        new_position = map.can_go_from_to(self.position, vec)
        if new_position != -1:
            pygame.draw.circle(screen, pygame.color.Color(0, 0, 0),
                               (self.position.x, self.position.y), 5)
            self.position = new_position
            pygame.draw.circle(screen, pygame.color.Color(0, 0, 255),
                               (self.position.x, self.position.y), 5)
            return 1
        pygame.draw.circle(screen, pygame.color.Color(0, 0, 0),
                           (self.position.x, self.position.y), 5)
        return 0

    def delete(self):
        pygame.draw.circle(screen, pygame.color.Color(0, 0, 0),
                           (self.position.x, self.position.y), 5)

    # получение следующей позиции пули
    def net_step(self):
        if self.move(self.vector):
            return 1
        return 0

    def draw(self):
        pygame.draw.circle(screen, pygame.color.Color(0, 0, 255),
                           (self.position.x, self.position.y), 5)


# Функция проверки дамага плееру
def check_damage_to_player():
    for m in mobs:
        if player.position.x == m.position.x and player.position.y == m.position.y:
            # проверяем, что это не развилка (на развилках урон не наносим во избежания ужасных ситуаций :( )
            for points in map.segments:
                if points[0] == (player.position.x, player.position.y) or points[1] == (
                        player.position.x, player.position.y):
                    return 0
            if not player.get_damage():
                print("Поражение :(")
                exit()


# Вывод кол-ва мобов на карте
def paint_info(live_bobs):
    screen.fill(pygame.Color(0, 0, 0), rect=(0, HEIGHT - 7 * INDENT, WIDTH, 7 * INDENT))
    font = pygame.font.SysFont(None, 50)
    img1 = font.render('Live mobs: ' + str(live_bobs), True, pygame.Color(178, 222, 100))
    screen.blit(img1, (INDENT, HEIGHT - 7 * INDENT))


# Вывод пасхалки на букву "З"
def draw_an_easter_egg():
    font = pygame.font.SysFont(None, WIDTH // 7)
    img1 = font.render('OOO LIZA GAMING', True, pygame.Color(130, 170, 200))
    screen.blit(img1, ((WIDTH // 14) / 2, HEIGHT / 2 - WIDTH // 14))


# (МОЖНО МЕНЯТЬ)!! Параметры игры
WIDTH = 1400  # Ширина окна в пикселях
HEIGHT = 750  # Высота окна в пиклесях
INDENT = 15  # Отступ слева, справа и сверху
STEP = 1  # шаг в пикселях (расстояние на которое перемещается плеер за 1 тик)
BULLET_KF = 2  # Целое число (во сколько раз пуля быстрее плеера)
COUNT_OF_MOBS = 50  # Количество мобов в начале игры
PLAYER_SIZE = 10  # Диаметр плеера в пикселях
DAMAGE_TO_PLAYER_BY_MOB = 20  # Дамаг который наносят мобы плееру врезаясь в него
print("Please wait while the game is being generated!")
map = Map(10, 10, 0, 0)  # Генерация карты, первые две переменные - размеры карты
###################################################################


# Создание окна игры
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Создание плеера
player = Player()

motion_now = Vec2(0, 0)
motion_next = Vec2(0, 0)
bullets = {}
mobs = {}
vectors = [Vec2(1, 0), Vec2(-1, 0), Vec2(0, 1),
           Vec2(0, -1)]  # возможные направления (вправо, влево, вверх и вниз соответственно)

# Генерация мобов
for i in range(COUNT_OF_MOBS):
    mobs[Mob(list(map.all_points)[randint(1, len(map.all_points))])] = 1

while True:
    # Обработка нажатий
    for i in pygame.event.get():
        if i.type == pygame.QUIT:
            sys.exit()
        elif i.type == pygame.KEYDOWN:
            if i.key == pygame.K_RIGHT:
                motion_next = Vec2(1, 0)
            if i.key == pygame.K_LEFT:
                motion_next = Vec2(-1, 0)
            if i.key == pygame.K_UP:
                motion_next = Vec2(0, 1)
            if i.key == pygame.K_DOWN:
                motion_next = Vec2(0, -1)
            if i.key == pygame.K_SPACE:
                bul = Bullet(player.position, Vec2(motion_now.x * 2, motion_now.y * 2))
                bullets[bul] = 1
            if i.key == pygame.K_p:
                draw_an_easter_egg()

    # Рисуем финишную точкy
    pygame.draw.circle(screen, pygame.color.Color(255, 255, 0),
                       (map.finish_position.x, map.finish_position.y), 15)

    # Проверяем какие мобы получают урон
    # удаляем мертвых мобов и врезавшиеся во что то пули
    mobs_to_delete = []
    bulls_to_delete = []

    positions_bullets_before_move = {}
    for b in bullets:
        positions_bullets_before_move[b] = b.position

    for bul in bullets.keys():
        if not bul.net_step():
            bulls_to_delete.append(bul)
    # проверка попаданий пуль в мобов
    for m in mobs.keys():
        for b in bullets.keys():
            if (m.position.x == b.position.x and (
                    (positions_bullets_before_move[b].y <= m.position.y <= b.position.y) or (
                    b.position.y <= m.position.y <= positions_bullets_before_move[b].y))) or (
                    m.position.y == b.position.y and (
                    (positions_bullets_before_move[b].x <= m.position.x <= b.position.x) or (
                    b.position.x <= m.position.x <= positions_bullets_before_move[b].x))):
                if (not m.get_damage()):
                    mobs_to_delete.append(m)
                    m.delete()
                    COUNT_OF_MOBS -= 1
                bulls_to_delete.append(b)
                b.delete()

    for i in mobs_to_delete:
        mobs.pop(i)

    for i in bulls_to_delete:
        try:
            bullets.pop(i)
        except:
            pass
    # Рисуем стены лабиринта
    for v in map.map:
        pygame.draw.line(screen, pygame.color.Color(255, 0, 0), [float(v["x1"]), float(v["y1"])],
                         [float(v["x2"]), float(v["y2"])], 3)

    # Проверяем урон игроку
    check_damage_to_player()

    # Передвижение мобов
    for i in range(COUNT_OF_MOBS):
        list(mobs.keys())[i].move()

    # Проверяем урон игроку
    check_damage_to_player()

    if not player.move(motion_next):
        player.move(motion_now)
    else:
        motion_now = motion_next

    # Проверяем не выиграл ли игрок
    if player.position.x == map.finish_position.x and player.position.y == map.finish_position.y:
        print("Победа!!!")
        exit()

    # draw player
    player.draw()

    # Вывод количества живых мобов
    paint_info(len(mobs))

    pygame.display.update()
    clock.tick(60)  # Количество кадров в секунду (влияет на скорость)
