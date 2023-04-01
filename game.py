import sys
import os
import paramiko
from _thread import *
import math
import pygame
from pygame.locals import *
import pygame_textinput
from cryptocode import encrypt, decrypt
import json
from enum import Enum
import random
from constants import *


class JSONSaveFileFormatError(Exception):
    def __init__(self, err=None, message = 'Save file format not supported'):
        self.message = message
        if err == 'not_dict':
            self.message = 'JSON file must be wrapped in a dictionary'
        elif err == 'difficulties_not_sole_element':
            self.message = 'Save file must have a single key: "difficulties"'
        elif err == 'difficulties_not_dict':
            self.message = 'Difficulties data type invalid'
        elif err == 'difficulties_wrong_name':
            self.message = 'Some of the difficulties have an invalid name'
        elif err == 'difficulties_wrong_key':
            self.message = 'Difficulty keys (stars) must be either "bronze", "silver" or "gold"'
        elif err == 'difficulties_stars_wrong_type':
            self.message = 'Stars must be of type bool'
        super().__init__(self.message)

class HighScoresInterface:
    def __init__(self, high_scores_type='local', difficulty=Difficulty.EASY):
        self.high_scores_type = high_scores_type
        self.difficulty_pages = {'local': dict.fromkeys(Difficulty, 0), 'global': dict.fromkeys(Difficulty, 0)}
        self.difficulty = difficulty

def load_high_scores():
    DEFAULT_HIGH_SCORES_DICT = HIGH_SCORES_DICT = {'EASY': [], 'NORMAL': [], 'EXTREME': [], 'HUGE': [], 'BLIND': [], 'HUGE_EXTREME': [], 'HUGE_BLIND': []}
    CORRUPTED_FILE_MSG = 'Corrupted JSON high scores file. Creating a new one...'
    try:
        with open(HIGH_SCORES_FILE_NAME, 'r') as f:
            try:
                HIGH_SCORES_DICT = json.loads(decrypt(f.read(), CRYPTO_PASSWORD))
                return HIGH_SCORES_DICT
            except (json.decoder.JSONDecodeError, TypeError, AttributeError) as e:
                print(CORRUPTED_FILE_MSG)
                with open(HIGH_SCORES_FILE_NAME, 'w') as f1:
                    f1.write(encrypt(json.dumps(DEFAULT_HIGH_SCORES_DICT, indent=4), CRYPTO_PASSWORD))
                return DEFAULT_HIGH_SCORES_DICT
            except JSONSaveFileFormatError as e:
                print(f'{e.message}. Resetting high scores file...')
                with open(HIGH_SCORES_FILE_NAME, 'w') as f1:
                    f1.write(encrypt(json.dumps(DEFAULT_HIGH_SCORES_DICT, indent=4), CRYPTO_PASSWORD))
                return DEFAULT_HIGH_SCORES_DICT
    except FileNotFoundError:
        print('High scores file not found. Recreating it...')
        with open(HIGH_SCORES_FILE_NAME, 'w') as f:
            f.write(encrypt(json.dumps(DEFAULT_HIGH_SCORES_DICT, indent=4), CRYPTO_PASSWORD))
            return DEFAULT_HIGH_SCORES_DICT

class User:
    def __init__(self, name="anonymous", color=WHITE) -> None:
        self.name = name
        self.color = color

def sort_high_score(high_score_list: list, score: int):
    i = 0
    while i < len(high_score_list) and score > high_score_list[i]['time']:
        i += 1
    if i < HIGH_SCORE_ENTRIES:
        return i
    return -1

pygame.init()
pygame.display.set_icon(ICON_IMG)

FPSCLOCK = pygame.time.Clock()

screen_shake = 0

pygame.display.set_caption("Mamono Sweeper")

def load_game():
    DEFAULT_STARS_DICT = STARS_DICT = {'difficulties': {difficulty.name: {'bronze': False, 'silver': False, 'gold': False} for difficulty in Difficulty}}
    CORRUPTED_FILE_MSG = 'Corrupted JSON save file. Creating a new one...'
    try:
        with open(SAVE_FILE_NAME, 'r') as f:
            try:
                read_stars = decrypt(f.read(), CRYPTO_PASSWORD)
                STARS_DICT = json.loads(read_stars)
                if type(STARS_DICT) != dict:
                    raise JSONSaveFileFormatError('not_dict')
                if len(STARS_DICT.keys()) != 1 or 'difficulties' not in STARS_DICT.keys():
                    raise JSONSaveFileFormatError('difficulties_not_sole_element')
                if list(STARS_DICT['difficulties'].keys()) != [difficulty.name for difficulty in Difficulty]:
                    raise JSONSaveFileFormatError('difficulties_wrong_name')
                if not all([type(STARS_DICT['difficulties'][difficulty.name]) is dict for difficulty in Difficulty]):
                    raise JSONSaveFileFormatError('difficulties_not_dict')
                if not all([list(STARS_DICT['difficulties'][difficulty.name].keys()) == ['bronze', 'silver', 'gold'] for difficulty in Difficulty]):
                    raise JSONSaveFileFormatError('difficulties_wrong_key')
                if not all([all(type(val) is bool for val in list(STARS_DICT['difficulties'][difficulty.name].values())) for difficulty in Difficulty]):
                    raise JSONSaveFileFormatError('difficulties_stars_wrong_type')
                return STARS_DICT
            except (json.decoder.JSONDecodeError, TypeError):
                print(CORRUPTED_FILE_MSG)
                with open(SAVE_FILE_NAME, 'w') as f1:
                    f1.write(encrypt(json.dumps(DEFAULT_STARS_DICT, indent=4), CRYPTO_PASSWORD))
                return DEFAULT_STARS_DICT
            except JSONSaveFileFormatError as e:
                print(f'{e.message}. Resetting save file...')
                with open(SAVE_FILE_NAME, 'w') as f1:
                    f1.write(encrypt(json.dumps(DEFAULT_STARS_DICT, indent=4), CRYPTO_PASSWORD))
                return DEFAULT_STARS_DICT
    except FileNotFoundError:
        print('Save file not found. Recreating it...')
        with open(SAVE_FILE_NAME, 'w') as f:
            f.write(encrypt(json.dumps(DEFAULT_STARS_DICT, indent=4), CRYPTO_PASSWORD))
            return DEFAULT_STARS_DICT

def load_user():
    DEFAULT_USER_FILE = encrypt(json.dumps({'name': '', 'color': '#333333'}, indent=4), CRYPTO_PASSWORD)
    try:
        with open(USER_FILE_NAME, 'r') as f:
            try:
                read_user = decrypt(f.read(), CRYPTO_PASSWORD)
                user = json.loads(read_user)
                return User(user['name'], user['color'])
            except (json.decoder.JSONDecodeError, TypeError):
                print('Couldnt parse User JSON file, recreating it...')
                with open(USER_FILE_NAME, 'w') as f1:
                    f1.write(DEFAULT_USER_FILE)
                return User()
    except FileNotFoundError:
        print("Couldn't find User JSON file, creating it...")
        with open(USER_FILE_NAME, 'w') as f1:
            f1.write(DEFAULT_USER_FILE)
        return User() 

def get_dimensions(difficulty):
    _x = _y = _N = None
    if difficulty == Difficulty.EASY:
        _x, _y, _N = 16, 16, 5
    if difficulty == Difficulty.NORMAL:
        _x, _y, _N = 30, 16, 5
    if difficulty == Difficulty.EXTREME:
        _x, _y, _N = 30, 16, 5
    if difficulty == Difficulty.HUGE:
        _x, _y, _N = 50, 25, 9
    if difficulty == Difficulty.BLIND:
        _x, _y, _N = 30, 16, 5
    if difficulty == Difficulty.HUGE_EXTREME:
        _x, _y, _N = 50, 25, 9
    if difficulty == Difficulty.HUGE_BLIND:
        _x, _y, _N = 50, 25, 9
    return _x, _y, _N

def format_time(milliseconds):
    centisecond = (milliseconds % 1000) // 10
    second = milliseconds // 1000
    minute = milliseconds // 60000
    hour = milliseconds // 3600000
    flag = False
    hour_str = minute_str = second_str = ''
    if hour > 0:
        hour_str = f'{hour}h'
        flag = True
    if minute > 0:
        minute_str = str(minute % 60)
        if flag:
            minute_str = minute_str.zfill(2)
        minute_str += 'm'
        flag = True
    if second > 0:
        second_str = str(second % 60)
        if flag:
            second_str = second_str.zfill(2)
        second_str += 's.'
    centisecond = str(centisecond).zfill(2)
    return hour_str + minute_str + second_str + centisecond

class Mode(Enum):
    MAIN_MENU = 0
    INGAME = 1
    HIGH_SCORES = 2
    HOW_TO_PLAY = 3
    CHANGE_USERNAME = 4

class Sizing:
    def __init__(self, x, y, size, difficulty, N):
        self.TILE_SIZE = 0
        self.SIZE = size
        if size == Size.SMALL:
            self.TILE_SIZE = 26
        if size == Size.MEDIUM:
            self.TILE_SIZE = 32
        if size == Size.LARGE:
            self.TILE_SIZE = 40
        self.SCORE_HEIGHT = int(self.TILE_SIZE * 1.1)
        self.MONSTER_SCORE_HEIGHT = int(self.TILE_SIZE * 1.6)
        self.WIDTH = max((x * self.TILE_SIZE), 30 * self.TILE_SIZE)
        self.HEIGHT = y * self.TILE_SIZE + self.SCORE_HEIGHT + self.MONSTER_SCORE_HEIGHT
        self.EASY_MODE_BUFFER = 7 * self.TILE_SIZE if difficulty == Difficulty.EASY else 0
        self.BAR_SIZE = int(self.TILE_SIZE * 3.5)
        self.BAR_SPACING = self.TILE_SIZE
        self.MONSTER_BAR_DIMENSIONS = ((N * self.BAR_SIZE + (N - 1) * self.BAR_SPACING), self.TILE_SIZE)
        self.MONSTER_BAR_X = (self.WIDTH - self.MONSTER_BAR_DIMENSIONS[0]) // 2
        self.MONSTER_BAR_Y = self.HEIGHT - self.TILE_SIZE - (self.MONSTER_SCORE_HEIGHT - self.TILE_SIZE) // 2

class MainMenuMode(Enum):
    START = 0
    DIFF = 1

class Player:
    def __init__(self, difficulty):
        self.level = 1
        self.hp = MAX_HP[difficulty]
        self.req = REQUIRED_EXP_FOR_LEVEL_UP[difficulty]
        if difficulty in [Difficulty.BLIND, Difficulty.HUGE_BLIND]:
            self.level = 0
        self.monster_count = MONSTER_COUNT[difficulty].copy()
        self.exp = 0

    def attack(self, monster):
        assert type(monster) is MonsterTile
        monster.hp -= self.level

class Graph:
    def __init__(self, x, y, screen, difficulty, sizing, font):
        self.x = x
        self.y = y
        self.sizing = sizing
        self.difficulty = difficulty
        self.font = font
        monster_shuffle = [k for k in range(x * y)]
        self.tiles = [['|' for _ in range(x)] for _ in range(y)]
        self.adj_list = dict()
        self.visited = dict()
        CURR_COUNT = MONSTER_COUNT[difficulty].copy()
        ACCUM_COUNT = [0]
        for k in range(len(CURR_COUNT)):
            ACCUM_COUNT.append(CURR_COUNT[k] + ACCUM_COUNT[k])
        for i in range(x * y):
            rand = random.randint(0, x * y - 1)
            temp = monster_shuffle[rand]
            monster_shuffle[rand] = monster_shuffle[i]
            monster_shuffle[i] = temp
        for i in range(len(monster_shuffle)):
            num = monster_shuffle[i]
            x_new = num // x
            y_new = num % x
            monster_test = False
            for k in range(1, len(ACCUM_COUNT)):
                if ACCUM_COUNT[k - 1] <= i <= ACCUM_COUNT[k]:
                    if k == len(ACCUM_COUNT) - 1 and i == ACCUM_COUNT[k]:
                        continue
                    monster_test = True
                    tile_new = MonsterTile(y_new, x_new, sizing.SIZE, difficulty, font, k)
            if not monster_test:
                tile_new = EmptyTile(y_new, x_new, sizing.SIZE, difficulty, font)
            self.tiles[x_new][y_new] = tile_new
        for i in range(y):
            for j in range(x):
                curr = self.tiles[i][j]
                neighbours = self.get_neighbours(i, j)
                neighbour_monster_count = len(list(filter(lambda mon: type(mon) is MonsterTile, neighbours)))
                for tile in neighbours:
                    if type(curr) is EmptyTile and type(tile) is EmptyTile:
                        self.add_edge(curr, tile)
                    if type(curr) is MonsterTile and neighbour_monster_count == 0:
                        self.add_edge(curr, tile)
                    if type(tile) is MonsterTile:
                        curr.monster_add(tile.get_level())
                if type(curr) is EmptyTile:
                    curr.num_surface = font.render("" if curr.monster_count == 0 else str(curr.monster_count), False, WHITE)
                if type(curr) is MonsterTile:
                    curr.num_surface = font.render(str(curr.monster_count), False, (255, 15, 15))
        for i in range(y):
            for j in range(x):
                self.visited[self.tiles[i][j]] = False

    def resize_tiles(self, size):
        for tiles in self.tiles:
            for tile in tiles:
                tile.font = self.font
                tile.hidden_img = HIDDEN_TILE_IMGS[size][self.difficulty.value]
                if type(tile) is EmptyTile:
                    tile.num_surface = self.font.render(str(tile.monster_count) if tile.monster_count != 0 else "", False, (255, 255, 255))
                if type(tile) is MonsterTile:
                    tile.num_surface = self.font.render(str(tile.monster_count), False, (200, 50, 50))
                    tile.img = MONSTER_IMGS[size][tile.level - 1]

    def add_edge(self, tile1, tile2):
        if tile1 in self.adj_list:
            self.adj_list[tile1].append(tile2)
        else:
            self.adj_list[tile1] = [tile2]
        if tile2 in self.adj_list:
            self.adj_list[tile2].append(tile1)
        else:
            self.adj_list[tile2] = [tile1]

    def get_neighbours(self, i, j):
        return [self.tiles[i + k // 3 - 1][j + k % 3 - 1] for k in range(9)
                if 0 <= i + k // 3 - 1 < self.y
                and 0 <= j + k % 3 - 1 < self.x
                and k != 4]

    def check_legal(self, i, j):
        if 0 <= i < self.y and 0 <= j < self.x:
            return True
        return False


class Board:
    def __init__(self, m, n, screen, difficulty, sizing, font):
        self.graph = Graph(m, n, screen, difficulty, sizing, font)

class Tile:
    def __init__(self, x, y, size, difficulty, font):
        self.monster_count = 0
        self.num_surface = font.render("", False, (255, 255, 255))
        self.font = font
        self.x = x
        self.y = y
        self.revealed = False
        self.marked_num = 0
        self.hidden_img = HIDDEN_TILE_IMGS[size][difficulty.value]

    def monster_add(self, k):
        self.monster_count += k

    def reveal(self):
        self.revealed = True
        self.marked_num = 0

    def draw(self, screen, sizing):
        screen.blit(REVEALED_TILE_IMG[sizing.SIZE] if self.revealed else self.hidden_img, (sizing.EASY_MODE_BUFFER + self.x * sizing.TILE_SIZE, sizing.SCORE_HEIGHT + self.y * sizing.TILE_SIZE))
        if self.marked_num > 0:
            temp_rect = pygame.Rect(sizing.EASY_MODE_BUFFER + self.x * sizing.TILE_SIZE, sizing.SCORE_HEIGHT + self.y * sizing.TILE_SIZE, sizing.TILE_SIZE, sizing.TILE_SIZE)
            marked_surface = self.font.render(str(self.marked_num), False, LIGHT_GREEN)
            text_rect = marked_surface.get_rect(center = temp_rect.center)
            screen.blit(marked_surface, text_rect)

class EmptyTile(Tile):
    def __init__(self, x, y, size, difficulty, font):
        super().__init__(x, y, size, difficulty, font)

    def __str__(self):
        return f'E{self.y}-{self.x}'
    __repr__ = __str__

    def draw(self, screen, sizing):
        Tile.draw(self, screen, sizing)
        if self.revealed:
            temp_rect = pygame.Rect(sizing.EASY_MODE_BUFFER + self.x * sizing.TILE_SIZE, sizing.SCORE_HEIGHT + self.y * sizing.TILE_SIZE, sizing.TILE_SIZE, sizing.TILE_SIZE)
            text_rect = self.num_surface.get_rect(center = temp_rect.center)
            screen.blit(self.num_surface, text_rect)

class MonsterTile(Tile):
    def __init__(self, x, y, size, difficulty, font, level):
        super().__init__(x, y, size, difficulty, font)
        self.level = level
        self.hp = self.level
        self.monster_form = False
        self.num_surface = font.render("", False, (200, 50, 50))
        self.img = MONSTER_IMGS[size][self.level - 1]
        self.fought = False

    def get_level(self):
        return self.level

    def __str__(self):
        return f'M{self.y}-{self.x} Lv. {self.level}'
    __repr__ = __str__

    def draw(self, screen, sizing):
        Tile.draw(self, screen, sizing)
        if self.revealed:
            temp_rect = pygame.Rect(sizing.EASY_MODE_BUFFER + self.x * sizing.TILE_SIZE, sizing.SCORE_HEIGHT + self.y * sizing.TILE_SIZE, sizing.TILE_SIZE, sizing.TILE_SIZE)
            text_rect = self.num_surface.get_rect(center = temp_rect.center)
            if self.monster_form:
                screen.blit(self.img, (sizing.EASY_MODE_BUFFER + self.x * sizing.TILE_SIZE, sizing.SCORE_HEIGHT + self.y * sizing.TILE_SIZE))
            else:
                Tile.draw(self, screen, sizing)
                screen.blit(self.num_surface, text_rect)

    def attack(self, player):
        player.hp -= self.level

class User:
    def __init__(self, name="", color="#333333") -> None:
        self.name = name
        self.color = color

    def R(self):
        return int(self.color[1:3], 16)

    def G(self):
        return int(self.color[3:5], 16)

    def B(self):
        return int(self.color[5:7], 16)

class Slider:
    def __init__(self, val: int, slider_rect: pygame.Rect) -> None:
        self.val = val / 255
        self.rect = slider_rect
        self.button_rect = pygame.Rect(self.rect.x + int(self.val * self.rect.width) - SLIDER_BUTTON_WIDTH // 2, self.rect.y, SLIDER_BUTTON_WIDTH, BUTTON_HEIGHT)

def init_sliders(red, green, blue):
    return {
        'red': Slider(red, slider_rect=SLIDER_RED_RECT),
        'green': Slider(green, slider_rect=SLIDER_GREEN_RECT),
        'blue': Slider(blue, slider_rect=SLIDER_BLUE_RECT)
    }

def is_valid_username(username: str):
    if len(username) == 0:
        return True
    return len(username) <= 20 and username[0] != ' '

class MainGame:
    def __init__(self) -> None:
        self.save = load_game()
        self.mode = Mode.MAIN_MENU
        self.main_menu_mode = MainMenuMode.START
        self.high_scores_interface = HighScoresInterface()
        self.size = Size.MEDIUM
        self.game = None
        self.running = False
        self.screen = pygame.display.set_mode((MAIN_MENU_IMG.get_width(), MAIN_MENU_IMG.get_height()))
        self.tutorial_page = 0
        self.size = Size.MEDIUM
        self.high_scores_data = load_high_scores()
        self.online_high_scores_data = None
        self.user = load_user()
        self.temp_user = User()
        self.load_request = True
        self.high_score_thread_flag = True
        self.username_input_field = pygame_textinput.TextInputVisualizer(manager=pygame_textinput.TextInputManager(initial=self.user.name, validator=is_valid_username),font_object=SCORERS_FONT, font_color=self.user.color, cursor_color=WHITE, antialias=False, cursor_blink_interval=500)
        self.sliders: list[Slider] = init_sliders(self.user.R(), self.user.G(), self.user.B())
        self.dragging = False
        self.current_slider = None
        self.current_placement = None

    def run(self):
        INTRO_MUSIC.play()
        while True:
            if self.mode == Mode.MAIN_MENU:
                if self.main_menu_mode == MainMenuMode.START:
                    self.main_menu_start()

                elif self.main_menu_mode == MainMenuMode.DIFF:
                    self.choose_difficulty()
            
            if self.mode == Mode.CHANGE_USERNAME:
                self.change_username()

            if self.mode == Mode.HOW_TO_PLAY:
                self.how_to_play()

            if self.mode == Mode.HIGH_SCORES:
                self.high_scores()
                if self.load_request:
                    self.online_high_scores_data = None
                    self.load_request = False
                    start_new_thread(self.fetch_online_scores, tuple())

            if self.mode == Mode.INGAME:
                self.game_window()

                if self.game.level_up_check:
                    self.game.draw_level_up_effect()
                if self.game.shake_check:
                    self.game.draw_screen_shake()
            elif self.running:
                self.draw_time()

            pygame.display.update()
            FPSCLOCK.tick(FPS)

    def draw_time(self):
        TIME_RECT = pygame.Rect(int(self.screen.get_width() * 0.7), 0, int(self.screen.get_width() * 0.3), 32 * 1.1)
        self.screen.fill(BLACK, TIME_RECT)
        TIME_SURFACE = MENU_FONT.render("TIME: " + str(( pygame.time.get_ticks() - self.game.start_time ) // 1000), False, WHITE)
        TIME_TEXT_RECT = TIME_SURFACE.get_rect(bottomright = pygame.Rect(0, 0, self.screen.get_width() - BUTTON_PADDING, 32 * 1.1).bottomright)
        self.screen.blit(TIME_SURFACE, TIME_TEXT_RECT)

    def get_tile_clicked(self, x, y, board, sizing):
        y -= sizing.SCORE_HEIGHT
        if not (type(x) is int and type(y) is int):
            return None
        tiles_list = board.graph.tiles
        for tiles in tiles_list:
            for tile in tiles:
                if tile.x * sizing.TILE_SIZE <= x - sizing.EASY_MODE_BUFFER < (tile.x + 1) * sizing.TILE_SIZE and tile.y * sizing.TILE_SIZE <= y < (tile.y + 1) * sizing.TILE_SIZE:
                    return tile

    def draw_button(self, screen: pygame.Surface, rect: pygame.Rect, text: str, background_color=MAMONO_ORANGE, font=MENU_FONT, font_color=WHITE, centered=True, hover_foreground_color=ORANGE, foreground_color=MAMONO_DARK_ORANGE, hover_background_color=MAMONO_ORANGE, button=True, hover_text_color=WHITE):
        milliseconds = pygame.time.get_ticks() / 800
        if hover_foreground_color == ORANGE:
            dark = DIFFICULTY_BACK_COLORS[Difficulty.HUGE]
            light = GREEN
            hover_background_color = light
            hover_foreground_color = (dark[0] + abs(int(math.sin(milliseconds) * (light[0] - dark[0]))), dark[1]  + abs(int(math.sin(milliseconds) * (light[1] - dark[1]))), dark[2] + abs(int(math.sin(milliseconds) * (light[2] - dark[2]))))
            hover_foreground_color = dark
        TEXT_SURFACE = font.render(text, False, font_color) 
        point = pygame.mouse.get_pos()
        FRONT_RECT = pygame.Rect(rect.x + 3, rect.y + 3, rect.width - 3, rect.height - 3)
        screen.fill(background_color, rect)
        screen.fill(foreground_color, FRONT_RECT)
        if rect.collidepoint(point) and button:
            screen.fill(hover_background_color, rect)
            screen.fill(hover_foreground_color, FRONT_RECT)
            TEXT_SURFACE = font.render(text, False, hover_text_color)
        if centered:
            screen.blit(TEXT_SURFACE, TEXT_SURFACE.get_rect(center = rect.center))
        else:
            rect = TEXT_SURFACE.get_rect(midleft = rect.midleft)
            rect.x += 8
            screen.blit(TEXT_SURFACE, rect)

    def draw_board_size_selection(self):
        self.screen.blit(BOARD_SIZE_TEXT, BOARD_SIZE_TEXT.get_rect(center = BOARD_SIZE_TEXT_RECT.center))
        SMALL_SIZE_BUTTON_SURFACE = MENU_FONT.render('S', False, WHITE)
        MEDIUM_SIZE_BUTTON_SURFACE = MENU_FONT.render('M',False,  WHITE)
        LARGE_SIZE_BUTTON_SURFACE = MENU_FONT.render('L',False,  WHITE)
        if self.size == Size.SMALL:
            self.screen.fill(MAMONO_ORANGE, SMALL_SIZE_BUTTON_RECT)
            self.screen.fill(MAMONO_DARK_ORANGE, pygame.Rect(SMALL_SIZE_BUTTON_RECT.x + 3, SMALL_SIZE_BUTTON_RECT.y + 3, SMALL_SIZE_BUTTON_RECT.width - 3, SMALL_SIZE_BUTTON_RECT.height - 3))
        if self.size == Size.MEDIUM:
            self.screen.fill(MAMONO_ORANGE, MEDIUM_SIZE_BUTTON_RECT)
            self.screen.fill(MAMONO_DARK_ORANGE, pygame.Rect(MEDIUM_SIZE_BUTTON_RECT.x + 3, MEDIUM_SIZE_BUTTON_RECT.y + 3, MEDIUM_SIZE_BUTTON_RECT.width - 3, MEDIUM_SIZE_BUTTON_RECT.height - 3))
        if self.size == Size.LARGE:
            self.screen.fill(MAMONO_ORANGE, LARGE_SIZE_BUTTON_RECT)
            self.screen.fill(MAMONO_DARK_ORANGE, pygame.Rect(LARGE_SIZE_BUTTON_RECT.x + 3, LARGE_SIZE_BUTTON_RECT.y + 3, LARGE_SIZE_BUTTON_RECT.width - 3, LARGE_SIZE_BUTTON_RECT.height - 3))
        self.screen.blit(SMALL_SIZE_BUTTON_SURFACE, SMALL_SIZE_BUTTON_SURFACE.get_rect(center = SMALL_SIZE_BUTTON_RECT.center))
        self.screen.blit(MEDIUM_SIZE_BUTTON_SURFACE, MEDIUM_SIZE_BUTTON_SURFACE.get_rect(center = MEDIUM_SIZE_BUTTON_RECT.center))
        self.screen.blit(LARGE_SIZE_BUTTON_SURFACE, LARGE_SIZE_BUTTON_SURFACE.get_rect(center = LARGE_SIZE_BUTTON_RECT.center))

    def draw_main_menu(self):
        self.screen.blit(MAIN_MENU_IMG, pygame.Rect(0, 0, MAIN_MENU_IMG.get_width(), MAIN_MENU_IMG.get_height()))
        self.screen.blit(MAMONO_TITLE_TEXT_SURFACE, MAMONO_TITLE_TEXT_SURFACE.get_rect(midbottom = MAMONO_TITLE_TEXT_RECT.midbottom))
        self.screen.blit(SWEEPER_TITLE_TEXT_SURFACE, SWEEPER_TITLE_TEXT_SURFACE.get_rect(midtop = SWEEPER_TITLE_TEXT_RECT.midtop))
        USERNAME_SURFACE = MENU_FONT_SMALL.render('USER:', False, WHITE)
        self.screen.blit(USERNAME_SURFACE, USERNAME_SURFACE.get_rect(center = USERNAME_RECT.center))
        self.draw_button(self.screen, USER_RECT, self.user.name if self.user.name != "" else 'ANONYMOUS', background_color=BLACK, foreground_color=BLACK, font_color=self.user.color, hover_background_color=BLACK, hover_foreground_color=BLACK, font=SCORERS_FONT)
        if self.running:
            self.draw_button(self.screen, CONTINUE_RECT, 'CONTINUE', hover_foreground_color=DIFFICULTY_COLORS[self.game.difficulty], hover_background_color=DIFFICULTY_BACK_COLORS[self.game.difficulty])
        self.draw_button(self.screen, NEW_GAME_RECT, 'NEW GAME')
        self.draw_button(self.screen, HIGH_SCORES_RECT, 'HIGH SCORES')
        self.draw_button(self.screen, HOW_TO_PLAY_RECT, 'HOW TO PLAY')
        self.draw_button(self.screen, EXIT_GAME_RECT, 'EXIT', hover_foreground_color=DARK_RED, hover_background_color=RED)
        self.draw_board_size_selection()
        point = pygame.mouse.get_pos()
        if SMALL_SIZE_BUTTON_RECT.collidepoint(point) or MEDIUM_SIZE_BUTTON_RECT.collidepoint(point) or LARGE_SIZE_BUTTON_RECT.collidepoint(point) or USER_RECT.collidepoint(point):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    def check_user_color(self, color):
        return color[0] * 0.8 + color[1] * 1.35 + color[2] * 0.9 >= 60

    def change_username(self):
        pygame.key.set_repeat(325, 40)
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        events = pygame.event.get()
        self.username_input_field.update(events)
        entered_name = self.username_input_field.value
        self.temp_user.name = entered_name if entered_name != "" else self.temp_user.name
        for event in events:
            point = pygame.mouse.get_pos()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if SLIDER_RED_RECT.collidepoint(event.pos) or self.sliders['red'].button_rect.collidepoint(event.pos):
                    self.current_slider = self.sliders['red']
                    self.dragging = True
                if SLIDER_GREEN_RECT.collidepoint(event.pos) or self.sliders['green'].button_rect.collidepoint(event.pos):
                    self.current_slider = self.sliders['green']
                    self.dragging = True
                if SLIDER_BLUE_RECT.collidepoint(event.pos) or self.sliders['blue'].button_rect.collidepoint(event.pos):
                    self.current_slider = self.sliders['blue']
                    self.dragging = True
            if event.type == MOUSEBUTTONUP and event.button == 1:
                self.dragging = False
                if EXIT_GAME_RECT.collidepoint(point):
                    pygame.key.set_repeat(10000, 10000)
                    MAIN_MENU_CLICK_SOUND.play()
                    self.mode = Mode.MAIN_MENU
                    self.username_input_field = pygame_textinput.TextInputVisualizer(manager=pygame_textinput.TextInputManager(initial=self.user.name, validator=is_valid_username),font_object=SCORERS_FONT, font_color=self.user.color, cursor_color=WHITE, antialias=False, cursor_blink_interval=500)
                    return
            if event.type == MOUSEMOTION and self.dragging:
                mouse_x, _ = event.pos
                self.current_slider.val = max(0, min((mouse_x - self.current_slider.rect.x) / SLIDER_WIDTH, 1))
                self.current_slider.button_rect.x = self.current_slider.rect.x + int(self.current_slider.val * SLIDER_WIDTH) - SLIDER_BUTTON_WIDTH // 2
            if event.type == MOUSEBUTTONUP and event.button == 1:
                if CHANGE_COLOR_BUTTON_RECT.collidepoint(point):
                    R = int(self.temp_user.color[1:3], 16)
                    G = int(self.temp_user.color[3:5], 16)
                    B = int(self.temp_user.color[5:7], 16)
                    if self.check_user_color((R, G, B)):
                        MAIN_MENU_CLICK_SOUND.play()
                        self.user.name = self.temp_user.name.strip()
                        self.user.color = self.temp_user.color
                        self.save_user()
                    else:
                        ERROR_SOUND.play()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.key.set_repeat(10000, 10000)
                    self.dragging = False
                    MAIN_MENU_CLICK_SOUND.play()
                    self.mode = Mode.MAIN_MENU
                    self.username_input_field = pygame_textinput.TextInputVisualizer(manager=pygame_textinput.TextInputManager(initial=self.user.name, validator=is_valid_username),font_object=SCORERS_FONT, font_color=self.user.color, cursor_color=WHITE, antialias=False, cursor_blink_interval=500)
                    return 
        self.draw_username_change()

    def draw_username_change(self):
        self.screen.fill(BLACK, pygame.Rect(0, 0, self.screen.get_width(), self.screen.get_height()))
        USERNAME_CHANGE_TITLE_SURFACE = MENU_FONT_TITLE.render('CHANGE USERNAME', False, WHITE)
        self.screen.blit(USERNAME_CHANGE_TITLE_SURFACE, USERNAME_CHANGE_TITLE_SURFACE.get_rect(center = MENU_TITLE_RECT.center))
        USERNAME_SURFACE = MENU_FONT.render('USERNAME:', False, WHITE)
        self.screen.blit(USERNAME_SURFACE, USERNAME_SURFACE.get_rect(center = CHANGE_USERNAME_RECT.center))
        CHANGE_COLOR_SURFACE = MENU_FONT.render('COLOR:', False, WHITE)
        self.screen.blit(CHANGE_COLOR_SURFACE, CHANGE_COLOR_SURFACE.get_rect(center = CHANGE_USERNAME_COLOR_RECT.center))
        self.draw_button(self.screen, EXIT_GAME_RECT, text='BACK TO MENU')
        for slider in self.sliders.values():
            slider_line_rect = pygame.Rect(slider.rect.x, slider.rect.y + 17, slider.rect.width, 2)
            self.screen.fill(WHITE, slider_line_rect)
            self.draw_button(self.screen, slider.button_rect, '')
        color = tuple(map(lambda x: int(x.val * 255), self.sliders.values()))
        self.screen.fill(color, USER_COLOR_RECT)
        if self.check_user_color(color):
            self.draw_button(self.screen, CHANGE_COLOR_BUTTON_RECT, 'CHANGE')
        else:
            self.draw_button(self.screen, CHANGE_COLOR_BUTTON_RECT, 'COLOR TOO DARK', background_color=BACKGROUND_GREYED, foreground_color=FOREGROUND_GREYED, hover_background_color=BACKGROUND_GREYED, hover_foreground_color=FOREGROUND_GREYED, font_color=BLACK, hover_text_color=BLACK)
        self.username_input_field.font_color = color
        self.temp_user.color = f"#{''.join(map(lambda x: hex(x)[2:].zfill(2), color))}"
        USER_INPUT_SURFACE = self.username_input_field.surface
        self.screen.blit(USER_INPUT_SURFACE, USER_INPUT_SURFACE.get_rect(center = CHANGE_USERNAME_USER_RECT.center))

    def draw_main_menu_diff(self):
        difficulty = None
        difficulty_selected = False
        self.screen.blit(MAIN_MENU_DIFF_IMG, pygame.Rect(0, 0, MAIN_MENU_IMG.get_width(), MAIN_MENU_IMG.get_height()))
        self.screen.blit(MAMONO_TITLE_TEXT_SURFACE, MAMONO_TITLE_TEXT_SURFACE.get_rect(midbottom = MAMONO_TITLE_TEXT_RECT.midbottom))
        self.screen.blit(SWEEPER_TITLE_TEXT_SURFACE, SWEEPER_TITLE_TEXT_SURFACE.get_rect(midtop = SWEEPER_TITLE_TEXT_RECT.midtop))
        self.screen.blit(CHOOSE_DIFFICULTY_SURFACE, CHOOSE_DIFFICULTY_SURFACE.get_rect(center = CHOOSE_DIFFICULTY_RECT.center))
        for i in range(len(Difficulty)):
            if DIFFICULTY_RECTS[i].collidepoint(pygame.mouse.get_pos()):
                difficulty = Difficulty(i)
                difficulty_selected = True
            self.draw_button(self.screen, DIFFICULTY_RECTS[i], Difficulty(i).name.replace('_', ' '), centered=False, hover_foreground_color=DIFFICULTY_COLORS[Difficulty(i)], hover_background_color=DIFFICULTY_BACK_COLORS[Difficulty(i)])
        self.draw_button(self.screen, DIFFICULTY_BACK_BUTTON_RECT, '<')
        return (difficulty, difficulty_selected)

    def main_menu_start(self):
        self.draw_main_menu()
        for event in pygame.event.get():
            if event.type == MOUSEBUTTONUP and event.button == 1:
                point = pygame.mouse.get_pos()
                if USER_RECT.collidepoint(point):
                    MAIN_MENU_CLICK_SOUND.play()
                    self.mode = Mode.CHANGE_USERNAME
                    return
                if NEW_GAME_RECT.collidepoint(point):
                    MAIN_MENU_CLICK_SOUND.play()
                    self.mode = Mode.MAIN_MENU
                    self.main_menu_mode = MainMenuMode.DIFF
                    return
                elif SMALL_SIZE_BUTTON_RECT.collidepoint(point):
                    MAIN_MENU_CLICK_SOUND.play()
                    self.size = Size.SMALL
                elif MEDIUM_SIZE_BUTTON_RECT.collidepoint(point):
                    MAIN_MENU_CLICK_SOUND.play()
                    self.size = Size.MEDIUM
                elif LARGE_SIZE_BUTTON_RECT.collidepoint(point):
                    MAIN_MENU_CLICK_SOUND.play()
                    self.size = Size.LARGE
                elif CONTINUE_RECT.collidepoint(point):
                    if self.running:
                        MAIN_MENU_CLICK_SOUND.play()
                        self.game.display_board()
                        self.game.draw_player_stats()
                        self.game.draw_monster_stats()
                        self.mode = Mode.INGAME
                        return
                elif HIGH_SCORES_RECT.collidepoint(point):
                    MAIN_MENU_CLICK_SOUND.play()
                    self.mode = Mode.HIGH_SCORES
                    return
                elif HOW_TO_PLAY_RECT.collidepoint(point):
                    MAIN_MENU_CLICK_SOUND.play()
                    self.mode = Mode.HOW_TO_PLAY
                    return
                elif EXIT_GAME_RECT.collidepoint(point):
                    MAIN_MENU_CLICK_SOUND.play()
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

    def fetch_online_scores(self):
        if HOST == 'HOST':
            return
        sftp = None
        try:
            transport = paramiko.Transport((HOST, PORT))
            transport.connect(username=USERNAME, password=PASSWORD)
            sftp = paramiko.SFTPClient.from_transport(transport)
            self.online_high_scores_data = json.loads(decrypt(str(sftp.open(ONLINE_HIGH_SCORES_FILE_NAME).read(), encoding='utf-8'), CRYPTO_PASSWORD))
            print('Server data retrieved successfully!')
        except FileNotFoundError:
            with open('tmp', 'w') as f:
                self.online_high_scores_data = {'EASY': [], 'NORMAL': [], 'EXTREME': [], 'HUGE': [], 'BLIND': [], 'HUGE_EXTREME': [], 'HUGE_BLIND': []}
                f.write(encrypt(json.dumps(self.online_high_scores_data, indent=4), CRYPTO_PASSWORD))
            print('Server file not found.')
        except AttributeError:
            with open('tmp', 'w') as f:
                self.online_high_scores_data = {'EASY': [], 'NORMAL': [], 'EXTREME': [], 'HUGE': [], 'BLIND': [], 'HUGE_EXTREME': [], 'HUGE_BLIND': []}
                f.write(encrypt(json.dumps(self.online_high_scores_data, indent=4), CRYPTO_PASSWORD))
            sftp.put('tmp', ONLINE_HIGH_SCORES_FILE_NAME)
            os.remove('tmp')
        except paramiko.ssh_exception.AuthenticationException:
            print('Wrong server info, authentication failed.')
        finally:
            if transport is not None:
                transport.close()
            if sftp is not None:
                sftp.close()
            try:
                os.remove('tmp')
            except Exception:
                pass

    def save_game(self):
        with open(SAVE_FILE_NAME, 'w') as f:
            f.write(encrypt(json.dumps(self.save, indent=4), CRYPTO_PASSWORD))

    def save_high_scores(self):
        with open(HIGH_SCORES_FILE_NAME, 'w') as f:
            f.write(encrypt(json.dumps(self.high_scores_data, indent=4), CRYPTO_PASSWORD))

    def save_online_high_scores(self, difficulty, score):
        if HOST == 'HOST':
            return
        transport = paramiko.Transport((HOST, PORT))
        transport.connect(username=USERNAME, password=PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transport)
        self.online_high_scores_data = json.loads(decrypt(str(sftp.open(ONLINE_HIGH_SCORES_FILE_NAME).read(), 'utf-8'), CRYPTO_PASSWORD))
        placement = sort_high_score(self.online_high_scores_data[difficulty], score)
        self.current_placement = placement
        if placement != -1:
            self.online_high_scores_data[difficulty] = (self.online_high_scores_data[difficulty][:placement] + [{"name": self.user.name if self.user.name != "" else 'ANONYMOUS', "time": score, "color": self.user.color}] + self.online_high_scores_data[difficulty][placement:])[:HIGH_SCORE_ENTRIES]
        with open('tmp', 'w') as f:
            f.write(encrypt(json.dumps(self.online_high_scores_data, indent=4), CRYPTO_PASSWORD))
        sftp.put('tmp', ONLINE_HIGH_SCORES_FILE_NAME)
        os.remove('tmp')
        transport.close()
        sftp.close()
    
    def save_user(self):
        with open(USER_FILE_NAME, 'w') as f:
            f.write(encrypt(json.dumps({'name': self.user.name, 'color': self.user.color}, indent=4), CRYPTO_PASSWORD))

    def draw_stars(self):
        for difficulty in Difficulty:
            if self.save['difficulties'][difficulty.name]['bronze']:
                self.screen.blit(BRONZE_STAR_IMG, pygame.Rect(BUTTON_WIDTH - 10, DIFFICULTY_RECTS[0].y + 2 + 5 + difficulty.value * 41, 19, 21))
            if self.save['difficulties'][difficulty.name]['silver']:
                self.screen.blit(SILVER_STAR_IMG, pygame.Rect(BUTTON_WIDTH - 45, DIFFICULTY_RECTS[0].y + 2 + 5 + difficulty.value  * 41, 19, 21))
            if self.save['difficulties'][difficulty.name]['gold']:
                self.screen.blit(GOLD_STAR_IMG, pygame.Rect(BUTTON_WIDTH - 80, DIFFICULTY_RECTS[0].y + 2 + 5 + difficulty.value  * 41, 19, 21))

    def choose_difficulty(self):
        difficulty, difficulty_selected = self.draw_main_menu_diff()
        self.draw_stars()

        for event in pygame.event.get():
            if event.type == MOUSEBUTTONUP and difficulty_selected and event.button == 1:
                MAIN_MENU_CLICK_SOUND.play()
                pygame.display.quit()
                pygame.display.init()
                pygame.display.set_icon(ICON_IMG)
                pygame.display.set_caption('Mamono Sweeper')
                self.game = Game(self, difficulty=difficulty)

                self.mode = Mode.INGAME
                self.main_menu_mode = MainMenuMode.START
                return
            if event.type == MOUSEBUTTONUP and event.button == 1 and DIFFICULTY_BACK_BUTTON_RECT.collidepoint(pygame.mouse.get_pos()) or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                MAIN_MENU_CLICK_SOUND.play()
                self.main_menu_mode = MainMenuMode.START
                return
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

    def draw_tutorial(self):
        self.screen.blit(TUTORIAL_PAGES[self.tutorial_page], pygame.Rect(0, 0, self.screen.get_width(), self.screen.get_height()))
        if self.tutorial_page != 0:
            self.draw_button(self.screen, TUTORIAL_BACK_BUTTON_RECT, '<')
        self.draw_button(self.screen, TUTORIAL_BACK_TO_MENU_BUTTON_RECT, 'BACK TO MENU')
        if self.tutorial_page != len(TUTORIAL_PAGES) - 1:
            self.draw_button(self.screen, TUTORIAL_FORWARD_BUTTON_RECT, '>')

    def how_to_play(self):
        self.draw_tutorial()
        for event in pygame.event.get():
            if event.type == MOUSEBUTTONUP and event.button == 1:
                point = pygame.mouse.get_pos()
                if self.tutorial_page != 0 and TUTORIAL_BACK_BUTTON_RECT.collidepoint(point):
                    MAIN_MENU_CLICK_SOUND.play()
                    self.mode = Mode.HOW_TO_PLAY
                    self.tutorial_page -= 1
                    return
                if TUTORIAL_BACK_TO_MENU_BUTTON_RECT.collidepoint(point):
                    MAIN_MENU_CLICK_SOUND.play()
                    self.mode = Mode.MAIN_MENU
                    self.tutorial_page = 0
                    return
                if self.tutorial_page != len(TUTORIAL_PAGES) - 1 and TUTORIAL_FORWARD_BUTTON_RECT.collidepoint(point):
                    MAIN_MENU_CLICK_SOUND.play()
                    self.mode = Mode.HOW_TO_PLAY
                    self.tutorial_page += 1
                    return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    MAIN_MENU_CLICK_SOUND.play()
                    self.mode = Mode.MAIN_MENU
                    self.tutorial_page = 0
                    return

    def draw_scorers(self, page, high_scores):
        if high_scores is None:
            LOADING_SURFACE = MENU_FONT.render('LOADING HIGH SCORES...' if HOST != 'HOST' else 'SERVER NOT CONFIGURED.', False, WHITE)
            self.screen.blit(LOADING_SURFACE, LOADING_SURFACE.get_rect(center = HIGH_SCORERS_RECTS[4].center))
            return
        for i in range(10):
            curr_index = page * 10 + i
            if curr_index < (len(high_scores)):
                name, time, player_color = high_scores[curr_index].values()
                SCORER_SURFACE = SCORERS_FONT.render(f"{name}", False, player_color)
                SCORER_RECT = SCORER_SURFACE.get_rect(midleft = HIGH_SCORERS_RECTS[i].midleft)
                self.screen.blit(SCORERS_NUM_FONT.render(f"{curr_index + 1}.", False, WHITE), SCORER_RECT)
                SCORER_RECT.left += 50
                SCORER_RECT.bottom -= 8
                self.screen.blit(SCORER_SURFACE, SCORER_RECT) 
                COLOR = WHITE
                if curr_index == 0:
                    COLOR = GOLD
                if curr_index == 1:
                    COLOR = SILVER
                if curr_index == 2:
                    COLOR = BRONZE
                TIME_SURFACE = SCORERS_NUM_FONT.render(format_time(time), False, COLOR)
                TIME_RECT = TIME_SURFACE.get_rect(midright = HIGH_SCORERS_RECTS[i].midright)
                self.screen.fill(BLACK, TIME_SURFACE.get_rect(midright = HIGH_SCORERS_RECTS[i].midright))
                self.screen.blit(TIME_SURFACE, TIME_RECT)
                point = pygame.mouse.get_pos()
                if SCORER_RECT.collidepoint(point):
                    self.screen.fill(BLACK, SCORER_RECT)
                    SCORER_SURFACE.set_palette([DIFFICULTY_BACK_COLORS[self.high_scores_interface.difficulty]] * 8)
                    self.screen.blit(SCORER_SURFACE, SCORER_RECT)
                self.screen.fill(BLACK, pygame.Rect(HIGH_SCORERS_RECTS[i].width + HIGH_SCORERS_RECTS[i].x, HIGH_SCORERS_RECTS[i].y, BUTTON_PADDING, 25))
            else:
                self.screen.blit(EMPTY_SCORE_IMG, HIGH_SCORERS_RECTS[i])

    def draw_high_scores(self, high_scores: list):
        interface  = self.high_scores_interface
        scorers_type = interface.high_scores_type
        try:
            online_scores = self.online_high_scores_data[interface.difficulty.name]
        except TypeError:
            online_scores = None
        self.screen.fill(BLACK, pygame.Rect(0, 0, self.screen.get_width(), self.screen.get_height()))
        TITLE_FONT_SURFACE = MENU_FONT_TITLE.render('HIGH SCORES', False, WHITE)
        LOCAL_FONT_SURFACE = MENU_FONT.render('LOCAL', False, WHITE)
        GLOBAL_FONT_SURFACE = MENU_FONT.render('ONLINE', False, WHITE)

        if scorers_type == 'local':
            self.draw_button(self.screen, HIGH_SCORES_LOCAL_RECT, 'LOCAL', hover_foreground_color=MAMONO_DARK_ORANGE, hover_background_color=MAMONO_ORANGE)
        if scorers_type == 'global':
            self.draw_button(self.screen, HIGH_SCORES_GLOBAL_RECT, 'ONLINE', hover_foreground_color=DIFFICULTY_COLORS[Difficulty.EXTREME], hover_background_color=DIFFICULTY_BACK_COLORS[Difficulty.EXTREME], foreground_color=DIFFICULTY_COLORS[Difficulty.EXTREME], background_color=DIFFICULTY_BACK_COLORS[Difficulty.EXTREME])

        self.screen.blit(TITLE_FONT_SURFACE, TITLE_FONT_SURFACE.get_rect(center = MENU_TITLE_RECT.center))
        self.screen.blit(LOCAL_FONT_SURFACE, LOCAL_FONT_SURFACE.get_rect(center = HIGH_SCORES_LOCAL_RECT.center))
        self.screen.blit(GLOBAL_FONT_SURFACE, GLOBAL_FONT_SURFACE.get_rect(center = HIGH_SCORES_GLOBAL_RECT.center))

        page = interface.difficulty_pages[interface.high_scores_type][interface.difficulty] 
        TOP_SCORES_SURFACE = MENU_FONT.render(f'TOP  {f"{page * 10 + 1} - {(page + 1) * 10}" if page > 0 else "10"}', False, WHITE)
        self.screen.blit(TOP_SCORES_SURFACE, TOP_SCORES_SURFACE.get_rect(center = TOP_SCORES_RECT.center))

        self.draw_scorers(page, high_scores if scorers_type == 'local' else online_scores)

        self.screen.fill(DIFFICULTY_BACK_COLORS[interface.difficulty], HIGH_SCORES_DIFFICULTY_RECT)
        HIGH_SCORES_DIFFICULTY_SURFACE = MENU_FONT.render(interface.difficulty.name.replace('_', ' '), False, WHITE)
        self.screen.blit(HIGH_SCORES_DIFFICULTY_SURFACE, HIGH_SCORES_DIFFICULTY_SURFACE.get_rect(center = HIGH_SCORES_DIFFICULTY_RECT.center))
        self.draw_button(self.screen, HIGH_SCORES_DIFFICULTY_RECT, interface.difficulty.name.replace('_', ' '), background_color=DIFFICULTY_BACK_COLORS[interface.difficulty], foreground_color=DIFFICULTY_COLORS[interface.difficulty], button=False) 
        self.draw_button(self.screen, TOP_SCORERS_BACK_RECT, text='<')
        self.draw_button(self.screen, TOP_SCORERS_FORWARD_RECT, text='>')
        self.draw_button(self.screen, HIGH_SCORES_DIFFICULTY_BACK_RECT, text='<')
        self.draw_button(self.screen, HIGH_SCORES_DIFFICULTY_FORWARD_RECT, text='>')

        self.draw_button(self.screen, EXIT_GAME_RECT, text='BACK TO MENU')

    def high_scores(self):
        high_scores = self.high_scores_data[self.high_scores_interface.difficulty.name]
        try:
            online_scores = self.online_high_scores_data[self.high_scores_interface.difficulty.name]
        except TypeError:
            online_scores = []
        self.draw_high_scores(high_scores)
        for event in pygame.event.get():
            interface = self.high_scores_interface
            point = pygame.mouse.get_pos()
            if HIGH_SCORES_LOCAL_RECT.collidepoint(point) or HIGH_SCORES_GLOBAL_RECT.collidepoint(point):
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            if event.type == MOUSEBUTTONUP and event.button == 1:
                if TOP_SCORERS_BACK_RECT.collidepoint(point):
                    MAIN_MENU_CLICK_SOUND.play()
                    interface.difficulty_pages[interface.high_scores_type][interface.difficulty] = (interface.difficulty_pages[interface.high_scores_type][interface.difficulty] - 1) % max(1, math.ceil(len(high_scores if interface.high_scores_type == 'local' else online_scores) / 10))
                if TOP_SCORERS_FORWARD_RECT.collidepoint(point):
                    MAIN_MENU_CLICK_SOUND.play()
                    interface.difficulty_pages[interface.high_scores_type][interface.difficulty] = (interface.difficulty_pages[interface.high_scores_type][interface.difficulty] + 1) % max(1, math.ceil(len(high_scores if interface.high_scores_type == 'local' else online_scores) / 10))
                if HIGH_SCORES_LOCAL_RECT.collidepoint(point):
                    MAIN_MENU_CLICK_SOUND.play()
                    interface.high_scores_type = 'local'
                if HIGH_SCORES_GLOBAL_RECT.collidepoint(point):
                    MAIN_MENU_CLICK_SOUND.play()
                    interface.high_scores_type = 'global'
                    if not self.high_score_thread_flag:
                        self.online_high_scores_data = None
                        start_new_thread(self.fetch_online_scores, tuple())
                    if self.high_score_thread_flag:
                        self.high_score_thread_flag = False

                if HIGH_SCORES_DIFFICULTY_BACK_RECT.collidepoint(point):
                    MAIN_MENU_CLICK_SOUND.play()
                    interface.difficulty = Difficulty((interface.difficulty.value - 1) % len(Difficulty))
                if HIGH_SCORES_DIFFICULTY_FORWARD_RECT.collidepoint(point):
                    MAIN_MENU_CLICK_SOUND.play()
                    interface.difficulty = Difficulty((interface.difficulty.value + 1) % len(Difficulty))
                if EXIT_GAME_RECT.collidepoint(point):
                    MAIN_MENU_CLICK_SOUND.play()
                    self.high_scores_interface = HighScoresInterface()
                    self.mode = Mode.MAIN_MENU
                    return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    MAIN_MENU_CLICK_SOUND.play()
                    self.high_scores_interface = HighScoresInterface()
                    self.mode = Mode.MAIN_MENU
                    return

    def click_tile(self, cursor_pos):
        mousex, mousey = cursor_pos
        tile_clicked = self.get_tile_clicked(mousex, mousey, self.game.board, self.game.sizing)
        if tile_clicked == None or (self.game.difficulty in [Difficulty.BLIND, Difficulty.HUGE_BLIND] and tile_clicked.marked_num > 0):
            return
        if tile_clicked != None and not self.game.started:
            self.running = True
            self.game.started = True
            self.game.start_time = pygame.time.get_ticks()
        if type(tile_clicked) is EmptyTile and not tile_clicked.revealed:
            EMPTY_TILE_CLICK_SOUND.play()
        is_single = tile_clicked.monster_count != 0
        self.game.reveal_tiles(tile_clicked, is_single)
        if type(tile_clicked) is MonsterTile:
            if not self.game.revealed_monsters[tile_clicked.level - 1]:
                self.game.revealed_monsters[tile_clicked.level - 1] = True
            tile_clicked.monster_form = not tile_clicked.monster_form
            self.game.battle(self.game.player, tile_clicked)
        tile_clicked.draw(self.screen, self.game.sizing)
        self.game.draw_player_stats()

    def game_window(self):
        self.game.draw_time()
        if self.game.started and not self.game.game_won and not self.game.game_is_over:
            self.game.time = (pygame.time.get_ticks() - self.game.start_time) // 1000
            self.game.milliseconds = pygame.time.get_ticks() - self.game.start_time
        for event in pygame.event.get():
            if event.type == MOUSEBUTTONUP and event.button == 1:
                if self.game.game_is_over:
                    self.game.restart_game()
                elif self.game.game_won:
                    self.game.game_is_over = True
                    self.game.game_won = False
                    self.game.draw_all()
                else:
                    self.click_tile(event.pos)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.display.quit()
                    pygame.display.init()
                    pygame.display.set_icon(ICON_IMG)
                    pygame.display.set_caption('Mamono Sweeper')

                    self.screen = pygame.display.set_mode((MAIN_MENU_IMG.get_width(), MAIN_MENU_IMG.get_height()))
                    self.mode = Mode.MAIN_MENU
                if not self.game.game_is_over and event.key in ([pygame.K_0, pygame.K_1 , pygame.K_2, pygame.K_3,
                        pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7,
                        pygame.K_8, pygame.K_9, pygame.K_0, pygame.K_BACKQUOTE]):
                    self.game.mark_hovered_tile(event.key)
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        self.game.draw_monster_stats()
        if self.game.win_condition()  and not self.game.game_is_over:
            self.game.victory()
            self.game.game_won = True
        if self.current_placement is not None:
            self.game.draw_victory()

class Game:
    def __init__(self, main: MainGame, difficulty = -1, is_restart=False):
        self.main = main
        self.main.running = False
        self.main.current_placement = None
        self._x, self._y, self._N = get_dimensions(difficulty)
        self.hidden_tile_img = HIDDEN_TILE_IMGS[main.size][difficulty.value]
        self.num_tiles = self._x * self._y
        self.num_revealed_tiles = 0
        self.start_time = 0
        self.game_is_over = False
        self.leveling_up = False
        self.difficulty = difficulty
        self.sizing = Sizing(self._x, self._y, main.size, difficulty, self._N)
        self.MAIN_FONT = pygame.font.Font("assets/fonts/type_writer.ttf", self.sizing.TILE_SIZE // 2)
        self.BOARD_SIZE = (max((self._x * self.sizing.TILE_SIZE), 30 * self.sizing.TILE_SIZE), self._y * self.sizing.TILE_SIZE + self.sizing.SCORE_HEIGHT + self.sizing.MONSTER_SCORE_HEIGHT)
        if not is_restart:
            self.main.screen = pygame.display.set_mode(self.BOARD_SIZE)
            self.main.current_placement = None
        self.VICTORY_FONT = pygame.font.Font("assets/fonts/type_writer.ttf", int(self.main.screen.get_height() / 7))
        self.board = Board(self._x, self._y, self.main.screen, difficulty, self.sizing, self.MAIN_FONT)
        self.ACHIEVEMENTS_FONT = pygame.font.Font("assets/fonts/type_writer.ttf", int(self.main.screen.get_height() / 10))
        self.PLACEMENT_FONT = pygame.font.Font("assets/fonts/type_writer.ttf", int(self.main.screen.get_height() / 10 * 2.5 / 4))
        self.mode = Mode.MAIN_MENU
        self.level_up_effect_surface = pygame.Surface((self.main.screen.get_width(), self.main.screen.get_height()))
        self.level_up_effect_surface.fill(GOLD)
        self.level_up_check = False
        self.light = 0
        self.level_up_effect_surface.set_alpha(0)
        self.shake_check = False
        self.screen_shake = 0
        self.player = Player(difficulty)
        self.game_won = False
        self.started = False
        self.has_marked = False
        self.main_menu_mode = MainMenuMode.START
        self.revealed_monsters = [False] * self._N
        self.time = 0
        self.milliseconds = 0
        self.start_time = 0
        self.MONSTER_IMG_BAR_RECTS = []
        self.MONSTER_TXT_BAR_RECTS = []
        self.PLAYER_STATS_FONT = pygame.font.Font("assets/fonts/type_writer.ttf", self.sizing.SCORE_HEIGHT - 2)
        self.formatted_time = 0
        self.score = None
        self.placement = None
        # self.reveal_monsters()
        for i in range(self._N):
            self.MONSTER_IMG_BAR_RECTS.append(pygame.Rect(self.sizing.MONSTER_BAR_X + i * (self.sizing.BAR_SIZE + self.sizing.BAR_SPACING), self.sizing.MONSTER_BAR_Y, self.sizing.TILE_SIZE, self.sizing.TILE_SIZE))
            self.MONSTER_TXT_BAR_RECTS.append(pygame.Rect(self.sizing.MONSTER_BAR_X + i * (self.sizing.BAR_SIZE + self.sizing.BAR_SPACING) + self.sizing.TILE_SIZE, self.sizing.MONSTER_BAR_Y, self.sizing.BAR_SIZE - self.sizing.TILE_SIZE, self.sizing.TILE_SIZE))
        self.draw_board()
        self.draw_player_stats()
        self.draw_monster_stats()

    def init_rects(self):
        self.MONSTER_IMG_BAR_RECTS = []
        self.MONSTER_TXT_BAR_RECTS = []
        for i in range(self._N):
            self.MONSTER_IMG_BAR_RECTS.append(pygame.Rect(self.sizing.MONSTER_BAR_X + i * (self.sizing.BAR_SIZE + self.sizing.BAR_SPACING), self.sizing.MONSTER_BAR_Y, self.sizing.TILE_SIZE, self.sizing.TILE_SIZE))
            self.MONSTER_TXT_BAR_RECTS.append(pygame.Rect(self.sizing.MONSTER_BAR_X + i * (self.sizing.BAR_SIZE + self.sizing.BAR_SPACING) + self.sizing.TILE_SIZE, self.sizing.MONSTER_BAR_Y, self.sizing.BAR_SIZE - self.sizing.TILE_SIZE, self.sizing.TILE_SIZE))

    def battle(self, player, monster):
        took_dmg = False
        if monster.fought:
            return
        self.formatted_time = format_time(self.milliseconds)
        monster.fought = True
        self.player.monster_count[monster.level - 1] -= 1
        self.player.exp += 2 ** (monster.level - 1)
        if monster.level > self.player.level:
            TAKING_DAMAGE_SOUND.play()
            if self.player.level == 0:
                self.player.hp = 0
            else:
                while monster.hp > 0:
                    self.player.attack(monster)
                    if monster.hp > 0:
                        monster.attack(self.player)
            took_dmg = True
        else:
            KILL_SOUNDS[random.randint(0, len(KILL_SOUNDS) - 1)].play()
        if player.hp > 0 and len(self.player.req) > 1 and isinstance(self.player.req[self.player.level - 1], int) and self.player.exp >= self.player.req[self.player.level - 1]:
            LEVEL_UP_SOUND.play()
            self.player.level += 1
            self.alighten()
        if self.player.hp <= 0:
            self.player.hp = 0
            self.game_over()
        if took_dmg:
            self.shake()

    def shake(self):
        self.screen_shake = 20
        self.shake_check = True

    def alighten(self):
        self.light = 255
        self.level_up_check = True

    def reveal_monsters(self):
        for i in range(len(self.board.graph.tiles)):
            for j in range(len(self.board.graph.tiles[0])):
                if type(self.board.graph.tiles[i][j]) is MonsterTile:
                    if not self.board.graph.tiles[i][j].revealed:
                        self.board.graph.tiles[i][j].monster_form = True
                        self.board.graph.tiles[i][j].reveal()
                        self.board.graph.tiles[i][j].draw(self.main.screen, self.sizing)

    def reveal_tiles(self, tile, is_single):
        if self.board.graph.visited[tile] or tile.revealed:
            return
        self.board.graph.visited[tile] = True
        self.num_revealed_tiles += 1
        tile.reveal()
        tile.draw(self.main.screen, self.sizing)
        if is_single:
            return
        for adj in self.board.graph.adj_list[tile]:
            if not self.board.graph.visited[adj] and not adj.revealed:
                if adj.monster_count == 0:
                    self.reveal_tiles(adj, False)
                else:
                    self.num_revealed_tiles += 1
                    adj.reveal()
                    adj.draw(self.main.screen, self.sizing)

    def mark_hovered_tile(self, key):
        mousex, mousey = pygame.mouse.get_pos()
        tile: Tile = self.main.get_tile_clicked(mousex, mousey, self.board, self.sizing)
        if tile is None or tile.revealed:
            return
        num = key - 48
        if key != pygame.K_BACKQUOTE and (num > len(self.player.monster_count) or num < 0):
            return
        if tile.marked_num == num or num == 0 or key == pygame.K_BACKQUOTE:
            if (self.difficulty == Difficulty.BLIND or self.difficulty == Difficulty.HUGE_BLIND) and tile.marked_num != 0:
                self.player.monster_count[tile.marked_num - 1] += 1
            tile.marked_num = 0
        else:
            self.has_marked = True
            if self.difficulty == Difficulty.BLIND or self.difficulty == Difficulty.HUGE_BLIND:
                if tile.marked_num != 0:
                    self.player.monster_count[tile.marked_num - 1] += 1
                self.player.monster_count[num - 1] -= 1
            tile.marked_num = num
        tile.draw(self.main.screen, self.sizing)

    def draw_time(self):
        if self.level_up_check:
            return
        TIME_SURFACE = self.PLAYER_STATS_FONT.render("TIME: " + str(self.time), False, WHITE)
        TIME_RECT = pygame.Rect(int(self.main.screen.get_width() * 0.7), 0, int(self.main.screen.get_width() * 0.3), self.sizing.SCORE_HEIGHT)
        self.main.screen.fill(BLACK, TIME_RECT)
        TIME_TEXT_RECT = TIME_SURFACE.get_rect(bottomright = pygame.Rect(0, 0, self.main.screen.get_width(), self.sizing.SCORE_HEIGHT).bottomright)
        self.main.screen.blit(TIME_SURFACE, TIME_TEXT_RECT)

    def draw_player_stats(self):
        if self.level_up_check:
            return
        PLAYER_STATS_FONT_SURFACE = self.PLAYER_STATS_FONT.render("LV: " + str(self.player.level) + "   HP: " + str(self.player.hp) + "   EX: " + str(self.player.exp) + "   NE: " + str(self.player.req[self.player.level - 1]), False, WHITE)
        STATS_TEXT_RECT = PLAYER_STATS_FONT_SURFACE.get_rect(bottomleft = pygame.Rect(0, 0, self.main.screen.get_width(), self.sizing.SCORE_HEIGHT).bottomleft)
        self.main.screen.fill(BLACK, pygame.Rect(0, 0, int(self.main.screen.get_width() * 0.7), self.sizing.SCORE_HEIGHT))
        self.main.screen.blit(PLAYER_STATS_FONT_SURFACE, STATS_TEXT_RECT)

    def draw_board(self):
        if self.difficulty == Difficulty.EASY:
            self.main.screen.fill(BLACK, pygame.Rect(0, self.sizing.SCORE_HEIGHT, 7 * self.sizing.EASY_MODE_BUFFER, self._y * self.sizing.TILE_SIZE))
            self.main.screen.fill(BLACK, pygame.Rect((30 * self.sizing.TILE_SIZE - self.BOARD_SIZE[0]) // 2, self.sizing.SCORE_HEIGHT, 7 * self.sizing.EASY_MODE_BUFFER, self._y * self.sizing.TILE_SIZE))
        for i in range(self._y):
            for j in range(self._x):
                self.board.graph.tiles[i][j].draw(self.main.screen, self.sizing)

    def draw_monster_stats(self):
        if self.level_up_check:
            return
        QUESTION_MARK_TXT = self.MAIN_FONT.render("?", False, GRAY)

        self.main.screen.fill(BLACK, pygame.Rect(0, self.sizing.HEIGHT - self.sizing.MONSTER_SCORE_HEIGHT, self.sizing.WIDTH, self.sizing.MONSTER_SCORE_HEIGHT))
        for i in range(self._N):
            if self.revealed_monsters[i]:
                self.main.screen.blit(MONSTER_IMGS[self.sizing.SIZE][i], self.MONSTER_IMG_BAR_RECTS[i])
            else:
                self.main.screen.blit(QUESTION_MARK_TXT, QUESTION_MARK_TXT.get_rect(center = self.MONSTER_IMG_BAR_RECTS[i].center))
            MONSTER_BAR_TXT = self.MAIN_FONT.render("     LV" + str(i + 1) + ":x" + str(self.player.monster_count[i]), False, DEFAULT_COLOR)
            self.main.screen.blit(MONSTER_BAR_TXT, MONSTER_BAR_TXT.get_rect(midright = self.MONSTER_TXT_BAR_RECTS[i].midright))

    def draw_all(self):
        self.draw_time()
        self.draw_player_stats()
        self.draw_monster_stats()
        self.draw_board()

    def draw_level_up_effect(self):
        self.light -= 40
        self.level_up_effect_surface.set_alpha(255 - abs(self.light))
        if self.light <= 0 and self.level_up_check:
            self.level_up_effect_surface.set_alpha(255)
            self.main.screen.blit(self.level_up_effect_surface, (0, 0))
            self.level_up_check = False
            self.draw_all()
        else:
            self.main.screen.blit(self.level_up_effect_surface, (0, 0))

    def draw_screen_shake(self):
        if self.screen_shake > 0:
            self.shake_check = True
            self.screen_shake -= 5
            render_offset = [0, 0]
            if self.screen_shake:
                render_offset[0] = random.randint(0, 8) - 2
                render_offset[1] = random.randint(0, 8) - 2
            self.main.screen.blit(pygame.transform.scale(self.main.screen, self.main.screen.get_size()), render_offset)
        if self.screen_shake == 0 and self.shake_check:
            self.draw_board()
            self.draw_player_stats()
            self.shake_check = False

    def display_board(self):
        pygame.display.quit()
        pygame.display.init()
        pygame.display.set_icon(ICON_IMG)
        pygame.display.set_caption('Mamono Sweeper')
        self.sizing = Sizing(self._x, self._y, self.main.size, self.difficulty, self._N)
        self.MAIN_FONT = pygame.font.Font("assets/fonts/type_writer.ttf", self.sizing.TILE_SIZE // 2)
        self.BOARD_SIZE = (max((self._x * self.sizing.TILE_SIZE), 30 * self.sizing.TILE_SIZE), self._y * self.sizing.TILE_SIZE + self.sizing.SCORE_HEIGHT + self.sizing.MONSTER_SCORE_HEIGHT)
        self.main.screen = pygame.display.set_mode(self.BOARD_SIZE)
        self.main.current_placement = None
        self.board.graph.sizing = self.sizing
        self.board.graph.screen = self.main.screen
        self.board.graph.font = self.MAIN_FONT
        self.board.graph.resize_tiles(self.main.size)
        self.PLAYER_STATS_FONT = pygame.font.Font("assets/fonts/type_writer.ttf", self.sizing.SCORE_HEIGHT - 2)
        self.VICTORY_FONT = pygame.font.Font("assets/fonts/type_writer.ttf", int(self.main.screen.get_height() / 7))
        self.ACHIEVEMENTS_FONT = pygame.font.Font("assets/fonts/type_writer.ttf", int(self.main.screen.get_height() / 11))
        self.PLACEMENT_FONT = pygame.font.Font("assets/fonts/type_writer.ttf", int(self.main.screen.get_height() / 10 * 2.5 / 4))
        self.level_up_effect_surface = pygame.Surface((self.main.screen.get_width(), self.main.screen.get_height()))
        self.level_up_effect_surface.fill(GOLD)
        self.init_rects()
        self.draw_board()

    def restart_game(self):
        self.__init__(self.main, difficulty=self.difficulty, is_restart=True)

    def check_stars(self):
        silver = True if self.player.hp == MAX_HP[self.difficulty] else False
        gold = True if not self.has_marked else False
        return silver, gold

    def win_condition(self):
        if self.difficulty == Difficulty.BLIND or self.difficulty == Difficulty.HUGE_BLIND:
            if self.num_tiles - sum(MONSTER_COUNT[self.difficulty]) <= self.num_revealed_tiles:
                return True
        else:
            if sum(self.player.monster_count) == 0:
                return True
        return False

    def victory(self):
        if not self.game_won:
            self.score = self.milliseconds
            self.main.running = False
            current_save = self.main.save['difficulties'][self.difficulty.name]
            silver, gold = self.check_stars()
            self.main.save['difficulties'][self.difficulty.name] = {'bronze': True, 'silver': silver or current_save['silver'], 'gold': gold or current_save['gold']}
            self.main.save_game()
            high_score_list = self.main.high_scores_data[self.difficulty.name]
            self.placement = sort_high_score(high_score_list, self.score)
            if self.placement != -1:
                self.main.high_scores_data[self.difficulty.name] = (high_score_list[:self.placement] + [{"name": self.main.user.name if self.main.user.name != "" else 'ANONYMOUS', "time": self.score, "color": self.main.user.color}] + high_score_list[self.placement:])[:HIGH_SCORE_ENTRIES]
            self.main.save_high_scores()
            start_new_thread(self.main.save_online_high_scores, (self.difficulty.name, self.score))
            self.victory_surface = pygame.Surface((self.main.screen.get_width(), self.main.screen.get_height() - self.sizing.SCORE_HEIGHT - self.sizing.MONSTER_SCORE_HEIGHT))
            self.victory_y = self.sizing.SCORE_HEIGHT
            self.victory_surface.set_alpha(180)
            VICTORY_SOUND.play()
            self.draw_victory()

    def draw_victory(self):
        self.main.screen.fill(BLACK)
        self.draw_all()
        self.main.screen.blit(self.victory_surface, (0, self.victory_y))
        VICTORY_FONT_SURFACE = self.VICTORY_FONT.render('YOU WIN', False, WHITE)
        VICTORY_FONT_RECT = VICTORY_FONT_SURFACE.get_rect(centerx = self.main.screen.get_rect().centerx)
        VICTORY_FONT_RECT.y += int(self.main.screen.get_height() * 0.150)
        self.main.screen.blit(VICTORY_FONT_SURFACE, VICTORY_FONT_RECT)
        alpha = 50
        WIN_GAME_FONT_SURFACE = self.ACHIEVEMENTS_FONT.render('WIN GAME', False, BRONZE)
        silver, gold = self.check_stars()
        NO_DMG_FONT_SURFACE = self.ACHIEVEMENTS_FONT.render('NO DAMAGE', False, SILVER if silver else WHITE)
        if not silver:
            NO_DMG_FONT_SURFACE.set_alpha(alpha)
        NO_MARKING_FONT_SURFACE = self.ACHIEVEMENTS_FONT.render('NO MARKING', False, GOLD if gold else WHITE)
        if not gold:
            NO_MARKING_FONT_SURFACE.set_alpha(alpha)
        WIN_GAME_FONT_RECT = WIN_GAME_FONT_SURFACE.get_rect(right = int(self.main.screen.get_width() * 0.48))
        WIN_GAME_FONT_RECT.y = int(self.main.screen.get_height() * 0.785 - self.sizing.TILE_SIZE * 1.15)
        NO_DMG_FONT_RECT = NO_DMG_FONT_SURFACE.get_rect(right = int(self.main.screen.get_width() * 0.48))
        NO_DMG_FONT_RECT.y = int(self.main.screen.get_height() * 0.785 - self.sizing.TILE_SIZE * 1.15 - self.main.screen.get_height() / 9)
        NO_MARKING_FONT_RECT = NO_MARKING_FONT_SURFACE.get_rect(right = int(self.main.screen.get_width() * 0.48))
        NO_MARKING_FONT_RECT.y = int(self.main.screen.get_height() * 0.785 - self.sizing.TILE_SIZE * 1.15 - self.main.screen.get_height() / 4.5)

        LOCAL_PLACEMENT_TEXT_SURFACE = self.PLACEMENT_FONT.render('LOCAL RANKING', False, WHITE)
        if self.placement != -1:
            placement_str = str(self.placement + 1)
            LOCAL_PLACEMENT_SURFACE = self.PLACEMENT_FONT.render("HIGH SCORE - ", False, WHITE)
            end = int(placement_str[-1])
            local_placement = f"{placement_str}{'th' if 10 < int(placement_str) < 20 or end in [0, 4, 5, 6, 7, 8, 9] else ('rd' if end == 3 else ('nd' if end == 2 else 'st'))}"
            LOCAL_PLACEMENT_SURFACE_NUM = self.PLACEMENT_FONT.render(local_placement, False, GOLD if self.placement + 1 == 1 else (SILVER if self.placement + 1 == 2 else (BRONZE if self.placement + 1 == 3 else WHITE)))
        else:
            LOCAL_PLACEMENT_SURFACE = self.PLACEMENT_FONT.render("NOT FAST ENOUGH", False, WHITE)
            LOCAL_PLACEMENT_SURFACE_NUM = self.PLACEMENT_FONT.render("", False, WHITE)

        ONLINE_PLACEMENT_TEXT_SURFACE = self.PLACEMENT_FONT.render('ONLINE RANKING', False, WHITE)
        if self.main.current_placement is None:
            ONLINE_PLACEMENT_SURFACE = self.PLACEMENT_FONT.render('CHECKING...' if HOST != 'HOST' else 'CONFIGURE SERVER', False, WHITE)
            ONLINE_PLACEMENT_SURFACE_NUM = self.PLACEMENT_FONT.render("", False, WHITE)
        else:
            if self.main.current_placement != -1:
                placement_str = str(self.main.current_placement + 1)
                ONLINE_PLACEMENT_SURFACE = self.PLACEMENT_FONT.render("HIGH SCORE - ", False, WHITE)
                end = int(placement_str[-1])
                local_placement = f"{placement_str}{'th' if 10 < int(placement_str) < 20 or end in [0, 4, 5, 6, 7, 8, 9] else ('rd' if end == 3 else ('nd' if end == 2 else 'st'))}"
                ONLINE_PLACEMENT_SURFACE_NUM = self.PLACEMENT_FONT.render(local_placement, False, GOLD if self.main.current_placement + 1 == 1 else (SILVER if self.main.current_placement + 1 == 2 else (BRONZE if self.main.current_placement + 1 == 3 else WHITE)))
            else:
                ONLINE_PLACEMENT_SURFACE = self.PLACEMENT_FONT.render("NOT FAST ENOUGH", False, WHITE)
                ONLINE_PLACEMENT_SURFACE_NUM = self.PLACEMENT_FONT.render("", False, WHITE)
            self.main.current_placement = None

        ONLINE_PLACEMENT_RECT = ONLINE_PLACEMENT_SURFACE.get_rect(left = int(self.main.screen.get_width() * 0.52))
        ONLINE_PLACEMENT_RECT.bottom = WIN_GAME_FONT_RECT.bottom - 5
        ONLINE_PLACEMENT_TEXT_RECT = ONLINE_PLACEMENT_TEXT_SURFACE.get_rect(left = int(self.main.screen.get_width() * 0.52))
        ONLINE_PLACEMENT_TEXT_RECT.y = int(ONLINE_PLACEMENT_RECT.y - self.main.screen.get_height() / 9 * 3 / 4)
        ONLINE_PLACEMENT_NUM_RECT = ONLINE_PLACEMENT_SURFACE.get_rect(left = int(self.main.screen.get_width() * 0.52))
        ONLINE_PLACEMENT_NUM_RECT.left = ONLINE_PLACEMENT_RECT.right
        ONLINE_PLACEMENT_NUM_RECT.bottom = ONLINE_PLACEMENT_RECT.bottom

        LOCAL_PLACEMENT_RECT = LOCAL_PLACEMENT_SURFACE.get_rect(left = int(self.main.screen.get_width() * 0.52))
        LOCAL_PLACEMENT_RECT.y = int(ONLINE_PLACEMENT_RECT.y - self.main.screen.get_height() / 4.5 * 3 / 4)
        LOCAL_PLACEMENT_NUM_RECT = LOCAL_PLACEMENT_SURFACE.get_rect(left = int(self.main.screen.get_width() * 0.52))
        LOCAL_PLACEMENT_NUM_RECT.left = LOCAL_PLACEMENT_RECT.right
        LOCAL_PLACEMENT_NUM_RECT.y = int(ONLINE_PLACEMENT_RECT.y - self.main.screen.get_height() / 4.5 * 3 / 4)

        LOCAL_PLACEMENT_TEXT_RECT = LOCAL_PLACEMENT_TEXT_SURFACE.get_rect(left = int(self.main.screen.get_width() * 0.52))
        LOCAL_PLACEMENT_TEXT_RECT.y = int(ONLINE_PLACEMENT_RECT.y - self.main.screen.get_height() / 3 * 3 / 4)

        SCORE_FONT_SURFACE = self.PLACEMENT_FONT.render(f'TIME: {format_time(self.score)}', False, WHITE)
        SCORE_FONT_RECT = SCORE_FONT_SURFACE.get_rect(centerx = self.main.screen.get_rect().centerx)
        SCORE_FONT_RECT.y = int(self.main.screen.get_height() * 0.315)
        self.main.screen.blit(WIN_GAME_FONT_SURFACE, WIN_GAME_FONT_RECT)
        self.main.screen.blit(NO_DMG_FONT_SURFACE, NO_DMG_FONT_RECT)
        self.main.screen.blit(NO_MARKING_FONT_SURFACE, NO_MARKING_FONT_RECT)
        self.main.screen.blit(SCORE_FONT_SURFACE, SCORE_FONT_RECT) 
        self.main.screen.blit(LOCAL_PLACEMENT_TEXT_SURFACE, LOCAL_PLACEMENT_TEXT_RECT)
        self.main.screen.blit(LOCAL_PLACEMENT_SURFACE, LOCAL_PLACEMENT_RECT)
        self.main.screen.blit(LOCAL_PLACEMENT_SURFACE_NUM, LOCAL_PLACEMENT_NUM_RECT)
        self.main.screen.blit(ONLINE_PLACEMENT_TEXT_SURFACE, ONLINE_PLACEMENT_TEXT_RECT)
        self.main.screen.blit(ONLINE_PLACEMENT_SURFACE, ONLINE_PLACEMENT_RECT)
        self.main.screen.blit(ONLINE_PLACEMENT_SURFACE_NUM, ONLINE_PLACEMENT_NUM_RECT)

    def game_over(self):
        self.main.running = False
        GAME_OVER_SOUND.play()
        for i in range(len(self.revealed_monsters)):
            self.revealed_monsters[i] = True
        self.reveal_monsters()
        self.game_is_over = True


def run_game():
    MainGame().run()

if __name__ == '__main__':
    run_game()
