import os
import ctypes

# pip install googletrans==3.1.0a0
import googletrans



SCREEN_W = ctypes.windll.user32.GetSystemMetrics(0)
SCREEN_H = ctypes.windll.user32.GetSystemMetrics(1)

WND_W = 700
WND_H = 400

DB_FILENAME = "proto.db"
PWD = os.path.dirname(os.path.realpath(__file__)) + "\\"

GOOGLE_IMAGE = PWD + "img\\google_256.png"

TRANSLATOR = googletrans.Translator()

INFO_MSG_DELAY = 3 # in seconds

# LANGUAGES - You can add any language, just use same dict template
ENG = {"token": "english", "tag": "en", "short": "ENG", "image": ""}
RUS = {"token": "russian", "tag": "ru", "short": "RUS", "image": ""}

# OPTIONS - Required at least 1 option setted up
OPTIONS = [{"text": "< 10", "min": 0.0, "max": 10.0},
           {"text": "5 - 15", "min": 5.0, "max": 15.0},
           {"text": "< 20", "min": 0.0, "max": 19.9},
           {"text": "All", "min": 0.0, "max": 20.9}]

# CUSOMIZING
# '#787DBA' '#73A1D6' '#D5E9FF' '#F46EB7'
# '#ab23ff' '#DC3586' '#9BB045' '#FFC607'
# '#d9c5ff' '#DC3222' '#D4C12A'

COLOR_BLACK = '#000'
COLOR_GREY = '#666'
COLOR_WHITE = '#FFF'

COLOR_PRIMARY = '#787DBA'
COLOR_SECONDARY = '#fcfcff'
COLOR_DECOR = '#D5E9FF'

COLOR_BUTTON_HOVER = '#73A1D6'
COLOR_BUTTON_ACTIVE = '#F46EB7'

COLOR_TABLE_HEADER = '#BBB'
COLOR_TABLE_ROW_1 = '#FFF'
COLOR_TABLE_ROW_2 = '#DDD'

COLOR_BAD = '#DC3586'
COLOR_LOW = '#DE9420'
COLOR_MID = '#FFC607' # need replace to more contrast
COLOR_AVG = '#8ADB23' # need replace to more contrast
COLOR_GOOD = '#23B139'
COLOR_TOP = '#007BFF'

# "Cascadia Code", "Bahnschrift Condensed",
# "Berlin Sans FB Demi", "Britannic Bold", "Playbill"

FONT_MAIN = "Cascadia Code"     # LABELS, BUTTONS, CHECKBUTTONS,
                                # INFOS, LABELS IN HEADER
FONT_TABLE = "Helvetica"        # TABLE HEADER, ROWS AND BUTTONS
FONT_ENTRY = "Cascadia Code"    # ENTRIES
FONT_QUIZ_WORD = "Cascadia Code"     # QUIZ WORD
FONT_SEQUENCE = "Playbill"      # GUESS SEQUENCE
