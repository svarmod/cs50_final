import os
import ctypes

# pip install googletrans==3.1.0a0		<- this
# pip install googletrans==4.0.0-rc1
import googletrans


SCREEN_W = ctypes.windll.user32.GetSystemMetrics(0)
SCREEN_H = ctypes.windll.user32.GetSystemMetrics(1)

WND_W = 700
WND_H = 400

DB_FILENAME = "test.db"
PWD = os.path.dirname(os.path.realpath(__file__)) + "\\"

GOOGLE_IMAGE = PWD + "img\\google_256.png"

COLOR_BG = "#fff"
COLOR_BG_ALT = "#d9c5ff"

COLOR_DEFAULT = '#777'
COLOR_BAD = '#DC3222'
COLOR_LOW = '#DE9420'
COLOR_MID = '#D4C12A'
COLOR_AVG = '#8ADB23'
COLOR_GOOD = '#23B139'
COLOR_TOP = '#B143FF'

FONT_MAIN = "Cascadia Code" # Variants: "Bahnschrift Condensed", "Berlin Sans FB Demi", "Britannic Bold", "Playbill"
INFO_MSG_DELAY = 3 # in seconds

ENG = {"token": "english", "tag": "en", "short": "RUS", "image": ""}
RUS = {"token": "russian", "tag": "ru", "short": "ENG", "image": ""}

TRANSLATOR = googletrans.Translator()

