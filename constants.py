import os
import ctypes
import googletrans



# vvvvv CUSTOMIZE SECTION STARTS vvvvv

# LANGUAGE LIST - You can add any language, just use same dict template
# Codes (tags) can be found on 'https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes'
ENG = {"token": "english", "tag": "en", "short": "ENG"}
RUS = {"token": "russian", "tag": "ru", "short": "RUS"}

# BASIC DICTIONARY SETUP
LANG_FROM = ENG     # Can be changed to any language from list above
LANG_TO = RUS       # Can be changed to any language from list above

# EXAM OPTIONS - borders included
OPTIONS = [{"text": "< 10",    "min": 0.0,   "max": 9.9},
           {"text": "5 - 15",  "min": 5.0,   "max": 15.0},
           {"text": "< 20",    "min": 0.0,   "max": 19.9},
           {"text": "All",     "min": 0.0,   "max": 20.0}]

# COLORIZING
COLOR_BLACK = '#000'
COLOR_GREY  = '#666'
COLOR_WHITE = '#FFF'

COLOR_PRIMARY   = '#787DBA'
COLOR_SECONDARY = '#fcfcff'
COLOR_DECOR     = '#D5E9FF'

COLOR_BUTTON_HOVER  = '#73A1D6'
COLOR_BUTTON_ACTIVE = '#F46EB7'

COLOR_TABLE_ROW_1 = '#FFF'
COLOR_TABLE_ROW_2 = '#DDD'

COLOR_BAD   = '#DC3586'
COLOR_LOW   = '#DE9420'
COLOR_MID   = '#FCC620'
COLOR_AVG   = '#82BD23'
COLOR_GOOD  = '#23B139'
COLOR_TOP   = '#007BFF'

# FONTS
FONT_MAIN      = "Cascadia Code"  # LABELS, BUTTONS, CHECKBUTTONS, INFOS, LABELS IN HEADER
FONT_ENTRY     = "Cascadia Code"  # ENTRIES
FONT_QUIZ_WORD = "Cascadia Code"  # QUIZ WORD
FONT_SEQUENCE  = "Playbill"       # GUESS SEQUENCE

# ^^^^^^ CUSTOMIZE SECTION ENDS ^^^^^^

WND_W = 700
WND_H = 400

TITLE = "Lang Buddy"

SCREEN_W = ctypes.windll.user32.GetSystemMetrics(0)
SCREEN_H = ctypes.windll.user32.GetSystemMetrics(1)

TRANSLATOR = googletrans.Translator()

PWD = os.path.dirname(os.path.realpath(__file__)) + "\\"

DB_FILENAME = "proto.db"
TABLE_NAME = f'{LANG_FROM["tag"]}_{LANG_TO["tag"]}'

GOOGLE_IMAGE = PWD + "img\\google_256.png"
ICON_IMAGE = PWD + "img\\icon.ico"

INFO_MSG_DELAY = 3 # in seconds

ALPHABETS = {"Latin": {"id": "LATIN",    "use_extra": True,  "use_encode": True},
  "Latin (extended)": {"id": "LATIN",    "use_extra": True,  "use_encode": False},
          "Cyrillic": {"id": "CYRILLIC", "use_extra": True,  "use_encode": False},
             "Greek": {"id": "GREEK",    "use_extra": False, "use_encode": False},
            "Arabic": {"id": "ARABIC",   "use_extra": False, "use_encode": False},
            "Hebrew": {"id": "HEBREW",   "use_extra": False, "use_encode": False},
               "CJK": {"id": "CJK",      "use_extra": False, "use_encode": False},
            "Hangul": {"id": "HANGUL",   "use_extra": False, "use_encode": False},
          "Hiragana": {"id": "HIRAGANA", "use_extra": False, "use_encode": False},
          "Katakana": {"id": "KATAKANA", "use_extra": False, "use_encode": False},
              "Thai": {"id": "THAI",     "use_extra": False, "use_encode": False},
           "- ANY -": {"id": "ALL",      "use_extra": False, "use_encode": False}}
