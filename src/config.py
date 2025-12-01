WIDTH, HEIGHT = 1280, 720
FPS = 60

BOTTOM_FRACTION = 1 / 4  # bottom quarter is castle
ENEMY_SIZE = 40
BASE_ENEMY_SPEED = 40

GOLD_PER_KILL = 10
GOLD_PER_WAVE_CLEAR = 20

DEFENCE_STATS = {
    "archer": {
        "damage": 8,
        "range": 300,
        "cooldown": 0.4,
        "proj_speed": 450,
        "color": (255, 255, 0),
        "base_cost": 30,
        "crit_chance": 0.20,
        "crit_multiplier": 2.0,
        "shop_cost": 40,
        "max_hp": 50,
    },
    "cannon": {
        "damage": 25,
        "range": 220,
        "cooldown": 1.1,
        "proj_speed": 350,
        "color": (200, 200, 200),
        "base_cost": 50,
        "crit_chance": 0.20,
        "crit_multiplier": 2.0,
        "shop_cost": 80,
        "max_hp": 50,
    },
    "mage": {
        "damage": 12,
        "range": 280,
        "cooldown": 0.7,
        "proj_speed": 400,
        "color": (150, 80, 255),
        "base_cost": 40,
        "crit_chance": 0.20,
        "crit_multiplier": 2.0,
        "shop_cost": 100,
        "max_hp": 50,
    },
}

DEFENCE_TYPES = ["archer", "cannon", "mage"]
