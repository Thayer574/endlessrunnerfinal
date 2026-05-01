import pygame
import math
import random
from collections import deque


import pygame
import random
import math
import time
from collections import deque
pygame.init()
pygame.mixer.init()
pygame.mixer.music.load("WalkingNight.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(loops=-1)

# -----------------------
# Constants & Settings
# -----------------------
WIDTH, HEIGHT = 1000, 800
FPS = 60

PLAYER_SPEED = 260
PLAYER_RADIUS = 20
PLAYER_MAX_HEALTH = 100
PLAYER_BASE_HEALTH = 100  # Base health for percentage calculations
PLAYER_BULLET_SPEED = 700
PLAYER_FIRE_RATE = 0.75
PLAYER_BASE_FIRE_RATE = 0.75  # Base fire rate for calculations
# MELEE_RADIUS = 75 # Now a player stat
MELEE_COOLDOWN_BASE = 2.5  # Increased from 1.5 for balance
DASH_SPEED = 900
DASH_DURATION = 0.15
DASH_COOLDOWN_BASE = 3.5  # Increased from 2.0 for balance
PLAYER_HEALTH_REGEN_RATE = 1.0  # Health points regenerated per second

# Upgrade System Constants
UPGRADE_COST_BASE = 15
UPGRADE_COST_MULTIPLIER = 1.2

PREDICT_HISTORY = 12
PREDICT_INTERVAL = 1.4

ENEMY_SPAWN_PADDING = 30

WHITE = (245, 245, 245)
BLACK = (20, 20, 20)
RED = (220, 60, 60)
GREEN = (60, 200, 80)
BLUE = (60, 160, 220)
YELLOW = (230, 210, 80)
ORANGE = (255, 165, 0)
GREY = (140, 140, 140)
PURPLE = (160, 32, 240)
BRIGHT_ORANGE = (255, 100, 0)
NEON_GREEN = (57, 255, 20)
DARK_GREEN = (0, 100, 0)
PALE_PURPLE = (174, 164, 191)
DARK_GREY = (60, 60, 60)

# Prestige Colors
PRESTIGE_COLORS = [
    WHITE,   # Level 0
    GREEN    # Level 1 (Prestige)
]

# Prestige Requirements
PRESTIGE_LEVEL_REQ = 15

# Class Definitions
CLASS_DATA = {
    "Wizard": {
        "sprite_prefix": "wizard",
        "color": (100, 50, 150),  # Purple
        "description": "A ranged specialist with a powerful cross attack.",
        "base_hp": 100,         # Standard HP
        "base_fire_rate": 0.3  # Standard Fire Rate
    },
    "Hero": {
        "sprite_prefix": "hero",
        "color": (50, 100, 150),  # Blue
        "description": "A balanced fighter with good health and melee range.",
        "base_hp": 250,         # Reduced from 200
        "base_fire_rate": 0.5   # Increased delay from 0.4s
    },
    "Archmage": {
        "sprite_prefix": "archmage",
        "color": (60, 160, 220),  # Blue
        "description": "A master of arcane arts. Shoots a piercing beam and summons allies.",
        "base_hp": 60,
        "base_fire_rate": 0.02
    },
        "Electrician": {
        "sprite_prefix": "electrician",
        "color": (184, 134, 11),  # Darker Gold
        "description": "A master of electricity. Uses chain attacks and screen-wide red lightning.",
        "base_hp": 100,
        "base_fire_rate": 1.0
    }
}

