import pygame
from enum import Enum
from pathlib import Path
import sys
import os


CRYPTO_PASSWORD = 'QWERASDFZXCV123123123'

GREEN = (50, 185, 40)
LIGHT_GREEN = (0, 255, 0)
DARK_ORANGE = (140, 30, 35)
ORANGE =  (160, 99, 67)
LIGHT_ORANGE = (180, 80, 20)
MAMONO_ORANGE = (254,116,13)
MAMONO_DARK_ORANGE = (176, 75, 0)
YELLOW = (200, 200, 0)
GOLD = (255, 215, 0)
GRAY = (192, 192, 192)
MEDIUM_GRAY = (140, 140, 140)
DARK_GRAY = (35, 35, 35)
DEFAULT_COLOR = (235, 235, 235)
RED = (255, 25, 25)
DARK_RED = (170, 0, 0)
LIGHT_RED = (255, 70, 70)
BLACK = (0, 0, 0)
WHITE = (255, 255 ,255)
BRONZE = (227, 63, 0)
SILVER = (186, 186, 186)
BLUE = (25, 70, 255)

FOREGROUND_GREYED = (88, 37, 0)
BACKGROUND_GREYED = (127, 58, 6)

dir_path = os.path.join(os.environ['APPDATA'], 'Mamono')
if not os.path.exists(dir_path):
    os.makedirs(dir_path)
if sys.platform.startswith('linux'):
    userdata_folder = str(Path.home()) + '\local\share\\'
if sys.platform.startswith('win32'):
    userdata_folder = os.getenv('APPDATA')
userdata_folder += '\Mamono Sweeper\\'
userdata_path = Path(fr"{userdata_folder}")
try:
    os.mkdir(userdata_path)
except FileExistsError:
    pass

HIGH_SCORES_FILE_NAME = f'{userdata_folder}\\high_scores'
ONLINE_HIGH_SCORES_FILE_NAME = 'high_scores_online'

USER_FILE_NAME = f'{userdata_folder}\\user'

SAVE_FILE_NAME = f'{userdata_folder}\\save'

HOST, PORT, PASSWORD, USERNAME = [None] * 4
with open('server_info', 'r') as f:
    HOST, PORT, PASSWORD, USERNAME = f.read().split()
    try:
        PORT = int(PORT)
    except:
        pass

class Size(Enum):
    SMALL = 0
    MEDIUM = 1
    LARGE = 2

class Difficulty(Enum):
    EASY = 0
    NORMAL = 1
    EXTREME = 2
    HUGE = 3
    BLIND = 4
    HUGE_EXTREME = 5
    HUGE_BLIND = 6

MONSTER_COUNT = dict({
    Difficulty.EASY:         [10, 8, 6, 4, 2],
    Difficulty.NORMAL:       [33, 27, 20, 13, 6],
    Difficulty.EXTREME:      [25, 25, 25, 25, 25],
    Difficulty.HUGE:         [52, 46, 40, 36, 30, 24, 18, 13, 1],
    Difficulty.BLIND:        [33, 27, 20, 13, 6],
    Difficulty.HUGE_EXTREME: [36, 36, 36, 36, 36, 36, 36, 36, 36],
    Difficulty.HUGE_BLIND:   [52, 46, 40, 36, 30, 24, 18, 13, 1]
})

MAX_HP = dict({
    Difficulty.EASY:         10,
    Difficulty.NORMAL:       10,
    Difficulty.EXTREME:      10,
    Difficulty.HUGE:         30,
    Difficulty.BLIND:        1,
    Difficulty.HUGE_EXTREME: 10,
    Difficulty.HUGE_BLIND:   1
})

REQUIRED_EXP_FOR_LEVEL_UP = dict({
    Difficulty.EASY:         [7, 20, 50, 82, '-'],
    Difficulty.NORMAL:       [10, 50, 167, 271, '-'],
    Difficulty.EXTREME:      [10, 50, 175, 375, '-'],
    Difficulty.HUGE:         [10, 90, 202, 400, 1072, 1840, 2992, 4656, 9180, '-'],
    Difficulty.BLIND:        ['-'],
    Difficulty.HUGE_EXTREME: [3, 10, 150, 540, 1116, 2268, 4572, 9180, '-'],
    Difficulty.HUGE_BLIND:   ['-']
})

DIFFICULTY_COLORS = dict({
    Difficulty.EASY: (149, 153, 0),
    Difficulty.NORMAL: (66, 41, 0),
    Difficulty.EXTREME: (43, 0, 187),
    Difficulty.HUGE: (0, 85, 9),
    Difficulty.BLIND: (69, 69, 69),
    Difficulty.HUGE_EXTREME: (43, 0, 187),
    Difficulty.HUGE_BLIND: (69, 69, 69)
})

DIFFICULTY_BACK_COLORS = dict({
    Difficulty.EASY: (221, 210, 0),
    Difficulty.NORMAL: (140, 88, 0),
    Difficulty.EXTREME: (112, 70, 255),
    Difficulty.HUGE: (4, 153, 0),
    Difficulty.BLIND: (175, 175, 175),
    Difficulty.HUGE_EXTREME: (112, 70, 255),
    Difficulty.HUGE_BLIND: (175, 175, 175)
})

FPS = 60

pygame.font.init()
TITLE_FONT = pygame.font.Font("assets/fonts/type_writer.ttf", 36)
MENU_FONT = pygame.font.Font("assets/fonts/type_writer.ttf", 20)
MENU_FONT_TITLE = pygame.font.Font("assets/fonts/type_writer.ttf", 30)
MENU_FONT_SMALL = pygame.font.Font("assets/fonts/type_writer.ttf", 16)
SCORERS_FONT = pygame.font.Font("assets/fonts/Windows_Regular.ttf", 32)
SCORERS_NUM_FONT = pygame.font.Font("assets/fonts/Mojang-Regular.ttf", 16)

MAIN_MENU_IMG = pygame.image.load('assets/pics/main_menu.png')
MAIN_MENU_DIFF_IMG = pygame.image.load('assets/pics/main_menu.png')
ICON_IMG = pygame.image.load('assets/logo/logo.png')

BRONZE_STAR_IMG = pygame.image.load('assets/pics/star_bronze.png')
SILVER_STAR_IMG = pygame.image.load('assets/pics/star_silver.png')
GOLD_STAR_IMG = pygame.image.load('assets/pics/star_gold.png')

EMPTY_SCORE_IMG = pygame.image.load('assets/pics/empty_score.png')

TUTORIAL_PAGES = []
for i in range(9):
    TUTORIAL_PAGES.append(pygame.image.load(f'assets/pics/how_to_play_pics/how_to_play_{i}.png'))

REVEALED_TILE_IMG = dict.fromkeys(list(Size))
MONSTER_IMGS = dict.fromkeys(list(Size))
HIDDEN_TILE_IMGS = dict.fromkeys(list(Size))

for size in list(Size):
    REVEALED_TILE_IMG[size] = pygame.image.load(f'assets/pics/tile_pics_{size.name.lower()}/empty_tile.png')

for size in list(Size):
    MONSTER_IMGS[size] = []
    for i in range(9):
        MONSTER_IMGS[size].append(pygame.image.load(f'assets/pics/tile_pics_{size.name.lower()}/monster{str(i + 1)}_img.png'))

for size in list(Size):
    HIDDEN_TILE_IMGS[size] = []
    for i in range(7):
        hidden_img_name = ''
        hidden_img_name_split = Difficulty(i).name.split('_')
        if len(hidden_img_name_split) == 1:
            hidden_img_name = hidden_img_name_split[0]
        else:
            hidden_img_name = hidden_img_name_split[1]
        HIDDEN_TILE_IMGS[size].append(pygame.image.load(f'assets/pics/tile_pics_{size.name.lower()}/tile_{str(hidden_img_name).lower()}.png'))

pygame.mixer.init(44100, -16, 2, 2048)
DEFAULT_VOLUME = 0.4
INTRO_MUSIC = pygame.mixer.Sound('assets/sounds/intro.mp3')
INTRO_MUSIC.set_volume(DEFAULT_VOLUME)
EMPTY_TILE_CLICK_SOUND = pygame.mixer.Sound('assets/sounds/empty_tile_click.mp3')
EMPTY_TILE_CLICK_SOUND.set_volume(DEFAULT_VOLUME) 
LEVEL_UP_SOUND = pygame.mixer.Sound('assets/sounds/level_up.mp3')
LEVEL_UP_SOUND.set_volume(DEFAULT_VOLUME) 
MAIN_MENU_CLICK_SOUND = pygame.mixer.Sound('assets/sounds/main_menu_click.mp3')
MAIN_MENU_CLICK_SOUND.set_volume(DEFAULT_VOLUME) 
TAKING_DAMAGE_SOUND = pygame.mixer.Sound('assets/sounds/taking_damage.mp3')
TAKING_DAMAGE_SOUND.set_volume(DEFAULT_VOLUME) 
VICTORY_SOUND = pygame.mixer.Sound('assets/sounds/victory.mp3')
VICTORY_SOUND.set_volume(DEFAULT_VOLUME) 
GAME_OVER_SOUND = pygame.mixer.Sound('assets/sounds/game_over.mp3')
GAME_OVER_SOUND.set_volume(DEFAULT_VOLUME) 
ERROR_SOUND = pygame.mixer.Sound('assets/sounds/error.mp3')
GAME_OVER_SOUND.set_volume(DEFAULT_VOLUME) 
KILL_SOUNDS = []
for i in range(4):
    KILL_SOUNDS.append(pygame.mixer.Sound('assets/sounds/kill/kill_' + str(i + 1) + '.mp3'))
    KILL_SOUNDS[i].set_volume(DEFAULT_VOLUME)

BUTTON_WIDTH = 385
BUTTON_HEIGHT = 37
BUTTON_PADDING = (427 - BUTTON_WIDTH) // 2
ARROW_BUTTON_WIDTH = 70
ARROW_FORWARD_PADDING = 427 - BUTTON_PADDING - ARROW_BUTTON_WIDTH
SIZE_BUTTON_WIDTH = SIZE_BUTTON_HEIGHT = 40
NAVIGATION_BUTTON_MARGIN = 4
BACK_TO_MENU_BUTTON_PADDING = ARROW_BUTTON_WIDTH + BUTTON_PADDING + NAVIGATION_BUTTON_MARGIN
BACK_TO_MENU_BUTTON_WIDTH = 427 - 2 * NAVIGATION_BUTTON_MARGIN - 2 * ARROW_BUTTON_WIDTH - 2 * BUTTON_PADDING

MAMONO_TITLE_TEXT_RECT = pygame.Rect(81, 116, 265, 39)
SWEEPER_TITLE_TEXT_RECT = pygame.Rect(81, 166, 265, 39)
MAMONO_TITLE_TEXT_SURFACE = TITLE_FONT.render('MAMONO', False, WHITE)
SWEEPER_TITLE_TEXT_SURFACE = TITLE_FONT.render('SWEEPER', False, WHITE)

CHOOSE_DIFFICULTY_RECT = pygame.Rect(BUTTON_PADDING, 226, BUTTON_WIDTH, 47)
CHOOSE_DIFFICULTY_SURFACE = MENU_FONT_SMALL.render('CHOOSE DIFFICULTY', False, WHITE)

USERNAME_RECT = pygame.Rect(BUTTON_PADDING, 232, BUTTON_WIDTH, BUTTON_HEIGHT)
USER_RECT = pygame.Rect(BUTTON_PADDING, 256, BUTTON_WIDTH, BUTTON_HEIGHT)

CONTINUE_RECT = pygame.Rect(BUTTON_PADDING, 314, BUTTON_WIDTH, BUTTON_HEIGHT)
NEW_GAME_RECT = pygame.Rect(BUTTON_PADDING, 355, BUTTON_WIDTH, BUTTON_HEIGHT)
HIGH_SCORES_RECT = pygame.Rect(BUTTON_PADDING, 396, BUTTON_WIDTH, BUTTON_HEIGHT)
HOW_TO_PLAY_RECT = pygame.Rect(BUTTON_PADDING, 437, BUTTON_WIDTH, BUTTON_HEIGHT)

EXIT_GAME_RECT = pygame.Rect(BUTTON_PADDING, 560, BUTTON_WIDTH, BUTTON_HEIGHT)

BOARD_SIZE_TEXT = MENU_FONT.render('BOARD SIZE:', False, WHITE)
BOARD_SIZE_TEXT_RECT = pygame.Rect(MAIN_MENU_IMG.get_width() - 244 - BUTTON_PADDING, 510, 40, 50)

SMALL_SIZE_BUTTON_RECT = pygame.Rect(MAIN_MENU_IMG.get_width() - 136 - BUTTON_PADDING, 515, SIZE_BUTTON_WIDTH, SIZE_BUTTON_HEIGHT)
MEDIUM_SIZE_BUTTON_RECT = pygame.Rect(MAIN_MENU_IMG.get_width() - 88 - BUTTON_PADDING, 515, SIZE_BUTTON_WIDTH, SIZE_BUTTON_HEIGHT)
LARGE_SIZE_BUTTON_RECT = pygame.Rect(MAIN_MENU_IMG.get_width() - 40 - BUTTON_PADDING, 515, SIZE_BUTTON_WIDTH, SIZE_BUTTON_HEIGHT)

DIFFICULTY_RECTS = []
for i in range(7):
    DIFFICULTY_RECTS.append(pygame.Rect(BUTTON_PADDING, 273 + i * 41, BUTTON_WIDTH, BUTTON_HEIGHT))

DIFFICULTY_BACK_BUTTON_RECT = pygame.Rect(BUTTON_PADDING, 560, 160, BUTTON_HEIGHT)

TUTORIAL_BACK_BUTTON_RECT = pygame.Rect(BUTTON_PADDING, 560, ARROW_BUTTON_WIDTH, BUTTON_HEIGHT)
TUTORIAL_BACK_TO_MENU_BUTTON_RECT = pygame.Rect(BACK_TO_MENU_BUTTON_PADDING, 560, BACK_TO_MENU_BUTTON_WIDTH, BUTTON_HEIGHT)
TUTORIAL_FORWARD_BUTTON_RECT = pygame.Rect(ARROW_FORWARD_PADDING, 560, ARROW_BUTTON_WIDTH, BUTTON_HEIGHT)

MENU_TITLE_RECT = pygame.Rect(BUTTON_PADDING, 43, BUTTON_WIDTH, BUTTON_HEIGHT)
HIGH_SCORES_LOCAL_RECT = pygame.Rect(BUTTON_PADDING, 98, int(BUTTON_WIDTH * 0.45), BUTTON_HEIGHT)
HIGH_SCORES_GLOBAL_RECT = pygame.Rect(BUTTON_PADDING + int(BUTTON_WIDTH * 0.55), 98, int(BUTTON_WIDTH * 0.45), BUTTON_HEIGHT)
TOP_SCORES_RECT = pygame.Rect(91, 150, 245, BUTTON_HEIGHT)
HIGH_SCORERS_RECTS = [pygame.Rect(BUTTON_PADDING, TOP_SCORES_RECT.y + 54 + i * 29, BUTTON_WIDTH, 25) for i in range(10)]
HIGH_SCORES_DIFFICULTY_RECT = pygame.Rect(BACK_TO_MENU_BUTTON_PADDING, HIGH_SCORERS_RECTS[-1].bottom + 17, BACK_TO_MENU_BUTTON_WIDTH, BUTTON_HEIGHT)
TOP_SCORERS_BACK_RECT = pygame.Rect(BUTTON_PADDING, 150, ARROW_BUTTON_WIDTH, BUTTON_HEIGHT)
TOP_SCORERS_FORWARD_RECT = pygame.Rect(ARROW_FORWARD_PADDING, 150, ARROW_BUTTON_WIDTH, BUTTON_HEIGHT)
HIGH_SCORES_DIFFICULTY_BACK_RECT = pygame.Rect(BUTTON_PADDING, HIGH_SCORES_DIFFICULTY_RECT.y, ARROW_BUTTON_WIDTH, BUTTON_HEIGHT)
HIGH_SCORES_DIFFICULTY_FORWARD_RECT = pygame.Rect(ARROW_FORWARD_PADDING, HIGH_SCORES_DIFFICULTY_RECT.y, ARROW_BUTTON_WIDTH, BUTTON_HEIGHT)


CHANGE_USERNAME_RECT = pygame.Rect(BUTTON_PADDING, 150, BUTTON_WIDTH, BUTTON_HEIGHT)
CHANGE_USERNAME_USER_RECT = pygame.Rect(BUTTON_PADDING, 191, BUTTON_WIDTH, BUTTON_HEIGHT)
CHANGE_USERNAME_BUTTON_RECT = pygame.Rect(BUTTON_PADDING, 232, BUTTON_WIDTH, BUTTON_HEIGHT)
CHANGE_USERNAME_COLOR_RECT = pygame.Rect(BUTTON_PADDING, 280, BUTTON_WIDTH, BUTTON_HEIGHT)

SLIDER_BUTTON_WIDTH = 20
SLIDER_BUTTON_HEIGHT = 41

SLIDER_WIDTH = int(BUTTON_WIDTH * 0.45) - SLIDER_BUTTON_WIDTH // 2
SLIDER_HEIGHT = 41


SLIDER_RED_RECT = pygame.Rect(BUTTON_PADDING + SLIDER_BUTTON_WIDTH // 2, CHANGE_USERNAME_COLOR_RECT.y + 41, SLIDER_WIDTH, BUTTON_HEIGHT)
SLIDER_GREEN_RECT = pygame.Rect(BUTTON_PADDING + SLIDER_BUTTON_WIDTH // 2, CHANGE_USERNAME_COLOR_RECT.y + 82, SLIDER_WIDTH, BUTTON_HEIGHT)
SLIDER_BLUE_RECT = pygame.Rect(BUTTON_PADDING + SLIDER_BUTTON_WIDTH // 2, CHANGE_USERNAME_COLOR_RECT.y + 123, SLIDER_WIDTH, BUTTON_HEIGHT)

CHANGE_COLOR_BUTTON_RECT = pygame.Rect(BUTTON_PADDING, SLIDER_BLUE_RECT.bottom + 8, BUTTON_WIDTH, BUTTON_HEIGHT)


USER_COLOR_RECT = pygame.Rect(BUTTON_PADDING + int(BUTTON_WIDTH * 0.55), CHANGE_USERNAME_COLOR_RECT.y + 41, int(BUTTON_WIDTH * 0.45), SLIDER_BLUE_RECT.bottom - SLIDER_RED_RECT.top)

NEW_GAME_FONT_SURFACE = MENU_FONT.render("NEW GAME", False, WHITE)
NEW_GAME_FONT_RECT = NEW_GAME_FONT_SURFACE.get_rect(center = NEW_GAME_RECT.center)

EXIT_GAME_FONT_SURFACE = MENU_FONT.render("EXIT", False, WHITE)
EXIT_GAME_FONT_RECT = EXIT_GAME_FONT_SURFACE.get_rect(center = EXIT_GAME_RECT.center)


HIGH_SCORE_ENTRIES = 100
HIGH_SCORE_ENTRIES = 100