import pygame
import sys
import random
import time
import json
import os
import math
import datetime
import array
from functools import lru_cache

import arabic_reshaper
from bidi.algorithm import get_display

pygame.init()

# ================================
# شاشة الهاتف / الشاشة الحالية
# ================================

screen_info = pygame.display.Info()
DISPLAY_WIDTH = screen_info.current_w
DISPLAY_HEIGHT = screen_info.current_h

# جعل اللعبة عرضية وليس طولية
if DISPLAY_HEIGHT > DISPLAY_WIDTH:
    DISPLAY_WIDTH, DISPLAY_HEIGHT = DISPLAY_HEIGHT, DISPLAY_WIDTH

if DISPLAY_WIDTH < 700 or DISPLAY_HEIGHT < 400:
    WIDTH, HEIGHT = 960, 540
else:
    WIDTH, HEIGHT = DISPLAY_WIDTH, DISPLAY_HEIGHT

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption("لعبة الهروب")

# ================================
# ثوابت اللعبة
# ================================

PLAYER_SIZE = 38
PLAYER_SPEED = 4
PLAYER_SPEED_MULTIPLIER = 1.1
PLAYER_MAX_HEALTH = 2
PLAYER_HIT_INVULNERABILITY = 1.25
INITIAL_GOLD = 100
PREVIOUS_INITIAL_GOLD = 10
SPEED_BOOST_COST = 5
SPEED_BOOST_DURATION = 20
SPEED_BOOST_MULTIPLIER = 1.5
SKIP_ROUND_COST = 10
CONTINUE_COST = 5
CONTINUE_BONUS_SECONDS = 10
ENEMY_SPEED = 2
ENEMY_SPEED_MULTIPLIER = 0.8
ENEMY_STYLES = ("jelly", "ghost", "robot", "eye", "fireball", "bat", "spiky", "jumper", "bomber", "slower")


BASE_ENEMY_COUNT = 6
MAX_ENEMY_COUNT = 25
ROUND_ENEMY_COUNT_INTERVAL = 2
ROUND_ENEMY_SPEED_START = 0.78
ROUND_ENEMY_SPEED_STEP = 0.012
ROUND_ENEMY_SPEED_MAX = 1.22
ROUND_PLAYER_SCORE_CAP = 100
ROUND_TIME_CAP = 150
ROUND_SCORE_INCREMENT = 3
ROUND_TIME_INCREMENT = 2
TARGET_FPS =60
MOVEMENT_REFERENCE_FPS = 75
SHIELD_SPAWN_INTERVAL = 20
FREEZE_SPAWN_INTERVAL = 15
SHIELD_BASE_DURATION = 5
PURCHASED_SHIELD_COST = 15
PURCHASED_SHIELD_DURATION = 20
HEART_COST = 25
ROOM_CARD_COST = 50
BOSS_MAX_HEALTH = 10
STORE_DAILY_PURCHASE_LIMIT = 3
STORE_PURCHASE_KEYS = ("speed_boost", "skip_round", "shield", "heart", "room_card")

ROOM_OBJECTIVES = (
    ("score", "جمع النقاط"),
    ("survive", "البقاء للنهاية"),
)
ROOM_ENEMY_TYPES = ["عادي", "صياد", "قافز", "مفجّر", "شبح", "مختلط"]
room_settings = {
    "target": 30,
    "objective_idx": 0,
    "speed_idx": 1,
    "enemy_idx": 0,
    "boss_count": 0,  # عدد الزعماء في الروم (0 إلى 3)
}

# إحداثيات أزرار التحكم بعدد الزعماء في نافذة الروم
room_boss_minus_rect = pygame.Rect(WIDTH // 2 + 10, 415, 42, 42)
room_boss_plus_rect = pygame.Rect(WIDTH // 2 + 120, 415, 42, 42)


SPECIAL_PICKUP_INTERVAL = 16
MAGNET_DURATION = 8
SLOW_ENEMIES_DURATION = 6
MAX_PLAYER_HEALTH = PLAYER_MAX_HEALTH + 1
DAILY_MISSION_VERSION = 5
DASH_DURATION = 0.25
DASH_COOLDOWN = 5.0
DASH_SPEED_MULTIPLIER = 2.6

PLAYER_SKINS = (
    ("thief", "اللص", 0, (120, 130, 145), "متوازن"),
    ("astro", "رائد الفضاء", 25, (90, 185, 245), "سرعة +5%"),
    ("robot", "الروبوت", 40, (255, 205, 65), "اندفاع أسرع"),
    ("fox", "الثعلب", 55, (245, 125, 55), "مغناطيس +2ث"),
    ("wizard", "الساحر", 75, (145, 105, 245), "درع +1ث"),
)

ROUND_VARIANTS = (
    {
        "objective": "score",
        "description": "اجمع النقاط قبل انتهاء الوقت",
        "modifiers": (),
        "scoreless": False,
        "enemy_styles": (),
    },
    {
        "objective": "survive",
        "description": "ابقَ على قيد الحياة حتى انتهاء الوقت",
        "modifiers": (),
        "scoreless": False,
        "enemy_styles": ("ghost", "bat"),
    },
    {
        "objective": "survive",
        "description": "ابقَ على قيد الحياة أمام الأعداء المتنوعين",
        "modifiers": (),
        "scoreless": True,
        "enemy_styles": ("robot", "spiky"),
    },
    {
        "objective": "waves",
        "description": "اصمد أمام موجات الأعداء السريعة",
        "modifiers": ("fast_enemies",),
        "scoreless": True,
        "enemy_styles": ("bat", "fireball"),
    },
    {
        "objective": "score",
        "description": "اجمع نقاطًا مضاعفة",
        "modifiers": ("bonus_points",),
        "scoreless": False,
        "enemy_styles": ("jelly", "eye"),
    },
    {
        "objective": "survive",
        "description": "تفادَ المنطقة الخطرة المتحركة",
        "modifiers": ("moving_hazard",),
        "scoreless": True,
        "enemy_styles": ("fireball", "spiky"),
    },
    {
        "objective": "score",
        "description": "تحرك بين المناطق الآمنة واجمع النقاط",
        "modifiers": ("shifting_safe_zone",),
        "scoreless": False,
        "enemy_styles": ("ghost", "robot"),
    },
    {
        "objective": "survive",
        "description": "جولة بلا درع؛ احذر الأعداء السريعين",
        "modifiers": ("no_shield", "fast_enemies"),
        "scoreless": True,
        "enemy_styles": ("bat", "fireball", "spiky"),
    },
)
DAILY_MISSION_TARGETS = {"points": 100, "survive_seconds": 60 * 60, "round_wins": 5}
DAILY_MISSION_REWARD_LABELS = {
    "points": "جائزة عشوائية",
    "survive_seconds": "5 قلوب + 5 دروع",
    "round_wins": "قلب + درع",
}
ACHIEVEMENTS = {
    "collector": ("جامع النقاط", "اجمع 500 نقطة", "points_collected", 500, 20),
    "champion": ("بطل الجولات", "فز بـ10 جولات", "round_wins", 10, 30),
    "dodger": ("مراوغ", "تفادَ 50 عدوًا", "enemies_evaded", 50, 20),
    "survivor": ("صامد", "العب لمدة 10 دقائق", "play_seconds", 600, 25),
}
DAILY_CHALLENGES = (
    ("no_shield", "فز بجولة دون درع", "round_wins", 1),
    ("time_attack", "اجمع 25 نقطة بوقت أقل", "points_collected", 25),
    ("fast_enemies", "ابقَ 60 ثانية مع أعداء أسرع", "survive_seconds", 60),
)
DIFFICULTY_LEVELS = ("easy", "normal", "hard")
DIFFICULTY_LABELS = {"easy": "سهل", "normal": "عادي", "hard": "صعب"}
GAME_TIME_SCALE = 0.9
PROGRESS_FILE = "mobile_progress.json"
SETTINGS_FILE = "mobile_settings.json"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKGROUND_ASSET_DIR = os.path.join(BASE_DIR, "game_assets")
DEATH_SOUND_FILE = os.path.join(BACKGROUND_ASSET_DIR, "death.mp3")
MOVEMENT_SOUND_FILE = os.path.join(BACKGROUND_ASSET_DIR, "movement.mp3")
PLAYER_IMAGE_FILE = os.path.join(BACKGROUND_ASSET_DIR, "player_character.png")
PLAYER_WALK_FILE = os.path.join(BACKGROUND_ASSET_DIR, "player_walk.png")
FONT_FILE = os.path.join(BACKGROUND_ASSET_DIR, "tahoma.ttf") # سطر إضافي لملف الخط المخصص

BACKGROUND_COLORS = (
    ("midnight", (10, 14, 28), "داكن"),
    ("white", (235, 235, 240), "أبيض"),
)

LANGUAGES = {
    "ar": "العربية",
    "en": "English",
}

TRANSLATIONS = {
    "en": {
        "بطاقة روم": "Room Card", "بطاقات الروم:": "Room Cards:",
        "إنشاء روم للاعبين": "Create 2P Room", "روم خاص": "Custom Room",
        "إعدادات الروم": "Room Settings", "مهمة الجولة:": "Mission:",
        "النقاط المطلوبة:": "Target Score:", "سرعة الحركة:": "Move Speed:",
        "نوع الأعداء:": "Enemy Type:", "ابدأ الروم": "Start Room",
        "متنوع": "Mixed", "أشباح": "Ghosts", "روبوتات": "Robots",
        "كرات نار": "Fireballs", "خفافيش": "Bats", "شائك": "Spiky",
        "جمع النقاط": "Collect Points", "البقاء للنهاية": "Survive Time",
        "بطيء": "Slow", "سريع": "Fast",
        "تحتاج بطاقة روم من المتجر": "Need a Room Card from Store",

        "لعبة الهروب": "Escape Game", "الإعدادات": "Settings",
        "اختر خلفية اللعب": "Choose background", "اختر لون الخلفية": "Choose background",
        "اختر المظهر": "Choose appearance", "داكن": "Dark", "أبيض": "White",
        "متابعة": "Resume", "خروج": "Exit", "المتجر": "Store",
        "المهام": "Missions", "المكافآت": "Rewards", "المكافآت اليومية": "Daily Rewards",
        "القائمة": "Menu", "المزيد": "More", "ابدأ اللعبة": "Start Game", "ابدأ": "GO!",
        "الجولة الحالية:": "Current round:", "الوضع: لاعب واحد": "Mode: 1 Player",
        "الوضع: لاعبان": "Mode: 2 Players", "الجولات المنجزة:": "Completed rounds:",
        "لا توجد جولات مكتملة بعد": "No completed rounds yet",
        "اجمع 100 نقطة": "Collect 100 points", "اقضِ 60 دقيقة في اللعب": "Play for 60 minutes",
        "فز بـ5 جولات": "Win 5 rounds", "النقاط:": "Score:",
        "اجمع النقاط قبل انتهاء الوقت": "Collect points before time runs out",
        "ابقَ على قيد الحياة حتى انتهاء الوقت": "Survive until time runs out",
        "ابقَ على قيد الحياة أمام الأعداء المتنوعين": "Survive against varied enemies",
        "تحرك بين المناطق الآمنة واجمع النقاط": "Move between safe zones and collect points",
        "اصمد أمام موجات الأعداء السريعة": "Survive waves of fast enemies",
        "اجمع نقاطًا مضاعفة": "Collect double points",
        "تفادَ المنطقة الخطرة المتحركة": "Avoid the moving danger zone",
        "تحرك بين المناطق الآمنة المتبدلة": "Move between shifting safe zones",
        "جولة بلا درع؛ احذر الأعداء السريعين": "No-shield round; watch out for fast enemies",
        "شراء": "Buy", "ملفات اللاعبين": "Player profiles", "الاسم:": "Name:",
        "اللاعب 1": "Player 1", "اللاعب 2": "Player 2",
        "اضغط على الاسم لتعديله": "Tap a name to edit it",
        "الجولات الفائزة:": "Rounds won:", "أعلى جولة وصل إليها:": "Highest round reached:",
        "اكتب الاسم ثم اضغط Enter": "Type a name, then press Enter",
        "إجمالي النقاط:": "Total points:", "وقت اللعب:": "Play time:",
        "الوقت:": "Time:", "الوقت": "Time", "الأعداء:": "Enemies:", "الأعداء": "Enemies",
        "ذهب:": "Gold:", "ذهب": "gold", "رصيد الذهب:": "Gold balance:",
        "الترقيات تتجدد يوميًا": "Upgrades reset daily",
        "حد الشراء اليومي: 3 لكل عنصر": "Daily limit: 3 purchases per item",
        "شراء اليوم:": "Bought today:", "اكتمل الحد": "Limit reached",
        "المخزون:": "Inventory:", "تم الشراء": "Purchased",
        "تسريع اللاعب ×1.5 | 20 ثانية": "Speed boost ×1.5 | 20s",
        "ترقية السرعة اليومية:": "Daily speed upgrade:",
        "ترقية الدرع اليومية:": "Daily shield upgrade:",
        "زيادة الحركة 8% لكل مستوى | تتجدد اليوم": "Movement +8% per level | Resets daily",
        "زيادة مدة الدرع العادي ثانية | تتجدد اليوم": "Shield +1s per level | Resets daily",
        "تخطي الجولة الحالية وتُحسب فوزًا": "Skip round & count as win",
        "المكافأة: جولة منجزة |": "Reward: completed round |",
        "تخطي": "Skip", "درع يدوي | 20 ثانية": "Manual shield | 20s",
        "قلب إضافي للجولة القادمة": "Extra heart for next round",
        "قلب إنقاذ عند الخسارة": "Revival heart on defeat",
        "استخدم قلبًا": "Use heart", "درع": "Shield", "اندفاع": "Dash", "جاهز": "Ready",
                "المظاهر:": "Skins:", "مجهّز": "Equipped", "تجهيز": "Equip",
        "اللص": "Thief", "رائد الفضاء": "Astronaut", "الروبوت": "Hover-Bot", "الثعلب": "Cyber Fox", "الساحر": "Star Wizard",
        "الافتراضي": "Default", "الذهبي": "Golden", "الظل": "Shadow", "الملكي": "Royal",
        "متوازن": "Balanced", "سرعة +5%": "Speed +5%", "اندفاع أسرع": "Faster Dash", "مغناطيس +2ث": "Magnet +2s", "درع +1ث": "Shield +1s",
        "تعديل مكان وحجم الأزرار": "Adjust controls layout",
        "اسحب الزر لتغيير مكانه، واستخدم − و+ لتغيير حجمه": "Drag control to move; use − and + to resize",
        "عصا اللاعب الأول": "P1 Joystick", "عصا اللاعب الثاني": "P2 Joystick",
        "زر الدرع": "Shield button", "درع اللاعب الأول": "P1 Shield",
        "درع اللاعب الثاني": "P2 Shield", "زر القائمة": "Menu button",
        "زر الإعدادات": "Settings button", "تم": "Done",
        "التحكم: أسهم": "Controls: Arrows", "التحكم: أنالوج": "Controls: Analog",
        "الترقيات اليومية": "Daily upgrades", "الإعدادات الصوتية": "Audio settings",
        "مؤثرات الصوت": "Sound effects", "الموسيقى": "Music",
        "اللغة": "Language", "الألوان": "Colors",
        "العربية": "Arabic", "English": "English",
        "الإحصائيات": "Statistics", "إحصائيات اللاعب": "Player statistics",
        "تحدي اليوم": "Daily challenge", "التحدي اليومي": "Daily challenge",
        "الصعوبة: سهل": "Difficulty: Easy", "الصعوبة: عادي": "Difficulty: Normal",
        "الصعوبة: صعب": "Difficulty: Hard", "الصعوبة": "Difficulty",
        "سهل": "Easy", "عادي": "Normal", "صعب": "Hard",
        "ابدأ التحدي اليومي": "Start daily challenge", "إيقاف التحدي اليومي": "Pause daily challenge",
        "مكافأة التحدي: 20 ذهب - اكتملت": "Challenge reward: 20 gold - Done",
        "اجمع 25 نقطة": "Collect 25 points", "ابقَ 60 ثانية في جولة": "Survive 60 seconds in a round",
        "فز بجولة واحدة": "Win one round", "الإنجازات ومكافآتها": "Achievements & rewards",
        "فز بجولة دون درع": "Win a round without shield",
        "اجمع 25 نقطة بوقت أقل": "Collect 25 points with less time",
        "ابقَ 60 ثانية مع أعداء أسرع": "Survive 60s with faster enemies",
        "النقاط التي جمعتها": "Points collected", "الجولات التي فزت بها": "Rounds won",
        "الأعداء الذين تفاديتهم": "Enemies dodged", "وقت اللعب": "Play time",
        "دقيقة": "min", "جامع النقاط": "Collector", "بطل الجولات": "Champion",
        "مراوغ": "Dodger", "صامد": "Survivor",
        "اجمع 500 نقطة": "Collect 500 points", "فز بـ10 جولات": "Win 10 rounds",
        "تفادَ 50 عدوًا": "Evade 50 enemies", "العب لمدة 10 دقائق": "Play for 10 minutes",
        "تحذير: الزعيم قادم!": "Warning: Boss incoming!",
        "مرحلة": "Phase", "كومبو": "Combo",
        "المهام اليومية": "Daily missions", "مكافآت الأيام السبعة": "7-day rewards",
        "اجمع النقاط": "Collect points", "ابقَ في اللعب": "Stay in the game",
        "استخدم العناصر": "Use power-ups", "الجائزة: قلب": "Prize: Heart",
        "الجائزة: درع": "Prize: Shield",
        "جائزة عشوائية": "Random reward", "قلب + درع": "Heart + Shield",
        "5 قلوب + 5 دروع": "5 Hearts + 5 Shields",
        "النقاط: جائزة عشوائية | 60 دقيقة: 5 قلوب + 5 دروع | 5 انتصارات: قلب + درع": "100 pts: Random | 60m: 5 Hearts+Shields | 5 Wins: Heart+Shield",
        "اكتملت": "Completed", "جمعت مكافأتك اليوم، عد غدًا": "Today's reward collected. Come back tomorrow",
        "إعادة الجولة": "Retry round", "إعادة الجولة ": "Replay round ",
        "الجولة التالية": "Next Round", "أحسنت!": "Well Done!",
        "لقد أكملت هذه الجولة بنجاح": "You completed this round successfully",
        "انتهت الجولة": "Round Over", "خسر": "lost",
        "متابعة الجولة مقابل": "Continue round for", "رصيدك:": "Balance:",
        "فاز": "Won", "مدة الصمود لكل لاعب": "Survival time per player",
        "النتيجة لكل لاعب": "Score per player", "مدة الصمود": "Survival time",
        "النتيجة": "Score", "الجولة": "Round", "جولة": "Round",
        "أفضل نتيجة": "Best score", "أسرع جولة": "Fastest round",
        "أسرع:": "Fastest:", "ترقية": "Upgrade", "تمت": "Done",
        "الوقت المتبقي:": "Time left:", "الدرع:": "Shield:",
        "التجميد:": "Freeze:", "التسريع:": "Speed:",
        "المغناطيس:": "Magnet:", "إبطاء الأعداء:": "Slow enemies:",
        "إعادة": "Retry", "فوز": "Victory", "خسرت": "Game over",
        "تجميع النقاط": "Collect points", "يوم": "Day", "جمع": "Claim",
        "المتاح الآن:": "Available now:", "عربي": "Arabic",
        "الفوز:": "Wins:", "اللعب:": "Play:",
        "أعلى مرحلة:": "Max round:", "ثانية": "seconds", "ث": "s", "د": "m",
    },
}



def build_background_theme(color):
    brightness = sum(color) / 3
    dark = brightness < 145
    background_color = pygame.Color(*color)
    hue, saturation, _, _ = background_color.hsva
    accent_hue = (hue + 145) % 360 if saturation > 18 else 195
    accent_color = pygame.Color(0)
    accent_color.hsva = (accent_hue, 72, 94 if dark else 78, 100)
    accent = tuple(accent_color)[:3]
    line = tuple(min(255, int(channel * 1.28 + (22 if dark else 0))) for channel in color)
    glow = tuple(min(255, int(channel * 0.55 + (80 if dark else 28))) for channel in color)
    player = (255, 125, 104) if dark else (120, 35, 55)
    enemy = (255, 222, 112) if dark else (32, 45, 76)
    return {
        "bg": color,
        "line": line,
        "glow": glow,
        "accent": accent,
        "accent_soft": tuple(min(255, int(channel * 0.55 + 90)) for channel in accent),
        "stars": tuple(min(255, channel + (45 if dark else 18)) for channel in color),
        "panel": tuple(max(0, int(channel * (0.68 if dark else 0.88))) for channel in color),
        "player": player,
        "player_outline": (50, 22, 32) if dark else (255, 245, 230),
        "enemy": enemy,
        "enemy_outline": (40, 35, 24) if dark else (255, 155, 65),
        "point": accent,
        "point_outline": tuple(min(255, channel + 80) for channel in accent),
        "frame": accent,
    }


BACKGROUND_THEMES = {
    color_id: build_background_theme(color)
    for color_id, color, _ in BACKGROUND_COLORS
}
BACKGROUND_COLOR_VALUES = {
    color_id: color for color_id, color, _ in BACKGROUND_COLORS
}

DEATH_SOUND = None
try:
    if pygame.mixer.get_init() is None:
        pygame.mixer.init()
    DEATH_SOUND = pygame.mixer.Sound(DEATH_SOUND_FILE)
except (pygame.error, OSError) as exc:
    print(f"تعذر تحميل صوت الموت: {exc}")

MOVEMENT_SOUND = None
try:
    MOVEMENT_SOUND = pygame.mixer.Sound(MOVEMENT_SOUND_FILE)
    MOVEMENT_SOUND.set_volume(0.4)
except (pygame.error, OSError) as exc:
    print(f"تعذر تحميل صوت حركة اللاعب: {exc}")

SFX_VOLUME = 0.7
MUSIC_VOLUME = 0.2
MUSIC_SOUND = None
MUSIC_CHANNEL = None
BOSS_WARNING_SOUND = None
try:
    if pygame.mixer.get_init() is None:
        pygame.mixer.init()
    sample_rate = pygame.mixer.get_init()[0]
    samples = array.array("h")
    melody = (220.0, 261.63, 329.63, 293.66, 196.0, 246.94, 293.66, 261.63)
    sample_count = sample_rate * 8
    for sample_index in range(sample_count):
        elapsed = sample_index / sample_rate
        note_index = int(elapsed) % len(melody)
        phase = elapsed - int(elapsed)
        envelope = min(1.0, phase * 12) * min(1.0, (1.0 - phase) * 7)
        note = melody[note_index]
        tone = math.sin(math.tau * note * elapsed) * 0.72
        tone += math.sin(math.tau * note * 2 * elapsed) * 0.18
        tone += math.sin(math.tau * note * 0.5 * elapsed) * 0.1
        samples.append(int(max(-1.0, min(1.0, tone * envelope * 2300))))
    MUSIC_SOUND = pygame.mixer.Sound(buffer=samples.tobytes())
    pygame.mixer.set_reserved(1)
    MUSIC_CHANNEL = pygame.mixer.Channel(0)
    MUSIC_CHANNEL.play(MUSIC_SOUND, loops=-1)
    MUSIC_CHANNEL.set_volume(MUSIC_VOLUME)
    warning_samples = array.array("h")
    for sample_index in range(sample_rate // 2):
        elapsed = sample_index / sample_rate
        envelope = min(1.0, elapsed * 18) * max(0.0, 1.0 - elapsed * 1.8)
        frequency = 360 + 260 * elapsed
        warning_samples.append(int(math.sin(math.tau * frequency * elapsed) * envelope * 8500))
    BOSS_WARNING_SOUND = pygame.mixer.Sound(buffer=warning_samples.tobytes())
except (pygame.error, OSError) as exc:
    print(f"تعذر تشغيل موسيقى اللعبة: {exc}")

movement_sound_channel = None

def load_best_arabic_font(size, bold=False):
    if os.path.isdir(BACKGROUND_ASSET_DIR):
        for fname in os.listdir(BACKGROUND_ASSET_DIR):
            if fname.lower().startswith(("tahoma", "cairo")) and fname.lower().endswith((".ttf", ".otf")):
                return pygame.font.Font(os.path.join(BACKGROUND_ASSET_DIR, fname), size)
    for font_name in ("tahoma", "arial", "segoeui", "dejavusans"):
        matched = pygame.font.match_font(font_name, bold=bold)
        if matched:
            return pygame.font.Font(matched, size)
    return pygame.font.SysFont("Tahoma", size, bold)


TITLE_FONT = load_best_arabic_font(48, True)
MED_FONT = load_best_arabic_font(28, False)
SMALL_FONT = load_best_arabic_font(20, False)
FPS_FONT = load_best_arabic_font(18, True)


ROUNDS_PER_PAGE = 10

# ================================
# دعم اللغات
# ================================

current_language = "ar"


def arabic_text(text):
    text = str(text)
    if current_language != "ar":
        translations = TRANSLATIONS.get(current_language, {})
        if text in translations:
            return translations[text]
        for source in sorted(translations, key=len, reverse=True):
            if source in text:
                text = text.replace(source, translations[source])
        return text
    return get_display(arabic_reshaper.reshape(text))


def apply_audio_settings():
    if DEATH_SOUND is not None:
        DEATH_SOUND.set_volume(SFX_VOLUME)
    if MOVEMENT_SOUND is not None:
        MOVEMENT_SOUND.set_volume(SFX_VOLUME * 0.4)
    if movement_sound_channel is not None:
        movement_sound_channel.set_volume(SFX_VOLUME * 0.4)
    if MUSIC_CHANNEL is not None:
        MUSIC_CHANNEL.set_volume(MUSIC_VOLUME)


def play_death_sound():
    if DEATH_SOUND is not None:
        DEATH_SOUND.play()


def play_boss_warning():
    if BOSS_WARNING_SOUND is not None:
        BOSS_WARNING_SOUND.set_volume(SFX_VOLUME)
        BOSS_WARNING_SOUND.play()


def update_movement_sound(should_play):
    global movement_sound_channel
    if MOVEMENT_SOUND is None:
        return
    if should_play:
        if movement_sound_channel is None or not movement_sound_channel.get_busy():
            movement_sound_channel = MOVEMENT_SOUND.play(loops=-1)
    elif movement_sound_channel is not None:
        movement_sound_channel.stop()
        movement_sound_channel = None


# ================================
# حفظ التقدم
# ================================

def default_progress():
    return {
        "round": 1,
        "target": 20,
        "time_limit": 50,
        "completed_rounds": [],
        "game_modes": {
            "1": default_mode_progress(),
            "2": default_mode_progress(),
        },
        "gold": INITIAL_GOLD,
        "stats": {
            "points_collected": 0,
            "round_wins": 0,
            "enemies_evaded": 0,
            "play_seconds": 0.0,
            "claimed_achievements": [],
        },
        "daily_challenge": {},
        "player_profiles": {
            "1": {"points": 0, "round_wins": 0, "play_seconds": 0.0, "highest_round": 1},
            "2": {"points": 0, "round_wins": 0, "play_seconds": 0.0, "highest_round": 1},
        },
        "speed_boost_pending": False,
        "purchased_shields": 0,
        "purchased_hearts": 0,
        "room_cards": 0,
        "last_daily_reward_date": "",
        "upgrade_reset_date": datetime.date.today().isoformat(),
        "daily_store_purchases": {},
        "next_daily_reward": 1,
        "speed_upgrade_level": 0,
        "shield_upgrade_level": 0,
                "best_score": 0,
        "best_round_time": 0,
        "daily_missions": {},
        "unlocked_skins": ["thief"],
        "equipped_skin": "thief",
    }


def default_mode_progress():
    return {
        "round": 1,
        "target": 20,
        "time_limit": 50,
        "completed_rounds": [],
        "best_score": 0,
        "best_round_time": 0,
    }


def normalize_daily_store_purchases(saved_purchases):
    if not isinstance(saved_purchases, dict):
        saved_purchases = {}
    purchases = {}
    for key in STORE_PURCHASE_KEYS:
        try:
            count = int(saved_purchases.get(key, 0))
        except (TypeError, ValueError, OverflowError):
            count = 0
        purchases[key] = min(STORE_DAILY_PURCHASE_LIMIT, max(0, count))
    return purchases


def normalize_mode_progress(saved_mode, fallback=None):
    if not isinstance(saved_mode, dict):
        saved_mode = fallback if isinstance(fallback, dict) else {}
    defaults = default_mode_progress()
    try:
        round_num = max(1, int(saved_mode.get("round", defaults["round"])))
        target = max(1, int(saved_mode.get("target", defaults["target"])))
        time_limit = max(1, int(saved_mode.get("time_limit", defaults["time_limit"])))
        best_score = max(0, int(saved_mode.get("best_score", defaults["best_score"])))
        best_round_time = max(
            0.0, float(saved_mode.get("best_round_time", defaults["best_round_time"])),
        )
    except (TypeError, ValueError, OverflowError):
        return defaults
    saved_rounds = saved_mode.get("completed_rounds", defaults["completed_rounds"])
    if not isinstance(saved_rounds, list):
        saved_rounds = []
    completed_rounds = sorted({
        round_value for round_value in saved_rounds
        if isinstance(round_value, int)
        and not isinstance(round_value, bool)
        and round_value > 0
    })
    return {
        "round": round_num,
        "target": target,
        "time_limit": time_limit,
        "completed_rounds": completed_rounds,
        "best_score": best_score,
        "best_round_time": best_round_time,
    }


def load_progress(legacy_player_count=2):
    if not os.path.exists(PROGRESS_FILE):
        return default_progress()

    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("ملف التقدم يجب أن يحتوي على كائن JSON")

        completed_rounds = data.get("completed_rounds", [])
        if not isinstance(completed_rounds, list):
            completed_rounds = []
        completed_rounds = sorted({
            round_value for round_value in completed_rounds
            if isinstance(round_value, int)
            and not isinstance(round_value, bool)
            and round_value > 0
        })
        saved_mode_progress = data.get("game_modes", {})
        if not isinstance(saved_mode_progress, dict):
            saved_mode_progress = {}
        legacy_mode_progress = {
            "round": data.get("round", 1),
            "target": data.get("target", 20),
            "time_limit": data.get("time_limit", 50),
            "completed_rounds": completed_rounds,
            "best_score": data.get("best_score", 0),
            "best_round_time": data.get("best_round_time", 0),
        }
        game_modes = {
            "1": normalize_mode_progress(saved_mode_progress.get("1")),
            "2": normalize_mode_progress(saved_mode_progress.get("2")),
        }
        legacy_mode_key = str(legacy_player_count)
        game_modes[legacy_mode_key] = normalize_mode_progress(
            saved_mode_progress.get(legacy_mode_key), legacy_mode_progress,
        )
        gold = max(0, int(data.get("gold", INITIAL_GOLD + len(set(completed_rounds)) // 3)))
        gold_migrated = "gold" in data and not data.get("initial_gold_bonus_applied", False)
        if gold_migrated:
            gold += INITIAL_GOLD - PREVIOUS_INITIAL_GOLD
        daily_missions = data.get("daily_missions", {})
        if not isinstance(daily_missions, dict):
            daily_missions = {}
        saved_stats = data.get("stats", {})
        if not isinstance(saved_stats, dict):
            saved_stats = {}
        saved_achievements = saved_stats.get("claimed_achievements", [])
        if not isinstance(saved_achievements, list):
            saved_achievements = []
        stats = {
            "points_collected": max(0, int(saved_stats.get("points_collected", 0))),
            "round_wins": max(0, int(saved_stats.get("round_wins", 0))),
            "enemies_evaded": max(0, int(saved_stats.get("enemies_evaded", 0))),
            "play_seconds": max(0.0, float(saved_stats.get("play_seconds", 0))),
            "claimed_achievements": [
                key for key in saved_achievements
                if key in ACHIEVEMENTS
            ],
        }
        saved_profiles = data.get("player_profiles", {})
        if not isinstance(saved_profiles, dict):
            saved_profiles = {}
        player_profiles = {}
        for player_id in ("1", "2"):
            saved_profile = saved_profiles.get(player_id, {})
            if not isinstance(saved_profile, dict):
                saved_profile = {}
            player_profiles[player_id] = {
                "points": max(0, int(saved_profile.get("points", 0))),
                "round_wins": max(0, int(saved_profile.get("round_wins", 0))),
                "play_seconds": max(0.0, float(saved_profile.get("play_seconds", 0))),
                "highest_round": max(1, int(saved_profile.get("highest_round", 1))),
            }
        if "1" not in saved_profiles:
            player_profiles["1"] = {
                "points": stats["points_collected"],
                "round_wins": stats["round_wins"],
                "play_seconds": stats["play_seconds"],
                "highest_round": max(
                    1, int(data.get("round", 1)),
                    max(completed_rounds, default=1),
                ),
            }
        daily_challenge = data.get("daily_challenge", {})
        if not isinstance(daily_challenge, dict):
            daily_challenge = {}
        saved_store_purchases = data.get("daily_store_purchases", {})
        daily_store_purchases = normalize_daily_store_purchases(saved_store_purchases)
        return {
            "round": data.get("round", 1),
            "target": data.get("target", 20),
            "time_limit": data.get("time_limit", 50),
            "completed_rounds": completed_rounds,
            "game_modes": game_modes,
            "gold": gold,
            "_gold_migrated": gold_migrated,
            "speed_boost_pending": bool(data.get("speed_boost_pending", False)),
            "purchased_shields": max(0, int(data.get("purchased_shields", 0))),
            "purchased_hearts": max(0, int(data.get("purchased_hearts", 0))),
            "room_cards": max(0, int(data.get("room_cards", 0))),
            "last_daily_reward_date": data.get("last_daily_reward_date", ""),
            "upgrade_reset_date": data.get(
                "upgrade_reset_date", datetime.date.today().isoformat()),
            "daily_store_purchases": daily_store_purchases,
            "next_daily_reward": min(7, max(1, int(data.get("next_daily_reward", 1)))),
            "speed_upgrade_level": min(3, max(0, int(data.get("speed_upgrade_level", 0)))),
            "shield_upgrade_level": min(3, max(0, int(data.get("shield_upgrade_level", 0)))),
            "best_score": max(0, int(data.get("best_score", 0))),
            "best_round_time": max(0.0, float(data.get("best_round_time", 0))),
            "daily_missions": daily_missions,
                       "stats": stats,
            "player_profiles": player_profiles,
            "daily_challenge": daily_challenge,
            "unlocked_skins": [s for s in data.get("unlocked_skins", ["thief"]) if s in [item[0] for item in PLAYER_SKINS]] or ["thief"],
            "equipped_skin": data.get("equipped_skin") if data.get("equipped_skin") in data.get("unlocked_skins", ["thief"]) else "thief",
        }
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:

        print(f"تعذر تحميل التقدم، ستبدأ اللعبة بتقدم جديد: {exc}")
        return default_progress()


def save_progress(round_num, target, time_limit, completed_rounds):
    game_mode_progress[str(player_count)] = {
        "round": round_num,
        "target": target,
        "time_limit": time_limit,
        "completed_rounds": completed_rounds,
        "best_score": best_score,
        "best_round_time": best_round_time,
    }
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "round": round_num,
                "target": target,
                "time_limit": time_limit,
                "completed_rounds": completed_rounds,
                "game_modes": game_mode_progress,
                "gold": gold_coins,
                "initial_gold_bonus_applied": True,
                "speed_boost_pending": speed_boost_pending,
                "purchased_shields": purchased_shields,
                "purchased_hearts": purchased_hearts,
                "room_cards": room_cards,
                "last_daily_reward_date": last_daily_reward_date,
                "upgrade_reset_date": upgrade_reset_date,
                "daily_store_purchases": daily_store_purchases,
                "next_daily_reward": next_daily_reward,
                "speed_upgrade_level": speed_upgrade_level,
                "shield_upgrade_level": shield_upgrade_level,
                "best_score": best_score,
                "best_round_time": best_round_time,
                "daily_missions": daily_missions,
                "stats": stats,
                "player_profiles": player_profiles,
                "daily_challenge": daily_challenge,
                "unlocked_skins": unlocked_skins,
                "equipped_skin": equipped_skin,
            }, f, ensure_ascii=False)
    except (OSError, TypeError, ValueError) as exc:
        print(f"تعذر حفظ التقدم: {exc}")


def default_control_layout():
    action_size = min(72, max(52, (WIDTH - 540) // 3))
    return {
        "movement_left": {"x": 150 / WIDTH, "y": (HEIGHT - 92) / HEIGHT, "scale": 1.0},
        "movement_right": {
            "x": (WIDTH - 150) / WIDTH,
            "y": (HEIGHT - 92) / HEIGHT,
            "scale": 1.0,
        },
        "actions_single": {
            "x": (WIDTH - 24 - action_size // 2) / WIDTH,
            "y": (HEIGHT - 92) / HEIGHT,
            "scale": 1.0,
        },
        "actions_player_1": {
            "x": 0.16,
            "y": (HEIGHT - 220 + action_size // 2) / HEIGHT,
            "scale": 1.0,
        },
        "actions_player_2": {
            "x": 0.84,
            "y": (HEIGHT - 220 + action_size // 2) / HEIGHT,
            "scale": 1.0,
        },
        "menu": {"x": (WIDTH // 2 - 29) / WIDTH, "y": 32 / HEIGHT, "scale": 1.0},
        "settings": {"x": (WIDTH // 2 + 42) / WIDTH, "y": 32 / HEIGHT, "scale": 1.0},
    }


def normalize_control_layout(saved_layout):
    defaults = default_control_layout()
    if not isinstance(saved_layout, dict):
        return defaults
    for key, default in defaults.items():
        saved = saved_layout.get(key)
        if not isinstance(saved, dict):
            continue
        try:
            defaults[key] = {
                "x": max(0.04, min(0.96, float(saved.get("x", default["x"])))),
                "y": max(0.06, min(0.94, float(saved.get("y", default["y"])))),
                "scale": max(0.65, min(1.6, float(saved.get("scale", 1.0)))),
            }
        except (TypeError, ValueError, OverflowError):
            continue
    return defaults


def load_settings():
    defaults = {
        "background_color": "midnight",
        "sfx_volume": 0.7,
        "music_volume": 0.2,
        "language": "ar",
        "difficulty": "normal",
        "player_count": 2,
        "control_style": "analog",
        "control_layout": default_control_layout(),
        "player_names": {"1": "اللاعب 1", "2": "اللاعب 2"},
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("ملف الإعدادات يجب أن يحتوي على كائن JSON")
            saved_color = data.get("background_color", data.get("background", "midnight"))
            legacy_colors = {"night": "midnight", "day": "sky", "forest": "forest", "sunset": "coral"}
            saved_color = legacy_colors.get(saved_color, saved_color)
            if saved_color not in ("midnight", "white"):
                saved_color_rgb = BACKGROUND_COLOR_VALUES.get(saved_color)
                saved_color = (
                    "white"
                    if saved_color_rgb and  sum(saved_color_rgb) / 3 >= 145
                    else "midnight"
                )
            defaults["background_color"] = saved_color
            defaults["language"] = (
                data.get("language") if data.get("language") in LANGUAGES else "ar")
            defaults["difficulty"] = (
                data.get("difficulty") if data.get("difficulty") in DIFFICULTY_LEVELS else "normal")
            saved_player_count = data.get("player_count", defaults["player_count"])
            if (isinstance(saved_player_count, int) and not isinstance(saved_player_count, bool)
                    and saved_player_count in (1, 2)):
                defaults["player_count"] = saved_player_count
            defaults["control_style"] = (
                data.get("control_style")
                if data.get("control_style") in ("analog", "arrows")
                else "analog"
            )
            defaults["control_layout"] = normalize_control_layout(
                data.get("control_layout")
            )
            saved_names = data.get("player_names", {})
            if isinstance(saved_names, dict):
                for player_id in ("1", "2"):
                    saved_name = saved_names.get(player_id)
                    if isinstance(saved_name, str):
                        saved_name = "".join(
                            character for character in saved_name if character.isprintable()
                        ).strip()[:18]
                        if saved_name:
                            defaults["player_names"][player_id] = saved_name
            for setting in ("sfx_volume", "music_volume"):
                try:
                    defaults[setting] = max(0.0, min(1.0, float(data.get(setting, defaults[setting]))))
                except (TypeError, ValueError):
                    pass
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            print(f"تعذر تحميل الإعدادات، ستُستخدم القيم الافتراضية: {exc}")
    return defaults


def save_settings(changes):
    global current_background_theme, current_language, current_difficulty, SFX_VOLUME, MUSIC_VOLUME
    global two_player_mode, player_count, control_style
    previous_player_count = player_count
    previous_control_style = control_style
    settings.update(changes)
    current_background_theme = settings.get("background_color", "midnight")
    current_language = settings.get("language", "ar")
    current_difficulty = settings.get("difficulty", "normal")
    player_count = settings.get("player_count", 2)
    two_player_mode = player_count == 2
    control_style = settings.get("control_style", "analog")
    if player_count != previous_player_count:
        configure_player_control_centers()
        reset_joystick()
    elif control_style != previous_control_style:
        reset_joystick()
    if "control_layout" in changes:
        apply_control_layout()
        reset_joystick()
    SFX_VOLUME = settings.get("sfx_volume", 0.7)
    MUSIC_VOLUME = settings.get("music_volume", 0.2)
    apply_audio_settings()
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False)
    except OSError as exc:
        print(f"تعذر حفظ الإعدادات: {exc}")


def save_player_name(player_index, value):
    cleaned_name = "".join(
        character for character in value if character.isprintable()
    ).strip()[:18]
    if not cleaned_name:
        cleaned_name = f"اللاعب {player_index}"
    names = dict(settings["player_names"])
    names[str(player_index)] = cleaned_name
    save_settings({"player_names": names})


def update_setting_slider(slider_name, position_x):
    slider_rect = settings_sfx_slider_rect if slider_name == "sfx_volume" else settings_music_slider_rect
    ratio = (position_x - slider_rect.left) / max(1, slider_rect.width)
    save_settings({slider_name: round(max(0.0, min(1.0, ratio)), 2)})


settings = load_settings()
progress = load_progress(settings["player_count"])
gold_migrated = progress.pop("_gold_migrated", False)
current_round = progress["round"]
target_score = progress["target"]
time_limit = progress["time_limit"]
completed_rounds = progress["completed_rounds"]
gold_coins = progress["gold"]
speed_boost_pending = progress["speed_boost_pending"]
purchased_shields = progress["purchased_shields"]
purchased_hearts = progress["purchased_hearts"]
room_cards = progress["room_cards"]
last_daily_reward_date = progress["last_daily_reward_date"]
upgrade_reset_date = progress["upgrade_reset_date"]
daily_store_purchases = progress["daily_store_purchases"]
next_daily_reward = progress["next_daily_reward"]
speed_upgrade_level = progress["speed_upgrade_level"]
shield_upgrade_level = progress["shield_upgrade_level"]
best_score = progress["best_score"]
best_round_time = progress["best_round_time"]
daily_missions = progress["daily_missions"]
stats = progress["stats"]
player_profiles = progress["player_profiles"]
daily_challenge = progress["daily_challenge"]
unlocked_skins = progress["unlocked_skins"]
equipped_skin = progress["equipped_skin"]
current_background_theme = settings["background_color"]

current_language = settings["language"]
current_difficulty = settings["difficulty"]
player_count = settings["player_count"]
two_player_mode = player_count > 1
control_style = settings["control_style"]
game_mode_progress = progress["game_modes"]
active_mode_progress = game_mode_progress[str(player_count)]
current_round = active_mode_progress["round"]
target_score = active_mode_progress["target"]
time_limit = active_mode_progress["time_limit"]
completed_rounds = active_mode_progress["completed_rounds"]
best_score = active_mode_progress["best_score"]
best_round_time = active_mode_progress["best_round_time"]
SFX_VOLUME = settings["sfx_volume"]
MUSIC_VOLUME = settings["music_volume"]
apply_audio_settings()
if gold_migrated:
    save_progress(current_round, target_score, time_limit, completed_rounds)


def switch_player_mode():
    global current_round, target_score, time_limit, completed_rounds
    global best_score, best_round_time, selected_replay_round, rounds_page
    next_player_count = 1 if player_count == 2 else 2
    save_progress(current_round, target_score, time_limit, completed_rounds)
    save_settings({"player_count": next_player_count})
    active_mode_progress = game_mode_progress[str(player_count)]
    current_round = active_mode_progress["round"]
    target_score = active_mode_progress["target"]
    time_limit = active_mode_progress["time_limit"]
    completed_rounds = active_mode_progress["completed_rounds"]
    best_score = active_mode_progress["best_score"]
    best_round_time = active_mode_progress["best_round_time"]
    selected_replay_round = None
    rounds_page = 0


def update_player_profile(player_index, points=0, play_seconds=0.0, round_wins=0,
                          reached_round=None):
    profile = player_profiles[str(player_index)]
    profile["points"] += points
    profile["play_seconds"] += play_seconds
    profile["round_wins"] += round_wins
    if reached_round is not None:
        profile["highest_round"] = max(profile["highest_round"], reached_round)


def earn_gold(amount):
    global gold_coins, round_gold_earned
    gold_coins += amount
    if round_gold_tracking:
        round_gold_earned += amount


def discard_round_gold_earnings():
    global gold_coins, round_gold_earned, round_gold_tracking
    gold_coins = max(0, gold_coins - round_gold_earned)
    round_gold_earned = 0
    round_gold_tracking = False
    save_progress(current_round, target_score, time_limit, completed_rounds)


def gold_reward_round(round_num):
    return (
        round_num == current_round
        and round_num not in completed_rounds
        and (len(set(completed_rounds)) + 1) % 3 == 0
    )


def boss_count_for_round(round_num):
    return player_count if gold_reward_round(round_num) else 0


def record_round_win():
    global round_win_recorded, round_gold_tracking
    if round_win_recorded:
        return
    round_win_recorded = True
    spawn_victory_fireworks()
    if current_round not in completed_rounds:
        if gold_reward_round(current_round):
            earn_gold(1)
        completed_rounds.append(current_round)
    winner_index = (
        match_winner_player_index
        if two_player_mode and competitive_match_finished
        else 1
    )
    update_player_profile(winner_index, round_wins=1, reached_round=current_round)
    update_player_stat("round_wins", 1)
    update_daily_missions(round_wins=1)
    update_daily_challenge(round_wins=1)
    round_gold_tracking = False


def update_player_stat(metric, amount):
    stats[metric] = stats.get(metric, 0) + amount
    claimed = set(stats.get("claimed_achievements", []))
    newly_unlocked = []
    for achievement_id, achievement in ACHIEVEMENTS.items():
        _, _, achievement_metric, target, reward = achievement
        if achievement_metric == metric and stats[metric] >= target and achievement_id not in claimed:
            claimed.add(achievement_id)
            newly_unlocked.append(achievement_id)
            earn_gold(reward)
    if newly_unlocked:
        stats["claimed_achievements"] = sorted(claimed)
        save_progress(current_round, target_score, time_limit, completed_rounds)


def ensure_daily_challenge():
    global daily_challenge
    today = datetime.date.today()
    today_key = today.isoformat()
    challenge_key = DAILY_CHALLENGES[today.toordinal() % len(DAILY_CHALLENGES)][0]
    if (daily_challenge.get("date") != today_key
            or daily_challenge.get("key") != challenge_key):
        challenge = DAILY_CHALLENGES[today.toordinal() % len(DAILY_CHALLENGES)]
        daily_challenge = {
            "date": today_key,
            "key": challenge[0],
            "progress": 0.0,
            "claimed": False,
            "active": False,
        }
    else:
        try:
            daily_challenge["progress"] = max(0.0, float(daily_challenge.get("progress", 0)))
        except (TypeError, ValueError):
            daily_challenge["progress"] = 0.0
        daily_challenge["claimed"] = bool(daily_challenge.get("claimed", False))
        daily_challenge["active"] = bool(daily_challenge.get("active", False))


def daily_challenge_rule_active(challenge_key):
    return (
        daily_challenge.get("active")
        and not daily_challenge.get("claimed")
        and daily_challenge.get("key") == challenge_key
    )


def update_daily_challenge(points=0, survive_seconds=0, round_wins=0):
    ensure_daily_challenge()
    if not daily_challenge.get("active") or daily_challenge.get("claimed"):
        return False
    _, _, metric, target = next(
        challenge for challenge in DAILY_CHALLENGES if challenge[0] == daily_challenge["key"])
    amount = {
        "points_collected": points,
        "survive_seconds": survive_seconds,
        "round_wins": round_wins,
    }[metric]
    if not amount:
        return False
    daily_challenge["progress"] = min(target, daily_challenge.get("progress", 0) + amount)
    if daily_challenge["progress"] >= target:
        daily_challenge["claimed"] = True
        earn_gold(20)
        save_progress(current_round, target_score, time_limit, completed_rounds)
        return True
    return False


def record_round_time():
    global best_round_time
    elapsed = max(0, time_limit - remaining_time)
    if best_round_time == 0 or elapsed < best_round_time:
        best_round_time = elapsed


def determine_match_winner():
    alive_players = [
        player_index for player_index in range(1, player_count + 1)
        if player_healths[player_index - 1] > 0
    ]
    contenders = alive_players or list(range(1, player_count + 1))
    if round_collects_points(current_round):
        rank_player = lambda player_index: (
            player_match_scores[player_index - 1],
            player_survival_times[player_index - 1],
            -player_index,
        )
    else:
        rank_player = lambda player_index: (
            player_survival_times[player_index - 1],
            player_healths[player_index - 1],
            -player_index,
        )
    return max(contenders, key=rank_player)


def finish_competitive_match():
    global game_over, game_started, round_won, remaining_time
    global match_winner_player_index, competitive_match_finished
    if competitive_match_finished:
        return
    competitive_match_finished = True
    match_winner_player_index = determine_match_winner()
    elapsed_time = int((time.time() - start_time) * GAME_TIME_SCALE)
    remaining_time = max(0, time_limit - elapsed_time)
    settle_midround_heart()
    game_started = False
    if match_winner_player_index:
        record_round_win()
        record_round_time()
        round_won = True
        save_progress(current_round, target_score, time_limit, completed_rounds)
    else:
        game_over = True
        discard_round_gold_earnings()


def daily_reward_available():
    return last_daily_reward_date != datetime.date.today().isoformat()


def collect_daily_reward():
    global last_daily_reward_date, next_daily_reward
    if not daily_reward_available():
        return False
    earn_gold(next_daily_reward)
    last_daily_reward_date = datetime.date.today().isoformat()
    next_daily_reward = 1 if next_daily_reward == 7 else next_daily_reward + 1
    save_progress(current_round, target_score, time_limit, completed_rounds)
    return True


def ensure_daily_missions():
    global daily_missions
    today = datetime.date.today().isoformat()
    if (daily_missions.get("date") == today
            and daily_missions.get("version") == DAILY_MISSION_VERSION - 1):
        rewards = daily_missions.get("rewards")
        if isinstance(rewards, dict):
            for reward in rewards.values():
                if isinstance(reward, dict):
                    reward.pop("weapon", None)
        daily_missions["version"] = DAILY_MISSION_VERSION
    elif (daily_missions.get("date") != today
            or daily_missions.get("version") != DAILY_MISSION_VERSION):
        daily_missions = {
            "date": today,
            "version": DAILY_MISSION_VERSION,
            "points": 0,
            "survive_seconds": 0.0,
            "round_wins": 0,
            "claimed": [],
            "rewards": {},
        }
    ensure_daily_challenge()


def grant_daily_mission_reward(mission):
    global purchased_hearts, purchased_shields
    reward_quantities = {
        "heart": 0,
        "shield": 0,
    }
    if mission == "points":
        reward = random.choice(tuple(reward_quantities))
        reward_quantities[reward] = 1
    elif mission == "survive_seconds":
        reward_quantities = {"heart": 5, "shield": 5}
    elif mission == "round_wins":
        reward_quantities = {"heart": 1, "shield": 1}
    else:
        raise ValueError(f"Unknown daily mission: {mission}")

    purchased_hearts += reward_quantities["heart"]
    purchased_shields += reward_quantities["shield"]
    return reward_quantities


def update_daily_missions(points=0, survive_seconds=0, round_wins=0):
    global daily_missions
    ensure_daily_missions()
    daily_missions["points"] = min(
        DAILY_MISSION_TARGETS["points"],
        int(daily_missions.get("points", 0)) + points,
    )
    daily_missions["survive_seconds"] = min(
        DAILY_MISSION_TARGETS["survive_seconds"],
        float(daily_missions.get("survive_seconds", 0)) + survive_seconds,
    )
    daily_missions["round_wins"] = min(
        DAILY_MISSION_TARGETS["round_wins"],
        int(daily_missions.get("round_wins", 0)) + round_wins,
    )
    claimed = set(daily_missions.get("claimed", []))
    completed = {
        mission for mission, target in DAILY_MISSION_TARGETS.items()
        if daily_missions[mission] >= target
    }
    new_rewards = completed - claimed
    if new_rewards:
        rewards = daily_missions.get("rewards")
        if not isinstance(rewards, dict):
            rewards = {}
            daily_missions["rewards"] = rewards
        for mission in sorted(new_rewards):
            rewards[mission] = grant_daily_mission_reward(mission)
        daily_missions["claimed"] = sorted(claimed | new_rewards)
        save_progress(current_round, target_score, time_limit, completed_rounds)
        return len(new_rewards)
    return 0


def toggle_difficulty():
    next_index = (DIFFICULTY_LEVELS.index(current_difficulty) + 1) % len(DIFFICULTY_LEVELS)
    save_settings({"difficulty": DIFFICULTY_LEVELS[next_index]})


def upgrade_cost(level):
    return 10 * (level + 1)


def store_purchase_available(item_key):
    return daily_store_purchases.get(item_key, 0) < STORE_DAILY_PURCHASE_LIMIT


def store_purchase_count_text(item_key):
    return (
        f"شراء اليوم: {daily_store_purchases.get(item_key, 0)}"
        f"/{STORE_DAILY_PURCHASE_LIMIT}"
    )


def record_store_purchase(item_key):
    if item_key not in STORE_PURCHASE_KEYS:
        raise ValueError(f"Unknown store item: {item_key}")
    if not store_purchase_available(item_key):
        return False
    daily_store_purchases[item_key] = daily_store_purchases.get(item_key, 0) + 1
    return True


def refresh_daily_upgrades():
    global speed_upgrade_level, shield_upgrade_level, upgrade_reset_date
    global daily_store_purchases
    today = datetime.date.today().isoformat()
    if upgrade_reset_date == today:
        return False
    speed_upgrade_level = 0
    shield_upgrade_level = 0
    daily_store_purchases = normalize_daily_store_purchases({})
    upgrade_reset_date = today
    save_progress(current_round, target_score, time_limit, completed_rounds)
    return True


def buy_speed_upgrade():
    refresh_daily_upgrades()
    global gold_coins, speed_upgrade_level
    if speed_upgrade_level >= 3:
        return
    cost = upgrade_cost(speed_upgrade_level)
    if gold_coins < cost:
        return
    gold_coins -= cost
    speed_upgrade_level += 1
    save_progress(current_round, target_score, time_limit, completed_rounds)


def buy_shield_upgrade():
    refresh_daily_upgrades()
    global gold_coins, shield_upgrade_level
    if shield_upgrade_level >= 3:
        return
    cost = upgrade_cost(shield_upgrade_level)
    if gold_coins < cost:
        return
    gold_coins -= cost
    shield_upgrade_level += 1
    save_progress(current_round, target_score, time_limit, completed_rounds)


ensure_daily_missions()
refresh_daily_upgrades()

# ================================
# وظائف العناصر
# ================================

def generate_point():
    return pygame.Rect(
        random.randint(30, WIDTH - 50),
        random.randint(30, HEIGHT - 80),
        12,
        12,
    )





def generate_shield():
    return pygame.Rect(
        random.randint(30, WIDTH - 80),
        random.randint(30, HEIGHT - 100),
        26,
        26,
    )


def generate_freeze():
    return pygame.Rect(
        random.randint(30, WIDTH - 80),
        random.randint(30, HEIGHT - 100),
        22,
        22,
    )


def generate_special_pickup(allow_magnet=True):
    return (
        pygame.Rect(
            random.randint(50, WIDTH - 80),
            random.randint(80, HEIGHT - 100),
            28,
            28,
        ),
        random.choice(("magnet", "slow") if allow_magnet else ("slow",)),
    )


def generate_midround_heart():
    return pygame.Rect(
        random.randint(50, WIDTH - 80),
        random.randint(80, HEIGHT - 100),
        32,
        32,
    )


def generate_enemies(player, count, include_boss=False, other_players=(), boss_count=1):
    enemies_list = []
    players = (player, *other_players)
    total_count = max(count, boss_count if include_boss else count)
    for enemy_index in range(total_count):
        is_boss = include_boss and enemy_index < boss_count
        enemy_size = 48 if is_boss else 24
        while True:
            ex = random.randint(60, WIDTH - 60)
            ey = random.randint(100, HEIGHT - 100)
            enemy = pygame.Rect(ex, ey, enemy_size, enemy_size)
            if all(
                abs(enemy.x - target_player.x) > 180
                and abs(enemy.y - target_player.y) > 180
                for target_player in players
            ):
                enemies_list.append(enemy)
                break
    return enemies_list


def move_enemy_axis(enemy, axis, direction, speed):
    enemy_id = id(enemy)
    remainder = enemy_motion_remainders.setdefault(enemy_id, [0.0, 0.0])
    axis_index = 0 if axis == "x" else 1
    exact_move = direction * speed + remainder[axis_index]
    move = int(exact_move)
    remainder[axis_index] = exact_move - move
    setattr(enemy, axis, getattr(enemy, axis) + move)

jumper_states = {}  # يخزن حالة القفز لكل عدو قافز: {"next_jump": float, "jump_until": float, "vx": float, "vy": float}


def move_jumper(enemy, player, base_speed, current_time):
    enemy_id = id(enemy)
    state = jumper_states.setdefault(enemy_id, {
        "next_jump": current_time + random.uniform(0.5, 1.5),
        "jump_until": 0.0,
        "vx": 0.0,
        "vy": 0.0,
    })

    # 1. لحظة بدء القفزة (يندفع بسرعة ×3.5 نحو موقع اللاعب الحالي)
    if current_time >= state["next_jump"]:
        dx = player.centerx - enemy.centerx
        dy = player.centery - enemy.centery
        dist = max(1.0, math.hypot(dx, dy))
        dash_speed = base_speed * 3.5
        state["vx"] = (dx / dist) * dash_speed
        state["vy"] = (dy / dist) * dash_speed
        state["jump_until"] = current_time + 0.32   # مدة الاندفاع السريع (0.32 ثانية)
        state["next_jump"] = current_time + 1.85    # ينتظر 1.5 ثانية قبل القفزة التالية
        spawn_particles(enemy.center, (255, 175, 60), 6)

    # 2. أثناء القفزة: يتحرك بسرعة عالية في اتجاه القفزة
    if current_time < state["jump_until"]:
        move_enemy_axis(enemy, "x", 1 if state["vx"] > 0 else -1, abs(state["vx"]))
        move_enemy_axis(enemy, "y", 1 if state["vy"] > 0 else -1, abs(state["vy"]))
        enemy.clamp_ip(SCREEN.get_rect())
    else:
        # 3. بين القفزات: يتحرك ببطء شديد (استعداد للقفزة القادمة)
        chase(enemy, player, base_speed * 0.25)

def chase(enemy, player, speed):
    move_enemy_axis(enemy, "x", (player.x > enemy.x) - (player.x < enemy.x), speed)
    move_enemy_axis(enemy, "y", (player.y > enemy.y) - (player.y < enemy.y), speed)


def enemy_speed(style, is_slowed):
    speed = {
        "jelly": 1,
        "ghost": 2,
        "robot": 2,
        "eye": 2,
        "fireball": 3,
        "bat": 3,
        "spiky": 2,
        "boss": 4,
    }.get(style, ENEMY_SPEED)
    if is_slowed:
        speed = max(1, speed // 2)
    if current_difficulty == "easy":
        speed = max(1, speed - 1)
    elif current_difficulty == "hard":
        speed += 1
    if daily_challenge_rule_active("fast_enemies"):
        speed += 1
    if round_has_modifier("fast_enemies"):
        speed += 1
    round_speed_multiplier = min(
        ROUND_ENEMY_SPEED_MAX,
        ROUND_ENEMY_SPEED_START + max(0, current_round - 1) * ROUND_ENEMY_SPEED_STEP,
    )
    speed *= round_speed_multiplier
    result = max(
        0.5,
        speed * MOVEMENT_REFERENCE_FPS / TARGET_FPS * ENEMY_SPEED_MULTIPLIER,
    )
    if style == "boss":
        boss_speed_limit = player_movement_speed() * 0.9 / math.sqrt(2)
        return min(result, boss_speed_limit)
    return result


player_dash_untils = [0.0] * 2
player_dash_cooldowns = [0.0] * 2


def player_movement_speed(player_index=1):
    speed = (
        PLAYER_SPEED
        * MOVEMENT_REFERENCE_FPS / TARGET_FPS
        * PLAYER_SPEED_MULTIPLIER
        * (1 + 0.08 * speed_upgrade_level)
    )
    if globals().get("equipped_skin") == "astro":
        speed *= 1.05
    if speed_boost_active:
        speed *= SPEED_BOOST_MULTIPLIER
    if custom_room_active:
        speed *= ROOM_SPEED_OPTIONS[room_settings["speed_idx"]][0]
    if time.time() < player_dash_untils[player_index - 1]:
        speed *= DASH_SPEED_MULTIPLIER
    # إبطاء حركة اللاعب لنصف السرعة لمدة 2 ثانية عند إصابته بمقذوف التبطيء
    if time.time() < player_slow_untils[player_index - 1]:
        speed *= 0.5
    return speed


def trigger_player_dash(player_index=1):
    now = time.time()
    idx = player_index - 1
    if not game_started or game_paused or player_healths[idx] <= 0 or now < player_dash_cooldowns[idx]:
        return False
    player_dash_untils[idx] = now + DASH_DURATION
    cd_time = DASH_COOLDOWN - (1.5 if globals().get("equipped_skin") == "robot" else 0.0)
    player_dash_cooldowns[idx] = now + cd_time
    spawn_particles(player_rects[idx].center, (120, 235, 255), 12)
    return True

def enemy_is_visible(style, current_time):
    return style != "ghost" or int(current_time * 2) % 4 != 3


def spawn_particles(position, color, count=10):
    for _ in range(count):
        angle = random.random() * math.tau
        speed = random.uniform(35, 115)
        particles.append([
            float(position[0]),
            float(position[1]),
            math.cos(angle) * speed,
            math.sin(angle) * speed,
            0.55,
            color,
            random.randint(2, 4),
        ])


def spawn_victory_fireworks():
    victory_fireworks.clear()
    colors = ((255, 195, 86), (105, 225, 210), (245, 112, 165), (150, 135, 255))
    for burst_index, center in enumerate((
        (WIDTH // 4, HEIGHT // 3),
        (WIDTH // 2, HEIGHT // 4),
        (WIDTH * 3 // 4, HEIGHT // 3),
    )):
        color = colors[burst_index % len(colors)]
        for particle_index in range(28):
            angle = math.tau * particle_index / 28
            speed = random.uniform(55, 145)
            victory_fireworks.append([
                float(center[0]), float(center[1]),
                math.cos(angle) * speed, math.sin(angle) * speed,
                random.uniform(1.0, 1.8), color,
            ])


def update_victory_fireworks(surface, delta_time):
    write_index = 0
    for particle in victory_fireworks:
        particle[0] += particle[2] * delta_time
        particle[1] += particle[3] * delta_time
        particle[3] += 42 * delta_time
        particle[4] -= delta_time
        if particle[4] <= 0:
            continue
        victory_fireworks[write_index] = particle
        write_index += 1
        radius = max(1, round(3 * min(1.0, particle[4])))
        pygame.draw.circle(
            surface, particle[5],
            (round(particle[0]), round(particle[1])), radius,
        )
    del victory_fireworks[write_index:]


def update_particles(surface, delta_time):
    write_index = 0
    for particle in particles:
        particle[0] += particle[2] * delta_time
        particle[1] += particle[3] * delta_time
        particle[4] -= delta_time
        if particle[4] <= 0:
            continue
        particles[write_index] = particle
        write_index += 1
        pygame.draw.circle(
            surface,
            particle[5],
            (round(particle[0]), round(particle[1])),
            particle[6],
        )
    del particles[write_index:]


def draw_enemy(surface, enemy, style, animation_time):
    center_x, center_y = enemy.center
    phase = animation_time * 7
    outline = (44, 27, 38)

    if style == "jelly":
        wobble = round(math.sin(phase) * 2)
        body = pygame.Rect(center_x - 17 - wobble, center_y - 15, 34 + wobble * 2, 29)
        pygame.draw.ellipse(surface, outline, body.inflate(4, 4))
        pygame.draw.ellipse(surface, (126, 238, 119), body)
        pygame.draw.ellipse(surface, (194, 255, 164), body.inflate(-12, -9))
        pygame.draw.circle(surface, outline, (center_x - 6, center_y - 3), 2)
        pygame.draw.circle(surface, outline, (center_x + 6, center_y - 3), 2)
        pygame.draw.arc(surface, outline, (center_x - 5, center_y, center_x + 5, center_y + 7), 3.2, 6.2, 2)
    elif style == "ghost":
        body = pygame.Rect(center_x - 15, center_y - 17, 30, 30)
        ghost_color = (190, 225, 255)
        pygame.draw.ellipse(surface, outline, body.inflate(4, 4))
        pygame.draw.ellipse(surface, ghost_color, body)
        for offset in (-10, 0, 10):
            pygame.draw.circle(surface, ghost_color, (center_x + offset, center_y + 11), 6)
            pygame.draw.circle(surface, outline, (center_x + offset, center_y + 15), 6, 1)
        pygame.draw.circle(surface, (32, 54, 91), (center_x - 5, center_y - 3), 2)
        pygame.draw.circle(surface, (32, 54, 91), (center_x + 5, center_y - 3), 2)
    elif style == "robot":
        pygame.draw.line(surface, outline, (center_x, center_y - 12), (center_x, center_y - 18), 3)
        pygame.draw.circle(surface, (255, 210, 94), (center_x, center_y - 19), 3)
        body = pygame.Rect(center_x - 14, center_y - 12, 28, 25)
        pygame.draw.rect(surface, outline, body.inflate(4, 4), border_radius=7)
        pygame.draw.rect(surface, (104, 190, 224), body, border_radius=6)
        pygame.draw.rect(surface, (184, 231, 244), (center_x - 9, center_y - 8, 18, 12), border_radius=4)
        pygame.draw.circle(surface, (48, 71, 103), (center_x - 4, center_y - 2), 2)
        pygame.draw.circle(surface, (48, 71, 103), (center_x + 4, center_y - 2), 2)
        pygame.draw.line(surface, outline, (center_x - 5, center_y + 7), (center_x + 5, center_y + 7), 2)
        for side in (-1, 1):
            pygame.draw.line(surface, outline, (center_x + side * 16, center_y - 2),
                             (center_x + side * 12, center_y - 2), 3)
    elif style == "eye":
        pygame.draw.ellipse(surface, outline, (center_x - 20, center_y - 15, 40, 30))
        pygame.draw.ellipse(surface, (255, 248, 226), (center_x - 17, center_y - 12, 34, 24))
        iris_x = center_x + round(math.sin(phase * 0.35) * 5)
        pygame.draw.circle(surface, (89, 190, 231), (iris_x, center_y), 8)
        pygame.draw.circle(surface, (39, 49, 74), (iris_x, center_y), 4)
        pygame.draw.circle(surface, (255, 255, 255), (iris_x - 2, center_y - 3), 2)
    elif style == "fireball":
        flicker = round(math.sin(phase * 1.4) * 3)
        flame_points = [
            (center_x - 15, center_y + 12), (center_x - 17, center_y + 1),
            (center_x - 10, center_y - 8 - flicker), (center_x - 8, center_y - 17),
            (center_x - 1, center_y - 11), (center_x + 3, center_y - 19 + flicker),
            (center_x + 8, center_y - 9), (center_x + 16, center_y - 12),
            (center_x + 12, center_y), (center_x + 17, center_y + 7),
            (center_x + 8, center_y + 14), (center_x - 8, center_y + 14),
        ]
        pygame.draw.polygon(surface, (183, 56, 38), flame_points)
        pygame.draw.polygon(surface, (255, 142, 43), [
            (center_x - 12, center_y + 9), (center_x - 10, center_y - 3),
            (center_x - 3, center_y - 11), (center_x + 1, center_y - 5),
            (center_x + 7, center_y - 12), (center_x + 11, center_y + 2),
            (center_x + 8, center_y + 10),
        ])
        pygame.draw.ellipse(surface, (255, 222, 102), (center_x - 8, center_y - 5, 16, 16))
        pygame.draw.circle(surface, outline, (center_x - 3, center_y + 1), 2)
        pygame.draw.circle(surface, outline, (center_x + 4, center_y + 1), 2)
    elif style == "bat":
        flap = round(math.sin(phase) * 5)
        pygame.draw.polygon(surface, outline, [
            (center_x - 4, center_y - 2), (center_x - 13, center_y - 12 - flap),
            (center_x - 18, center_y + 8), (center_x - 7, center_y + 4),
            (center_x, center_y + 11), (center_x + 7, center_y + 4),
            (center_x + 18, center_y + 8), (center_x + 13, center_y - 12 + flap),
            (center_x + 4, center_y - 2),
        ])
        pygame.draw.polygon(surface, (132, 91, 190), [
            (center_x - 4, center_y), (center_x - 12, center_y - 8 - flap),
            (center_x - 14, center_y + 5), (center_x - 5, center_y + 2),
            (center_x, center_y + 8), (center_x + 5, center_y + 2),
            (center_x + 14, center_y + 5), (center_x + 12, center_y - 8 + flap),
            (center_x + 4, center_y),
        ])
        pygame.draw.circle(surface, (236, 213, 255), (center_x - 4, center_y - 2), 2)
        pygame.draw.circle(surface, (236, 213, 255), (center_x + 4, center_y - 2), 2)
    elif style == "boss":
        pygame.draw.circle(surface, (49, 21, 64), (center_x, center_y), 29)
        pygame.draw.circle(surface, (160, 74, 199), (center_x, center_y), 25)
        pygame.draw.circle(surface, (223, 142, 255), (center_x - 8, center_y - 8), 7)
        pygame.draw.circle(surface, (42, 24, 57), (center_x - 8, center_y - 7), 3)
        pygame.draw.circle(surface, (255, 215, 106), (center_x + 9, center_y - 4), 4)
        pygame.draw.arc(surface, (52, 23, 55), (center_x - 10, center_y + 3, center_x + 11, center_y + 17), 3.2, 6.1, 3)
    elif style == "bomber":
        pygame.draw.circle(surface, (20, 20, 25), (center_x, center_y + 2), 16)
        pygame.draw.circle(surface, (255, 95, 50), (center_x, center_y + 2), 16, 2)
        pygame.draw.line(surface, (230, 200, 140), (center_x, center_y - 14), (center_x + 6, center_y - 20), 3)
        pygame.draw.circle(surface, (255, 220, 60), (center_x + 7, center_y - 21), 4)
    elif style == "slower":
        pygame.draw.polygon(surface, (40, 130, 210), [
            (center_x, center_y - 18), (center_x + 16, center_y),
            (center_x, center_y + 18), (center_x - 16, center_y)
        ])
        pygame.draw.polygon(surface, (180, 240, 255), [
            (center_x, center_y - 12), (center_x + 10, center_y),
            (center_x, center_y + 12), (center_x - 10, center_y)
        ], 2)
    elif style == "jumper":
        pygame.draw.circle(surface, (255, 140, 40), (center_x, center_y), 15)
        pygame.draw.circle(surface, (255, 235, 160), (center_x, center_y), 15, 2)
    else:
        spikes = []
        for index in range(16):
            angle = math.tau * index / 16
            radius = 21 if index % 2 == 0 else 15
            spikes.append((center_x + round(math.cos(angle) * radius),
                           center_y + round(math.sin(angle) * radius)))
        pygame.draw.polygon(surface, outline, spikes)
        pygame.draw.circle(surface, (211, 92, 111), (center_x, center_y), 13)
        pygame.draw.circle(surface, (255, 185, 190), (center_x - 5, center_y - 3), 2)
        pygame.draw.circle(surface, (255, 185, 190), (center_x + 5, center_y - 3), 2)
        pygame.draw.circle(surface, outline, (center_x - 5, center_y - 3), 1)
        pygame.draw.circle(surface, outline, (center_x + 5, center_y - 3), 1)


def draw_boss_health(surface, enemy, health):
    for heart_index in range(BOSS_MAX_HEALTH):
        color = (255, 92, 130) if heart_index < health else (76, 62, 76)
        heart_x = enemy.centerx - 54 + heart_index * 12
        pygame.draw.circle(surface, color, (heart_x - 3, enemy.top - 8), 4)
        pygame.draw.circle(surface, color, (heart_x + 3, enemy.top - 8), 4)
        pygame.draw.polygon(surface, color, [
            (heart_x - 7, enemy.top - 7), (heart_x + 7, enemy.top - 7),
            (heart_x, enemy.top + 1),
        ])
    phase = 1 if health > 6 else 2 if health > 3 else 3
    label = SMALL_FONT.render(arabic_text(f"مرحلة {phase}"), True, (242, 207, 255))
    surface.blit(label, (enemy.centerx - label.get_width() // 2, enemy.top - 34))


def current_enemy_count_for_round(round_num):
    count = BASE_ENEMY_COUNT + max(0, round_num - 1) // ROUND_ENEMY_COUNT_INTERVAL
    if current_difficulty == "easy":
        count = max(4, round(count * 0.75))
    elif current_difficulty == "hard":
        count = round(count * 1.25)
    return min(MAX_ENEMY_COUNT, count)


def find_next_uncompleted(start_round, completed):
    r = start_round
    while r in completed:
        r += 1
    return r


def get_round_settings(round_num):
    round_steps = max(0, round_num - 1)
    target = min(
        ROUND_PLAYER_SCORE_CAP,
        20 + round_steps * ROUND_SCORE_INCREMENT,
    )
    time_limit = min(
        ROUND_TIME_CAP,
        50 + round_steps * ROUND_TIME_INCREMENT,
    )
    if round_variant(round_num)["objective"] == "waves":
        time_limit = max(
            time_limit, round_objective_goal(round_num) * 10 + 15,
        )
    return target, time_limit


def round_variant(round_num):
    return ROUND_VARIANTS[(max(1, round_num) - 1) % len(ROUND_VARIANTS)]


def round_has_modifier(modifier, round_num=None):
    variant = round_variant(current_round if round_num is None else round_num)
    return modifier in variant["modifiers"]


def round_collects_points(round_num):
    if globals().get("custom_room_active", False):
        return ROOM_OBJECTIVES[room_settings["objective_idx"]][0] == "score"
    return not round_variant(round_num)["scoreless"]


def round_objective_description(round_num):
    if globals().get("custom_room_active", False):
        return ROOM_OBJECTIVES[room_settings["objective_idx"]][1]
    return round_variant(round_num)["description"]

def round_objective_goal(round_num):
    objective = round_variant(round_num)["objective"]
    if objective == "waves":
        return min(6, 3 + (round_num - 1) // (len(ROUND_VARIANTS) * 2))
    return get_round_settings(round_num)[0]


def boss_count_for_round(round_num):
    if globals().get("custom_room_active", False):
        return room_settings.get("boss_count", 0)
    return player_count if gold_reward_round(round_num) else 0


def round_enemy_style(round_num, enemy_index):
    if globals().get("custom_room_active", False):
        enemy_item = ROOM_ENEMY_TYPES[room_settings["enemy_idx"] % len(ROOM_ENEMY_TYPES)]
        chosen = enemy_item[0] if isinstance(enemy_item, (tuple, list)) else str(enemy_item)
        ar_to_en = {
            "متنوع": "mixed", "مختلط": "mixed",
            "عادي": "jelly",
            "صياد": "robot",
            "قافز": "jumper",
            "مفجّر": "bomber",
            "مبطئ": "slower",
            "أشباح": "ghost", "شبح": "ghost",
        }
        chosen = ar_to_en.get(chosen, chosen)
        if chosen != "mixed":
            return chosen
        return random.choice(ENEMY_STYLES)

    if round_num > 3:
        return random.choice(ENEMY_STYLES)
    basic_styles = ("jelly", "ghost", "robot", "eye", "fireball", "bat", "spiky")
    styles = round_variant(round_num)["enemy_styles"]
    return styles[enemy_index % len(styles)] if styles else random.choice(basic_styles)


def spawn_round_wave(round_num, wave_number):
    global enemies
    available_slots = MAX_ENEMY_COUNT - len(enemies)
    wave_size = min(available_slots, 3 + wave_number)
    if wave_size <= 0:
        return
    new_enemies = generate_enemies(
        player_rect, wave_size, False, tuple(player_rects[1:player_count]),
    )
    styles = round_variant(round_num)["enemy_styles"]
    for enemy in new_enemies:
        enemies.append(enemy)
        enemy_styles[id(enemy)] = (
            styles[(wave_number + len(enemies)) % len(styles)]
            if styles else random.choice(ENEMY_STYLES)
        )


target_score, time_limit = get_round_settings(current_round)
remaining_time = time_limit


# ================================
# اللاعب
# ================================

player_rect = pygame.Rect(80, 80, PLAYER_SIZE, PLAYER_SIZE)
player_two_rect = pygame.Rect(WIDTH - 80 - PLAYER_SIZE, 80, PLAYER_SIZE, PLAYER_SIZE)
player_rects = [player_rect, player_two_rect]
player_healths = [PLAYER_MAX_HEALTH] * 2
player_health_caps = [PLAYER_MAX_HEALTH] * 2
player_hit_untils = [0.0] * 2
player_match_scores = [0] * 2
player_survival_times = [0.0] * 2
match_winner_player_index = 0
competitive_match_finished = False

# ================================
# عصا التحكم (لمس)
# ================================

JOYSTICK_RADIUS = 68
JOYSTICK_KNOB_RADIUS = 24
JOYSTICK_CENTER = (150, HEIGHT - 100)
JOYSTICK_TWO_CENTER = (WIDTH - 150, HEIGHT - 100)
JOYSTICK_PLAYER_LABELS = {
    player_index: SMALL_FONT.render(f"P{player_index}", True, (235, 243, 246))
    for player_index in (1, 2)
}
joystick_pointer_players = {}
joystick_default_centers = {
    1: JOYSTICK_CENTER,
    2: JOYSTICK_TWO_CENTER,
}
joystick_touch_centers = dict(joystick_default_centers)
move_vectors = [[0.0, 0.0] for _ in range(2)]
player_move_remainders = [[0.0, 0.0] for _ in range(2)]
joystick_knobs = list(joystick_default_centers.values())
arrow_pointer_directions = {}
arrow_button_size = 56
arrow_button_gap = 16


def configure_player_control_centers():
    layout = settings["control_layout"]
    for player_index, key in ((1, "movement_left"), (2, "movement_right")):
        entry = layout[key]
        x_position = round(entry["x"] * WIDTH)
        if player_index == 1:
            x_position = min(WIDTH // 2 - JOYSTICK_RADIUS, x_position)
        else:
            x_position = max(WIDTH // 2 + JOYSTICK_RADIUS, x_position)
        y_position = round(entry["y"] * HEIGHT)
        joystick_default_centers[player_index] = (
            max(JOYSTICK_RADIUS, min(WIDTH - JOYSTICK_RADIUS, x_position)),
            max(JOYSTICK_RADIUS, min(HEIGHT - JOYSTICK_RADIUS, y_position)),
        )
    joystick_touch_centers.update(joystick_default_centers)
    joystick_knobs[:] = list(joystick_default_centers.values())


configure_player_control_centers()


def pointer_position(event):
    if event.type in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
        return round(event.x * WIDTH), round(event.y * HEIGHT)
    return event.pos


def arrow_control_rects(player_index):
    center_x = joystick_default_centers[player_index][0]
    center_y = joystick_default_centers[player_index][1]
    step = arrow_button_size + arrow_button_gap
    return {
        "up": pygame.Rect(center_x - arrow_button_size // 2, center_y - step,
                          arrow_button_size, arrow_button_size),
        "down": pygame.Rect(center_x - arrow_button_size // 2, center_y + 3,
                            arrow_button_size, arrow_button_size),
        "left": pygame.Rect(center_x - step, center_y - arrow_button_size // 2,
                            arrow_button_size, arrow_button_size),
        "right": pygame.Rect(center_x + 3, center_y - arrow_button_size // 2,
                             arrow_button_size, arrow_button_size),
    }


ARROW_CONTROL_SURFACES = {}
for direction, (dx, dy) in {
    "up": (0, -1), "down": (0, 1),
    "left": (-1, 0), "right": (1, 0),
}.items():
    button_surface = pygame.Surface(
        (arrow_button_size, arrow_button_size), pygame.SRCALPHA,
    )
    pygame.draw.rect(
        button_surface, (220, 235, 245, 48),
        button_surface.get_rect(), border_radius=14,
    )
    pygame.draw.rect(
        button_surface, (230, 240, 250, 45),
        button_surface.get_rect(), 2, border_radius=14,
    )
    center = arrow_button_size // 2, arrow_button_size // 2
    arrow_tip = arrow_button_size // 4
    arrow_base = arrow_button_size // 6
    arrow_half_width = arrow_button_size // 6
    points = (
        (
            (center[0] + dx * arrow_tip, center[1]),
            (center[0] - dx * arrow_base, center[1] - arrow_half_width),
            (center[0] - dx * arrow_base, center[1] + arrow_half_width),
        )
        if dx else (
            (center[0], center[1] + dy * arrow_tip),
            (center[0] - arrow_half_width, center[1] - dy * arrow_base),
            (center[0] + arrow_half_width, center[1] - dy * arrow_base),
        )
    )
    pygame.draw.polygon(button_surface, (240, 248, 255, 180), points)
    ARROW_CONTROL_SURFACES[direction] = button_surface


JOYSTICK_BASE_IMAGE = pygame.Surface((JOYSTICK_RADIUS * 2, JOYSTICK_RADIUS * 2), pygame.SRCALPHA)
pygame.draw.circle(JOYSTICK_BASE_IMAGE, (80, 80, 80, 55), (JOYSTICK_RADIUS, JOYSTICK_RADIUS), JOYSTICK_RADIUS)
pygame.draw.circle(JOYSTICK_BASE_IMAGE, (190, 210, 225, 110), (JOYSTICK_RADIUS, JOYSTICK_RADIUS), JOYSTICK_RADIUS, 3)
JOYSTICK_KNOB_IMAGE = pygame.Surface((JOYSTICK_KNOB_RADIUS * 2, JOYSTICK_KNOB_RADIUS * 2), pygame.SRCALPHA)
pygame.draw.circle(JOYSTICK_KNOB_IMAGE, (225, 235, 245, 100), (JOYSTICK_KNOB_RADIUS, JOYSTICK_KNOB_RADIUS), JOYSTICK_KNOB_RADIUS)
pygame.draw.circle(JOYSTICK_KNOB_IMAGE, (255, 255, 255, 150), (JOYSTICK_KNOB_RADIUS, JOYSTICK_KNOB_RADIUS), JOYSTICK_KNOB_RADIUS, 2)


def refresh_control_images():
    global JOYSTICK_RADIUS, JOYSTICK_KNOB_RADIUS, JOYSTICK_BASE_IMAGE
    global JOYSTICK_KNOB_IMAGE, arrow_button_size, arrow_button_gap
    global ARROW_CONTROL_SURFACES
    movement_scale = settings["control_layout"]["movement_left"]["scale"]
    JOYSTICK_RADIUS = round(68 * movement_scale)
    JOYSTICK_KNOB_RADIUS = round(24 * movement_scale)
    arrow_button_size = round(56 * movement_scale)
    arrow_button_gap = round(16 * movement_scale)
    JOYSTICK_BASE_IMAGE = pygame.Surface(
        (JOYSTICK_RADIUS * 2, JOYSTICK_RADIUS * 2), pygame.SRCALPHA,
    )
    pygame.draw.circle(
        JOYSTICK_BASE_IMAGE, (80, 80, 80, 55),
        (JOYSTICK_RADIUS, JOYSTICK_RADIUS), JOYSTICK_RADIUS,
    )
    pygame.draw.circle(
        JOYSTICK_BASE_IMAGE, (190, 210, 225, 110),
        (JOYSTICK_RADIUS, JOYSTICK_RADIUS), JOYSTICK_RADIUS, 3,
    )
    JOYSTICK_KNOB_IMAGE = pygame.Surface(
        (JOYSTICK_KNOB_RADIUS * 2, JOYSTICK_KNOB_RADIUS * 2), pygame.SRCALPHA,
    )
    pygame.draw.circle(
        JOYSTICK_KNOB_IMAGE, (225, 235, 245, 100),
        (JOYSTICK_KNOB_RADIUS, JOYSTICK_KNOB_RADIUS), JOYSTICK_KNOB_RADIUS,
    )
    pygame.draw.circle(
        JOYSTICK_KNOB_IMAGE, (255, 255, 255, 150),
        (JOYSTICK_KNOB_RADIUS, JOYSTICK_KNOB_RADIUS), JOYSTICK_KNOB_RADIUS, 2,
    )
    ARROW_CONTROL_SURFACES = {}
    for direction, (dx, dy) in {
        "up": (0, -1), "down": (0, 1),
        "left": (-1, 0), "right": (1, 0),
    }.items():
        button_surface = pygame.Surface(
            (arrow_button_size, arrow_button_size), pygame.SRCALPHA,
        )
        pygame.draw.rect(
            button_surface, (220, 235, 245, 48),
            button_surface.get_rect(), border_radius=14,
        )
        pygame.draw.rect(
            button_surface, (230, 240, 250, 45),
            button_surface.get_rect(), 2, border_radius=14,
        )
        center = arrow_button_size // 2, arrow_button_size // 2
        arrow_tip = arrow_button_size // 4
        arrow_base = arrow_button_size // 6
        arrow_half_width = arrow_button_size // 6
        points = (
            (
                (center[0] + dx * arrow_tip, center[1]),
                (center[0] - dx * arrow_base, center[1] - arrow_half_width),
                (center[0] - dx * arrow_base, center[1] + arrow_half_width),
            )
            if dx else (
                (center[0], center[1] + dy * arrow_tip),
                (center[0] - arrow_half_width, center[1] - dy * arrow_base),
                (center[0] + arrow_half_width, center[1] - dy * arrow_base),
            )
        )
        pygame.draw.polygon(button_surface, (240, 248, 255, 180), points)
        ARROW_CONTROL_SURFACES[direction] = button_surface
    configure_player_control_centers()


refresh_control_images()


def update_joystick(pos, player_index=1):
    center = joystick_touch_centers[player_index]
    dx = pos[0] - center[0]
    dy = pos[1] - center[1]
    distance = (dx * dx + dy * dy) ** 0.5
    if distance > JOYSTICK_RADIUS:
        dx = (dx / distance) * JOYSTICK_RADIUS
        dy = (dy / distance) * JOYSTICK_RADIUS
    joystick_knobs[player_index - 1] = (center[0] + dx, center[1] + dy)
    move_vectors[player_index - 1] = [dx / JOYSTICK_RADIUS, dy / JOYSTICK_RADIUS]


def reset_joystick(player_index=None):
    reset_players = range(1, 3) if player_index is None else (player_index,)
    for current_player in reset_players:
        move_vectors[current_player - 1] = [0.0, 0.0]
        player_move_remainders[current_player - 1] = [0.0, 0.0]
        joystick_knobs[current_player - 1] = joystick_default_centers[current_player]
        joystick_touch_centers[current_player] = joystick_default_centers[current_player]
        for pointer_id, direction in list(arrow_pointer_directions.items()):
            if direction[0] == current_player:
                arrow_pointer_directions.pop(pointer_id, None)
    if player_index is None:
        joystick_pointer_players.clear()


def draw_joystick(surface, player_index=1):
    center = joystick_touch_centers[player_index]
    knob = joystick_knobs[player_index - 1]
    surface.blit(JOYSTICK_BASE_IMAGE, (center[0] - JOYSTICK_RADIUS, center[1] - JOYSTICK_RADIUS))
    surface.blit(
        JOYSTICK_KNOB_IMAGE,
        (int(knob[0]) - JOYSTICK_KNOB_RADIUS, int(knob[1]) - JOYSTICK_KNOB_RADIUS),
    )
    if player_index > 1:
        pygame.draw.circle(surface, BACKGROUND_THEMES[current_background_theme]["accent"],
                           center, JOYSTICK_RADIUS, 1)
    if two_player_mode:
        player_label = JOYSTICK_PLAYER_LABELS[player_index]
        surface.blit(
            player_label,
            (center[0] - player_label.get_width() // 2, center[1] - JOYSTICK_RADIUS - 24),
        )


def update_arrow_movement():
    direction_vectors = {
        "up": (0.0, -1.0), "down": (0.0, 1.0),
        "left": (-1.0, 0.0), "right": (1.0, 0.0),
    }
    for player_index in range(1, player_count + 1):
        x = y = 0.0
        for controlled_player, direction in arrow_pointer_directions.values():
            if controlled_player == player_index:
                dx, dy = direction_vectors[direction]
                x += dx
                y += dy
        magnitude = math.hypot(x, y)
        if magnitude > 1:
            x /= magnitude
            y /= magnitude
        move_vectors[player_index - 1] = [x, y]


def draw_player_control(surface, player_index):
    if control_style == "analog":
        draw_joystick(surface, player_index)
        return
    arrows = arrow_control_rects(player_index)
    for direction, rect in arrows.items():
        surface.blit(ARROW_CONTROL_SURFACES[direction], rect.topleft)

# ================================
# أزرار الواجهة
# ================================

start_button_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 75, 300, 64)
game_over_button_width = 190
game_over_button_gap = 8
game_over_buttons_left = WIDTH // 2 - (game_over_button_width * 3 + game_over_button_gap * 2) // 2
continue_button_rect = pygame.Rect(
    game_over_buttons_left, HEIGHT // 2 + 100, game_over_button_width, 80)
heart_continue_button_rect = pygame.Rect(
    continue_button_rect.right + game_over_button_gap, HEIGHT // 2 + 100,
    game_over_button_width, 80)
retry_button_rect = pygame.Rect(
    heart_continue_button_rect.right + game_over_button_gap, HEIGHT // 2 + 100,
    game_over_button_width, 80)
next_button_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 100, 300, 80)
menu_button_rect = pygame.Rect(WIDTH // 2 - 68, 10, 78, 44)
game_settings_button_rect = pygame.Rect(menu_button_rect.right + 8, 10, 48, 44)
menu_mode_button_rect = pygame.Rect(WIDTH // 2 - 125, 176, 250, 42)
menu_room_button_rect = pygame.Rect(20, 20, 185, 44)
room_panel_rect = pygame.Rect(WIDTH // 2 - 280, HEIGHT // 2 - 190, 560, 380)
room_close_rect = pygame.Rect(room_panel_rect.right - 46, room_panel_rect.top + 12, 34, 34)
room_score_minus_rect = pygame.Rect(room_panel_rect.left + 210, room_panel_rect.top + 85, 42, 36)
room_score_plus_rect = pygame.Rect(room_panel_rect.left + 350, room_panel_rect.top + 85, 42, 36)
room_obj_toggle_rect = pygame.Rect(room_panel_rect.left + 210, room_panel_rect.top + 135, 182, 36)
room_speed_toggle_rect = pygame.Rect(room_panel_rect.left + 210, room_panel_rect.top + 185, 182, 36)
room_enemy_toggle_rect = pygame.Rect(room_panel_rect.left + 210, room_panel_rect.top + 235, 182, 36)
room_start_btn_rect = pygame.Rect(room_panel_rect.centerx - 120, room_panel_rect.bottom - 62, 240, 46)
menu_more_button_rect = pygame.Rect(WIDTH // 2 - 90, HEIGHT - 72, 180, 44)
main_options_panel_rect = pygame.Rect(
    WIDTH // 2 - min(280, (WIDTH - 32) // 2),
    HEIGHT // 2 - min(160, (HEIGHT - 24) // 2),
    min(560, WIDTH - 32),
    min(320, HEIGHT - 24),
)
main_options_close_rect = pygame.Rect(
    main_options_panel_rect.right - 48, main_options_panel_rect.top + 10, 36, 36,
)
main_options_labels = {
    "shop": "المتجر",
    "missions": "المهام",
    "rewards": "المكافآت اليومية",
    "statistics": "الإحصائيات",
    "challenge": "تحدي اليوم",
    "profiles": "ملفات اللاعبين",
    "difficulty": "الصعوبة",
    "exit": "خروج",
}
main_options_button_width = (main_options_panel_rect.width - 48) // 2
main_options_button_height = 42
main_options_button_rects = {
    key: pygame.Rect(
        main_options_panel_rect.left + 16
        + (index % 2) * (main_options_button_width + 16),
        main_options_panel_rect.top + 66 + (index // 2) * 52,
        main_options_button_width,
        main_options_button_height,
    )
    for index, key in enumerate(main_options_labels)
}
game_action_button_width = min(72, max(52, (WIDTH - 540) // 3))
two_player_action_width = game_action_button_width
two_player_action_gap = 12
two_player_actions_left = WIDTH // 2 - (
    two_player_action_width + two_player_action_gap
) // 2
two_player_shield_use_button_rect = pygame.Rect(
    two_player_actions_left, HEIGHT - 220,
    two_player_action_width, two_player_action_width)
two_player_player_two_shield_use_button_rect = pygame.Rect(
    WIDTH - two_player_actions_left - two_player_action_width,
    HEIGHT - 220, two_player_action_width, two_player_action_width)
stats_panel_width = min(700, WIDTH - 32)
stats_panel_height = min(440, HEIGHT - 24)
stats_panel_rect = pygame.Rect(
    (WIDTH - stats_panel_width) // 2, (HEIGHT - stats_panel_height) // 2,
    stats_panel_width, stats_panel_height,
)
stats_close_rect = pygame.Rect(stats_panel_rect.right - 48, stats_panel_rect.top + 12, 36, 36)
challenge_panel_width = min(620, WIDTH - 32)
challenge_panel_height = min(320, HEIGHT - 24)
challenge_panel_rect = pygame.Rect(
    (WIDTH - challenge_panel_width) // 2, (HEIGHT - challenge_panel_height) // 2,
    challenge_panel_width, challenge_panel_height,
)
challenge_close_rect = pygame.Rect(challenge_panel_rect.right - 48, challenge_panel_rect.top + 12, 36, 36)
player_profiles_panel_width = min(760, WIDTH - 32)
player_profiles_panel_height = min(460, HEIGHT - 24)
player_profiles_panel_rect = pygame.Rect(
    (WIDTH - player_profiles_panel_width) // 2,
    (HEIGHT - player_profiles_panel_height) // 2,
    player_profiles_panel_width,
    player_profiles_panel_height,
)
player_profiles_close_rect = pygame.Rect(
    player_profiles_panel_rect.right - 48, player_profiles_panel_rect.top + 12, 36, 36,
)
def player_profile_card_rect(player_index):
    card_width = (player_profiles_panel_rect.width - 56) // 2
    return pygame.Rect(
        player_profiles_panel_rect.left + 24 + (player_index - 1) * (card_width + 8),
        player_profiles_panel_rect.top + 84,
        card_width, player_profiles_panel_rect.height - 132,
    )


def player_profile_name_rect(player_index):
    card = player_profile_card_rect(player_index)
    return pygame.Rect(card.left + 14, card.top + 76, card.width - 28, 44)
challenge_toggle_rect = pygame.Rect(challenge_panel_rect.centerx - 120,
                                    challenge_panel_rect.bottom - 72, 240, 46)
shop_panel_height = min(610, HEIGHT - 8)
shop_panel_width = min(880, WIDTH - 24)
shop_panel_rect = pygame.Rect(
    (WIDTH - shop_panel_width) // 2,
    (HEIGHT - shop_panel_height) // 2,
    shop_panel_width,
    shop_panel_height,
)
shop_close_rect = pygame.Rect(shop_panel_rect.right - 46, shop_panel_rect.top + 12, 34, 34)
shop_row_count = 7
shop_row_gap = 4
shop_row_height = max(
    36,
    min(52, (shop_panel_height - 162 - (shop_row_count - 1) * shop_row_gap) // shop_row_count),
)
shop_skin_rects = []
skin_card_w = (shop_panel_width - 70) // len(PLAYER_SKINS)
for s_idx in range(len(PLAYER_SKINS)):
    shop_skin_rects.append(pygame.Rect(
        shop_panel_rect.left + 20 + s_idx * (skin_card_w + 10),
        shop_panel_rect.bottom - 60,
        skin_card_w,
        50,
    ))

shop_row_rects = [
    pygame.Rect(
        shop_panel_rect.left + 20,
        shop_panel_rect.top + 96 + index * (shop_row_height + shop_row_gap),
        shop_panel_width - 40,
        shop_row_height,
    )
    for index in range(shop_row_count)
]
shop_button_width = min(172, shop_panel_width // 3)
shop_button_rects = [
    pygame.Rect(
        row.right - shop_button_width - 10,
        row.centery - min(18, (row.height - 4) // 2),
        shop_button_width,
        min(36, row.height - 4),
    )
    for row in shop_row_rects
]
(
    shop_buy_rect,
    shop_speed_upgrade_rect,
    shop_shield_upgrade_rect,
    shop_skip_rect,
    shop_purchased_shield_rect,
    shop_heart_rect,
    shop_room_card_rect,
) = shop_button_rects[:7]
daily_rewards_panel_height = min(330, HEIGHT - 24)
daily_rewards_panel_rect = pygame.Rect(WIDTH // 2 - 350, (HEIGHT - daily_rewards_panel_height) // 2,
                                       700, daily_rewards_panel_height)
daily_rewards_close_rect = pygame.Rect(daily_rewards_panel_rect.right - 48,
                                       daily_rewards_panel_rect.top + 12, 34, 34)
daily_missions_panel_width = min(700, WIDTH - 32)
daily_missions_panel_height = min(390, HEIGHT - 24)
daily_missions_panel_rect = pygame.Rect(
    (WIDTH - daily_missions_panel_width) // 2,
    (HEIGHT - daily_missions_panel_height) // 2,
    daily_missions_panel_width,
    daily_missions_panel_height,
)
daily_missions_close_rect = pygame.Rect(
    daily_missions_panel_rect.right - 48, daily_missions_panel_rect.top + 12, 34, 34)
daily_mission_row_rects = [
    pygame.Rect(
        daily_missions_panel_rect.left + 28,
        daily_missions_panel_rect.top + 112 + index * 72,
        daily_missions_panel_width - 56,
        58,
    )
    for index in range(len(DAILY_MISSION_TARGETS))
]
daily_reward_card_rects = []
daily_reward_collect_rects = []
daily_cards_width = 7 * 72 + 6 * 8
daily_cards_start_x = daily_rewards_panel_rect.centerx - daily_cards_width // 2
for day_index in range(7):
    card_rect = pygame.Rect(daily_cards_start_x + day_index * 80,
                            daily_rewards_panel_rect.top + 116, 72, 132)
    daily_reward_card_rects.append(card_rect)
    daily_reward_collect_rects.append(
        pygame.Rect(card_rect.centerx - 30, card_rect.bottom - 29, 60, 25))
settings_button_rect = pygame.Rect(WIDTH - 222, HEIGHT - 116, 146, 48)
game_actions_right = WIDTH - 24
shield_use_button_rect = pygame.Rect(
    game_actions_right - game_action_button_width,
    HEIGHT - 92 - game_action_button_width // 2,
    game_action_button_width, game_action_button_width)
settings_panel_width = min(920, WIDTH - 24)
settings_panel_height = min(520, HEIGHT - 24)
settings_panel_rect = pygame.Rect(
    (WIDTH - settings_panel_width) // 2,
    (HEIGHT - settings_panel_height) // 2,
    settings_panel_width,
    settings_panel_height,
)
settings_vertical_scale = min(1.0, max(0.65, (settings_panel_height - 110) / 410))
settings_theme_y = settings_panel_rect.top + round(106 * settings_vertical_scale)
settings_sfx_y = settings_panel_rect.top + round(176 * settings_vertical_scale)
settings_music_y = settings_panel_rect.top + round(216 * settings_vertical_scale)
settings_language_y = settings_panel_rect.top + round(294 * settings_vertical_scale)
settings_control_y = settings_panel_rect.top + round(364 * settings_vertical_scale)
settings_layout_y = settings_panel_rect.top + round(410 * settings_vertical_scale)
settings_close_rect = pygame.Rect(settings_panel_rect.right - 48, settings_panel_rect.top + 12, 36, 36)
settings_footer_button_width = 170
settings_footer_gap = 18
settings_footer_left = settings_panel_rect.centerx - (
    settings_footer_button_width * 2 + settings_footer_gap
) // 2
settings_resume_rect = pygame.Rect(
    settings_footer_left, settings_panel_rect.bottom - 54,
    settings_footer_button_width, 40,
)
settings_exit_rect = pygame.Rect(
    settings_resume_rect.right + settings_footer_gap,
    settings_panel_rect.bottom - 54,
    settings_footer_button_width, 40,
)
settings_theme_button_width = 150
settings_theme_gap = 16
settings_theme_rects = {
    theme: pygame.Rect(
        settings_panel_rect.centerx
        + (index * 2 - 1) * (settings_theme_button_width + settings_theme_gap) // 2,
        settings_theme_y,
        settings_theme_button_width,
        36,
    )
    for index, theme in enumerate(("midnight", "white"))
}
settings_slider_width = min(360, settings_panel_width - 390)
settings_slider_left = settings_panel_rect.left + 220
settings_sfx_slider_rect = pygame.Rect(
    settings_slider_left, settings_sfx_y,
    settings_slider_width, 8,
)
settings_music_slider_rect = pygame.Rect(
    settings_slider_left, settings_music_y,
    settings_slider_width, 8,
)
settings_control_style_rect = pygame.Rect(
    settings_panel_rect.centerx - 130, settings_control_y, 260, 36,
)
settings_control_layout_rect = pygame.Rect(
    settings_panel_rect.centerx - 170, settings_layout_y, 340, 38,
)
settings_language_rects = {}
language_button_width = 150
language_gap = 16
language_row_width = len(LANGUAGES) * language_button_width + (len(LANGUAGES) - 1) * language_gap
language_row_left = settings_panel_rect.centerx - language_row_width // 2
for language_index, language_code in enumerate(LANGUAGES):
    settings_language_rects[language_code] = pygame.Rect(
        language_row_left + language_index * (language_button_width + language_gap),
        settings_language_y,
        language_button_width,
        36,
    )



def configure_action_control_rects():
    global shield_use_button_rect
    global two_player_shield_use_button_rect
    global two_player_player_two_shield_use_button_rect
    global menu_button_rect, game_settings_button_rect
    for key, rect in (
        ("actions_single", shield_use_button_rect),
        ("actions_player_1", two_player_shield_use_button_rect),
        ("actions_player_2", two_player_player_two_shield_use_button_rect),
    ):
        entry = settings["control_layout"][key]
        size = max(40, round(game_action_button_width * entry["scale"]))
        center_x = round(entry["x"] * WIDTH)
        center_y = round(entry["y"] * HEIGHT)
        rect.update(center_x - size // 2, center_y - size // 2, size, size)

    for key, rect, width, height in (
        ("menu", menu_button_rect, 78, 44),
        ("settings", game_settings_button_rect, 48, 44),
    ):
        entry = settings["control_layout"][key]
        scaled_width = max(36, round(width * entry["scale"]))
        scaled_height = max(32, round(height * entry["scale"]))
        rect.update(
            round(entry["x"] * WIDTH) - scaled_width // 2,
            round(entry["y"] * HEIGHT) - scaled_height // 2,
            scaled_width,
            scaled_height,
        )


def apply_control_layout():
    refresh_control_images()
    for key in settings["control_layout"]:
        constrain_control_layout_entry(key)
    configure_player_control_centers()
    configure_action_control_rects()


def control_layout_hit_rect(key):
    if key.startswith("movement_"):
        player_index = 1 if key == "movement_left" else 2
        center = joystick_default_centers[player_index]
        extent = JOYSTICK_RADIUS
        if control_style == "arrows":
            extent = arrow_button_size + arrow_button_gap
        return pygame.Rect(
            center[0] - extent, center[1] - extent,
            extent * 2, extent * 2,
        )
    if key == "actions_single":
        return shield_use_button_rect
    if key == "actions_player_1":
        return two_player_shield_use_button_rect
    if key == "actions_player_2":
        return two_player_player_two_shield_use_button_rect
    if key == "menu":
        return menu_button_rect
    return game_settings_button_rect


def move_control_layout(key, pos):
    entry = settings["control_layout"][key]
    entry["x"] = pos[0] / WIDTH
    entry["y"] = pos[1] / HEIGHT
    constrain_control_layout_entry(key)
    configure_player_control_centers()
    reset_joystick()
    configure_action_control_rects()


def constrain_control_layout_entry(key):
    entry = settings["control_layout"][key]
    center_x = round(entry["x"] * WIDTH)
    center_y = round(entry["y"] * HEIGHT)
    if key.startswith("movement_"):
        extent_x = JOYSTICK_RADIUS
        extent_y = JOYSTICK_RADIUS
        if control_style == "arrows":
            extent_x = extent_y = arrow_button_size + arrow_button_gap
        if key == "movement_left":
            center_x = min(WIDTH // 2 - extent_x, center_x)
        else:
            center_x = max(WIDTH // 2 + extent_x, center_x)
    elif key.startswith("actions_"):
        size = max(40, round(game_action_button_width * entry["scale"]))
        extent_x = size // 2
        extent_y = size // 2
        if key == "actions_player_1":
            center_x = min(WIDTH // 2 - extent_x, center_x)
        elif key == "actions_player_2":
            center_x = max(WIDTH // 2 + extent_x, center_x)
    else:
        width, height = (78, 44) if key == "menu" else (48, 44)
        extent_x = max(18, round(width * entry["scale"]) // 2)
        extent_y = max(16, round(height * entry["scale"]) // 2)
    center_x = max(extent_x, min(WIDTH - extent_x, center_x))
    center_y = max(extent_y, min(HEIGHT - extent_y, center_y))
    entry["x"] = center_x / WIDTH
    entry["y"] = center_y / HEIGHT


def change_control_layout_scale(key, amount):
    if key.startswith("movement_"):
        movement_scale = settings["control_layout"]["movement_left"]["scale"]
        movement_scale = max(0.65, min(1.6, movement_scale + amount))
        settings["control_layout"]["movement_left"]["scale"] = movement_scale
        settings["control_layout"]["movement_right"]["scale"] = movement_scale
        constrain_control_layout_entry("movement_left")
        constrain_control_layout_entry("movement_right")
    else:
        entry = settings["control_layout"][key]
        entry["scale"] = max(0.65, min(1.6, entry["scale"] + amount))
        constrain_control_layout_entry(key)
    save_settings({"control_layout": settings["control_layout"]})


configure_action_control_rects()

dragging_settings_slider = None
editing_controls = False
selected_control_layout_key = "movement_left"
dragging_control_layout = False
control_layout_drag_offset = (0, 0)
control_editor_keys = (
    "movement_left", "movement_right", "actions_single",
    "actions_player_1", "actions_player_2", "menu", "settings",
)
control_editor_done_rect = pygame.Rect(settings_panel_rect.right - 114,
                                       settings_panel_rect.bottom - 58, 90, 38)
control_editor_smaller_rect = pygame.Rect(settings_panel_rect.left + 18,
                                          settings_panel_rect.bottom - 58, 54, 38)
control_editor_larger_rect = pygame.Rect(settings_panel_rect.left + 80,
                                         settings_panel_rect.bottom - 58, 54, 38)
control_editor_previous_rect = pygame.Rect(settings_panel_rect.left + 142,
                                           settings_panel_rect.bottom - 58, 38, 38)
control_editor_next_rect = pygame.Rect(settings_panel_rect.left + 186,
                                       settings_panel_rect.bottom - 58, 38, 38)
completed_panel_rect = pygame.Rect(100, HEIGHT // 2 - 40, WIDTH - 200, 100)
rounds_previous_rect = pygame.Rect(completed_panel_rect.left + 12, completed_panel_rect.top + 30, 40, 40)
rounds_next_rect = pygame.Rect(completed_panel_rect.right - 52, completed_panel_rect.top + 30, 40, 40)
show_settings = False
show_shop = False
show_daily_rewards = False
show_daily_missions = False
show_statistics = False
show_daily_challenge = False
show_player_profiles = False
show_main_options = False
active_player_name = None
player_name_draft = ""
rounds_page = 0
rounds_swipe_start_x = None
selected_replay_round = None


@lru_cache(maxsize=32)
def get_cached_font(font_size, bold):
    return load_best_arabic_font(font_size, bold)




@lru_cache(maxsize=512)
def _render_fit_text_cached(
    text, text_color, max_width, max_height, font_size, bold, language,
):
    max_width = max(1, max_width)
    max_height = max(1, max_height)
    font_size = max(10, font_size)
    rendered = get_cached_font(font_size, bold).render(
        arabic_text(text), True, text_color,
    )
    while font_size > 10 and (
        rendered.get_width() > max_width or rendered.get_height() > max_height
    ):
        font_size -= 1
        rendered = get_cached_font(font_size, bold).render(
            arabic_text(text), True, text_color,
        )
    if rendered.get_width() > max_width or rendered.get_height() > max_height:
        scale = min(max_width / rendered.get_width(), max_height / rendered.get_height())
        rendered = pygame.transform.smoothscale(
            rendered,
            (max(1, int(rendered.get_width() * scale)),
             max(1, int(rendered.get_height() * scale))),
        )
    return rendered


def render_fit_text(text, text_color, max_width, max_height, font_size, bold=False):
    text = str(text)
    text_color = tuple(text_color)
    max_width = max(1, int(max_width))
    max_height = max(1, int(max_height))
    font_size = max(10, int(font_size))
    return _render_fit_text_cached(
        text, text_color, max_width, max_height, font_size, bool(bold),
        current_language,
    )


def draw_theme_frame(surface, rect, border_width=2, radius=18):
    frame_color = BACKGROUND_THEMES.get(
        current_background_theme, BACKGROUND_THEMES["midnight"]
    )["frame"]
    pygame.draw.rect(surface, frame_color, rect, border_width, border_radius=radius)


def draw_button(surface, text, rect, color, text_color=(255,255,255), font_size=28):
    shadow_color = tuple(max(0, channel // 3) for channel in color)
    highlight_color = tuple(min(255, channel + 34) for channel in color)
    pygame.draw.rect(surface, shadow_color, rect.move(0, 3), border_radius=12)
    pygame.draw.rect(surface, color, rect, border_radius=12)
    pygame.draw.line(surface, highlight_color, (rect.left + 12, rect.top + 2),
                     (rect.right - 12, rect.top + 2), 2)
    if rect.width > 8 and rect.height > 8:
        pygame.draw.rect(surface, tuple(min(255, channel + 18) for channel in color),
                         rect.inflate(-4, -4), 1, border_radius=10)
    draw_theme_frame(surface, rect, 1, 12)
    txt = render_fit_text(text, text_color, rect.width - 24, rect.height - 12, font_size, True)
    surface.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))


def draw_game_action_button(surface, lines, rect, color, icon=None):
    radius = min(rect.width, rect.height) // 2
    center = rect.center
    pygame.draw.circle(surface, (8, 12, 20), (center[0], center[1] + 4), radius)
    pygame.draw.circle(surface, color, center, radius)
    frame_color = BACKGROUND_THEMES.get(
        current_background_theme, BACKGROUND_THEMES["midnight"]
    )["frame"]
    pygame.draw.circle(surface, frame_color, center, radius, 2)

    if icon is not None:
        icon_rect = pygame.Rect(
            rect.left + 5, rect.top + 5, rect.width - 10,
            max(18, rect.height // 2),
        )
        pygame.draw.rect(surface, (245, 245, 245), icon_rect, border_radius=5)
        scale = min(
            (icon_rect.width - 4) / icon.get_width(),
            (icon_rect.height - 4) / icon.get_height(),
        )
        icon_size = (
            max(1, int(icon.get_width() * scale)),
            max(1, int(icon.get_height() * scale)),
        )
        fitted_icon = pygame.transform.smoothscale(icon, icon_size)
        surface.blit(fitted_icon, fitted_icon.get_rect(center=icon_rect.center))
        label = render_fit_text(
            f"{lines[0]} ×{lines[1]}", (255, 255, 255),
            rect.width - 8, max(12, rect.height // 3), 13, True,
        )
        surface.blit(
            label,
            (center[0] - label.get_width() // 2,
             rect.bottom - label.get_height() - 6),
        )
        return

    line_height = max(14, (rect.height - 12) // len(lines))
    for index, line in enumerate(lines):
        label = render_fit_text(
            line, (255, 255, 255), rect.width - 12, line_height, 15, True,
        )
        line_y = center[1] + (index - (len(lines) - 1) / 2) * line_height
        surface.blit(
            label,
            (center[0] - label.get_width() // 2,
             round(line_y - label.get_height() / 2)),
        )


def draw_result_screen(won):
    scoreless_round = not round_collects_points(current_round)
    background_color = (10, 23, 24) if won else (25, 14, 20)
    panel_color = (17, 35, 36) if won else (39, 24, 31)
    accent_color = (70, 205, 155) if won else (235, 105, 115)
    SCREEN.fill(background_color)

    panel_width = min(680, WIDTH - 40)
    panel = pygame.Rect((WIDTH - panel_width) // 2, (HEIGHT - 460) // 2, panel_width, 460)
    pygame.draw.rect(SCREEN, panel_color, panel, border_radius=24)
    pygame.draw.rect(SCREEN, accent_color, panel, 2, border_radius=24)

    icon_center = (panel.centerx, panel.top + 58)
    pygame.draw.circle(SCREEN, accent_color, icon_center, 25, 3)
    if won:
        pygame.draw.line(SCREEN, accent_color, (icon_center[0] - 11, icon_center[1]),
                         (icon_center[0] - 3, icon_center[1] + 8), 4)
        pygame.draw.line(SCREEN, accent_color, (icon_center[0] - 3, icon_center[1] + 8),
                         (icon_center[0] + 13, icon_center[1] - 10), 4)
        title_text = "أحسنت!"
        subtitle_text = "لقد أكملت هذه الجولة بنجاح"
        button_text = "الجولة التالية"
        button_color = (20, 150, 100)
    else:
        pygame.draw.line(SCREEN, accent_color, (icon_center[0] - 9, icon_center[1] - 9),
                         (icon_center[0] + 9, icon_center[1] + 9), 4)
        pygame.draw.line(SCREEN, accent_color, (icon_center[0] + 9, icon_center[1] - 9),
                         (icon_center[0] - 9, icon_center[1] + 9), 4)
        title_text = "انتهت الجولة"
        if two_player_mode and defeated_player_index:
            subtitle_text = (
                f"{settings['player_names'][str(defeated_player_index)]} خسر | متابعة الجولة مقابل "
                f"{CONTINUE_COST} ذهب | رصيدك: {gold_coins}"
            )
        else:
            subtitle_text = f"متابعة الجولة مقابل {CONTINUE_COST} ذهب | رصيدك: {gold_coins}"

    if two_player_mode and competitive_match_finished:
        title_text = f"فاز {settings['player_names'][str(match_winner_player_index)]}!"
        if scoreless_round:
            subtitle_text = " | ".join(
                f"{settings['player_names'][str(index)]}: "
                f"{int(player_survival_times[index - 1])}ث"
                for index in range(1, player_count + 1)
            )
        else:
            subtitle_text = " | ".join(
                f"{settings['player_names'][str(index)]}: {player_match_scores[index - 1]}"
                for index in range(1, player_count + 1)
            )

    title = render_fit_text(title_text, (248, 250, 252), panel.width - 80, 52, 44, True)
    SCREEN.blit(title, (panel.centerx - title.get_width() // 2, panel.top + 88))
    subtitle = render_fit_text(subtitle_text, (190, 205, 215), panel.width - 48, 24, 20)
    SCREEN.blit(subtitle, (panel.centerx - subtitle.get_width() // 2, panel.top + 148))
    pygame.draw.line(SCREEN, (75, 90, 100), (panel.left + 90, panel.top + 184),
                     (panel.right - 90, panel.top + 184), 1)

    if two_player_mode and competitive_match_finished:
        if scoreless_round:
            score_label_text = "مدة الصمود لكل لاعب"
            score_value_text = " / ".join(
                f"{settings['player_names'][str(index)]} "
                f"{int(player_survival_times[index - 1])}ث"
                for index in range(1, player_count + 1)
            )
        else:
            score_label_text = "النتيجة لكل لاعب"
            score_value_text = " / ".join(
                f"{settings['player_names'][str(index)]} {player_match_scores[index - 1]}"
                for index in range(1, player_count + 1)
            )
    else:
        if scoreless_round:
            score_label_text = "مدة الصمود"
            score_value_text = f"{int(player_survival_times[0])} ثانية"
        else:
            score_label_text = "النتيجة"
            score_value_text = f"{score} / {target_score}"
    score_label = render_fit_text(score_label_text, (175, 195, 205), panel.width - 80, 24, 20)
    SCREEN.blit(score_label, (panel.centerx - score_label.get_width() // 2, panel.top + 198))
    score_text = render_fit_text(score_value_text, accent_color, panel.width - 80, 52, 36 if two_player_mode else 44, True)
    SCREEN.blit(score_text, (panel.centerx - score_text.get_width() // 2, panel.top + 220))
    if two_player_mode and competitive_match_finished:
        round_details = f"الجولة {current_round}"
    elif scoreless_round:
        fastest_time = f"{best_round_time:.1f}" if best_round_time else "--"
        round_details = f"الجولة {current_round} | أسرع جولة {fastest_time}ث"
    else:
        fastest_time = f"{best_round_time:.1f}" if best_round_time else "--"
        round_details = (
            f"الجولة {current_round} | أفضل نتيجة {best_score} | "
            f"أسرع جولة {fastest_time}ث"
        )
    round_text = render_fit_text(
        round_details,
        (225, 232, 238), panel.width - 48, 24, 20,
    )
    SCREEN.blit(round_text, (panel.centerx - round_text.get_width() // 2, panel.top + 282))

    if won:
        draw_button(SCREEN, button_text, next_button_rect, button_color, font_size=26)
    elif two_player_mode and competitive_match_finished:
        draw_button(SCREEN, "إعادة الجولة", retry_button_rect, (175, 55, 70), font_size=19)
    else:
        continue_color = (25, 145, 105) if gold_coins >= CONTINUE_COST else (75, 82, 90)
        heart_color = (170, 55, 85) if purchased_hearts else (75, 82, 90)
        draw_button(SCREEN, f"متابعة {CONTINUE_COST} ذهب", continue_button_rect, continue_color, font_size=17)
        draw_button(
            SCREEN, f"استخدم قلبًا ×{purchased_hearts}",
            heart_continue_button_rect, heart_color, font_size=17,
        )
        draw_button(SCREEN, "إعادة الجولة", retry_button_rect, (175, 55, 70), font_size=19)


def draw_settings_icon(surface, rect):
    pygame.draw.rect(surface, (30, 43, 55), rect, border_radius=14)
    pygame.draw.rect(surface, (82, 125, 143), rect, 2, border_radius=14)
    cx, cy = rect.center if rect.width < 100 else (rect.right - 25, rect.centery)
    pygame.draw.circle(surface, (20, 30, 40), (cx, cy), 17)
    pygame.draw.circle(surface, (145, 180, 193), (cx, cy), 17, 1)
    r = 10
    for angle in range(0, 360, 45):
        rad = angle * math.pi / 180
        x1 = cx + int((r - 3) * math.cos(rad))
        y1 = cy + int((r - 3) * math.sin(rad))
        x2 = cx + int((r + 3) * math.cos(rad))
        y2 = cy + int((r + 3) * math.sin(rad))
        pygame.draw.line(surface, (195, 220, 228), (x1, y1), (x2, y2), 2)
    pygame.draw.circle(surface, (115, 165, 182), (cx, cy), 7, 2)
    if rect.width >= 100:
        label = render_fit_text(
            "الإعدادات", (235, 243, 246), cx - rect.left - 34, rect.height - 8, 20,
        )
        surface.blit(label, (rect.left + 12, rect.centery - label.get_height() // 2))


def control_layout_label(key):
    return {
        "movement_left": "عصا اللاعب الأول",
        "movement_right": "عصا اللاعب الثاني",
        "actions_single": "زر الدرع",
        "actions_player_1": "درع اللاعب الأول",
        "actions_player_2": "درع اللاعب الثاني",
        "menu": "زر القائمة",
        "settings": "زر الإعدادات",
    }[key]


def draw_control_layout_editor(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((3, 8, 15, 85))
    surface.blit(overlay, (0, 0))
    for player_index in (1, 2):
        draw_player_control(surface, player_index)

    if two_player_mode:
        action_buttons = (
            (two_player_shield_use_button_rect, 1),
            (two_player_player_two_shield_use_button_rect, 2),
        )
    else:
        action_buttons = ((shield_use_button_rect, 1),)
    for shield_button, player_index in action_buttons:
        draw_game_action_button(
            surface, ["درع", str(purchased_shields)], shield_button,
            (53, 134, 117),
        )
    draw_button(surface, "القائمة", menu_button_rect, (70, 70, 70), font_size=16)
    draw_settings_icon(surface, game_settings_button_rect)

    selected_rect = control_layout_hit_rect(selected_control_layout_key)
    pygame.draw.rect(surface, (90, 230, 177), selected_rect, 3, border_radius=18)

    toolbar = pygame.Rect(
        settings_panel_rect.left + 12,
        settings_panel_rect.bottom - 116,
        settings_panel_rect.width - 24,
        102,
    )
    pygame.draw.rect(surface, (9, 17, 27), toolbar, border_radius=16)
    pygame.draw.rect(surface, (83, 132, 145), toolbar, 2, border_radius=16)
    instructions = render_fit_text(
        "اسحب الزر لتغيير مكانه، واستخدم − و+ لتغيير حجمه",
        (224, 237, 242), toolbar.width - 24, 24, 18,
    )
    surface.blit(
        instructions,
        (toolbar.centerx - instructions.get_width() // 2, toolbar.top + 10),
    )
    draw_button(surface, "−", control_editor_smaller_rect, (58, 76, 91), font_size=24)
    draw_button(surface, "+", control_editor_larger_rect, (58, 76, 91), font_size=24)
    draw_button(surface, "‹", control_editor_previous_rect, (58, 76, 91), font_size=22)
    draw_button(surface, "›", control_editor_next_rect, (58, 76, 91), font_size=22)
    selected_label = render_fit_text(
        control_layout_label(selected_control_layout_key),
        (255, 227, 155), toolbar.width - 360, 24, 18, True,
    )
    surface.blit(
        selected_label,
        (toolbar.centerx - selected_label.get_width() // 2, toolbar.top + 47),
    )
    draw_button(surface, "تم", control_editor_done_rect, (25, 137, 95), font_size=19)


def draw_store_icon(surface, rect):
    pygame.draw.rect(surface, (48, 43, 31), rect, border_radius=14)
    pygame.draw.rect(surface, (190, 150, 70), rect, 2, border_radius=14)
    cx, cy = rect.right - 25, rect.centery
    pygame.draw.circle(surface, (35, 31, 24), (cx, cy), 17)
    pygame.draw.circle(surface, (225, 190, 105), (cx, cy), 17, 1)
    bag_rect = pygame.Rect(cx - 8, cy - 4, 16, 13)
    pygame.draw.arc(surface, (255, 220, 130), pygame.Rect(cx - 5, cy - 11, 10, 11), math.pi, 2 * math.pi, 2)
    pygame.draw.rect(surface, (195, 150, 55), bag_rect, border_radius=3)
    pygame.draw.rect(surface, (255, 225, 145), bag_rect, 1, border_radius=3)
    label = render_fit_text("المتجر", (255, 239, 195), cx - rect.left - 34, rect.height - 8, 20)
    surface.blit(label, (rect.left + 12, rect.centery - label.get_height() // 2))


def draw_daily_rewards_icon(surface, rect):
    pygame.draw.rect(surface, (30, 48, 47), rect, border_radius=14)
    pygame.draw.rect(surface, (83, 150, 130), rect, 2, border_radius=14)
    cx, cy = rect.right - 25, rect.centery
    pygame.draw.circle(surface, (19, 34, 35), (cx, cy), 17)
    pygame.draw.circle(surface, (130, 205, 170), (cx, cy), 17, 1)
    calendar = pygame.Rect(cx - 9, cy - 8, 18, 17)
    pygame.draw.rect(surface, (220, 244, 224), calendar, 2, border_radius=3)
    pygame.draw.line(surface, (130, 205, 170), (calendar.left + 1, cy - 3),
                     (calendar.right - 1, cy - 3), 2)
    pygame.draw.line(surface, (220, 244, 224), (cx - 4, cy - 11), (cx - 4, cy - 6), 2)
    pygame.draw.line(surface, (220, 244, 224), (cx + 4, cy - 11), (cx + 4, cy - 6), 2)
    for dot_x in (cx - 4, cx + 4):
        pygame.draw.circle(surface, (130, 205, 170), (dot_x, cy + 2), 1)
        pygame.draw.circle(surface, (130, 205, 170), (dot_x, cy + 7), 1)
    label = render_fit_text("المكافآت", (225, 245, 230), cx - rect.left - 34, rect.height - 8, 20)
    surface.blit(label, (rect.left + 12, rect.centery - label.get_height() // 2))


def button_clicked(rect, pos):
    return rect.collidepoint(pos)


def draw_round_arrow(surface, rect, direction, enabled):
    fill = (35, 57, 68) if enabled else (30, 38, 45)
    edge = (100, 190, 185) if enabled else (65, 75, 82)
    pygame.draw.circle(surface, fill, rect.center, rect.width // 2)
    pygame.draw.circle(surface, edge, rect.center, rect.width // 2, 2)
    cx, cy = rect.center
    if direction == "left":
        points = ((cx + 4, cy - 7), (cx - 3, cy), (cx + 4, cy + 7))
    else:
        points = ((cx - 4, cy - 7), (cx + 3, cy), (cx - 4, cy + 7))
    pygame.draw.lines(surface, (225, 240, 240) if enabled else (105, 115, 120), False, points, 3)


def draw_shop_item_icon(surface, center, icon, color, size):
    cx, cy = center
    scale = max(0.55, min(1.0, size / 40))
    x = lambda offset: round(cx + offset * scale)
    y = lambda offset: round(cy + offset * scale)
    line_width = max(2, round(3 * scale))

    if icon == "speed_boost":
        points = ((x(2), y(-17)), (x(-10), y(1)), (x(-1), y(1)),
                  (x(-4), y(17)), (x(10), y(-4)), (x(2), y(-4)))
        pygame.draw.polygon(surface, color, points)
    elif icon == "speed_upgrade":
        pygame.draw.line(surface, color, (x(-13), y(9)), (x(-5), y(9)), line_width)
        pygame.draw.line(surface, color, (x(-13), y(15)), (x(-2), y(15)), line_width)
        pygame.draw.line(surface, color, (x(1), y(12)), (x(1), y(-9)), line_width)
        pygame.draw.lines(
            surface, color, False,
            ((x(-6), y(-3)), (x(1), y(-11)), (x(8), y(-3))),
            line_width,
        )
    elif icon in ("shield_upgrade", "shield"):
        shield = ((x(0), y(-17)), (x(13), y(-12)), (x(11), y(3)),
                  (x(0), y(16)), (x(-11), y(3)), (x(-13), y(-12)))
        pygame.draw.polygon(surface, color, shield, line_width)
        if icon == "shield_upgrade":
            pygame.draw.line(surface, color, (x(0), y(-6)), (x(0), y(5)), line_width)
            pygame.draw.line(surface, color, (x(-5), y(-1)), (x(5), y(-1)), line_width)
    elif icon == "skip_round":
        for offset in (-7, 5):
            pygame.draw.lines(
                surface, color, False,
                ((x(offset - 5), y(-9)), (x(offset + 4), y(0)),
                 (x(offset - 5), y(9))),
                line_width,
            )
    elif icon == "heart":
        pygame.draw.circle(surface, color, (x(-6), y(-4)), max(4, round(7 * scale)))
        pygame.draw.circle(surface, color, (x(6), y(-4)), max(4, round(7 * scale)))
        pygame.draw.polygon(
            surface, color,
            ((x(-13), y(-1)), (x(13), y(-1)), (x(0), y(15))),
        )
    elif icon == "room_card":
        card = pygame.Rect(x(-14), y(-10), max(14, round(28 * scale)), max(10, round(20 * scale)))
        pygame.draw.rect(surface, color, card, line_width, border_radius=4)
        pygame.draw.line(surface, color, (card.left + 3, y(-3)), (card.right - 3, y(-3)), line_width)
        pygame.draw.circle(surface, color, (x(-6), y(4)), max(2, round(2.5 * scale)))
        pygame.draw.line(surface, color, (x(0), y(4)), (card.right - 4, y(4)), max(1, line_width - 1))


def draw_shop_panel(surface):
    global unlocked_skins, equipped_skin
    valid_ids = [item[0] for item in PLAYER_SKINS]
    if "unlocked_skins" not in globals() or not unlocked_skins:
        unlocked_skins = ["thief"]
    if "equipped_skin" not in globals() or equipped_skin not in valid_ids:
        equipped_skin = "thief"
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 165))
    surface.blit(overlay, (0, 0))

    panel = shop_panel_rect
    pygame.draw.rect(surface, (4, 7, 13), panel.move(0, 8), border_radius=26)
    pygame.draw.rect(surface, (15, 25, 38), panel, border_radius=26)
    pygame.draw.rect(surface, (48, 69, 82), panel.inflate(-8, -8), 1, border_radius=22)
    draw_theme_frame(surface, panel, 2, 26)

    header = pygame.Rect(panel.left + 10, panel.top + 10, panel.width - 20, 82)
    pygame.draw.rect(surface, (27, 44, 58), header, border_radius=18)
    pygame.draw.rect(surface, (63, 91, 103), header, 1, border_radius=18)
    pygame.draw.rect(surface, (74, 194, 164),
                     pygame.Rect(header.left + 1, header.top + 12, 4, header.height - 24),
                     border_radius=2)

    pygame.draw.rect(surface, (145, 55, 66), shop_close_rect, border_radius=10)
    pygame.draw.rect(surface, (227, 128, 132), shop_close_rect, 1, border_radius=10)
    close_text = SMALL_FONT.render("X", True, (255, 255, 255))
    surface.blit(close_text, (shop_close_rect.centerx - close_text.get_width() // 2,
                              shop_close_rect.centery - close_text.get_height() // 2))

    title = render_fit_text("المتجر", (255, 245, 220), panel.width - 240, 42, 38, True)
    surface.blit(title, (panel.centerx - title.get_width() // 2, panel.top + 4))
    refresh_text = render_fit_text(
        "حد الشراء اليومي: 3 لكل عنصر",
        (126, 220, 190), panel.width - 240, 20, 16, True,
    )
    surface.blit(refresh_text, (panel.centerx - refresh_text.get_width() // 2, panel.top + 55))
    balance_badge = pygame.Rect(panel.right - 194, panel.top + 28, 132, 38)
    pygame.draw.rect(surface, (74, 59, 34), balance_badge, border_radius=14)
    pygame.draw.rect(surface, (205, 165, 75), balance_badge, 1, border_radius=14)
    balance_text = SMALL_FONT.render(arabic_text(f"ذهب: {gold_coins}"), True, (255, 226, 151))
    surface.blit(balance_text, (balance_badge.centerx - balance_text.get_width() // 2,
                                balance_badge.centery - balance_text.get_height() // 2))

    speed_upgrade_cost = upgrade_cost(speed_upgrade_level)
    shield_upgrade_cost = upgrade_cost(shield_upgrade_level)
    items = (
        ("تسريع اللاعب ×1.5 | 20 ثانية",
         f"المخزون: {int(speed_boost_pending)} | {store_purchase_count_text('speed_boost')}",
         shop_buy_rect,
         "تم الشراء" if speed_boost_pending else (
             "اكتمل الحد" if not store_purchase_available("speed_boost")
             else f"شراء {SPEED_BOOST_COST}"
         ),
         not speed_boost_pending
         and store_purchase_available("speed_boost")
         and gold_coins >= SPEED_BOOST_COST, False, "speed_boost"),
        (f"ترقية السرعة اليومية: {speed_upgrade_level}/3", "زيادة الحركة 8% لكل مستوى | تتجدد اليوم",
         shop_speed_upgrade_rect,
         f"ترقية {speed_upgrade_cost}" if speed_upgrade_level < 3 else "اكتملت",
         speed_upgrade_level < 3 and gold_coins >= speed_upgrade_cost,
         False, "speed_upgrade"),
        (f"ترقية الدرع اليومية: {shield_upgrade_level}/3", "زيادة مدة الدرع العادي ثانية | تتجدد اليوم",
         shop_shield_upgrade_rect,
         f"ترقية {shield_upgrade_cost}" if shield_upgrade_level < 3 else "اكتملت",
         shield_upgrade_level < 3 and gold_coins >= shield_upgrade_cost,
         False, "shield_upgrade"),
        ("تخطي الجولة الحالية وتُحسب فوزًا",
         f"المكافأة: جولة منجزة | {SKIP_ROUND_COST} ذهب | {store_purchase_count_text('skip_round')}",
         shop_skip_rect,
         "اكتمل الحد" if not store_purchase_available("skip_round") else f"تخطي {SKIP_ROUND_COST}",
         store_purchase_available("skip_round") and gold_coins >= SKIP_ROUND_COST,
         True, "skip_round"),
        ("درع يدوي | 20 ثانية",
         f"المخزون: {purchased_shields} | {PURCHASED_SHIELD_COST} ذهب | {store_purchase_count_text('shield')}",
         shop_purchased_shield_rect,
         "اكتمل الحد" if not store_purchase_available("shield") else f"شراء {PURCHASED_SHIELD_COST}",
         store_purchase_available("shield") and gold_coins >= PURCHASED_SHIELD_COST,
         False, "shield"),
        ("قلب إنقاذ عند الخسارة",
         f"المخزون: {purchased_hearts} | {HEART_COST} ذهب | {store_purchase_count_text('heart')}",
         shop_heart_rect,
         "اكتمل الحد" if not store_purchase_available("heart") else f"شراء {HEART_COST}",
         store_purchase_available("heart") and gold_coins >= HEART_COST,
         False, "heart"),
        ("بطاقة روم | لفتح روم خاص للاعبين",
         f"المخزون: {room_cards} | {ROOM_CARD_COST} ذهب | {store_purchase_count_text('room_card')}",
         shop_room_card_rect,
         "اكتمل الحد" if not store_purchase_available("room_card") else f"شراء {ROOM_CARD_COST}",
         store_purchase_available("room_card") and gold_coins >= ROOM_CARD_COST,
         True, "room_card"),
    )
    row_accents = (
        (87, 211, 165), (88, 178, 236), (176, 138, 238),
        (232, 183, 83), (127, 199, 255), (246, 115, 145),
        (255, 195, 75),
    )

    for row_index, (row, item) in enumerate(zip(shop_row_rects, items)):
        description, subtitle, button_rect, button_text, can_buy, gold_button, icon = item
        accent = row_accents[row_index]
        pygame.draw.rect(
            surface, (22, 38, 51),
            row, border_radius=13,
        )
        pygame.draw.rect(
            surface, (58, 80, 92),
            row, 1, border_radius=13,
        )
        pygame.draw.rect(surface, accent, pygame.Rect(row.left + 1, row.top + 8, 4, row.height - 16),
                         border_radius=2)
        icon_center = (row.left + 27, row.centery)
        draw_shop_item_icon(surface, icon_center, icon, accent, row.height - 8)
        title_color = (235, 242, 245)
        subtitle_color = (220, 195, 140) if gold_button else (190, 205, 210)
        previous_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(row.left + 50, row.top, button_rect.left - row.left - 58, row.height))
        text_x = row.left + 52
        text_width = max(1, button_rect.left - text_x - 8)
        if row.height >= 42:
            title_text = render_fit_text(description, title_color, text_width, 24, 21, True)
            subtitle_text = render_fit_text(subtitle, subtitle_color, text_width, 18, 16)
            surface.blit(title_text, (text_x, row.top + 2))
            surface.blit(subtitle_text, (text_x, row.top + 26))
        elif row.height >= 34:
            title_text = render_fit_text(description, title_color, text_width, 19, 18, True)
            subtitle_text = render_fit_text(subtitle, subtitle_color, text_width, 16, 14)
            surface.blit(title_text, (text_x, row.top + 1))
            surface.blit(subtitle_text, (text_x, row.top + 20))
        else:
            combined = f"{description} | {subtitle}"
            combined_text = render_fit_text(combined, title_color, text_width, row.height - 6, 17)
            surface.blit(combined_text, (text_x, row.centery - combined_text.get_height() // 2))
        surface.set_clip(previous_clip)
        button_color = (25, 145, 105) if can_buy else (80, 85, 92)
        if gold_button and can_buy:
            button_color = (170, 125, 45)
        if can_buy and not gold_button:
            button_color = (28, 131, 118)
        draw_button(surface, button_text, button_rect, button_color,
                    font_size=16 if row.height < 42 else 17)

    for (skin_id, skin_name, skin_cost, skin_color, skin_perk), s_rect in zip(PLAYER_SKINS, shop_skin_rects):
        is_equipped = (equipped_skin == skin_id)
        is_unlocked = (skin_id in unlocked_skins)
        bg_col = (28, 95, 82) if is_equipped else ((34, 52, 68) if is_unlocked else (45, 42, 34))
        pygame.draw.rect(surface, bg_col, s_rect, border_radius=10)
        pygame.draw.rect(surface, skin_color, s_rect, 2 if is_equipped else 1, border_radius=10)
        pygame.draw.circle(surface, skin_color, (s_rect.left + 16, s_rect.centery), 9)
        status_str = "مجهّز" if is_equipped else ("تجهيز" if is_unlocked else f"شراء {skin_cost}")
        s_title = render_fit_text(f"{skin_name} ({skin_perk})", (245, 248, 250), s_rect.width - 34, 20, 13, True)
        s_sub = render_fit_text(status_str, (255, 225, 145) if not is_unlocked else (155, 235, 195), s_rect.width - 34, 18, 13, True)
        surface.blit(s_title, (s_rect.left + 30, s_rect.top + 4))
        surface.blit(s_sub, (s_rect.left + 30, s_rect.top + 26))


def draw_daily_rewards_panel(surface):

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))
    surface.blit(overlay, (0, 0))

    panel = daily_rewards_panel_rect
    pygame.draw.rect(surface, (5, 10, 15), panel.move(0, 7), border_radius=22)
    pygame.draw.rect(surface, (23, 36, 43), panel, border_radius=22)
    draw_theme_frame(surface, panel, 2, 22)

    pygame.draw.rect(surface, (145, 55, 66), daily_rewards_close_rect, border_radius=10)
    close_text = SMALL_FONT.render("X", True, (255, 255, 255))
    surface.blit(close_text, (daily_rewards_close_rect.centerx - close_text.get_width() // 2,
                              daily_rewards_close_rect.centery - close_text.get_height() // 2))

    title = render_fit_text(
        "مكافآت الأيام السبعة", (238, 248, 240), panel.width - 96, 48, 38, True,
    )
    surface.blit(title, (panel.centerx - title.get_width() // 2, panel.top + 20))
    if daily_reward_available():
        status_text = f"المتاح الآن: {next_daily_reward} ذهب"
        status_color = (155, 235, 185)
    else:
        status_text = "جمعت مكافأتك اليوم، عد غدًا"
        status_color = (190, 205, 210)
    status = render_fit_text(status_text, status_color, panel.width - 96, 24, 20)
    surface.blit(status, (panel.centerx - status.get_width() // 2, panel.top + 82))

    for day_index, card_rect in enumerate(daily_reward_card_rects, start=1):
        available = daily_reward_available() and day_index == next_daily_reward
        claimed = day_index < next_daily_reward
        if not daily_reward_available() and day_index == (7 if next_daily_reward == 1 else next_daily_reward - 1):
            claimed = True

        if available:
            fill = (31, 104, 75)
            outline = (105, 225, 155)
            text_color = (245, 255, 246)
            button_color = (22, 145, 85)
            button_text = "جمع"
        elif claimed:
            fill = (12, 17, 20)
            outline = (63, 75, 78)
            text_color = (155, 168, 172)
            button_color = (25, 31, 34)
            button_text = "تم"
        else:
            fill = (126, 98, 36)
            outline = (222, 187, 80)
            text_color = (255, 242, 195)
            button_color = (157, 122, 42)
            button_text = "جمع"
        pygame.draw.rect(surface, fill, card_rect, border_radius=12)
        pygame.draw.rect(surface, outline, card_rect, 2 if available else 1, border_radius=12)

        day_text = render_fit_text(
            f"يوم {day_index}", text_color, card_rect.width - 8, 22, 18,
        )
        surface.blit(day_text, (card_rect.centerx - day_text.get_width() // 2, card_rect.top + 6))
        coin_center = (card_rect.centerx, card_rect.top + 57)
        pygame.draw.circle(surface, (225, 175, 55), coin_center, 15)
        pygame.draw.circle(surface, (255, 232, 150), coin_center, 15, 2)
        pygame.draw.circle(surface, (178, 123, 32), coin_center, 5, 2)
        amount_text = render_fit_text(f"+{day_index}", text_color, card_rect.width - 12, 22, 18)
        surface.blit(amount_text, (card_rect.centerx - amount_text.get_width() // 2, card_rect.top + 76))

        draw_button(surface, button_text, daily_reward_collect_rects[day_index - 1], button_color,
                text_color=text_color, font_size=17)

    balance = render_fit_text(
        f"رصيد الذهب: {gold_coins}", (255, 220, 135), panel.width - 48, 22, 20,
    )
    surface.blit(balance, (panel.centerx - balance.get_width() // 2, panel.bottom - 29))


def draw_daily_missions_panel(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))
    surface.blit(overlay, (0, 0))

    panel = daily_missions_panel_rect
    pygame.draw.rect(surface, (4, 8, 14), panel.move(0, 7), border_radius=24)
    pygame.draw.rect(surface, (18, 30, 43), panel, border_radius=24)
    draw_theme_frame(surface, panel, 2, 24)

    pygame.draw.rect(surface, (145, 55, 66), daily_missions_close_rect, border_radius=10)
    pygame.draw.rect(surface, (227, 128, 132), daily_missions_close_rect, 1, border_radius=10)
    close_text = SMALL_FONT.render("X", True, (255, 255, 255))
    surface.blit(close_text, (daily_missions_close_rect.centerx - close_text.get_width() // 2,
                              daily_missions_close_rect.centery - close_text.get_height() // 2))

    title = render_fit_text("المهام اليومية", (238, 248, 240), panel.width - 96, 48, 38, True)
    surface.blit(title, (panel.centerx - title.get_width() // 2, panel.top + 12))
    reward_summary = render_fit_text(
        "النقاط: جائزة عشوائية | 60 دقيقة: 5 قلوب + 5 دروع | 5 انتصارات: قلب + درع",
        (145, 224, 193), panel.width - 72, 22, 16, True,
    )
    surface.blit(reward_summary, (panel.centerx - reward_summary.get_width() // 2, panel.top + 72))

    mission_labels = {
        "points": "اجمع 100 نقطة",
        "survive_seconds": "اقضِ 60 دقيقة في اللعب",
        "round_wins": "فز بـ5 جولات",
    }
    claimed_missions = set(daily_missions.get("claimed", []))
    for (mission, target), row in zip(DAILY_MISSION_TARGETS.items(), daily_mission_row_rects):
        current = daily_missions.get(mission, 0)
        if mission == "survive_seconds":
            progress_label = f"{min(60, int(current // 60))}/60 دقيقة"
            progress_ratio = min(1.0, current / target)
        else:
            progress_label = f"{int(current)}/{target}"
            progress_ratio = min(1.0, current / target)
        completed = mission in claimed_missions
        accent = (109, 220, 164) if completed else (91, 166, 199)
        pygame.draw.rect(surface, (26, 44, 57), row, border_radius=14)
        pygame.draw.rect(surface, accent, row, 2 if completed else 1, border_radius=14)

        progress_text = render_fit_text(
            "اكتملت" if completed else progress_label, accent, row.width // 3, 22, 16, True,
        )
        progress_x = row.right - progress_text.get_width() - 16
        mission_text = render_fit_text(
            mission_labels[mission], (240, 246, 248),
            max(1, progress_x - row.left - 32), 22, 20,
        )
        surface.blit(mission_text, (row.left + 16, row.top + 5))
        surface.blit(progress_text, (progress_x, row.top + 7))

        reward_labels = {
            "heart": "قلب",
            "shield": "درع",
        }
        reward = daily_missions.get("rewards", {}).get(mission)
        if mission == "points" and isinstance(reward, dict):
            prize = next((name for name, quantity in reward.items() if quantity), None)
            reward_label = f"الجائزة: {reward_labels[prize]}" if prize else "جائزة عشوائية"
        else:
            reward_label = DAILY_MISSION_REWARD_LABELS[mission]
        reward_text = render_fit_text(
            reward_label, (175, 198, 208), row.width - 32, 18, 14,
        )
        surface.blit(reward_text, (row.left + 16, row.top + 30))

        progress_bar = pygame.Rect(row.left + 16, row.bottom - 9, row.width - 32, 4)
        pygame.draw.rect(surface, (12, 21, 29), progress_bar, border_radius=4)
        fill_width = round(progress_bar.width * progress_ratio)
        if fill_width:
            pygame.draw.rect(surface, accent,
                             pygame.Rect(progress_bar.left, progress_bar.top, fill_width, progress_bar.height),
                             border_radius=4)

    balance = render_fit_text(
        f"رصيد الذهب: {gold_coins}", (255, 220, 135), panel.width - 48, 22, 20,
    )
    surface.blit(balance, (panel.centerx - balance.get_width() // 2, panel.bottom - 29))


def draw_statistics_panel(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))
    surface.blit(overlay, (0, 0))
    panel = stats_panel_rect
    pygame.draw.rect(surface, (4, 8, 14), panel.move(0, 7), border_radius=24)
    pygame.draw.rect(surface, (18, 30, 43), panel, border_radius=24)
    draw_theme_frame(surface, panel, 2, 24)
    draw_button(surface, "X", stats_close_rect, (145, 55, 66), font_size=16)

    title = render_fit_text(
        "إحصائيات اللاعب", (240, 248, 255), panel.width - 96, 48, 38, True,
    )
    surface.blit(title, (panel.centerx - title.get_width() // 2, panel.top + 18))
    rows = (
        ("النقاط التي جمعتها", int(stats["points_collected"])),
        ("الجولات التي فزت بها", int(stats["round_wins"])),
        ("الأعداء الذين تفاديتهم", int(stats["enemies_evaded"])),
        ("وقت اللعب", f"{int(stats['play_seconds'] // 60)} دقيقة"),
    )
    card_width = (panel.width - 72) // 2
    card_height = 72
    for index, (label, value) in enumerate(rows):
        card = pygame.Rect(
            panel.left + 24 + (index % 2) * (card_width + 16),
            panel.top + 78 + (index // 2) * (card_height + 12),
            card_width, card_height,
        )
        pygame.draw.rect(surface, (29, 47, 64), card, border_radius=14)
        pygame.draw.rect(surface, (64, 101, 128), card, 1, border_radius=14)
        label_text = render_fit_text(label, (180, 203, 218), card.width - 20, 22, 18)
        value_text = render_fit_text(str(value), (245, 220, 145), card.width - 20, 28, 24)
        surface.blit(label_text, (card.centerx - label_text.get_width() // 2, card.top + 8))
        surface.blit(value_text, (card.centerx - value_text.get_width() // 2, card.top + 34))

    achievement_title = render_fit_text(
        "الإنجازات ومكافآتها", (225, 238, 248), panel.width - 64, 30, 26, True,
    )
    surface.blit(achievement_title, (panel.centerx - achievement_title.get_width() // 2, panel.top + 254))
    claimed = set(stats.get("claimed_achievements", []))
    for index, (achievement_id, achievement) in enumerate(ACHIEVEMENTS.items()):
        label, description, metric, target, reward = achievement
        achieved = achievement_id in claimed
        text = f"{label} — {description} | +{reward} ذهب"
        color = (126, 223, 171) if achieved else (166, 188, 203)
        line = render_fit_text(text, color, panel.width - 64, 24, 18)
        surface.blit(line, (panel.centerx - line.get_width() // 2, panel.top + 292 + index * 29))


def draw_daily_challenge_panel(surface):
    ensure_daily_challenge()
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))
    surface.blit(overlay, (0, 0))
    panel = challenge_panel_rect
    pygame.draw.rect(surface, (4, 8, 14), panel.move(0, 7), border_radius=24)
    pygame.draw.rect(surface, (18, 30, 43), panel, border_radius=24)
    draw_theme_frame(surface, panel, 2, 24)
    draw_button(surface, "X", challenge_close_rect, (145, 55, 66), font_size=16)

    challenge = next(item for item in DAILY_CHALLENGES if item[0] == daily_challenge["key"])
    _, description, _, target = challenge
    title = render_fit_text("التحدي اليومي", (255, 239, 195), panel.width - 96, 48, 38, True)
    surface.blit(title, (panel.centerx - title.get_width() // 2, panel.top + 20))
    challenge_text = render_fit_text(
        description, (235, 243, 248), panel.width - 80, 36, 26,
    )
    surface.blit(challenge_text, (panel.centerx - challenge_text.get_width() // 2, panel.top + 92))

    progress = min(target, daily_challenge.get("progress", 0))
    if daily_challenge["key"] == "fast_enemies":
        progress_text = f"{int(progress)}/{target} ثانية"
    else:
        progress_text = f"{int(progress)}/{target}"
    progress_label = render_fit_text(
        progress_text, (195, 220, 232), panel.width - 96, 24, 20,
    )
    surface.blit(progress_label, (panel.centerx - progress_label.get_width() // 2, panel.top + 145))
    progress_rect = pygame.Rect(panel.left + 72, panel.top + 180, panel.width - 144, 14)
    pygame.draw.rect(surface, (10, 20, 29), progress_rect, border_radius=7)
    fill_width = round(progress_rect.width * progress / target)
    if fill_width:
        pygame.draw.rect(surface, (75, 205, 166),
                         pygame.Rect(progress_rect.left, progress_rect.top, fill_width, progress_rect.height),
                         border_radius=7)

    if daily_challenge.get("claimed"):
        button_text, button_color = "مكافأة التحدي: 20 ذهب - اكتملت", (71, 132, 98)
    elif daily_challenge.get("active"):
        button_text, button_color = "إيقاف التحدي اليومي", (143, 87, 67)
    else:
        button_text, button_color = "ابدأ التحدي اليومي", (35, 145, 109)
    draw_button(surface, button_text, challenge_toggle_rect, button_color, font_size=17)


# ================================
# متغيرات اللعبة
# ================================

score = 0
points = (
    [generate_point(), generate_point()]
    if round_collects_points(current_round) else []
)
particles = []
victory_fireworks = []
screen_shake_until = 0
screen_shake_intensity = 0
stats_save_elapsed = 0.0
round_gold_earned = 0
round_gold_tracking = False
round_wave_number = 1
round_waves_completed = 0
round_next_wave_at = 10
round_hazard_rect = None
safe_zone_rect = None
daily_survival_update_elapsed = 0.0
combo_count = 0
combo_last_pickup = 0.0
enemy_proximity = set()
shield_circle = None
freeze_circle = None
special_pickup = None
last_special_pickup_time = time.time()
magnet_until = 0
slow_enemies_until = 0
shield_active = False
shield_duration = SHIELD_BASE_DURATION
freeze_active = False
speed_boost_active = False
speed_boost_start = 0
shield_start = 0
freeze_start = 0
last_shield_time = time.time()
last_freeze_time = time.time()
start_time = 0
remaining_time = time_limit
game_started = False
game_over = False
round_won = False
round_win_recorded = False
defeated_player_index = 0
countdown_active = False
countdown_value = 3
countdown_started_at = 0
game_paused = False
pause_started_at = 0
paused_screen = None
player_healths = [PLAYER_MAX_HEALTH] * 2
player_health_caps = [PLAYER_MAX_HEALTH] * 2
player_hit_untils = [0.0] * 2
player_match_scores = [0] * 2
player_survival_times = [0.0] * 2
match_winner_player_index = 0
competitive_match_finished = False
midround_heart_pickup = None
midround_heart_spawned = False
midround_heart_collected = False
midround_heart_resolved = False
boss_warning_active = False

# enemies

enemies = generate_enemies(
    player_rect,
    current_enemy_count_for_round(current_round),
    boss_count_for_round(current_round) > 0,
    tuple(player_rects[1:player_count]),
    boss_count=boss_count_for_round(current_round),
)
enemy_styles = {
    id(enemy): "boss" if index < boss_count_for_round(current_round)
    else round_enemy_style(current_round, index - boss_count_for_round(current_round))
    for index, enemy in enumerate(enemies)
}
enemy_health = {
    id(enemy): BOSS_MAX_HEALTH
    for enemy in enemies if enemy_styles[id(enemy)] == "boss"
}
enemy_motion_remainders = {}
boss_contact_started = {}
best_score_this_round = 0
enemy_collision_frames = {}
COLLISION_FRAMES_REQUIRED = 3
show_room_setup = False
custom_room_active = False

ROOM_SPEED_OPTIONS = (
    (0.8, "بطيء"),
    (1.0, "عادي"),
    (1.35, "سريع"),
)

clock = pygame.time.Clock()

def damage_player_from_attack(player_index, controlled_player, current_time):
    global screen_shake_until, screen_shake_intensity, game_over, game_started
    if shield_active or freeze_active:
        return
    health_index = player_index - 1
    if current_time < player_hit_untils[health_index]:
        return
    screen_shake_until = current_time + 0.24
    screen_shake_intensity = 5
    spawn_particles(controlled_player.center, (255, 85, 110), 16)
    player_healths[health_index] = max(0, player_healths[health_index] - 1)
    player_hit_untils[health_index] = current_time + PLAYER_HIT_INVULNERABILITY
    if player_healths[health_index] == 0:
        for pointer_id, controlled_index in list(joystick_pointer_players.items()):
            if controlled_index == player_index:
                joystick_pointer_players.pop(pointer_id, None)
        reset_joystick(player_index)
        play_death_sound()
        if not two_player_mode:
            settle_midround_heart()
            game_over = True
            game_started = False
        elif sum(health > 0 for health in player_healths[:player_count]) == 0:
            finish_competitive_match()


def update_special_attacks(active_players, round_num, current_time):
    if not active_players or freeze_active:
        return

    # 1. هجمات الوحوش الخاصة والزعماء
    for enemy in enemies:
        enemy_id = id(enemy)
        style = enemy_styles.get(enemy_id, "jelly")
        target_player = min(
            (p_rect for _, p_rect, _, _ in active_players),
            key=lambda p: math.hypot(p.centerx - enemy.centerx, p.centery - enemy.centery)
        )
        dx = target_player.centerx - enemy.centerx
        dy = target_player.centery - enemy.centery
        dist = max(1.0, math.hypot(dx, dy))

        # المفجّر: يزرع قنبلة بجانب اللاعب عند الاقتراب منه
        if style == "bomber":
            if dist < 140 and current_time >= enemy_action_timers.get(enemy_id, 0):
                active_bombs.append({
                    "pos": (target_player.centerx, target_player.centery),
                    "explode_at": current_time + 1.1,
                    "radius": 85,
                })
                enemy_action_timers[enemy_id] = current_time + 3.0

        # الوحش المبطئ: يرمي طلقة كل 1 ثانية بعد الجولة 3 (أو في الروم) تبطئ اللاعب 2 ثانية
        elif style == "slower" and (round_num > 3 or custom_room_active):
            if current_time >= enemy_action_timers.get(enemy_id, 0):
                proj_speed = 6.5
                slow_projectiles.append({
                    "rect": pygame.Rect(enemy.centerx - 7, enemy.centery - 7, 14, 14),
                    "vx": (dx / dist) * proj_speed,
                    "vy": (dy / dist) * proj_speed,
                })
                enemy_action_timers[enemy_id] = current_time + 1.0

        # الزعيم: يرمي 3 شوكات كل 1 ثانية باتجاه اللاعب بعد الجولة 3 (أو في الروم)
        elif style == "boss" and (round_num > 3 or custom_room_active):
            if current_time >= enemy_action_timers.get(enemy_id, 0):
                base_angle = math.atan2(dy, dx)
                spike_speed = 7.5
                for spread in (-0.26, 0.0, 0.26):
                    angle = base_angle + spread
                    boss_spikes.append({
                        "rect": pygame.Rect(enemy.centerx - 6, enemy.centery - 6, 12, 12),
                        "vx": math.cos(angle) * spike_speed,
                        "vy": math.sin(angle) * spike_speed,
                    })
                enemy_action_timers[enemy_id] = current_time + 1.0

    # 2. انفجار القنابل
    for bomb in active_bombs[:]:
        if current_time >= bomb["explode_at"]:
            bx, by = bomb["pos"]
            spawn_particles((bx, by), (255, 130, 50), 18)
            for player_index, controlled_player, _, _ in active_players:
                if math.hypot(controlled_player.centerx - bx, controlled_player.centery - by) <= bomb["radius"]:
                    damage_player_from_attack(player_index, controlled_player, current_time)
            active_bombs.remove(bomb)

    # 3. حركة شوكات الزعيم وفحص التصادم
    for spike in boss_spikes[:]:
        spike["rect"].x += spike["vx"]
        spike["rect"].y += spike["vy"]
        if not SCREEN.get_rect().colliderect(spike["rect"]):
            boss_spikes.remove(spike)
            continue
        for player_index, controlled_player, _, _ in active_players:
            if spike["rect"].colliderect(controlled_player):
                damage_player_from_attack(player_index, controlled_player, current_time)
                if spike in boss_spikes:
                    boss_spikes.remove(spike)
                break

    # 4. حركة مقذوفات التبطيء وفحص التصادم
    for proj in slow_projectiles[:]:
        proj["rect"].x += proj["vx"]
        proj["rect"].y += proj["vy"]
        if not SCREEN.get_rect().colliderect(proj["rect"]):
            slow_projectiles.remove(proj)
            continue
        for player_index, controlled_player, _, _ in active_players:
            if proj["rect"].colliderect(controlled_player):
                player_slow_untils[player_index - 1] = current_time + 2.0
                spawn_particles(controlled_player.center, (80, 210, 255), 10)
                if proj in slow_projectiles:
                    slow_projectiles.remove(proj)
                break


def draw_special_attacks(surface, active_players, current_time):
    # رسم القنابل مع دائرة تحذير حمراء
    for bomb in active_bombs:
        bx, by = bomb["pos"]
        pygame.draw.circle(surface, (255, 70, 70), (bx, by), bomb["radius"], 2)
        pygame.draw.circle(surface, (25, 25, 30), (bx, by), 14)
        pygame.draw.circle(surface, (255, 190, 40), (bx, by - 14), 5)

    # رسم شوكات الزعيم
    for spike in boss_spikes:
        pygame.draw.polygon(surface, (235, 50, 90), [
            (spike["rect"].centerx, spike["rect"].top),
            (spike["rect"].right, spike["rect"].centery),
            (spike["rect"].centerx, spike["rect"].bottom),
            (spike["rect"].left, spike["rect"].centery),
        ])

    # رسم مقذوفات التبطيء
    for proj in slow_projectiles:
        pygame.draw.circle(surface, (80, 210, 255), proj["rect"].center, 8)
        pygame.draw.circle(surface, (255, 255, 255), proj["rect"].center, 4)

    # هالة التبطيء حول اللاعب المتأثر
    for player_index, controlled_player, _, _ in active_players:
        if current_time < player_slow_untils[player_index - 1]:
            pygame.draw.rect(surface, (80, 210, 255), controlled_player.inflate(10, 10), 3, border_radius=10)

# ================================
# إعادة الجولة
# ================================
active_bombs = []
boss_spikes = []
slow_projectiles = []
enemy_action_timers = {}
player_slow_untils = [0.0, 0.0]

def reset_round(round_num):
    global score, points, shield_circle, freeze_circle, shield_active, freeze_active
    global shield_start, freeze_start, start_time, remaining_time, enemies, enemy_styles, enemy_health
    global enemy_collision_frames, special_pickup, last_special_pickup_time
    global magnet_until, slow_enemies_until, best_score_this_round, particles
    global speed_boost_active, speed_boost_start
    global midround_heart_pickup, midround_heart_spawned
    global midround_heart_collected, midround_heart_resolved, shield_duration
    global defeated_player_index
    global round_win_recorded
    global match_winner_player_index, competitive_match_finished
    global combo_count, combo_last_pickup, enemy_proximity
    global enemy_motion_remainders
    global boss_contact_started
    global round_gold_earned, round_gold_tracking
    global round_wave_number, round_waves_completed, round_next_wave_at
    global round_hazard_rect, safe_zone_rect
    active_bombs.clear()
    jumper_states.clear()
    boss_spikes.clear()
    slow_projectiles.clear()
    enemy_action_timers.clear()
    player_slow_untils[:] = [0.0, 0.0]

    score = 0
    round_wave_number = 1
    round_waves_completed = 0
    round_next_wave_at = 10
    round_hazard_rect = None
    safe_zone_rect = None
    player_match_scores[:] = [0] * 2
    player_survival_times[:] = [0.0] * 2
    match_winner_player_index = 0
    competitive_match_finished = False
    update_player_profile(1, reached_round=round_num)
    for player_index in range(2, player_count + 1):
        update_player_profile(player_index, reached_round=round_num)
    combo_count = 0
    combo_last_pickup = 0.0
    enemy_proximity.clear()
    round_win_recorded = False
    round_gold_earned = 0
    round_gold_tracking = True
    best_score_this_round = 0
    player_healths[:] = [PLAYER_MAX_HEALTH] * 2
    player_health_caps[:] = [PLAYER_MAX_HEALTH] * 2
    player_hit_untils[:] = [0.0] * 2
    points = (
        [generate_point(), generate_point()]
        if round_collects_points(round_num) else []
    )
    particles.clear()
    shield_circle = None
    freeze_circle = None
    special_pickup = None
    last_special_pickup_time = time.time()
    midround_heart_pickup = None
    midround_heart_spawned = False
    midround_heart_collected = False
    midround_heart_resolved = False
    magnet_until = 0
    slow_enemies_until = 0
    shield_active = False
    shield_duration = SHIELD_BASE_DURATION + shield_upgrade_level + (1 if globals().get("equipped_skin") == "wizard" else 0)
    freeze_active = False
    speed_boost_active = False
    speed_boost_start = 0
    starting_positions = (
        (80, 80),
        (WIDTH - 80 - PLAYER_SIZE, 80),
    )
    for controlled_player, position in zip(player_rects, starting_positions):
        controlled_player.topleft = position
    start_time = 0
    remaining_time = time_limit
    enemies = generate_enemies(
        player_rect,
        current_enemy_count_for_round(round_num),
        boss_count_for_round(round_num) > 0,
        tuple(player_rects[1:player_count]),
        boss_count=boss_count_for_round(round_num),
    )
    enemy_styles = {
        id(enemy): "boss" if index < boss_count_for_round(round_num)
        else round_enemy_style(round_num, index - boss_count_for_round(round_num))
        for index, enemy in enumerate(enemies)
    }
    enemy_health = {
        id(enemy): BOSS_MAX_HEALTH
        for enemy in enemies if enemy_styles[id(enemy)] == "boss"
    }
    enemy_motion_remainders = {}
    boss_contact_started = {}
    enemy_collision_frames = {}


def start_match_countdown():
    global countdown_active, countdown_value, countdown_started_at, game_started, boss_warning_active
    countdown_active = True
    countdown_value = 3
    countdown_started_at = time.time()
    boss_warning_active = boss_count_for_round(current_round) > 0
    if boss_warning_active:
        play_boss_warning()
    game_started = False
    reset_joystick()


def open_settings():
    global show_settings, game_paused, pause_started_at, paused_screen
    if game_started or countdown_active:
        paused_screen = SCREEN.copy()
        game_paused = True
        pause_started_at = time.time()
        reset_joystick()
    show_settings = True


def close_settings():
    global show_settings, game_paused, paused_screen, start_time, countdown_started_at
    global shield_start, freeze_start, speed_boost_start, last_shield_time, last_freeze_time
    global magnet_until, slow_enemies_until, last_special_pickup_time
    if game_paused:
        paused_duration = time.time() - pause_started_at
        start_time += paused_duration
        countdown_started_at += paused_duration
        shield_start += paused_duration
        freeze_start += paused_duration
        speed_boost_start += paused_duration
        last_shield_time += paused_duration
        last_freeze_time += paused_duration
        last_special_pickup_time += paused_duration
        magnet_until += paused_duration
        slow_enemies_until += paused_duration
        game_paused = False
        paused_screen = None
    show_settings = False
    reset_joystick()


def buy_speed_boost():
    global gold_coins, speed_boost_pending
    refresh_daily_upgrades()
    if (speed_boost_pending or not store_purchase_available("speed_boost")
            or gold_coins < SPEED_BOOST_COST):
        return
    record_store_purchase("speed_boost")
    gold_coins -= SPEED_BOOST_COST
    speed_boost_pending = True
    save_progress(current_round, target_score, time_limit, completed_rounds)


def buy_purchased_shield():
    global gold_coins, purchased_shields
    refresh_daily_upgrades()
    if (not store_purchase_available("shield")
            or gold_coins < PURCHASED_SHIELD_COST):
        return
    record_store_purchase("shield")
    gold_coins -= PURCHASED_SHIELD_COST
    purchased_shields += 1
    save_progress(current_round, target_score, time_limit, completed_rounds)


def buy_heart():
    global gold_coins, purchased_hearts
    refresh_daily_upgrades()
    if not store_purchase_available("heart") or gold_coins < HEART_COST:
        return
    record_store_purchase("heart")
    gold_coins -= HEART_COST
    purchased_hearts += 1
    save_progress(current_round, target_score, time_limit, completed_rounds)


def buy_room_card():
    global gold_coins, room_cards
    refresh_daily_upgrades()
    if not store_purchase_available("room_card") or gold_coins < ROOM_CARD_COST:
        return
    record_store_purchase("room_card")
    gold_coins -= ROOM_CARD_COST
    room_cards += 1
    save_progress(current_round, target_score, time_limit, completed_rounds)


def select_or_buy_skin(skin_id, cost):
    global gold_coins, equipped_skin, unlocked_skins
    valid_ids = {s[0] for s in PLAYER_SKINS}
    if "unlocked_skins" not in globals() or not unlocked_skins:
        unlocked_skins = ["thief"]
    if "equipped_skin" not in globals() or equipped_skin not in valid_ids:
        equipped_skin = "thief"
    if skin_id in unlocked_skins:
        equipped_skin = skin_id
        save_progress(current_round, target_score, time_limit, completed_rounds)
        return
    if gold_coins >= cost:
        gold_coins -= cost
        unlocked_skins.append(skin_id)
        equipped_skin = skin_id
        save_progress(current_round, target_score, time_limit, completed_rounds)


def activate_purchased_shield():
    global purchased_shields, shield_active, shield_start, shield_duration
    if (purchased_shields < 1 or not game_started or game_paused
            or daily_challenge_rule_active("no_shield")
            or round_has_modifier("no_shield")):
        return False
    purchased_shields -= 1
    shield_active = True
    shield_start = time.time()
    shield_duration = PURCHASED_SHIELD_DURATION
    save_progress(current_round, target_score, time_limit, completed_rounds)
    return True


def settle_midround_heart():
    global midround_heart_pickup, midround_heart_resolved
    if midround_heart_resolved:
        return
    midround_heart_pickup = None
    midround_heart_resolved = True
    save_progress(current_round, target_score, time_limit, completed_rounds)


def collect_midround_heart(player_index=1):
    global midround_heart_pickup, midround_heart_collected
    if midround_heart_pickup is None:
        return
    health_index = player_index - 1
    if player_healths[health_index] < MAX_PLAYER_HEALTH:
        player_healths[health_index] += 1
        player_health_caps[health_index] = max(
            player_health_caps[health_index], player_healths[health_index],
        )
    midround_heart_collected = True
    spawn_particles(midround_heart_pickup.center, (255, 90, 125), 18)
    midround_heart_pickup = None
    save_progress(current_round, target_score, time_limit, completed_rounds)


def skip_round_with_gold():
    global gold_coins, current_round, target_score, time_limit, remaining_time, show_shop
    global round_win_recorded
    refresh_daily_upgrades()
    if (not store_purchase_available("skip_round")
            or gold_coins < SKIP_ROUND_COST):
        return
    record_store_purchase("skip_round")
    current_round = find_next_uncompleted(current_round, completed_rounds)
    gold_coins -= SKIP_ROUND_COST
    round_win_recorded = False
    record_round_win()
    current_round = find_next_uncompleted(current_round + 1, completed_rounds)
    target_score, time_limit = get_round_settings(current_round)
    remaining_time = time_limit
    show_shop = False
    save_progress(current_round, target_score, time_limit, completed_rounds)


def continue_round_with_gold():
    global gold_coins, game_over, game_started, start_time, remaining_time
    global shield_active, shield_start, shield_duration
    global enemy_collision_frames
    if gold_coins < CONTINUE_COST:
        return
    gold_coins -= CONTINUE_COST
    resume_failed_round()


def continue_round_with_heart():
    global purchased_hearts
    if not game_over or purchased_hearts < 1:
        return
    purchased_hearts -= 1
    resume_failed_round()


def resume_failed_round():
    global game_over, game_started, start_time, remaining_time
    global round_gold_tracking
    global shield_active, shield_start, shield_duration
    global enemy_collision_frames
    global defeated_player_index
    remaining_time = max(CONTINUE_BONUS_SECONDS, remaining_time)
    round_gold_tracking = True
    start_time = time.time() - (time_limit - remaining_time) / GAME_TIME_SCALE
    starting_positions = (
        (80, 80),
        (WIDTH - 80 - PLAYER_SIZE, 80),
    )
    for player_index in range(player_count):
        player_rects[player_index].topleft = starting_positions[player_index]
        player_healths[player_index] = max(1, player_health_caps[player_index])
        player_hit_untils[player_index] = time.time() + PLAYER_HIT_INVULNERABILITY
    shield_active = (
        not daily_challenge_rule_active("no_shield")
        and not round_has_modifier("no_shield")
    )
    shield_start = time.time()
    shield_duration = SHIELD_BASE_DURATION + shield_upgrade_level
    enemy_collision_frames = {}
    defeated_player_index = 0
    game_over = False
    game_started = True
    reset_joystick()
    save_progress(current_round, target_score, time_limit, completed_rounds)

# ================================
# خلفية
# ================================

def create_space_background(theme_key):
    theme = BACKGROUND_THEMES.get(theme_key, BACKGROUND_THEMES["midnight"])
    background = pygame.Surface((WIDTH, HEIGHT))
    background.fill(theme["bg"])
    if theme_key not in BACKGROUND_THEMES:
        return background

    decorations = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    rng = random.Random(sum(ord(char) for char in theme_key))

    for nebula_x, nebula_y, nebula_width, nebula_height, alpha in (
        (WIDTH // 5, HEIGHT // 3, WIDTH // 3, HEIGHT // 4, 10),
        (WIDTH * 3 // 5, HEIGHT * 2 // 3, WIDTH // 2, HEIGHT // 3, 8),
        (WIDTH * 4 // 5, HEIGHT // 5, WIDTH // 4, HEIGHT // 3, 9),
    ):
        pygame.draw.ellipse(
            decorations, (*theme["glow"], alpha),
            (nebula_x - nebula_width // 2, nebula_y - nebula_height // 2,
             nebula_width, nebula_height),
        )

    star_count = min(180, max(90, WIDTH * HEIGHT // 6000))
    for _ in range(star_count):
        x = rng.randrange(WIDTH)
        y = rng.randrange(HEIGHT)
        radius = rng.choices((1, 2, 3), weights=(7, 2, 1), k=1)[0]
        alpha = rng.randint(55, 155)
        pygame.draw.circle(decorations, (*theme["stars"], alpha), (x, y), radius)
        if radius == 3:
            pygame.draw.line(decorations, (*theme["stars"], alpha // 2),
                             (x - 5, y), (x + 5, y), 1)
            pygame.draw.line(decorations, (*theme["stars"], alpha // 2),
                             (x, y - 5), (x, y + 5), 1)

    for _ in range(3):
        x = rng.randint(32, WIDTH - 32)
        y = rng.randint(32, HEIGHT - 32)
        trail_length = rng.randint(18, 38)
        pygame.draw.line(
            decorations, (*theme["stars"], 105),
            (x, y), (x - trail_length, y + trail_length // 2), 2,
        )

    small_radius = max(12, min(WIDTH, HEIGHT) // 38)
    small_x, small_y = WIDTH // 5, HEIGHT // 4
    pygame.draw.ellipse(
        decorations, (*theme["line"], 72),
        (small_x - small_radius * 2, small_y - small_radius // 3,
         small_radius * 4, small_radius * 2 // 3), 2,
    )
    pygame.draw.circle(decorations, (*theme["glow"], 115), (small_x, small_y), small_radius)
    pygame.draw.circle(decorations, (*theme["line"], 135), (small_x, small_y), small_radius, 1)
    pygame.draw.circle(
        decorations, (*theme["stars"], 75),
        (small_x - small_radius // 3, small_y - small_radius // 3), max(2, small_radius // 5),
    )

    planet_x, planet_y = WIDTH * 4 // 5, HEIGHT // 4
    planet_radius = max(18, min(WIDTH, HEIGHT) // 24)
    pygame.draw.ellipse(
        decorations, (*theme["line"], 85),
        (planet_x - planet_radius * 2, planet_y - planet_radius // 3,
         planet_radius * 4, planet_radius * 2 // 3), 2,
    )
    pygame.draw.circle(decorations, (*theme["glow"], 145), (planet_x, planet_y), planet_radius)
    pygame.draw.ellipse(
        decorations, (*theme["line"], 95),
        (planet_x - planet_radius, planet_y - planet_radius // 2,
         planet_radius * 2, planet_radius), 1,
    )
    pygame.draw.circle(decorations, (*theme["stars"], 95),
                       (planet_x - planet_radius // 3, planet_y - planet_radius // 3),
                       max(3, planet_radius // 5))
    pygame.draw.ellipse(
        decorations, (*theme["line"], 125),
        (planet_x - planet_radius * 2, planet_y - planet_radius // 3,
         planet_radius * 4, planet_radius * 2 // 3), 2,
    )

    moon_x, moon_y = WIDTH * 3 // 5, HEIGHT // 5
    moon_radius = max(18, min(WIDTH, HEIGHT) // 28)
    moon_color = tuple(min(255, int(channel * 0.62 + 82)) for channel in theme["stars"])
    moon_shadow = tuple(max(0, int(channel * 0.55)) for channel in moon_color)
    pygame.draw.circle(decorations, (*moon_color, 180), (moon_x, moon_y), moon_radius)
    pygame.draw.circle(
        decorations, (*moon_shadow, 155),
        (moon_x + moon_radius // 2, moon_y - moon_radius // 5), moon_radius * 4 // 5,
    )
    for crater_x, crater_y, crater_radius in (
        (-moon_radius // 3, -moon_radius // 4, max(2, moon_radius // 7)),
        (moon_radius // 4, moon_radius // 3, max(2, moon_radius // 9)),
        (-moon_radius // 5, moon_radius // 2, max(2, moon_radius // 11)),
    ):
        pygame.draw.circle(
            decorations, (*moon_shadow, 115),
            (moon_x + crater_x, moon_y + crater_y), crater_radius,
        )
    pygame.draw.circle(decorations, (*theme["stars"], 150), (moon_x, moon_y), moon_radius, 1)

    pygame.draw.polygon(
        decorations, (*theme["line"], 18),
        [(0, HEIGHT), (0, HEIGHT * 9 // 10), (WIDTH // 4, HEIGHT * 19 // 20),
         (WIDTH // 2, HEIGHT * 9 // 10), (WIDTH * 3 // 4, HEIGHT * 19 // 20),
         (WIDTH, HEIGHT * 9 // 10), (WIDTH, HEIGHT)],
    )
    background.blit(decorations, (0, 0))
    return background


SPACE_BACKGROUND_CACHE = {}
BACKGROUND_PREVIEW_CACHE = {}


def get_background_image(theme_key):
    if theme_key not in SPACE_BACKGROUND_CACHE:
        SPACE_BACKGROUND_CACHE[theme_key] = create_space_background(theme_key)
    return SPACE_BACKGROUND_CACHE[theme_key]


SKIN_FILES = {
    "thief": ("thief_idle.png", "thief_walk.png", 5),
    "astro": ("astro_idle.png", "astro_walk.png", 5),
    "robot": ("robot_idle.png", "robot_walk.png", 4),
    "fox": ("fox_idle.png", "fox_walk.png", 4),
    "wizard": ("wizard_idle.png", "wizard_walk.png", 4),
}


def clean_sprite_surface(surf):
    surf = surf.convert_alpha()
    w, h = surf.get_size()
    for x in range(w):
        for y in range(h):
            r, g, b, a = surf.get_at((x, y))
            if a > 0 and r > 220 and g > 220 and b > 220 and abs(r - g) < 12 and abs(g - b) < 12:
                surf.set_at((x, y), (255, 255, 255, 0))
    return surf


def load_all_skin_images():
    loaded = {}
    for skin_id, (idle_name, walk_name, frame_count) in SKIN_FILES.items():
        idle_r, idle_l, walk_r, walk_l = None, None, (), ()
        idle_path = os.path.join(BACKGROUND_ASSET_DIR, idle_name)
        walk_path = os.path.join(BACKGROUND_ASSET_DIR, walk_name)
        try:
            if os.path.exists(idle_path):
                img = clean_sprite_surface(pygame.image.load(idle_path))
                idle_r = pygame.transform.smoothscale(img, (56, 84))
                idle_l = pygame.transform.flip(idle_r, True, False)
        except (pygame.error, OSError) as exc:
            print(f"تعذر تحميل {idle_name}: {exc}")
        try:
            if os.path.exists(walk_path):
                sheet = clean_sprite_surface(pygame.image.load(walk_path))
                fw = sheet.get_width() // frame_count
                fh = sheet.get_height()
                walk_r = tuple(
                    pygame.transform.smoothscale(
                        sheet.subsurface((i * fw, 0, fw, fh)).copy(),
                        (56, 84),
                    )
                    for i in range(frame_count)
                )
                walk_l = tuple(pygame.transform.flip(f, True, False) for f in walk_r)
        except (pygame.error, OSError) as exc:
            print(f"تعذر تحميل {walk_name}: {exc}")
        loaded[skin_id] = (idle_r, idle_l, walk_r, walk_l)
    return loaded


ALL_SKIN_IMAGES = load_all_skin_images()
PLAYER_IMAGE, PLAYER_IMAGE_LEFT, PLAYER_WALK_FRAMES, PLAYER_WALK_FRAMES_LEFT = ALL_SKIN_IMAGES["thief"]


def draw_player_tag(surface, top_rect, player_index, theme_colors):
    if not two_player_mode:
        return
    tag_color = (75, 195, 255) if player_index == 1 else (255, 185, 75)
    badge = pygame.Rect(top_rect.centerx - 11, top_rect.top - 22, 22, 18)
    pygame.draw.rect(surface, (12, 20, 34), badge, border_radius=6)
    pygame.draw.rect(surface, tag_color, badge, 1, border_radius=6)
    num_surf = FPS_FONT.render(str(player_index), True, tag_color)
    surface.blit(num_surf, (badge.centerx - num_surf.get_width() // 2, badge.centery - num_surf.get_height() // 2))


def draw_player_visual(surface, rect, movement_x, moving, theme_colors, player_index=1):
    skin = globals().get("equipped_skin", "thief")
    if skin not in ALL_SKIN_IMAGES:
        skin = "thief"

    if time.time() < player_dash_untils[player_index - 1]:
        pygame.draw.ellipse(surface, (110, 235, 255), rect.inflate(18, 18), 3)

    idle_r, idle_l, walk_r, walk_l = ALL_SKIN_IMAGES[skin]

    if moving and walk_r:
        walk_frame_index = (pygame.time.get_ticks() // 100) % len(walk_r)
        walk_frames = walk_l if movement_x < -0.1 else walk_r
        image = walk_frames[walk_frame_index]
    else:
        image = idle_l if movement_x < -0.1 else idle_r

    if image is not None:
        image_rect = image.get_rect(midbottom=rect.midbottom)
        if player_index == 2:
            tinted = image.copy()
            tinted.fill((255, 225, 185, 255), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(tinted, image_rect)
        else:
            surface.blit(image, image_rect)
        draw_player_tag(surface, image_rect, player_index, theme_colors)
        return image_rect, True

    skin_color = next((s[3] for s in PLAYER_SKINS if s[0] == skin), theme_colors["player"])
    player_color = (255, 185, 75) if player_index == 2 else skin_color
    pygame.draw.rect(surface, theme_colors["player_outline"], rect.inflate(6, 6), border_radius=12)
    pygame.draw.rect(surface, player_color, rect, border_radius=9)
    draw_player_tag(surface, rect, player_index, theme_colors)
    return rect, False


    skin_color = next((s for s in PLAYER_SKINS if s == skin), theme_colors["player"])
    player_color = theme_colors["accent"] if player_index == 2 else skin_color
    pygame.draw.rect(surface, theme_colors["player_outline"], rect.inflate(6, 6), border_radius=12)
    pygame.draw.rect(surface, player_color, rect, border_radius=9)
    return rect, False


def create_pickup_images():
    shield = pygame.Surface((48, 48), pygame.SRCALPHA)
    shield_points = [(24, 3), (43, 10), (40, 29), (24, 45), (8, 29), (5, 10)]
    pygame.draw.polygon(shield, (110, 50, 210, 100), shield_points)
    pygame.draw.polygon(shield, (190, 130, 255), shield_points, 4)
    pygame.draw.polygon(shield, (105, 65, 180), [(24, 10), (36, 14), (34, 27), (24, 38), (14, 27), (12, 14)])
    pygame.draw.line(shield, (235, 220, 255), (16, 16), (22, 21), 3)

    ice = pygame.Surface((48, 48), pygame.SRCALPHA)
    ice_points = [(24, 2), (30, 16), (43, 8), (37, 22), (47, 24), (37, 29),
                  (43, 41), (30, 33), (24, 46), (18, 33), (5, 41), (11, 28),
                  (1, 24), (11, 19), (5, 8), (18, 16)]
    pygame.draw.polygon(ice, (55, 175, 255, 100), ice_points)
    pygame.draw.polygon(ice, (175, 235, 255), ice_points, 2)
    pygame.draw.line(ice, (230, 250, 255), (24, 7), (24, 41), 3)
    pygame.draw.line(ice, (230, 250, 255), (9, 15), (39, 33), 2)
    pygame.draw.line(ice, (230, 250, 255), (9, 33), (39, 15), 2)
    return shield, ice


def create_heart_image():
    heart = pygame.Surface((38, 36), pygame.SRCALPHA)
    color = (245, 76, 103)
    pygame.draw.circle(heart, color, (12, 12), 10)
    pygame.draw.circle(heart, color, (26, 12), 10)
    pygame.draw.polygon(heart, color, [(3, 14), (35, 14), (19, 34)])
    pygame.draw.line(heart, (255, 170, 182), (9, 8), (13, 6), 2)
    return heart


SHIELD_IMAGE, FREEZE_IMAGE = create_pickup_images()
HEART_IMAGE = create_heart_image()
DUAL_HUD_HEART_IMAGE = pygame.transform.smoothscale(HEART_IMAGE, (19, 18))
HEART_GLOW_IMAGE = pygame.Surface((48, 48), pygame.SRCALPHA)
pygame.draw.circle(HEART_GLOW_IMAGE, (255, 75, 120, 65), (24, 24), 22)
DAMAGE_FLASH = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
DAMAGE_FLASH.fill((255, 45, 70, 24))
DUAL_HUD_SURFACE_CACHE = {}


def draw_background(surface):
    surface.blit(get_background_image(current_background_theme), (0, 0))

room_panel_rect = pygame.Rect(WIDTH // 2 - 280, HEIGHT // 2 - 215, 560, 430)
room_close_rect = pygame.Rect(room_panel_rect.right - 46, room_panel_rect.top + 12, 34, 34)
room_score_minus_rect = pygame.Rect(room_panel_rect.left + 210, room_panel_rect.top + 85, 42, 36)
room_score_plus_rect = pygame.Rect(room_panel_rect.left + 350, room_panel_rect.top + 85, 42, 36)
room_obj_toggle_rect = pygame.Rect(room_panel_rect.left + 210, room_panel_rect.top + 135, 182, 36)
room_speed_toggle_rect = pygame.Rect(room_panel_rect.left + 210, room_panel_rect.top + 185, 182, 36)
room_enemy_toggle_rect = pygame.Rect(room_panel_rect.left + 210, room_panel_rect.top + 235, 182, 36)
room_boss_minus_rect = pygame.Rect(room_panel_rect.left + 210, room_panel_rect.top + 285, 42, 36)
room_boss_plus_rect = pygame.Rect(room_panel_rect.left + 350, room_panel_rect.top + 285, 42, 36)
room_start_btn_rect = pygame.Rect(room_panel_rect.centerx - 120, room_panel_rect.bottom - 58, 240, 46)


def draw_room_setup_panel(surface):
    room_settings.setdefault("boss_count", 0)
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))
    surface.blit(overlay, (0, 0))
    panel = room_panel_rect
    pygame.draw.rect(surface, (16, 28, 42), panel, border_radius=22)
    draw_theme_frame(surface, panel, 2, 22)
    draw_button(surface, "X", room_close_rect, (145, 55, 66), font_size=16)

    title = render_fit_text("إعدادات الروم", (255, 235, 175), panel.width - 100, 36, 28, True)
    surface.blit(title, (panel.centerx - title.get_width() // 2, panel.top + 14))

    cards_lbl = render_fit_text(f"بطاقات الروم: {room_cards}", (125, 225, 190), panel.width - 80, 22, 17, True)
    surface.blit(cards_lbl, (panel.centerx - cards_lbl.get_width() // 2, panel.top + 52))

    rows = (
        ("النقاط المطلوبة:", room_score_minus_rect.centery),
        ("مهمة الجولة:", room_obj_toggle_rect.centery),
        ("سرعة الحركة:", room_speed_toggle_rect.centery),
        ("نوع الأعداء:", room_enemy_toggle_rect.centery),
        ("عدد الزعماء:", room_boss_minus_rect.centery),
    )
    for lbl_txt, ry in rows:
        lbl = render_fit_text(lbl_txt, (225, 235, 242), 175, 24, 18, True)
        surface.blit(lbl, (panel.left + 24, ry - lbl.get_height() // 2))

    draw_button(surface, "-", room_score_minus_rect, (55, 80, 105), font_size=20)
    score_val = render_fit_text(str(room_settings["target"]), (255, 255, 255), 90, 28, 22, True)
    surface.blit(score_val, (room_score_minus_rect.right + 48 - score_val.get_width() // 2, room_score_minus_rect.centery - score_val.get_height() // 2))
    draw_button(surface, "+", room_score_plus_rect, (55, 80, 105), font_size=20)

    obj_item = ROOM_OBJECTIVES[room_settings["objective_idx"] % len(ROOM_OBJECTIVES)]
    obj_label = obj_item[1] if isinstance(obj_item, (tuple, list)) else str(obj_item)
    draw_button(surface, obj_label, room_obj_toggle_rect, (42, 95, 120), font_size=16)

    spd_item = ROOM_SPEED_OPTIONS[room_settings["speed_idx"] % len(ROOM_SPEED_OPTIONS)]
    spd_label = spd_item[1] if isinstance(spd_item, (tuple, list)) else str(spd_item)
    draw_button(surface, spd_label, room_speed_toggle_rect, (42, 95, 120), font_size=16)

    enemy_item = ROOM_ENEMY_TYPES[room_settings["enemy_idx"] % len(ROOM_ENEMY_TYPES)]
    enemy_label = enemy_item[1] if isinstance(enemy_item, (tuple, list)) else str(enemy_item)
    draw_button(surface, enemy_label, room_enemy_toggle_rect, (42, 95, 120), font_size=16)

    draw_button(surface, "-", room_boss_minus_rect, (55, 80, 105), font_size=20)
    boss_val = render_fit_text(str(room_settings["boss_count"]), (255, 255, 255), 90, 28, 22, True)
    surface.blit(boss_val, (room_boss_minus_rect.right + 48 - boss_val.get_width() // 2, room_boss_minus_rect.centery - boss_val.get_height() // 2))
    draw_button(surface, "+", room_boss_plus_rect, (55, 80, 105), font_size=20)

    can_start = room_cards > 0
    btn_txt = "ابدأ الروم" if can_start else "تحتاج بطاقة روم من المتجر"
    btn_col = (22, 150, 100) if can_start else (85, 88, 95)
    draw_button(surface, btn_txt, room_start_btn_rect, btn_col, font_size=18)


# ================================
# الحلقة الرئيسية
# ================================

running = True

while running:
    refresh_daily_upgrades()
    ensure_daily_challenge()
    dt = clock.tick(TARGET_FPS) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_progress(current_round, target_score, time_limit, completed_rounds)
            pygame.quit()
            sys.exit()

        if (editing_controls and event.type in (pygame.MOUSEMOTION, pygame.FINGERMOTION)
                and dragging_control_layout):
            pointer = pointer_position(event)
            move_control_layout(
                selected_control_layout_key,
                (pointer[0] + control_layout_drag_offset[0],
                 pointer[1] + control_layout_drag_offset[1]),
            )
            continue
        if editing_controls and event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP):
            if dragging_control_layout:
                dragging_control_layout = False
                save_settings({"control_layout": settings["control_layout"]})
            continue

        if show_player_profiles and active_player_name is not None:
            if event.type == pygame.TEXTINPUT:
                player_name_draft = "".join(
                    character for character in player_name_draft + event.text
                    if character.isprintable()
                )[:18]
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    save_player_name(active_player_name, player_name_draft)
                    active_player_name = None
                    pygame.key.stop_text_input()
                elif event.key == pygame.K_BACKSPACE:
                    player_name_draft = player_name_draft[:-1]
                elif event.key == pygame.K_ESCAPE:
                    active_player_name = None
                    pygame.key.stop_text_input()

        if event.type == pygame.KEYDOWN and active_player_name is None:
            if event.key == pygame.K_ESCAPE:
                if show_settings:
                    close_settings()
                elif show_shop:
                    show_shop = False
                elif show_room_setup:
                    show_room_setup = False
                elif show_daily_rewards:
                    show_daily_rewards = False
                elif show_daily_missions:
                    show_daily_missions = False
                elif show_statistics:
                    show_statistics = False
                elif show_daily_challenge:
                    show_daily_challenge = False
                elif show_player_profiles:
                    show_player_profiles = False
                elif show_main_options:
                    show_main_options = False
                elif game_started and not game_over and not round_won:
                    open_settings()
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if (not game_started and not game_over and not round_won
                        and not countdown_active and not show_settings and not show_shop
                        and not show_room_setup and not show_daily_rewards
                        and not show_daily_missions and not show_statistics
                        and not show_daily_challenge and not show_player_profiles
                        and not show_main_options):
                    custom_room_active = False
                    if selected_replay_round is not None:
                        current_round = selected_replay_round
                        selected_replay_round = None
                    else:
                        current_round = find_next_uncompleted(current_round, completed_rounds)
                    target_score, time_limit = get_round_settings(current_round)
                    remaining_time = time_limit
                    reset_round(current_round)
                    start_match_countdown()
            elif game_started and not game_over and not round_won and not game_paused:
                if event.key in (pygame.K_SPACE, pygame.K_e, pygame.K_RCTRL):
                    activate_purchased_shield()

        if (show_settings and event.type in (pygame.MOUSEMOTION, pygame.FINGERMOTION)
                and dragging_settings_slider):
            slider_x = event.pos[0] if hasattr(event, "pos") else event.x * WIDTH
            update_setting_slider(dragging_settings_slider, slider_x)
        elif event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP):
            dragging_settings_slider = None

        # touch / mouse input
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
            pos = pointer_position(event)
            if editing_controls:
                if button_clicked(control_editor_done_rect, pos):
                    editing_controls = False
                    dragging_control_layout = False
                    save_settings({"control_layout": settings["control_layout"]})
                elif button_clicked(control_editor_smaller_rect, pos):
                    change_control_layout_scale(selected_control_layout_key, -0.1)
                elif button_clicked(control_editor_larger_rect, pos):
                    change_control_layout_scale(selected_control_layout_key, 0.1)
                elif button_clicked(control_editor_previous_rect, pos):
                    index = control_editor_keys.index(selected_control_layout_key)
                    selected_control_layout_key = control_editor_keys[
                        (index - 1) % len(control_editor_keys)
                    ]
                elif button_clicked(control_editor_next_rect, pos):
                    index = control_editor_keys.index(selected_control_layout_key)
                    selected_control_layout_key = control_editor_keys[
                        (index + 1) % len(control_editor_keys)
                    ]
                else:
                    tapped_control = next(
                        (
                            key for key in control_editor_keys
                            if control_layout_hit_rect(key).inflate(20, 20).collidepoint(pos)
                        ),
                        None,
                    )
                    if tapped_control is not None:
                        selected_control_layout_key = tapped_control
                        dragging_control_layout = True
                        layout_entry = settings["control_layout"][tapped_control]
                        control_layout_drag_offset = (
                            round(layout_entry["x"] * WIDTH) - pos[0],
                            round(layout_entry["y"] * HEIGHT) - pos[1],
                        )
                continue

            main_options_was_open = show_main_options
            if (not show_shop and not show_settings and not game_started and not game_over
                    and not show_daily_rewards and not show_daily_missions
                    and not show_statistics and not show_daily_challenge
                    and not show_player_profiles and not show_main_options
                    and not show_room_setup and not round_won
                    and len(completed_rounds) > ROUNDS_PER_PAGE
                    and completed_panel_rect.collidepoint(pos)):
                rounds_swipe_start_x = pos[0]
            else:
                rounds_swipe_start_x = None

            if show_main_options:
                if button_clicked(main_options_close_rect, pos):
                    show_main_options = False
                else:
                    selected_option = next(
                        (
                            option for option, rect in main_options_button_rects.items()
                            if rect.collidepoint(pos)
                        ),
                        None,
                    )
                    if selected_option is not None:
                        show_main_options = False
                        if selected_option == "shop":
                            show_shop = True
                        elif selected_option == "missions":
                            show_daily_missions = True
                        elif selected_option == "rewards":
                            show_daily_rewards = True
                        elif selected_option == "statistics":
                            show_statistics = True
                        elif selected_option == "challenge":
                            show_daily_challenge = True
                        elif selected_option == "profiles":
                            show_player_profiles = True
                        elif selected_option == "difficulty":
                            toggle_difficulty()
                        elif selected_option == "exit":
                            save_progress(current_round, target_score, time_limit, completed_rounds)
                            pygame.quit()
                            sys.exit()
            elif show_room_setup:
                if button_clicked(room_close_rect, pos):
                    show_room_setup = False
                elif button_clicked(room_boss_minus_rect, pos):
                    room_settings["boss_count"] = max(0, room_settings["boss_count"] - 1)
                elif button_clicked(room_boss_plus_rect, pos):
                    room_settings["boss_count"] = min(3, room_settings["boss_count"] + 1)

                elif button_clicked(room_score_minus_rect, pos):
                    room_settings["target"] = max(10, room_settings["target"] - 5)
                elif button_clicked(room_score_plus_rect, pos):
                    room_settings["target"] = min(200, room_settings["target"] + 5)
                elif button_clicked(room_obj_toggle_rect, pos):
                    room_settings["objective_idx"] = (room_settings["objective_idx"] + 1) % len(ROOM_OBJECTIVES)
                elif button_clicked(room_speed_toggle_rect, pos):
                    room_settings["speed_idx"] = (room_settings["speed_idx"] + 1) % len(ROOM_SPEED_OPTIONS)
                elif button_clicked(room_enemy_toggle_rect, pos):
                    room_settings["enemy_idx"] = (room_settings["enemy_idx"] + 1) % len(ROOM_ENEMY_TYPES)
                elif button_clicked(room_start_btn_rect, pos) and room_cards > 0:
                    room_cards -= 1
                    custom_room_active = True
                    show_room_setup = False
                    target_score = room_settings["target"]
                    time_limit = 60
                    remaining_time = time_limit
                    save_progress(current_round, target_score, time_limit, completed_rounds)
                    reset_round(current_round)
                    start_match_countdown()
            elif show_player_profiles:
                if button_clicked(player_profiles_close_rect, pos):
                    if active_player_name is not None:
                        save_player_name(active_player_name, player_name_draft)
                        active_player_name = None
                        pygame.key.stop_text_input()
                    show_player_profiles = False
                else:
                    clicked_player = next(
                        (
                            player_index for player_index in range(1, 3)
                            if player_profile_name_rect(player_index).collidepoint(pos)
                        ),
                        None,
                    )
                    if clicked_player is not None:
                        if active_player_name is not None:
                            save_player_name(active_player_name, player_name_draft)
                        active_player_name = clicked_player
                        player_name_draft = ""
                        pygame.key.start_text_input()
                        pygame.key.set_text_input_rect(
                            player_profile_name_rect(clicked_player)
                        )
                    elif active_player_name is not None:
                        save_player_name(active_player_name, player_name_draft)

                        active_player_name = None
                        pygame.key.stop_text_input()
            elif show_statistics:
                if button_clicked(stats_close_rect, pos):
                    show_statistics = False
            elif show_daily_challenge:
                if button_clicked(challenge_close_rect, pos):
                    show_daily_challenge = False
                elif button_clicked(challenge_toggle_rect, pos) and not daily_challenge.get("claimed"):
                    daily_challenge["active"] = not daily_challenge.get("active", False)
                    save_progress(current_round, target_score, time_limit, completed_rounds)
            elif show_daily_rewards:
                if button_clicked(daily_rewards_close_rect, pos):
                    show_daily_rewards = False
                else:
                    for day_index, collect_rect in enumerate(daily_reward_collect_rects, start=1):
                        if button_clicked(collect_rect, pos):
                            if daily_reward_available() and day_index == next_daily_reward:
                                collect_daily_reward()
                            break
            elif show_daily_missions:
                if button_clicked(daily_missions_close_rect, pos):
                    show_daily_missions = False
            elif show_shop:
                if button_clicked(shop_close_rect, pos):
                    show_shop = False
                elif button_clicked(shop_buy_rect, pos):
                    buy_speed_boost()
                elif button_clicked(shop_speed_upgrade_rect, pos):
                    buy_speed_upgrade()
                elif button_clicked(shop_shield_upgrade_rect, pos):
                    buy_shield_upgrade()
                elif button_clicked(shop_skip_rect, pos):
                    skip_round_with_gold()
                elif button_clicked(shop_purchased_shield_rect, pos):
                    buy_purchased_shield()
                elif button_clicked(shop_heart_rect, pos):
                    buy_heart()
                elif button_clicked(shop_room_card_rect, pos):
                    buy_room_card()

                else:
                    for (skin_id, _, skin_cost, _, _), s_rect in zip(PLAYER_SKINS, shop_skin_rects):
                        if s_rect.collidepoint(pos):
                            select_or_buy_skin(skin_id, skin_cost)
                            break
            elif show_settings:

                if settings_sfx_slider_rect.inflate(0, 24).collidepoint(pos):
                    dragging_settings_slider = "sfx_volume"
                    update_setting_slider(dragging_settings_slider, pos[0])
                    continue
                elif settings_music_slider_rect.inflate(0, 24).collidepoint(pos):
                    dragging_settings_slider = "music_volume"
                    update_setting_slider(dragging_settings_slider, pos[0])
                    continue
                elif button_clicked(settings_control_layout_rect, pos):
                    editing_controls = True
                    selected_control_layout_key = "movement_left"
                elif button_clicked(settings_close_rect, pos):
                    close_settings()
                elif button_clicked(settings_resume_rect, pos):
                    close_settings()
                elif any(rect.collidepoint(pos) for rect in settings_theme_rects.values()):
                    for color_id, rect in settings_theme_rects.items():
                        if rect.collidepoint(pos):
                            save_settings({"background_color": color_id})
                            break
                elif any(rect.collidepoint(pos) for rect in settings_language_rects.values()):
                    for language_code, rect in settings_language_rects.items():
                        if rect.collidepoint(pos):
                            save_settings({"language": language_code})
                            break
                elif button_clicked(settings_control_style_rect, pos):
                    save_settings({
                        "control_style": "arrows" if control_style == "analog" else "analog",
                    })
                elif button_clicked(settings_exit_rect, pos):
                    save_progress(current_round, target_score, time_limit, completed_rounds)
                    pygame.quit()
                    sys.exit()
                continue
            elif not game_started and not game_over and not round_won:
                page_count = max(1, (len(completed_rounds) + ROUNDS_PER_PAGE - 1) // ROUNDS_PER_PAGE)
                clicked_round = None
                if completed_rounds:
                    page_start = rounds_page * ROUNDS_PER_PAGE
                    visible_rounds = completed_rounds[page_start:page_start + ROUNDS_PER_PAGE]
                    badge_width = (len(visible_rounds) - 1) * 52 + 38
                    badge_start_x = completed_panel_rect.centerx - badge_width // 2
                    for badge_index, round_num in enumerate(visible_rounds):
                        badge_rect = pygame.Rect(badge_start_x + badge_index * 52,
                                                 completed_panel_rect.top + 39, 38, 38)
                        if badge_rect.collidepoint(pos):
                            clicked_round = round_num
                            break

                if clicked_round is not None:
                    selected_replay_round = clicked_round
                elif page_count > 1 and button_clicked(rounds_previous_rect, pos):
                    rounds_page = max(0, rounds_page - 1)
                elif page_count > 1 and button_clicked(rounds_next_rect, pos):
                    rounds_page = min(page_count - 1, rounds_page + 1)
                elif button_clicked(menu_mode_button_rect, pos):
                    switch_player_mode()
                elif two_player_mode and button_clicked(menu_room_button_rect, pos):
                    show_room_setup = True
                elif button_clicked(menu_more_button_rect, pos):
                    show_main_options = True
                elif button_clicked(start_button_rect, pos):
                    if selected_replay_round is not None:
                        current_round = selected_replay_round
                        selected_replay_round = None
                    else:
                        current_round = find_next_uncompleted(current_round, completed_rounds)
                    target_score, time_limit = get_round_settings(current_round)
                    remaining_time = time_limit
                    reset_round(current_round)
                    start_match_countdown()

                elif button_clicked(settings_button_rect, pos):
                    open_settings()
            elif game_over:
                if competitive_match_finished and button_clicked(retry_button_rect, pos):
                    game_over = False
                    reset_round(current_round)
                    start_match_countdown()
                elif not competitive_match_finished and button_clicked(continue_button_rect, pos):
                    continue_round_with_gold()
                elif not competitive_match_finished and button_clicked(heart_continue_button_rect, pos):
                    continue_round_with_heart()
                elif not competitive_match_finished and button_clicked(retry_button_rect, pos):
                    game_over = False
                    reset_round(current_round)
                    start_match_countdown()
                if show_room_setup:
                        draw_room_setup_panel(SCREEN)

            elif round_won:
                if button_clicked(next_button_rect, pos):
                    current_round = find_next_uncompleted(current_round + 1, completed_rounds)
                    target_score, time_limit = get_round_settings(current_round)
                    save_progress(current_round, target_score, time_limit, completed_rounds)
                    round_won = False
                    reset_round(current_round)
                    start_match_countdown()

            if game_started and not game_over and not round_won:
                is_touch = event.type == pygame.FINGERDOWN
                pointer_id = (
                    ("finger", event.finger_id) if is_touch else ("mouse", 0)
                )
                if control_style == "analog" and pointer_id not in joystick_pointer_players:
                    player_index = (
                        1 if pos[0] < WIDTH // 2 else 2
                    )
                    active_player_indices = (
                        (1, 2) if two_player_mode else (1,)
                    )
                    excluded_controls = (
                        menu_button_rect,
                        game_settings_button_rect,
                    ) + (
                        (
                            two_player_shield_use_button_rect,
                            two_player_player_two_shield_use_button_rect,
                        )
                        if two_player_mode else (
                            shield_use_button_rect,
                        )
                    )
                    if (
                        player_index in active_player_indices
                        and player_healths[player_index - 1] > 0
                        and not any(rect.collidepoint(pos) for rect in excluded_controls)
                    ):
                        joystick_touch_centers[player_index] = tuple(map(int, pos))
                        joystick_pointer_players[pointer_id] = player_index
                        update_joystick(pos, player_index)
                elif control_style == "arrows" and pointer_id not in arrow_pointer_directions:
                    arrow_hit = next(
                        (
                            (player_index, direction)
                            for player_index in range(1, player_count + 1)
                            if player_healths[player_index - 1] > 0
                            for direction, rect in arrow_control_rects(player_index).items()
                            if rect.collidepoint(pos)
                        ),
                        None,
                    )
                    if arrow_hit is not None:
                        arrow_pointer_directions[pointer_id] = arrow_hit

                if two_player_mode:
                    player_action_buttons = (
                        (two_player_shield_use_button_rect, 1),
                        (two_player_player_two_shield_use_button_rect, 2),
                    )
                else:
                    player_action_buttons = (
                        (shield_use_button_rect, 1),
                    )
                if any(
                    button_clicked(shield_button, pos)
                    for shield_button, _ in player_action_buttons
                ):
                    activate_purchased_shield()
                elif button_clicked(menu_button_rect, pos):
                    settle_midround_heart()
                    game_started = False
                    game_over = False
                    round_won = False
                elif button_clicked(game_settings_button_rect, pos):
                    open_settings()

            if (not game_started and not game_over and not round_won and not show_settings
                    and not show_shop and not show_daily_rewards and not show_daily_missions
                    and not main_options_was_open
                    and button_clicked(settings_button_rect, pos)):
                open_settings()

        elif event.type in (pygame.MOUSEMOTION, pygame.FINGERMOTION):
            pos = pointer_position(event)
            pointer_id = (
                ("finger", event.finger_id)
                if event.type == pygame.FINGERMOTION else ("mouse", 0)
            )
            player_index = joystick_pointer_players.get(pointer_id)
            if player_index is not None:
                update_joystick(pos, player_index)

        elif event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP):
            pos = pointer_position(event)
            if rounds_swipe_start_x is not None:
                swipe_distance = pos[0] - rounds_swipe_start_x
                page_count = max(1, (len(completed_rounds) + ROUNDS_PER_PAGE - 1) // ROUNDS_PER_PAGE)
                if swipe_distance <= -45:
                    rounds_page = min(page_count - 1, rounds_page + 1)
                elif swipe_distance >= 45:
                    rounds_page = max(0, rounds_page - 1)
                rounds_swipe_start_x = None
            pointer_id = (
                ("finger", event.finger_id)
                if event.type == pygame.FINGERUP else ("mouse", 0)
            )
            player_index = joystick_pointer_players.pop(pointer_id, None)
            if (
                player_index is not None
                and player_index not in joystick_pointer_players.values()
            ):
                reset_joystick(player_index)
            arrow_pointer_directions.pop(pointer_id, None)

    update_movement_sound(
        game_started
        and not game_over
        and not round_won
        and not game_paused
        and not countdown_active
        and any(
            abs(horizontal) > 0.05 or abs(vertical) > 0.05
            for horizontal, vertical in move_vectors[:player_count]
        )
    )

    if game_paused and paused_screen is not None:
        SCREEN.blit(paused_screen, (0, 0))
    elif countdown_active:
        elapsed = time.time() - countdown_started_at
        countdown_value = max(0, 3 - int(elapsed))
        if elapsed >= 3:
            countdown_active = False
            game_started = True
            boss_warning_active = False
            time_penalty = 15 if daily_challenge_rule_active("time_attack") else 0
            start_time = time.time() - time_penalty / GAME_TIME_SCALE
            shield_active = (
                not daily_challenge_rule_active("no_shield")
                and not round_has_modifier("no_shield")
            )
            shield_start = start_time
            shield_duration = SHIELD_BASE_DURATION + shield_upgrade_level
            last_shield_time = start_time
            last_freeze_time = start_time
            if speed_boost_pending:
                speed_boost_pending = False
                speed_boost_active = True
                speed_boost_start = start_time
                save_progress(current_round, target_score, time_limit, completed_rounds)

        draw_background(SCREEN)
        pygame.draw.rect(SCREEN, (255, 255, 255), pygame.Rect(WIDTH // 2 - 90, HEIGHT // 2 - 90, 180, 180), border_radius=28)
        number = TITLE_FONT.render(str(countdown_value) if countdown_value > 0 else "ابدأ", True, (20, 20, 20))
        SCREEN.blit(number, (WIDTH // 2 - number.get_width() // 2, HEIGHT // 2 - number.get_height() // 2))
        countdown_objective = render_fit_text(
            round_objective_description(current_round),
            BACKGROUND_THEMES.get(
                current_background_theme, BACKGROUND_THEMES["midnight"],
            )["accent"],
            WIDTH - 48, 30, 22, True,
        )
        SCREEN.blit(
            countdown_objective,
            (WIDTH // 2 - countdown_objective.get_width() // 2, HEIGHT // 2 - 145),
        )
        if boss_warning_active:
            warning_text = MED_FONT.render(arabic_text("تحذير: الزعيم قادم!"), True, (255, 115, 130))
            warning_rect = warning_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 95))
            pygame.draw.rect(SCREEN, (42, 18, 30), warning_rect.inflate(32, 16), border_radius=12)
            pygame.draw.rect(SCREEN, (216, 75, 96), warning_rect.inflate(32, 16), 2, border_radius=12)
            SCREEN.blit(warning_text, warning_rect)
        for player_index in range(1, player_count + 1):
            if player_healths[player_index - 1] > 0:
                draw_player_control(SCREEN, player_index)

    # ================================
    # منطق اللعب أثناء اللعب
    # ================================
    elif game_started and not game_over and not round_won:
        draw_background(SCREEN)
        current_time = time.time()
        round_elapsed = max(0, current_time - start_time) * GAME_TIME_SCALE
        if round_has_modifier("moving_hazard"):
            hazard_x = 25 + int(
                (math.sin(round_elapsed * 0.65) + 1) * 0.5 * max(0, WIDTH - 290)
            )
            round_hazard_rect = pygame.Rect(
                hazard_x, HEIGHT // 2 - 26, 265, 52,
            )
            pygame.draw.rect(SCREEN, (140, 38, 48), round_hazard_rect, border_radius=18)
            pygame.draw.rect(SCREEN, (255, 105, 110), round_hazard_rect, 3, border_radius=18)
        else:
            round_hazard_rect = None
        if round_has_modifier("shifting_safe_zone"):
            safe_positions = (
                (24, 145),
                (WIDTH - 184, 145),
                (WIDTH - 184, HEIGHT - 184),
                (24, HEIGHT - 184),
            )
            safe_index = int(round_elapsed // 8) % len(safe_positions)
            safe_zone_rect = pygame.Rect(*safe_positions[safe_index], 160, 140)
            pygame.draw.rect(SCREEN, (19, 94, 72), safe_zone_rect, border_radius=22)
            pygame.draw.rect(SCREEN, (80, 235, 165), safe_zone_rect, 3, border_radius=22)
        else:
            safe_zone_rect = None
        theme_colors = BACKGROUND_THEMES.get(current_background_theme, BACKGROUND_THEMES["midnight"])
        if two_player_mode:
            player_hud_width = min(180, max(108, (WIDTH - 24) // player_count - 8))
            player_hud_height = 58
            hud_gap = max(4, (WIDTH - 24 - player_hud_width * player_count) // max(1, player_count - 1))
            hud_cards = [
                pygame.Rect(
                    12 + player_index * (player_hud_width + hud_gap),
                    10, player_hud_width, player_hud_height,
                )
                for player_index in range(player_count)
            ]
            if hud_cards[-1].right > WIDTH - 12:
                hud_gap = 4
                hud_cards = [
                    pygame.Rect(
                        12 + player_index * (player_hud_width + hud_gap),
                        10, player_hud_width, player_hud_height,
                    )
                    for player_index in range(player_count)
                ]
            general_hud = pygame.Rect(WIDTH // 2 - 120, 76, 240, 56)
            for hud_card in (*hud_cards, general_hud):
                hud_surface = DUAL_HUD_SURFACE_CACHE.get(hud_card.size)
                if hud_surface is None:
                    hud_surface = pygame.Surface(hud_card.size, pygame.SRCALPHA)
                    pygame.draw.rect(
                        hud_surface,
                        (5, 12, 24, 210),
                        hud_surface.get_rect(),
                        border_radius=16,
                    )
                    DUAL_HUD_SURFACE_CACHE[hud_card.size] = hud_surface
                SCREEN.blit(hud_surface, hud_card.topleft)
                draw_theme_frame(SCREEN, hud_card, 2, 16)


            for player_index, hud_card in enumerate(hud_cards, start=1):
                player_label = render_fit_text(
                    settings["player_names"][str(player_index)],
                    theme_colors["accent"], hud_card.width - 12, 18, 15, True,
                )
                SCREEN.blit(player_label, (hud_card.left + 6, hud_card.top + 4))
                heart_label = render_fit_text(
                    f"×{player_healths[player_index - 1]}",
                    (255, 235, 240), 44, 18, 14, True,
                )
                SCREEN.blit(DUAL_HUD_HEART_IMAGE, (hud_card.left + 6, hud_card.top + 30))
                SCREEN.blit(heart_label, (hud_card.left + 28, hud_card.top + 30))
                goal_label = render_fit_text(
                    (
                        f"{player_match_scores[player_index - 1]}/{target_score}"
                        if round_collects_points(current_round)
                        else f"{int(player_survival_times[player_index - 1])}ث"
                    ),
                    (225, 235, 242), hud_card.width - 58, 18, 14, True,
                )
                SCREEN.blit(goal_label, (hud_card.right - goal_label.get_width() - 6, hud_card.top + 30))

            score_line = render_fit_text(
                f"جولة {current_round}: {round_objective_description(current_round)}",
                (248, 250, 252), general_hud.width - 16, 24, 18, True,
            )
            time_line = render_fit_text(
                f"الوقت {remaining_time}ث   |   الأعداء {len(enemies)}",
                (205, 220, 232), general_hud.width - 16, 22, 16,
            )
            SCREEN.blit(
                score_line,
                (general_hud.centerx - score_line.get_width() // 2, general_hud.top + 7),
            )
            SCREEN.blit(
                time_line,
                (general_hud.centerx - time_line.get_width() // 2, general_hud.top + 37),
            )
        if speed_boost_active and current_time - speed_boost_start >= SPEED_BOOST_DURATION:
            speed_boost_active = False
        movement_speed = player_movement_speed()

        active_players = []
        if control_style == "arrows":
            update_arrow_movement()

        keys = pygame.key.get_pressed()
        # تحكم اللاعب الأول (WASD، وفي وضع اللاعب الواحد تعمل الأسهم أيضاً)
        kb_p1_x = (1.0 if keys[pygame.K_d] else 0.0) - (1.0 if keys[pygame.K_a] else 0.0)
        kb_p1_y = (1.0 if keys[pygame.K_s] else 0.0) - (1.0 if keys[pygame.K_w] else 0.0)
        if not two_player_mode:
            kb_p1_x = kb_p1_x or ((1.0 if keys[pygame.K_RIGHT] else 0.0) - (1.0 if keys[pygame.K_LEFT] else 0.0))
            kb_p1_y = kb_p1_y or ((1.0 if keys[pygame.K_DOWN] else 0.0) - (1.0 if keys[pygame.K_UP] else 0.0))

        p1_touch_active = (
            1 in joystick_pointer_players.values()
            or any(ctrl == 1 for ctrl, _ in arrow_pointer_directions.values())
        )
        if kb_p1_x or kb_p1_y:
            mag = math.hypot(kb_p1_x, kb_p1_y)
            move_vectors[0] = [kb_p1_x / mag, kb_p1_y / mag]
        elif not p1_touch_active:
            move_vectors[0] = [0.0, 0.0]

        # تحكم اللاعب الثاني (أسهم الاتجاهات)
        if two_player_mode:
            kb_p2_x = (1.0 if keys[pygame.K_RIGHT] else 0.0) - (1.0 if keys[pygame.K_LEFT] else 0.0)
            kb_p2_y = (1.0 if keys[pygame.K_DOWN] else 0.0) - (1.0 if keys[pygame.K_UP] else 0.0)
            p2_touch_active = (
                2 in joystick_pointer_players.values()
                or any(ctrl == 2 for ctrl, _ in arrow_pointer_directions.values())
            )
            if kb_p2_x or kb_p2_y:
                mag2 = math.hypot(kb_p2_x, kb_p2_y)
                move_vectors[1] = [kb_p2_x / mag2, kb_p2_y / mag2]
            elif not p2_touch_active:
                move_vectors[1] = [0.0, 0.0]

        for player_index in range(1, player_count + 1):

            if player_healths[player_index - 1] > 0:
                horizontal_move, vertical_move = move_vectors[player_index - 1]
                active_players.append(
                    (player_index, player_rects[player_index - 1], horizontal_move, vertical_move)
                )
        player_collision_rects = []
        for player_index, controlled_player, horizontal_move, vertical_move in active_players:
            player_survival_times[player_index - 1] += dt * GAME_TIME_SCALE
            update_player_profile(player_index, play_seconds=dt)
            movement_remainder = player_move_remainders[player_index - 1]
            exact_move_x = horizontal_move * movement_speed + movement_remainder[0]
            exact_move_y = vertical_move * movement_speed + movement_remainder[1]
            move_x = int(exact_move_x)
            move_y = int(exact_move_y)
            movement_remainder[0] = exact_move_x - move_x
            movement_remainder[1] = exact_move_y - move_y
            controlled_player.x += move_x
            controlled_player.y += move_y
            unclamped_position = controlled_player.topleft
            controlled_player.clamp_ip(SCREEN.get_rect())
            if controlled_player.x != unclamped_position[0]:
                movement_remainder[0] = 0.0
            if controlled_player.y != unclamped_position[1]:
                movement_remainder[1] = 0.0
            player_moving = abs(horizontal_move) > 0.05 or abs(vertical_move) > 0.05
            image_rect, has_player_image = draw_player_visual(
                SCREEN, controlled_player, horizontal_move, player_moving,
                theme_colors, player_index,
            )
            player_collision_rects.append(controlled_player)
            if shield_active:
                shield_rect = (
                    image_rect.inflate(12, 12) if has_player_image
                    else controlled_player.inflate(18, 18)
                )
                pygame.draw.ellipse(SCREEN, theme_colors["accent"], shield_rect, 3)
        for player_index in range(1, player_count + 1):
            if player_healths[player_index - 1] > 0:
                draw_player_control(SCREEN, player_index)

        # جمع النقاط
        for point in points[:]:
            if round_collects_points(current_round) and current_time < magnet_until:
                magnet_target = min(
                    player_collision_rects,
                    key=lambda controlled_player: math.hypot(
                        controlled_player.centerx - point.centerx,
                        controlled_player.centery - point.centery,
                    ),
                )
                dx = magnet_target.centerx - point.centerx
                dy = magnet_target.centery - point.centery
                distance = math.hypot(dx, dy)
                if 0 < distance < 210:
                    pull = min(150 * dt, distance)
                    point.x += round(dx / distance * pull)
                    point.y += round(dy / distance * pull)
            pygame.draw.circle(SCREEN, theme_colors["point"], point.center, 9)
            pygame.draw.circle(SCREEN, theme_colors["point_outline"], point.center, 5)
            collector = next(
                (player_index for player_index, controlled_player, _, _ in active_players
                 if controlled_player.colliderect(point)),
                None,
            )
            if collector is not None:
                points.remove(point)
                if current_time - combo_last_pickup <= 2.5:
                    combo_count += 1
                else:
                    combo_count = 1
                combo_last_pickup = current_time
                combo_bonus = 1 if combo_count % 5 == 0 else 0
                points_awarded = (
                    (2 if round_has_modifier("bonus_points") else 1) + combo_bonus
                )
                score += points_awarded
                update_player_profile(collector, points=points_awarded)
                if two_player_mode:
                    player_match_scores[collector - 1] += points_awarded
                update_player_stat("points_collected", 1)
                best_score_this_round = max(best_score_this_round, score)
                if score > best_score:
                    best_score = score
                spawn_particles(point.center, theme_colors["point"], 8)
                update_daily_missions(points=points_awarded)
                update_daily_challenge(points=1)
                replacement = generate_point()
                points.append(replacement)

        if (not two_player_mode and not midround_heart_spawned and not midround_heart_resolved
                and score >= max(1, (target_score + 1) // 2)):
            midround_heart_pickup = generate_midround_heart()
            midround_heart_spawned = True

        if midround_heart_pickup is not None:
            SCREEN.blit(HEART_GLOW_IMAGE, HEART_GLOW_IMAGE.get_rect(center=midround_heart_pickup.center))
            SCREEN.blit(HEART_IMAGE, HEART_IMAGE.get_rect(center=midround_heart_pickup.center))
            heart_collector = next(
                (
                    player_index for player_index in range(1, player_count + 1)
                    if player_healths[player_index - 1] > 0
                    and player_rects[player_index - 1].colliderect(midround_heart_pickup)
                ),
                None,
            )
            if heart_collector is not None:
                collect_midround_heart(heart_collector)

        # الدرع
        if (shield_circle is None and not daily_challenge_rule_active("no_shield")
                and not round_has_modifier("no_shield")
                and current_time - last_shield_time >= SHIELD_SPAWN_INTERVAL):
            shield_circle = generate_shield()
            last_shield_time = current_time

        if shield_circle is not None:
            SCREEN.blit(SHIELD_IMAGE, SHIELD_IMAGE.get_rect(center=shield_circle.center))
            if any(controlled_player.colliderect(shield_circle)
                   for controlled_player in player_collision_rects):
                if (not daily_challenge_rule_active("no_shield")
                        and not round_has_modifier("no_shield")):
                    shield_active = True
                    shield_start = time.time()
                    shield_duration = SHIELD_BASE_DURATION + shield_upgrade_level
                    spawn_particles(shield_circle.center, (190, 130, 255), 12)
                shield_circle = None

        if shield_active:
            elapsed = time.time() - shield_start
            if elapsed >= shield_duration:
                shield_active = False

        # التجميد
        if freeze_circle is None and current_time - last_freeze_time >= FREEZE_SPAWN_INTERVAL:
            freeze_circle = generate_freeze()
            last_freeze_time = current_time

        if freeze_circle is not None:
            SCREEN.blit(FREEZE_IMAGE, FREEZE_IMAGE.get_rect(center=freeze_circle.center))
            if any(controlled_player.colliderect(freeze_circle)
                   for controlled_player in player_collision_rects):
                freeze_active = True
                freeze_start = time.time()
                spawn_particles(freeze_circle.center, (120, 220, 255), 12)
                freeze_circle = None

        if freeze_active:
            elapsed = time.time() - freeze_start
            if elapsed > 4:
                freeze_active = False

        if special_pickup is None and current_time - last_special_pickup_time >= SPECIAL_PICKUP_INTERVAL:
            special_pickup = generate_special_pickup(
                allow_magnet=round_collects_points(current_round),
            )
            last_special_pickup_time = current_time

        if special_pickup is not None:
            pickup_rect, pickup_type = special_pickup
            pickup_colors = {
                "heart": (255, 90, 125),
                "magnet": (90, 190, 245),
                "slow": (135, 205, 255),
            }
            pickup_color = pickup_colors[pickup_type]
            pygame.draw.circle(SCREEN, pickup_color, pickup_rect.center, 18)
            pygame.draw.circle(SCREEN, (245, 250, 255), pickup_rect.center, 18, 2)
            if pickup_type == "heart":
                SCREEN.blit(HEART_IMAGE, HEART_IMAGE.get_rect(center=pickup_rect.center))
            elif pickup_type == "magnet":
                pygame.draw.arc(SCREEN, (255, 255, 255), pickup_rect.inflate(-12, -8), 0.4, 5.9, 3)
                pygame.draw.line(SCREEN, (255, 255, 255),
                                 (pickup_rect.centerx - 6, pickup_rect.centery + 3),
                                 (pickup_rect.centerx - 6, pickup_rect.centery + 9), 3)
                pygame.draw.line(SCREEN, (255, 255, 255),
                                 (pickup_rect.centerx + 6, pickup_rect.centery + 3),
                                 (pickup_rect.centerx + 6, pickup_rect.centery + 9), 3)
            else:
                pygame.draw.circle(SCREEN, (255, 255, 255), pickup_rect.center, 9, 2)
                pygame.draw.line(SCREEN, (255, 255, 255), pickup_rect.center,
                                 (pickup_rect.centerx, pickup_rect.centery - 6), 2)
                pygame.draw.line(SCREEN, (255, 255, 255), pickup_rect.center,
                                 (pickup_rect.centerx + 5, pickup_rect.centery + 3), 2)
            pickup_player_index = next(
                (player_index for player_index, controlled_player, _, _ in active_players
                 if controlled_player.colliderect(pickup_rect)),
                None,
            )
            if pickup_player_index is not None:
                if pickup_type == "heart":
                    player_slot = pickup_player_index - 1
                    player_healths[player_slot] = min(
                        MAX_PLAYER_HEALTH, player_healths[player_slot] + 1,
                    )
                    player_health_caps[player_slot] = max(
                        player_health_caps[player_slot], player_healths[player_slot],
                    )
                elif pickup_type == "magnet" and round_collects_points(current_round):
                    magnet_until = current_time + MAGNET_DURATION + (2 if globals().get("equipped_skin") == "fox" else 0)

                else:
                    slow_enemies_until = current_time + SLOW_ENEMIES_DURATION
                spawn_particles(pickup_rect.center, pickup_color, 14)
                special_pickup = None

        remaining_projectiles = []
        # الأعداء
        slowed_enemies = current_time < slow_enemies_until
        for enemy in enemies[:]:
            style = enemy_styles[id(enemy)]
            enemy_id = id(enemy)
            enemy_target = min(
                player_collision_rects,
                key=lambda controlled_player: math.hypot(
                    enemy.centerx - controlled_player.centerx,
                    enemy.centery - controlled_player.centery,
                ),
            )
            if not freeze_active:
                current_enemy_speed = enemy_speed(style, slowed_enemies)
                if style == "jumper":
                    move_jumper(enemy, enemy_target, current_enemy_speed, current_time)
                elif style == "robot":
                    dx = enemy_target.centerx - enemy.centerx
                    dy = enemy_target.centery - enemy.centery
                    distance = math.hypot(dx, dy)
                    if distance:
                        move_enemy_axis(
                            enemy, "x", dx / distance, current_enemy_speed,
                        )
                        move_enemy_axis(
                            enemy, "y", dy / distance, current_enemy_speed,
                        )
                else:
                    chase(enemy, enemy_target, current_enemy_speed)

            if not freeze_active and not any(
                enemy.colliderect(controlled_player)
                for controlled_player in player_collision_rects
            ):
                distance_to_player = math.hypot(
                    enemy.centerx - enemy_target.centerx,
                    enemy.centery - enemy_target.centery,
                )
                if 35 < distance_to_player < 58 and enemy_id not in enemy_proximity:
                    enemy_proximity.add(enemy_id)
                    update_player_stat("enemies_evaded", 1)
            visible = enemy_is_visible(style, current_time)
            if visible:
                draw_enemy(SCREEN, enemy, style, current_time)
                if style == "boss":
                    draw_boss_health(SCREEN, enemy, enemy_health[enemy_id])

            if visible:
                for player_index, controlled_player, _, _ in active_players:
                    collision_key = (enemy_id, player_index)
                    touching_enemy = controlled_player.colliderect(enemy)
                    if style == "boss" and (not touching_enemy or not shield_active):
                        boss_contact_started.pop(collision_key, None)
                    if not touching_enemy:
                        enemy_collision_frames[collision_key] = 0
                        continue
                    if (safe_zone_rect is not None
                            and safe_zone_rect.colliderect(controlled_player)
                            and not shield_active):
                        enemy_collision_frames[collision_key] = 0
                        boss_contact_started.pop(collision_key, None)
                        continue
                    if shield_active:
                        enemy_collision_frames[collision_key] = 0
                        if style == "boss":
                            contact_started = boss_contact_started.setdefault(
                                collision_key, current_time,
                            )
                            if current_time - contact_started < 2:
                                continue
                            boss_contact_started[collision_key] = current_time
                            enemy_health[enemy_id] -= 1
                            spawn_particles(enemy.center, (210, 135, 255), 12)
                            if enemy_health[enemy_id] <= 0:
                                enemies.remove(enemy)
                                enemy_styles.pop(enemy_id)
                                enemy_health.pop(enemy_id)
                                enemy_motion_remainders.pop(enemy_id, None)
                                boss_contact_started.pop((enemy_id, 1), None)
                                boss_contact_started.pop((enemy_id, 2), None)
                                enemy_collision_frames.pop((enemy_id, 1), None)
                                enemy_collision_frames.pop((enemy_id, 2), None)
                                enemy_proximity.discard(enemy_id)
                                spawn_particles(enemy.center, (255, 215, 100), 22)
                                save_progress(current_round, target_score, time_limit, completed_rounds)
                        if enemy not in enemies:
                            break
                        continue

                    if freeze_active:
                        enemy_collision_frames[collision_key] = 0
                        continue

                    hit_until = player_hit_untils[player_index - 1]
                    if current_time < hit_until:
                        enemy_collision_frames[collision_key] = 0
                        continue
                    enemy_collision_frames[collision_key] = (
                        enemy_collision_frames.get(collision_key, 0) + 1
                    )
                    if enemy_collision_frames[collision_key] < COLLISION_FRAMES_REQUIRED:
                        continue

                    enemy_collision_frames[collision_key] = 0
                    screen_shake_until = current_time + 0.24
                    screen_shake_intensity = 5
                    spawn_particles(controlled_player.center, (255, 85, 110), 16)
                    health_index = player_index - 1
                    player_healths[health_index] = max(0, player_healths[health_index] - 1)
                    player_hit_untils[health_index] = current_time + PLAYER_HIT_INVULNERABILITY
                    player_is_dead = player_healths[health_index] == 0
                    if player_is_dead:
                        for pointer_id, controlled_index in list(joystick_pointer_players.items()):
                            if controlled_index == player_index:
                                joystick_pointer_players.pop(pointer_id, None)
                        reset_joystick(player_index)
                        play_death_sound()
                        if not two_player_mode:
                            settle_midround_heart()
                            game_over = True
                            game_started = False
                        elif sum(health > 0 for health in player_healths[:player_count]) == 0:
                            finish_competitive_match()
                        break
            else:
                for player_index, _, _, _ in active_players:
                    enemy_collision_frames[(enemy_id, player_index)] = 0
            if game_over or competitive_match_finished:
                break

        if round_hazard_rect is not None and not shield_active:
            for player_index, controlled_player, _, _ in active_players:
                health_index = player_index - 1
                if (not controlled_player.colliderect(round_hazard_rect)
                        or current_time < player_hit_untils[health_index]):
                    continue
                player_healths[health_index] = max(0, player_healths[health_index] - 1)
                player_hit_untils[health_index] = current_time + PLAYER_HIT_INVULNERABILITY
                screen_shake_until = current_time + 0.24
                screen_shake_intensity = 5
                spawn_particles(controlled_player.center, (255, 85, 110), 16)
                if player_healths[health_index] == 0:
                    reset_joystick(player_index)
                    play_death_sound()
                    if not two_player_mode:
                            settle_midround_heart()
                            game_over = True
                            game_started = False
                    elif sum(health > 0 for health in player_healths[:player_count]) == 0:
                            finish_competitive_match()
                    break


        if round_variant(current_round)["objective"] == "waves":
            while round_elapsed >= round_next_wave_at:
                round_waves_completed += 1
                if round_waves_completed >= round_objective_goal(current_round):
                    break
                round_wave_number += 1
                spawn_round_wave(current_round, round_wave_number)
                round_next_wave_at += 10
            if round_waves_completed >= round_objective_goal(current_round):
                round_next_wave_at = float("inf")

        if two_player_mode and sum(
            health > 0 for health in player_healths[:player_count]
        ) == 0 and not competitive_match_finished:
            finish_competitive_match()

        if (
            any(hit_until > current_time for hit_until in player_hit_untils[:player_count])
            and int(current_time * 12) % 2 == 0
        ):
            SCREEN.blit(DAMAGE_FLASH, (0, 0))
        update_particles(SCREEN, dt)
        daily_survival_update_elapsed += dt
        if daily_survival_update_elapsed >= 1:
            survival_delta = daily_survival_update_elapsed
            daily_survival_update_elapsed = 0.0
            update_daily_missions(survive_seconds=survival_delta)
            update_daily_challenge(survive_seconds=survival_delta)
        update_player_stat("play_seconds", dt)
        if game_over and not two_player_mode and round_gold_earned:
            discard_round_gold_earnings()
        stats_save_elapsed += dt
        if stats_save_elapsed >= 30:
            stats_save_elapsed %= 30
            save_progress(current_round, target_score, time_limit, completed_rounds)

        elapsed_time = int((time.time() - start_time) * GAME_TIME_SCALE)
        remaining_time = time_limit - elapsed_time

        round_objective = (
            ROOM_OBJECTIVES[room_settings["objective_idx"]][0]
            if custom_room_active
            else round_variant(current_round)["objective"]
        )
        objective_goal = round_objective_goal(current_round)
        objective_complete = (
            (round_objective == "score" and score >= target_score)
            or (round_objective == "waves"
                and round_waves_completed >= objective_goal)
        )
        competitive_objective_complete = (
            (round_objective == "score"
             and max(player_match_scores[:player_count], default=0) >= target_score)
            or (round_objective == "waves"
                and round_waves_completed >= objective_goal)
        )
        if (two_player_mode and competitive_objective_complete
                and not competitive_match_finished):
            finish_competitive_match()
        if two_player_mode and remaining_time <= 0 and not competitive_match_finished:
            finish_competitive_match()
        elif not two_player_mode and remaining_time <= 0 and not game_over:
            if round_objective == "survive" or objective_complete:
                settle_midround_heart()
                record_round_win()
                record_round_time()
                round_won = True
                game_started = False
                save_progress(current_round, target_score, time_limit, completed_rounds)
            else:
                settle_midround_heart()
                game_over = True
                game_started = False
                discard_round_gold_earnings()
                play_death_sound()

        if not two_player_mode and objective_complete and not game_over:
            settle_midround_heart()
            record_round_win()
            record_round_time()
            round_won = True
            game_started = False
            save_progress(current_round, target_score, time_limit, completed_rounds)

        if not two_player_mode:
            player_name_text = render_fit_text(
                f"الاسم: {settings['player_names']['1']}",
                (180, 218, 234), 390, 24, 19, True,
            )
            SCREEN.blit(player_name_text, (20, 15))
            if round_collects_points(current_round):
                points_text = MED_FONT.render(
                    arabic_text(f"النقاط: {score}/{target_score}"), True, (255, 255, 255),
                )
                SCREEN.blit(points_text, (20, 42))

            objective_status = round_objective_description(current_round)
            if round_objective == "waves":
                objective_status += (
                    f": {round_waves_completed}/{objective_goal}"
                )
            objective_text = render_fit_text(
                objective_status, theme_colors["accent"], WIDTH - 40, 24, 18,
            )
            SCREEN.blit(objective_text, (20, 76))

            time_text = MED_FONT.render(
                arabic_text(f"الوقت: {remaining_time}"), True, (255, 255, 255),
            )
            SCREEN.blit(time_text, (20, 108))

            enemy_text = MED_FONT.render(
                arabic_text(f"الأعداء: {len(enemies)}"), True, (255, 255, 255),
            )
            SCREEN.blit(enemy_text, (20, 140))

            SCREEN.blit(HEART_IMAGE, (20, 176))
            health_text = MED_FONT.render(
                f"x {player_healths[0]}", True, (255, 235, 240),
            )
            SCREEN.blit(health_text, (62, 177))

        active_statuses = []
        if combo_count >= 2 and current_time - combo_last_pickup <= 2.5:
            active_statuses.append((f"كومبو ×{combo_count}", theme_colors["point"]))
        if shield_active:
            shield_remaining = max(0, shield_duration - int(time.time() - shield_start))
            active_statuses.append((f"الدرع: {shield_remaining}s", (180, 130, 255)))
        if freeze_active:
            freeze_remaining = max(0, 4 - int(time.time() - freeze_start))
            active_statuses.append((f"التجميد: {freeze_remaining}s", (80, 190, 255)))
        if speed_boost_active:
            boost_remaining = max(0, SPEED_BOOST_DURATION - int(time.time() - speed_boost_start))
            active_statuses.append((f"التسريع: {boost_remaining}s", (100, 235, 190)))
        if round_collects_points(current_round) and current_time < magnet_until:
            magnet_remaining = max(0, int(magnet_until - current_time))
            active_statuses.append((f"المغناطيس: {magnet_remaining}s", (100, 200, 255)))
        if current_time < slow_enemies_until:
            slow_remaining = max(0, int(slow_enemies_until - current_time))
            active_statuses.append((f"إبطاء الأعداء: {slow_remaining}s", (150, 220, 255)))

        status_max_width = min(
            general_hud.width if two_player_mode else 320,
            WIDTH - 40,
        )
        for status_index, (status_text, status_color) in enumerate(active_statuses):
            status_column_width = (
                (status_max_width - 10) // 2 if two_player_mode else status_max_width
            )
            status_label = render_fit_text(
                status_text, status_color, status_column_width - 16, 22, 18,
            )
            status_column = status_index % 2 if two_player_mode else 0
            status_row = status_index // 2 if two_player_mode else status_index
            status_x = (
                general_hud.left + status_column * (status_column_width + 10)
                if two_player_mode
                else WIDTH - 24 - status_label.get_width() - 20
            )
            status_y = 82 + status_row * 34
            status_badge = pygame.Rect(
                status_x,
                status_y,
                status_column_width if two_player_mode else status_label.get_width() + 20,
                30,
            )
            pygame.draw.rect(SCREEN, (8, 15, 28), status_badge, border_radius=12)
            pygame.draw.rect(SCREEN, status_color, status_badge, 1, border_radius=12)
            SCREEN.blit(
                status_label,
                (status_badge.centerx - status_label.get_width() // 2,
                 status_badge.centery - status_label.get_height() // 2),
            )

        draw_button(SCREEN, "القائمة", menu_button_rect, (70, 70, 70), font_size=17)
        shield_available = (
            purchased_shields > 0
            and not daily_challenge_rule_active("no_shield")
            and not round_has_modifier("no_shield")
        )
        shield_button_color = (
            theme_colors["accent"] if shield_available else (65, 70, 78)
        )
        if two_player_mode:
            player_action_buttons = (
                (two_player_shield_use_button_rect, 1),
                (two_player_player_two_shield_use_button_rect, 2),
            )
        else:
            player_action_buttons = (
                (shield_use_button_rect, 1),
            )
        for shield_button, player_index in player_action_buttons:
            draw_game_action_button(
                SCREEN, ["درع", str(purchased_shields)], shield_button,
                shield_button_color,
            )
            if two_player_mode:
                player_label = SMALL_FONT.render(f"P{player_index}", True, (235, 243, 246))
                player_label_rect = player_label.get_rect(
                    center=(
                        shield_button.centerx,
                        shield_button.top - 13,
                    ),
                )
                SCREEN.blit(player_label, player_label_rect)
        draw_settings_icon(SCREEN, game_settings_button_rect)

    elif not game_started and not game_over and not round_won:
        draw_background(SCREEN)
        menu_panel = pygame.Rect(0, 0, WIDTH, HEIGHT)
        pygame.draw.rect(SCREEN, (12, 21, 36), menu_panel)
        draw_theme_frame(SCREEN, menu_panel, 2, 0)

        title = TITLE_FONT.render(arabic_text("لعبة الهروب"), True, (255,255,255))
        title_y = menu_panel.top + 14
        SCREEN.blit(title, (menu_panel.centerx - title.get_width() // 2, title_y))

        info_card = pygame.Rect(menu_panel.left + 40, menu_panel.top + 90, menu_panel.width - 80, 56)

        info = render_fit_text(
            f"الجولة الحالية: {current_round}", (235, 240, 245),
            info_card.width - 190, info_card.height - 12, 25,
        )
        SCREEN.blit(info, (info_card.centerx - info.get_width() // 2, info_card.top + 12))
        gold_badge = pygame.Rect(info_card.right - 154, info_card.top + 11, 138, 42)
        gold_badge.centery = info_card.centery
        pygame.draw.rect(SCREEN, (61, 48, 25), gold_badge, border_radius=14)
        pygame.draw.rect(SCREEN, (184, 142, 56), gold_badge, 1, border_radius=14)
        coin_center = (gold_badge.left + 22, gold_badge.centery)
        pygame.draw.circle(SCREEN, (255, 205, 70), coin_center, 12)
        pygame.draw.circle(SCREEN, (255, 238, 170), coin_center, 12, 2)
        pygame.draw.circle(SCREEN, (190, 130, 35), coin_center, 4)
        gold_text_area = pygame.Rect(
            gold_badge.left + 40, gold_badge.top + 5,
            gold_badge.width - 48, gold_badge.height - 10,
        )
        gold_text = render_fit_text(
            f"ذهب: {gold_coins}", (255, 235, 180),
            gold_text_area.width, gold_text_area.height, 20,
        )
        SCREEN.blit(
            gold_text,
            (gold_text_area.centerx - gold_text.get_width() // 2,
             gold_text_area.centery - gold_text.get_height() // 2),
        )
        mode_label = "الوضع: لاعبان" if two_player_mode else "الوضع: لاعب واحد"
        draw_button(SCREEN, mode_label, menu_mode_button_rect, (54, 91, 126), font_size=18)
        if two_player_mode:
            room_btn_col = (165, 120, 42) if room_cards > 0 else (65, 72, 82)
            draw_button(SCREEN, f"روم خاص ({room_cards})", menu_room_button_rect, room_btn_col, font_size=16)

        variant_card = pygame.Rect(menu_panel.left + 40, menu_mode_button_rect.bottom + 8, menu_panel.width - 80, 40)
        menu_theme_colors = BACKGROUND_THEMES.get(current_background_theme, BACKGROUND_THEMES["midnight"])
        pygame.draw.rect(SCREEN, (17, 40, 50), variant_card, border_radius=12)
        pygame.draw.rect(SCREEN, menu_theme_colors["accent"], variant_card, 1, border_radius=12)
        variant_text = render_fit_text(round_objective_description(current_round), menu_theme_colors["accent"], variant_card.width - 20, variant_card.height - 8, 18)
        SCREEN.blit(variant_text, (variant_card.centerx - variant_text.get_width() // 2, variant_card.centery - variant_text.get_height() // 2))

        completed_panel = completed_panel_rect
        completed_label = render_fit_text(
            "الجولات المنجزة:", (220, 220, 220),
            completed_panel.width - 32, 28, 20,
        )
        SCREEN.blit(completed_label, (completed_panel.centerx - completed_label.get_width() // 2, completed_panel.top + 8))

        if completed_rounds:
            page_count = max(1, (len(completed_rounds) + ROUNDS_PER_PAGE - 1) // ROUNDS_PER_PAGE)
            rounds_page = min(rounds_page, page_count - 1)
            page_start = rounds_page * ROUNDS_PER_PAGE
            visible_rounds = completed_rounds[page_start:page_start + ROUNDS_PER_PAGE]
            badge_width = (len(visible_rounds) - 1) * 52 + 38
            x_start = completed_panel.centerx - badge_width // 2
            for i, round_num in enumerate(visible_rounds):
                badge = pygame.Rect(x_start + i * 52, completed_panel.top + 34, 38, 38)
                pygame.draw.rect(SCREEN, (80, 180, 120), badge, border_radius=10)
                if round_num == selected_replay_round:
                    pygame.draw.rect(SCREEN, (255, 210, 95), badge.inflate(6, 6), 2, border_radius=12)
                badge_text = render_fit_text(
                    str(round_num), (255, 255, 255), badge.width - 8, badge.height - 8, 20,
                )
                SCREEN.blit(badge_text, (badge.centerx - badge_text.get_width() // 2, badge.centery - badge_text.get_height() // 2))
            if page_count > 1:
                draw_round_arrow(SCREEN, rounds_previous_rect, "left", rounds_page > 0)
                draw_round_arrow(SCREEN, rounds_next_rect, "right", rounds_page < page_count - 1)
                page_text = render_fit_text(
                    f"{rounds_page + 1} / {page_count}", (170, 195, 205),
                    completed_panel.width - 48, 24, 20,
                )
                SCREEN.blit(page_text, (completed_panel.centerx - page_text.get_width() // 2,
                                        completed_panel.top + 74))
        else:
            empty_text = render_fit_text(
                "لا توجد جولات مكتملة بعد", (180, 200, 220),
                completed_panel.width - 64, 30, 20,
            )
            SCREEN.blit(empty_text, (completed_panel.centerx - empty_text.get_width() // 2, completed_panel.top + 48))

        start_label = f"إعادة الجولة {selected_replay_round}" if selected_replay_round is not None else "ابدأ اللعبة"
        draw_button(SCREEN, start_label, start_button_rect, (0, 140, 80), font_size=28)
        draw_button(SCREEN, "المزيد", menu_more_button_rect, (54, 91, 126), font_size=19)
        draw_settings_icon(SCREEN, settings_button_rect)

    elif game_over:
        draw_result_screen(False)

    elif round_won:
        draw_result_screen(True)

    if show_main_options:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        SCREEN.blit(overlay, (0, 0))
        panel = main_options_panel_rect
        pygame.draw.rect(SCREEN, (17, 29, 43), panel, border_radius=20)
        draw_theme_frame(SCREEN, panel, 2, 20)
        draw_button(SCREEN, "X", main_options_close_rect, (145, 55, 66), font_size=16)
        title = render_fit_text(
            "المزيد", (255, 239, 195), panel.width - 100, 36, 28, True,
        )
        SCREEN.blit(title, (panel.centerx - title.get_width() // 2, panel.top + 13))
        option_colors = {
            "shop": (54, 91, 126),
            "missions": (31, 98, 91),
            "rewards": (114, 88, 42),
            "statistics": (55, 102, 150),
            "challenge": (37, 135, 105) if daily_challenge.get("active") else (54, 91, 126),
            "profiles": (54, 91, 126),
            "difficulty": (114, 76, 151),
            "exit": (145, 55, 66),
        }
        for option, rect in main_options_button_rects.items():
            label = (
                f"الصعوبة: {DIFFICULTY_LABELS[current_difficulty]}"
                if option == "difficulty"
                else main_options_labels[option]
            )
            draw_button(
                SCREEN, label, rect, option_colors[option],
                font_size=16 if option in ("challenge", "difficulty") else 18,
            )

    if show_shop:
        draw_shop_panel(SCREEN)

    if show_room_setup:
        draw_room_setup_panel(SCREEN)

    if show_daily_rewards:
        draw_daily_rewards_panel(SCREEN)

    if show_daily_missions:
        draw_daily_missions_panel(SCREEN)

    if show_statistics:
        draw_statistics_panel(SCREEN)

    if show_daily_challenge:
        draw_daily_challenge_panel(SCREEN)

    if show_settings:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        SCREEN.blit(overlay, (0, 0))

        panel = settings_panel_rect
        pygame.draw.rect(SCREEN, (12, 22, 35), panel, border_radius=22)
        draw_theme_frame(SCREEN, panel, 2, 22)

        draw_button(SCREEN, "X", settings_close_rect, (145, 55, 66), font_size=16)

        title = render_fit_text(
            "الإعدادات", (255, 255, 255), panel.width - 120, 38, 34, True,
        )
        SCREEN.blit(title, (panel.centerx - title.get_width() // 2, panel.top + 7))

        theme_label = SMALL_FONT.render(arabic_text("اختر المظهر"), True, (175, 205, 215))
        SCREEN.blit(theme_label, (panel.centerx - theme_label.get_width() // 2, panel.top + 58))
        for theme, rect in settings_theme_rects.items():
            draw_button(
                SCREEN,
                "داكن" if theme == "midnight" else "أبيض",
                rect,
                (43, 57, 72) if theme != current_background_theme else (32, 132, 112),
                font_size=16,
            )

        for divider_y in (
            settings_sfx_slider_rect.top - 16,
            settings_language_y - 18,
            settings_control_y - 16,
        ):
            pygame.draw.line(
                SCREEN, (52, 72, 89),
                (panel.left + 28, divider_y),
                (panel.right - 28, divider_y), 1,
            )

        sfx_label = SMALL_FONT.render(arabic_text("مؤثرات الصوت"), True, (220, 230, 238))
        music_label = SMALL_FONT.render(arabic_text("الموسيقى"), True, (220, 230, 238))
        SCREEN.blit(sfx_label, (panel.left + 30, settings_sfx_slider_rect.centery - sfx_label.get_height() // 2))
        SCREEN.blit(music_label, (panel.left + 30, settings_music_slider_rect.centery - music_label.get_height() // 2))
        for slider_rect, volume in (
            (settings_sfx_slider_rect, SFX_VOLUME),
            (settings_music_slider_rect, MUSIC_VOLUME),
        ):
            pygame.draw.rect(SCREEN, (60, 75, 91), slider_rect, border_radius=5)
            filled_width = round(slider_rect.width * volume)
            if filled_width:
                pygame.draw.rect(
                    SCREEN, (52, 194, 166),
                    pygame.Rect(slider_rect.left, slider_rect.top, filled_width, slider_rect.height),
                    border_radius=5,
                )
            knob_x = slider_rect.left + filled_width
            pygame.draw.circle(SCREEN, (245, 249, 252), (knob_x, slider_rect.centery), 10)
            pygame.draw.circle(SCREEN, (52, 194, 166), (knob_x, slider_rect.centery), 5)
            value_label = SMALL_FONT.render(f"{round(volume * 100)}%", True, (210, 220, 230))
            SCREEN.blit(value_label, (slider_rect.right + 12,
                                      slider_rect.centery - value_label.get_height() // 2))

        language_label = SMALL_FONT.render(arabic_text("اللغة"), True, (175, 205, 215))
        language_label_y = next(iter(settings_language_rects.values())).centery
        SCREEN.blit(language_label, (panel.left + 30,
                                     language_label_y - language_label.get_height() // 2))
        for language_code, rect in settings_language_rects.items():
            draw_button(
                SCREEN,
                LANGUAGES[language_code],
                rect,
                (32, 132, 112) if language_code == current_language else (43, 57, 72),
                font_size=16,
            )

        draw_button(
            SCREEN,
            "التحكم: أسهم" if control_style == "arrows" else "التحكم: أنالوج",
            settings_control_style_rect,
            (32, 132, 112) if control_style == "analog" else (43, 57, 72),
            font_size=16,
        )
        draw_button(
            SCREEN, "تعديل مكان وحجم الأزرار",
            settings_control_layout_rect, (55, 96, 123), font_size=18,
        )

        draw_button(SCREEN, "متابعة", settings_resume_rect, (20, 130, 80), font_size=22)
        draw_button(SCREEN, "خروج", settings_exit_rect, (180, 40, 40), font_size=22)
        if editing_controls:
            draw_control_layout_editor(SCREEN)

    if show_player_profiles:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        SCREEN.blit(overlay, (0, 0))
        panel = player_profiles_panel_rect
        pygame.draw.rect(SCREEN, (5, 8, 14), panel.move(0, 7), border_radius=24)
        pygame.draw.rect(SCREEN, (18, 30, 43), panel, border_radius=24)
        draw_theme_frame(SCREEN, panel, 2, 24)
        draw_button(SCREEN, "X", player_profiles_close_rect, (145, 55, 66), font_size=16)
        title = render_fit_text(
            "ملفات اللاعبين", (255, 239, 195), panel.width - 100, 44, 34, True,
        )
        SCREEN.blit(title, (panel.centerx - title.get_width() // 2, panel.top + 22))

        profile_indices = range(1, 3)
        for player_index in profile_indices:
            card = player_profile_card_rect(player_index)
            pygame.draw.rect(SCREEN, (25, 40, 55), card, border_radius=18)
            draw_theme_frame(SCREEN, card, 1, 18)
            profile_name = settings["player_names"][str(player_index)]
            label = render_fit_text(
                f"اللاعب {player_index}", (200, 220, 232),
                card.width - 32, 28, 22, True,
            )
            SCREEN.blit(label, (card.centerx - label.get_width() // 2, card.top + 24))

            name_rect = player_profile_name_rect(player_index)
            pygame.draw.rect(
                SCREEN,
                (35, 91, 83) if active_player_name == player_index else (13, 23, 35),
                name_rect,
                border_radius=12,
            )
            draw_theme_frame(SCREEN, name_rect, 1, 12)
            displayed_name = (
                player_name_draft if active_player_name == player_index else profile_name
            )
            name_text = render_fit_text(
                displayed_name or "...", (250, 250, 250),
                name_rect.width - 20, name_rect.height - 10, 21, True,
            )
            SCREEN.blit(
                name_text,
                (name_rect.centerx - name_text.get_width() // 2,
                 name_rect.centery - name_text.get_height() // 2),
            )

            profile = player_profiles[str(player_index)]
            play_minutes = int(profile["play_seconds"] // 60)
            play_seconds = int(profile["play_seconds"] % 60)
            profile_lines = (
                f"النقاط: {profile['points']} | الفوز: {profile['round_wins']}",
                f"اللعب: {play_minutes}د {play_seconds}ث | أعلى مرحلة: {profile['highest_round']}",
            )
            for line_index, line in enumerate(profile_lines):
                line_text = render_fit_text(
                    line, (225, 235, 242), card.width - 36, 28, 18,
                )
                SCREEN.blit(
                    line_text,
                    (card.centerx - line_text.get_width() // 2,
                     card.top + 143 + line_index * 38),
                )

        hint = render_fit_text(
            "اضغط على الاسم لتعديله" if active_player_name is None
            else "اكتب الاسم ثم اضغط Enter",
            (165, 190, 205), panel.width - 60, 26, 17,
        )
        SCREEN.blit(hint, (panel.centerx - hint.get_width() // 2, panel.bottom - 42))

    if round_won:
        update_victory_fireworks(SCREEN, dt)
    if screen_shake_until > time.time():
        shake_x = random.randint(-screen_shake_intensity, screen_shake_intensity)
        shake_y = random.randint(-screen_shake_intensity, screen_shake_intensity)
        SCREEN.scroll(shake_x, shake_y)
        if shake_x > 0:
            SCREEN.fill((10, 14, 28), pygame.Rect(0, 0, shake_x, HEIGHT))
        elif shake_x < 0:
            SCREEN.fill((10, 14, 28), pygame.Rect(WIDTH + shake_x, 0, -shake_x, HEIGHT))
        if shake_y > 0:
            SCREEN.fill((10, 14, 28), pygame.Rect(0, 0, WIDTH, shake_y))
        elif shake_y < 0:
            SCREEN.fill((10, 14, 28), pygame.Rect(0, HEIGHT + shake_y, WIDTH, -shake_y))

    fps_value = int(clock.get_fps())
    fps_color = BACKGROUND_THEMES.get(
        current_background_theme, BACKGROUND_THEMES["midnight"],
    )["accent"]
    fps_text = FPS_FONT.render(f"{fps_value} FPS", True, fps_color)
    if not (show_shop or show_daily_rewards or show_daily_missions
            or show_statistics or show_daily_challenge or show_settings
            or show_player_profiles):
        SCREEN.blit(fps_text, (WIDTH - fps_text.get_width() - 12, 10))

    pygame.display.flip()

save_progress(current_round, target_score, time_limit, completed_rounds)
pygame.quit()
sys.exit()




