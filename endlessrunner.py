
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

# -----------------------
# Helper functions
# -----------------------

def lerp_color(color1, color2, t):
    return (
        int(color1[0] + (color2[0] - color1[0]) * t),
        int(color1[1] + (color2[1] - color1[1]) * t),
        int(color1[2] + (color2[2] - color1[2]) * t),
    )

def draw_health_bar(surface, x, y, current_hp, max_hp, dt):
    width = 240
    height = 18

    if not hasattr(draw_health_bar, "display_hp"):
        draw_health_bar.display_hp = current_hp

    draw_health_bar.display_hp += (current_hp - draw_health_bar.display_hp) * min(10 * dt, 1)
    hp_ratio = max(draw_health_bar.display_hp / max_hp, 0)

    t_clamped = clamp(hp_ratio, 0, 1)
    if t_clamped > 0.5:
        t = (t_clamped - 0.5) * 2
        color = lerp_color((245, 209, 43), (43, 245, 66), t)
    else:
        t = t_clamped * 2
        color = lerp_color((230, 57, 57), (245, 209, 43), t)

    if hp_ratio < 0.2:
        pulse = (math.sin(pygame.time.get_ticks() * 0.008) + 1) / 2
        color = lerp_color(color, (255, 255, 255), pulse * 0.25)

    pygame.draw.rect(surface, (40, 40, 40), (x - 2, y - 2, width + 4, height + 4), border_radius=4)
    pygame.draw.rect(surface, color, (x, y, width * hp_ratio, height), border_radius=4)

    font = pygame.font.SysFont(None, 24)
    hp_text = font.render(f"HP: {int(current_hp)} / {max_hp}", True, (230, 220, 200))
    surface.blit(hp_text, (x + width + 10, y - 2))

def draw_cooldown_bar(surface, x, y, cooldown_left, cooldown_max, label):
    width = 180
    height = 12

    ratio = 1 - min(cooldown_left / cooldown_max, 1)

    if ratio < 0.5:
        t = ratio * 2
        color = lerp_color((255, 40, 40), (255, 200, 40), t)
    else:
        t = (ratio - 0.5) * 2
        color = lerp_color((255, 200, 40), (40, 255, 40), t)

    pop_scale = 1.0
    if cooldown_left <= 0:
        pop = (math.sin(pygame.time.get_ticks() * 0.015) + 1) / 2
        pop_scale = 1 + pop * 0.05

    bar_width = width * ratio * pop_scale

    pygame.draw.rect(surface, (30, 30, 30), (x - 2, y - 2, width + 4, height + 4), border_radius=4)
    pygame.draw.rect(surface, color, (x, y, bar_width, height), border_radius=4)

    font = pygame.font.SysFont(None, 20)
    if cooldown_left <= 0:
        text = font.render(f"{label}: READY", True, (200, 255, 200))
    else:
        text = font.render(f"{label}: {cooldown_left:.1f}s", True, (230, 220, 200))

    surface.blit(text, (x + width + 10, y - 3))

def vec_from_angle(angle_radians):
    return pygame.math.Vector2(math.cos(angle_radians), math.sin(angle_radians))

def clamp(v, a, b):
    return max(a, min(b, v))

def normalize_safe(v):
    if v.length_squared() == 0:
        return pygame.math.Vector2(0, 0)
    return v.normalize()

def predict_future_position(history_deque, forward_time):
    if len(history_deque) < 2:
        return history_deque[-1][0] if history_deque else pygame.math.Vector2(0, 0)
    total_v = pygame.math.Vector2(0, 0)
    count = 0
    for i in range(1, len(history_deque)):
        p0, t0 = history_deque[i-1]
        p1, t1 = history_deque[i]
        dt = t1 - t0
        if dt <= 0:
            continue
        total_v += (p1 - p0) / dt
        count += 1
    if count == 0:
        return history_deque[-1][0]
    avg_v = total_v / count
    return history_deque[-1][0] + avg_v * forward_time

# -----------------------
# Pygame Entities
# -----------------------

def draw_laser(surface, start_pos, end_pos, color, thickness=2):
    pygame.draw.line(surface, color, start_pos, end_pos, thickness)
    # Add a glow effect
    glow_color = (min(255, color[0] + 50), min(255, color[1] + 50), min(255, color[2] + 50), 100)
    s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.line(s, glow_color, start_pos, end_pos, thickness + 4)
    surface.blit(s, (0, 0))

def draw_jagged_lightning(surface, start_pos, end_pos, color, thickness=2):
    dist = (end_pos - start_pos).length()
    if dist < 2: return
    points = [start_pos]
    num_segments = max(3, int(dist / 15))
    for i in range(1, num_segments):
        t = i / num_segments
        base_pos = start_pos + (end_pos - start_pos) * t
        offset = pygame.math.Vector2(random.uniform(-10, 10), random.uniform(-10, 10))
        points.append(base_pos + offset)
    points.append(end_pos)
    for i in range(len(points) - 1):
        pygame.draw.line(surface, color, points[i], points[i+1], thickness)

class DamagePopup:
    def __init__(self, pos, amount, color=(255, 255, 255), is_crit=False, enemy_id=None):
        self.pos = pygame.math.Vector2(pos)
        try:
            self.amount = round(float(amount))
        except (ValueError, TypeError):
            self.amount = amount
        self.color = color
        self.is_crit = is_crit
        self.enemy_id = enemy_id
        self.lifetime = 0.8  # Seconds
        self.max_lifetime = 0.8
        self.vel = pygame.math.Vector2(random.uniform(-20, 20), -40) # Float upwards slightly

    def update(self, dt):
        self.lifetime -= dt
        self.pos += self.vel * dt

    def draw(self, surface, font, crit_font):
        if self.lifetime <= 0: return
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        # Use larger font for crits
        use_font = crit_font if self.is_crit else font
        text_surf = use_font.render(str(self.amount), True, self.color)
        text_surf.set_alpha(alpha)
        surface.blit(text_surf, (self.pos.x - text_surf.get_width() // 2, self.pos.y - text_surf.get_height() // 2))

class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, vel, owner, damage=25, color=None, radius=5):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.owner = owner
        self.damage = damage
        self.radius = radius
        self.color = color if color else (YELLOW if owner == "player" else GREY)
        self.lifetime = 3.5
        self.hp = 1
        self.max_hp = 1
        self.is_friendly = (owner == "player")
        self.piercing = False
        self.hit_enemies = set()  # Track enemies hit to prevent double damage (especially for splits)

    def update(self, dt):
        self.pos += self.vel * dt
        self.velocity = self.vel # Keep velocity synced
        self.lifetime -= dt
        if (self.pos.x < -100 or self.pos.x > WIDTH+100 or self.pos.y < -100 or self.pos.y > HEIGHT+100 or self.lifetime <= 0):
            self.kill()

    def draw(self, surface):
        # Draw a small glow for special bullets
        if self.color != YELLOW and self.color != GREY:
            glow_surf = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color, 100), (self.radius * 2, self.radius * 2), self.radius * 2)
            surface.blit(glow_surf, (int(self.pos.x - self.radius * 2), int(self.pos.y - self.radius * 2)))
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
class TetherBullet(Bullet):
    def __init__(self, pos, vel, owner, damage, color, radius, parent):
        super().__init__(pos, vel, owner, damage, color, radius)
        self.parent = parent

    def on_hit_player(self, player, game):
        if self.parent in game.enemy_group:
            self.parent.is_tethering = True
            self.parent.tether_timer = 2.5 # Increased duration
            self.parent.tether_target_pos = player.pos # Direct reference to player pos for dynamic tether
            game.tether_haze_timer = 2.5
        self.kill()


class TriSplitBullet(Bullet):
    def __init__(self, pos, vel, owner, damage=25):
        # Big orb: 200% damage, larger radius
        super().__init__(pos, vel, owner, damage * 2.0, color=NEON_GREEN, radius=12)
        self.has_split = False
        self.split_delay = 0.5
        self.split_timer = 0
        self.hit_enemy_pos = None

    def on_hit(self, game, enemy_hit):
        if not self.has_split:
            self.has_split = True
            self.hit_enemy_pos = enemy_hit.pos.copy()
            self.split_timer = self.split_delay
            # Instead of splitting immediately, we start a timer.
            # The main game loop will handle the actual splitting.
            if hasattr(game, "pending_splits"):
                game.pending_splits.append(self)
            self.kill()

class HomingOrb(Bullet):
    def __init__(self, pos, owner, damage, target_enemy, color):
        # Wizard split projectiles: Pink/Purple theme
        super().__init__(pos, pygame.math.Vector2(0,0), owner, damage, color=(255, 100, 255), radius=8)
        self.target = target_enemy
        self.speed = PLAYER_BULLET_SPEED * 0.9
        self.turn_speed = 10  # Increased turn speed for better homing
        self.lifetime = 3.0
        self.spiral_angle = 0
        self.pulse_timer = 0

    def update(self, dt, enemies):
        self.spiral_angle += dt * 15
        self.pulse_timer += dt
        
        if self.target and self.target.hp > 0:
            dir_to_target = normalize_safe(self.target.pos - self.pos)
            # Apply homing force
            target_vel = dir_to_target * self.speed
            self.vel += (target_vel - self.vel) * self.turn_speed * dt
            if self.vel.length() > self.speed:
                self.vel = normalize_safe(self.vel) * self.speed
        else:
            # If target is dead, find a new one
            self.target = None
            min_dist = float('inf')
            for e in enemies:
                if not getattr(e, "is_friendly", False):
                    dist = (e.pos - self.pos).length()
                    if dist < min_dist:
                        min_dist = dist
                        self.target = e
            
            # If still no target, just move forward
            if not self.target and self.vel.length_squared() == 0:
                self.vel = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * self.speed

        super().update(dt)
        # Add special trail for split orbs
        if random.random() < 0.2:
            trail_color = random.choice([(255, 150, 255), (200, 100, 255)])
            self.trail_particles.extend(create_trail_particles(self.pos, trail_color, -self.vel * 0.1, count=1))

    def draw(self, surface):
        # Pulsing effect
        pulse = (math.sin(self.pulse_timer * 10) + 1) / 2
        current_radius = self.radius * (0.8 + 0.4 * pulse)
        
        # Draw spiral trail
        draw_spinning_rings(surface, self.pos, (255, 255, 255), current_radius * 1.5, self.spiral_angle, num_rings=1)
        
        # Draw main orb with glow
        glow_surf = pygame.Surface((int(current_radius * 4), int(current_radius * 4)), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color, 150), (int(current_radius * 2), int(current_radius * 2)), int(current_radius * 2))
        surface.blit(glow_surf, (int(self.pos.x - current_radius * 2), int(self.pos.y - current_radius * 2)))
        
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), int(current_radius))
        pygame.draw.circle(surface, (255, 255, 255), (int(self.pos.x), int(self.pos.y)), int(current_radius * 0.5))tart_pos).length() >= self.max_dist:
                self.returning = True
        else:
            # Return to player
            if self.player:
                dir_to_player = normalize_safe(self.player.pos - self.pos)
                self.vel = dir_to_player * PLAYER_BULLET_SPEED
                self.pos += self.vel * dt
                if (self.pos - self.player.pos).length() < 20:
                    self.kill()
            else:
                self.kill()

        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()

    def update(self, dt):
        if not self.returning:
            self.pos += self.vel * dt
            if (self.pos - self.start_pos).length() >= self.max_dist:
                self.returning = True
        else:
            # Return to player
            if self.player:
                dir_to_player = normalize_safe(self.player.pos - self.pos)
                self.vel = dir_to_player * PLAYER_BULLET_SPEED
                self.pos += self.vel * dt
                if (self.pos - self.player.pos).length() < 20:
                    self.kill()
            else:
                self.kill()

        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()

class Bomb(pygame.sprite.Sprite):
    def __init__(self, pos, damage=40, player=None):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.damage = damage
        self.player = player
        self.radius = 15  # Yellow bomb radius
        self.exploded = False
        self.explosion_radius = 150  # White circle radius
        self.explosion_timer = 0.2
        self.hit_enemies = set() # To fix the crash

    def update(self, dt, enemies):
        if not self.exploded:
            # Check if any enemy touches the bomb
            for e in enemies:
                if (e.pos - self.pos).length() <= self.radius + e.radius:
                    self.explode(enemies)
                    break
        else:
            self.explosion_timer -= dt
            if self.explosion_timer <= 0:
                self.kill()

    def explode(self, enemies):
        self.exploded = True
        for e in enemies:
            # Friendly fire protection: Bombs don't hit friendly summons
            if getattr(e, "is_friendly", False):
                continue
            if (e.pos - self.pos).length() <= self.explosion_radius + e.radius:
                e.take_damage(self.damage, None, player=self.player, game=getattr(self.player, 'game_ref', None))

    def draw(self, surface):
        if not self.exploded:
            # Draw white outline circle (explosion radius)
            pygame.draw.circle(surface, WHITE, (int(self.pos.x), int(self.pos.y)), self.explosion_radius, 2)
            # Draw yellow bomb
            pygame.draw.circle(surface, YELLOW, (int(self.pos.x), int(self.pos.y)), self.radius)
        else:
            # Draw explosion
            alpha = int(255 * (self.explosion_timer / 0.2))
            s = pygame.Surface((self.explosion_radius*2, self.explosion_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 100, 0, alpha), (self.explosion_radius,
                               self.explosion_radius), self.explosion_radius)
            surface.blit(s, (int(self.pos.x - self.explosion_radius), int(self.pos.y - self.explosion_radius)))

class BurningGarden(pygame.sprite.Sprite):
    def __init__(self, pos, radius,duration=5.0):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.radius = radius
        self.duration = duration
        self.timer = duration
        self.damage_tick_timer = 0.0
        self.damage_interval = 0.01
        self.damage_per_tick = 2.0**(radius/150)

    def update(self, dt, enemies, player):
        self.timer -= dt
        if self.timer <= 0:
            self.kill()
            return

        self.damage_tick_timer += dt
        if self.damage_tick_timer >= self.damage_interval:
            self.damage_tick_timer = 0
            for e in enemies:
                if not getattr(e, "is_friendly", False):
                    if (e.pos - self.pos).length() <= self.radius + e.radius:
                        e.take_damage(self.damage_per_tick, None, player=player, game=getattr(player, 'game_ref', None))

    def draw(self, surface):
        # Draw semi-opulent orange circle
        alpha = int(120 * (self.timer / self.duration))
        s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 140, 0, alpha), (self.radius, self.radius), self.radius)
        # Draw border
        pygame.draw.circle(s, (255, 69, 0, alpha + 30), (self.radius, self.radius), self.radius, 3)
        surface.blit(s, (int(self.pos.x - self.radius), int(self.pos.y - self.radius)))

class Wall(pygame.sprite.Sprite):
    def __init__(self, pos, angle, hp=150):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.angle = angle
        self.max_hp = hp
        self.hp = hp
        self.radius = 120 # Arc radius (doubled from 60)
        self.thickness = 15
        self.arc_width = 180 # Degrees (doubled from 90)

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.kill()
            return True
        return False

    def draw(self, surface):
        # Draw dark grey arc
        rect = pygame.Rect(self.pos.x - self.radius, self.pos.y - self.radius, self.radius * 2, self.radius * 2)
        start_angle = math.radians(self.angle - self.arc_width / 2)
        end_angle = math.radians(self.angle + self.arc_width / 2)
        
        # Pygame draw.arc uses a different coordinate system (0 is right, goes counter-clockwise)
        # Our angle is 0 is right, goes clockwise. Need to adjust.
        # Actually pygame.draw.arc(surface, color, rect, start_angle, stop_angle, width)
        # angles are in radians.
        
        pygame.draw.arc(surface, (60, 60, 60), rect, -end_angle, -start_angle, self.thickness)
        
        # Draw small health bar
        bar_width = 40
        bar_height = 5
        bar_x = self.pos.x - bar_width / 2
        bar_y = self.pos.y - self.radius - 10
        pygame.draw.rect(surface, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, (200, 60, 60), (bar_x, bar_y, bar_width * (self.hp / self.max_hp), bar_height))

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, class_name):
        super().__init__()
        self.class_name = class_name
        self.class_data = CLASS_DATA[class_name]
        self.pos = pygame.math.Vector2(pos)
        self.velocity = pygame.math.Vector2(0, 0)

        # LOAD BASE STATS FROM CLASS DATA
        self.base_health = self.class_data["base_hp"]
        self.base_fire_rate = self.class_data["base_fire_rate"]

        # New stat levels
        self.speed_level = 0
        self.health_level = 0
        self.firerate_level = 0
        self.regen_level = 0
        self.damage_level = 0
        self.cooldown_level = 0
        self.range_level = 0
        self.intrinsic_ability = "Summon" if class_name == "Archmage" else ("Red Lightning" if class_name == "Electrician" else None)
        self.secondary_ability = None
        self.ability_level = 0
        self.leech_timer = 0.0
        self.last_summon_time = 0.0

        # Prestige levels
        self.prestige = {
            "health": 0,
            "speed": 0,
            "fire_rate": 0,
            "regen": 0,
            "damage": 0,
            "cooldown": 0,
            "ability": 0
        }

        # Prestige Perk Variables
        self.last_damage_time = -999
        self.archmage_ramp = 1.0
        self.archmage_contact = False
        self.spaceman_echo_hits = [] # List of (enemy, time, damage)

        # Initial stat values
        self.speed = PLAYER_SPEED
        self.fire_rate = self.base_fire_rate  # Use class specific base
        self.damage = 25
        self.cooldown_reduction = 0.0
        self.melee_radius = 75

        # Wizard Cross Attack
        self.cross_attack_requested = False
        if self.class_name == "Wizard":
            self.cross_attack_requested = False

        self.radius = 20
        sprite_size = self.radius * 2.5
        sprite_prefix = self.class_data["sprite_prefix"]

        # Load sprites
        self.sprites = {}
        directions = ["up", "down", "left", "right", "left_up", "left_down", "right_up", "right_down"]
        for d in directions:
            try:
                # Try both naming conventions
                path = f"{d}_{sprite_prefix}.png"
                try:
                    img = pygame.image.load(path).convert_alpha()
                except pygame.error:
                    path = f"{sprite_prefix}_{d}.png"
                    img = pygame.image.load(path).convert_alpha()
                self.sprites[d] = pygame.transform.smoothscale(img, (int(sprite_size), int(sprite_size)))
            except pygame.error:
                # Fallback to colored surface
                s = pygame.Surface((int(sprite_size), int(sprite_size)), pygame.SRCALPHA)
                s.fill(self.class_data["color"])
                self.sprites[d] = s

        self.current_sprite = self.sprites["down"]

        # Initialize Health using the class base
        self.health = self.base_health
        self.radius = PLAYER_RADIUS
        self.last_shot = -999
        self.last_melee = -999
        self.dashing = False
        self.dash_time = 0
        self.last_dash = -999
        self.ability = "Dash"  # Default
        self.blink_effect_timer = 0.0
        self.heal_effect_timer = 0.0
        self.push_effect_timer = 0.0
        self.push_effect_max_radius = 150  # Max radius for force push
        self.push_effect_duration = 0.3  # Duration of the push effect
        self.defiance_timer = 0.0
        self.defiance_duration = 2.0
        self.history = deque(maxlen=60)
        self.history.append((self.pos.copy(), 0))
        self.invulnerable_enemies = {}
        self.melee_just_used = False
        self.chain_visuals = []
        
        # Ability Charges System
        self.ability_charges = 1
        self.max_ability_charges = 1

        # Combat and Ability Flags
        self.shot_count = 0
        self.bomb_requested = False
        self.push_requested = False
        self.burning_garden_requested = False
        self.wall_requested = False
        self.red_lightning_requested = False
        self.cross_attack_requested = False
        self.summon_requested = False
        self.hero_prestige_slash_requested = False
        self.ability_shield_hp = 0.0
        self.wizard_pattern_index = 0
        self.wizard_attack_pattern = ["normal", "normal", "normal", "tri-split"]
        self.ability_shield_timer = 0.0

    def calculate_health(self):
        """Calculate current max health based on upgrade level and class base"""
        if self.health_level == 0:
            return self.base_health
        total_increase = 0
        for i in range(1, self.health_level + 1):
            if i <= 4:
                total_increase += 0.10 * self.base_health
            elif i <= 9:
                total_increase += 0.20 * self.base_health
            else:
                total_increase += 0.25 * self.base_health
        return self.base_health + total_increase

    def calculate_speed(self):
        """Calculate current speed based on upgrade level"""
        if self.speed_level == 0:
            return PLAYER_SPEED
        total_increase = 0
        for i in range(1, self.speed_level + 1):
            if i <= 10:
                total_increase += 5.0
            else:
                total_increase += 10.0
        return PLAYER_SPEED + total_increase

    def calculate_fire_rate(self):
        """Calculate current fire rate based on upgrade level and class base"""
        if self.firerate_level == 0:
            fr = self.base_fire_rate
        else:
            if self.class_name == "Archmage":
                # For Archmage, each upgrade halves the fire rate (0.01 -> 0.005 -> 0.0025...)
                fr = self.base_fire_rate * (0.5 ** self.firerate_level)
            else:
                total_decrease = 0
                for i in range(1, self.firerate_level + 1):
                    if i <= 5:
                        total_decrease += 0.025
                    else:
                        total_decrease += 0.04
                fr = max(0.1, self.base_fire_rate - total_decrease)

        return fr

    def calculate_regen_rate(self):
        """Calculate current regen rate based on upgrade level"""
        if self.regen_level == 0:
            return 1.0
        total_increase = 1
        for i in range(1, self.regen_level + 1):
            if i <= 9:
                total_increase += 0.5
            else:
                total_increase += 1.0
        return total_increase

    def calculate_damage(self):
        """Calculate current damage based on upgrade level"""
        # Archmage base damage is 1, Electrician (Spaceman) is 30, others are 25.
        if self.class_name == "Archmage":
            base_dmg = 1
        elif self.class_name == "Electrician":
            base_dmg = 30
        else:
            base_dmg = 25
            
        # Starts at base, adds 3 per upgrade.
        dmg = base_dmg + (self.damage_level * 3)

        return dmg

    def calculate_cooldown_reduction(self):
        """Calculate current cooldown reduction based on upgrade level"""
        # Starts at 0%, adds 3% (0.03) per upgrade. Capped at 90%.
        return min(0.9, self.cooldown_level * 0.03)

    def calculate_range(self):
        """Calculate current range based on upgrade level"""
        if self.class_name == "Wizard":
            return 1500  # Screen is 1000x700, 1500 covers all
        # Hero range is fixed at 75
        if self.class_name == "Hero":
            return 75
        # Starts at 75, adds 3 per upgrade.
        r = 75 + (self.range_level * 3)
        return r

    def calculate_ability_scaling(self):
        """Calculate current ability scaling based on upgrade level (7% per level)"""
        return 1.0 + (self.ability_level * 0.07)

    def calculate_cross_damage(self):
        """Calculate Wizard's cross attack damage based on ability level"""
        if self.class_name != "Wizard":
            return 0
        # Base x15 damage of normal attack
        return self.calculate_damage() * 15

    def calculate_leech_percent(self):
        """Calculate Hero's leech percentage based on ability level"""
        if self.class_name != "Hero":
            return 0
        # Base 2%, adds 0.5% per level
        return 0.02 + (self.ability_level * 0.005)

    def get_upgrade_cost(self, current_level, stat_name=None):
        """Calculate the cost of the next upgrade, capped at level 30"""
        # Cap the level used for cost calculation at 30
        effective_level = min(current_level, 30)
        next_level = effective_level + 1

        cost = UPGRADE_COST_BASE * (UPGRADE_COST_MULTIPLIER ** (next_level - 1))
        return round(cost, 2)

    def update(self, dt, keys, mouse, current_time):
        if hasattr(self, "leech_timer") and self.leech_timer > 0:
            self.leech_timer -= dt
        dir_vec = pygame.math.Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dir_vec.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dir_vec.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dir_vec.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dir_vec.x += 1
        dir_vec = normalize_safe(dir_vec)

        # Sprite selection logic
        if dir_vec.x < 0 and dir_vec.y < 0:
            self.current_sprite = self.sprites["left_up"]
        elif dir_vec.x < 0 and dir_vec.y > 0:
            self.current_sprite = self.sprites["left_down"]
        elif dir_vec.x > 0 and dir_vec.y < 0:
            self.current_sprite = self.sprites["right_up"]
        elif dir_vec.x > 0 and dir_vec.y > 0:
            self.current_sprite = self.sprites["right_down"]
        elif dir_vec.x < 0:
            self.current_sprite = self.sprites["left"]
        elif dir_vec.x > 0:
            self.current_sprite = self.sprites["right"]
        elif dir_vec.y < 0:
            self.current_sprite = self.sprites["up"]
        elif dir_vec.y > 0:
            self.current_sprite = self.sprites["down"]

        # Update calculated stats
        self.speed = self.calculate_speed()
        self.fire_rate = self.calculate_fire_rate()
        self.damage = self.calculate_damage()
        self.cooldown_reduction = self.calculate_cooldown_reduction()
        self.melee_radius = self.calculate_range()

        # --- Prestige Perk Logic ---
        # Speed Prestige: Dodge Chance (15%)
        # Handled in apply_damage_to_player

        # Archmage Ramp Logic
        if self.class_name == "Archmage" and self.prestige["fire_rate"] >= 1:
            if self.archmage_contact:
                self.archmage_ramp = min(4.0, self.archmage_ramp + dt * 0.5) # Slow ramp
            else:
                self.archmage_ramp = 1.0
            self.archmage_contact = False # Reset every frame, set in perform_archmage_beam

        # Spaceman Echo Hits Logic
        for hit in list(self.spaceman_echo_hits):
            enemy, hit_time, damage = hit
            if current_time >= hit_time:
                if enemy in getattr(self, 'game_ref_enemies', []):
                    enemy.take_damage(damage, player=self, game=getattr(self, 'game_ref', None))
                    # Flash yellow effect
                    enemy.flash_timer = 0.1
                    enemy.flash_color = YELLOW
                self.spaceman_echo_hits.remove(hit)

        # Ability Cooldowns
         # Ability Cooldowns
        ability_cooldowns = {
            "Dash": 2.0,
            "Blink Step": 3.0,
            "Quick Bomb": 4.0,
            "Small Heal": 10.0,
            "Force Push": 5.0,
            "Burning Garden": 8.0,
            "Defiance": 7.0,
            "Wall Arc": 8.0, # Decreased from 10.0
            "Melee": 1.5,
            "Cross Attack": 8.0,
            "Summon": 15.0,
            "Leech": 15.0,
            "Red Lightning": 10.0
        }

        # Apply cooldown reduction
        for k in ability_cooldowns:
            ability_cooldowns[k] *= (1 - self.cooldown_reduction)

        # --- Handle Intrinsic Ability (Space key) ---
        intrinsic_cooldown = ability_cooldowns.get(self.intrinsic_ability, 2.0)
        
        if keys[pygame.K_SPACE] and (current_time - self.last_melee) >= intrinsic_cooldown:
            result = self.use_ability(self.intrinsic_ability, current_time, dir_vec, mouse)
            if result == "melee_slash":
                self.melee_just_used = True
            self.last_melee = current_time
            # Sync last_summon_time for Archmage if needed, but we'll use last_melee for all intrinsic
            if self.class_name == "Archmage":
                self.last_summon_time = current_time

        # --- Handle Secondary Ability (Shift key) ---
        secondary_cooldown = ability_cooldowns.get(self.secondary_ability, 2.0)

        # Charge regeneration
        if self.ability_charges < self.max_ability_charges:
            if (current_time - self.last_dash) >= secondary_cooldown:
                self.ability_charges += 1
                if self.ability_charges < self.max_ability_charges:
                    self.last_dash = current_time  # Start next charge
                else:
                    # Charges are full, reset last_dash to -999 to indicate ready
                    self.last_dash = -999

        if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and self.ability_charges > 0:
            result = self.use_ability(self.secondary_ability, current_time, dir_vec, mouse)
            if result == "melee_slash":
                self.melee_just_used = True

            self.ability_charges -= 1
            # If we just used a charge and it's no longer full, start the cooldown timer
            if self.ability_charges < self.max_ability_charges:
                # If we were at full charges, start the timer from now
                if self.last_dash == -999:
                    self.last_dash = current_time

        # Wizard Cross Attack damage is calculated on use

        if self.dashing:
            self.dash_time -= dt
            if self.dash_time <= 0:
                self.dashing = False
        else:
            self.velocity = dir_vec * self.speed

        # Apply movement
        self.pos += self.velocity * dt
        self.pos.x = clamp(self.pos.x, self.radius, WIDTH - self.radius)
        self.pos.y = clamp(self.pos.y, self.radius, HEIGHT - self.radius)
        self.history.append((self.pos.copy(), current_time))
        # Update chain visuals
        self.chain_visuals = [(s, e, t - dt, c) for s, e, t, c in self.chain_visuals if t > 0]
        if self.class_name == "Electrician":
            if current_time - self.last_shot >= self.fire_rate:
                # We need access to enemies here. The original code might not pass them.
                # We will handle the attack in the main loop or pass enemies to update.
                pass

    def use_ability(self, ability_name, current_time, dir_vec, mouse):
        scaling = self.calculate_ability_scaling()

        # Ability Prestige: using an ability grants you a 10% temporary shield for 2 seconds.
        if self.prestige["ability"] >= 1:
            self.ability_shield_hp = self.calculate_health() * 0.10
            self.ability_shield_timer = 2.0

        if ability_name == "Dash":
            dash_dir = dir_vec if dir_vec.length_squared() > 0 else normalize_safe(pygame.math.Vector2(mouse) - self.pos)
            if dash_dir.length_squared() > 0:
                self.dashing = True
                self.dash_time = DASH_DURATION
                # Scale dash distance (speed * duration)
                self.velocity = dash_dir * (DASH_SPEED * scaling)

        elif ability_name == "Blink Step":
            blink_dir = dir_vec if dir_vec.length_squared() > 0 else normalize_safe(pygame.math.Vector2(mouse) - self.pos)
            if blink_dir.length_squared() > 0:
                self.blink_effect_timer = 0.2
                # Scale blink distance
                self.pos += blink_dir * (120 * scaling)

        elif ability_name == "Small Heal":
            # Scale heal amount
            heal_amount = self.calculate_health() * 0.15 * scaling
            self.health = min(self.calculate_health(), self.health + heal_amount)
            self.heal_effect_timer = 0.4

        elif ability_name == "Quick Bomb":
            self.bomb_requested = True

        elif ability_name == "Force Push":
            self.push_requested = True
            # Scale push range
            self.push_effect_max_radius = 150 * scaling
            self.push_effect_timer = self.push_effect_duration

        elif ability_name == "Burning Garden":
            self.burning_garden_requested = True

        elif ability_name == "Defiance":
            self.defiance_timer = self.defiance_duration * scaling

        elif ability_name == "Wall Arc":
            self.wall_requested = True

        elif ability_name == "Leech":
            # Hero's intrinsic ability: Life Leech
            # Duration scales: 5s + 0.5s per level
            self.leech_timer = 5.0 + (self.ability_level * 0.5)
            return "leech_active"

        elif ability_name == "Red Lightning":
            self.red_lightning_requested = True
        elif ability_name == "Cross Attack":
            # Wizard's intrinsic ability: Purple Cross Attack
            self.cross_attack_requested = True

        elif ability_name == "Summon":
            # Archmage's intrinsic ability: Summon 3 random friendly enemies
            self.summon_requested = True

    def can_shoot(self, current_time):
        return (current_time - self.last_shot) >= self.fire_rate

    def shoot(self, target_pos, current_time):
        self.last_shot = current_time
        self.shot_count += 1

        dmg = self.damage

        if self.class_name == "Wizard":
            # Wizard: Ranged Bullet Attack with Pattern
            dir_vec = normalize_safe(pygame.math.Vector2(target_pos) - self.pos)
            
            # Pattern: normal, tri-split, normal, boomerang, normal, normal
            attack_type = self.wizard_attack_pattern[self.wizard_pattern_index % len(self.wizard_attack_pattern)]
            self.wizard_pattern_index += 1

            # Fire Rate Prestige: fires 2 twin shots instead of one (handled per type)
            is_prestige = self.prestige["fire_rate"] >= 1
            
            bullets = []
            
            def spawn_bullet(pos, vel, a_type):
                if a_type == "tri-split":
                    return TriSplitBullet(pos, vel, owner="player", damage=dmg)
                else: # normal
                    # Only normal attacks are yellow
                    return Bullet(pos, vel, owner="player", damage=dmg, color=YELLOW)

            if is_prestige:
                perp = pygame.math.Vector2(-dir_vec.y, dir_vec.x) * 10
                bullets.append(spawn_bullet(self.pos + perp, dir_vec * PLAYER_BULLET_SPEED, attack_type))
                bullets.append(spawn_bullet(self.pos - perp, dir_vec * PLAYER_BULLET_SPEED, attack_type))
            else:
                bullets.append(spawn_bullet(self.pos, dir_vec * PLAYER_BULLET_SPEED, attack_type))
            
            return bullets if len(bullets) > 1 else bullets[0]

        elif self.class_name == "Hero":
            # Hero Prestige: throws a short range slash to 100px then disappears every attack
            if self.prestige["fire_rate"] >= 1:
                self.hero_prestige_slash_requested = True
            return "primary_melee"

        elif self.class_name == "Archmage":
            # Archmage Prestige: attack ramps up (4x) as long as you stay in contact
            # Handled in perform_archmage_beam and Player.update
            return "piercing_beam"
        elif self.class_name == "Electrician":
            return "chain_lightning"

        return None

    def can_melee(self, current_time):
        if self.class_name == "Wizard":
            return False
        cooldown = MELEE_COOLDOWN_BASE * (1 - self.cooldown_reduction)
        return (current_time - self.last_melee) >= cooldown

    def melee(self, current_time):
        self.last_melee = current_time
        return True

    def can_dash(self, current_time):
        cooldown = DASH_COOLDOWN_BASE * (1 - self.cooldown_reduction)
        return (current_time - self.last_dash) >= cooldown

    def cleanup_invulnerability(self, current_time):
        """Remove expired invulnerability entries"""
        expired = [enemy_id for enemy_id, vuln_time in self.invulnerable_enemies.items() if current_time >= vuln_time]
        for enemy_id in expired:
            del self.invulnerable_enemies[enemy_id]

    def perform_chain_attack(self, mouse_pos, enemies, game=None):
        best_enemy = None
        min_dist = float('inf')
        
        # Spaceman (Electrician) logic: shoot at nearest enemy on click
        for e in enemies:
            if getattr(e, "is_friendly", False): continue
            dist = self.pos.distance_to(e.pos)
            if dist < min_dist:
                min_dist = dist
                best_enemy = e
        
        if best_enemy:
            hit_enemies = set()
            current_source = self.pos
            current_target = best_enemy
            damage = self.calculate_damage()
            while current_target and current_target not in hit_enemies:
                hit_enemies.add(current_target)
                current_target.take_damage(damage, player=self, game=game)
                
                # Spaceman Prestige: Hit them for damage again after a pause
                if self.prestige["fire_rate"] >= 1:
                    # Schedule a second hit in 0.5 seconds
                    self.spaceman_echo_hits.append((current_target, (game.survival_time if game else 0) + 0.5, damage))

                current_target.stun_timer = 0.3
                self.chain_visuals.append((current_source, current_target.pos.copy(), 0.2, "yellow"))
                next_enemy = None
                next_min_dist = 100
                for e in enemies:
                    if e in hit_enemies or getattr(e, "is_friendly", False): continue
                    d = (e.pos - current_target.pos).length()
                    if d < next_min_dist:
                        next_min_dist = d
                        next_enemy = e
                current_source = current_target.pos.copy()
                current_target = next_enemy

    def perform_red_ability(self, enemies, game=None):
        for e in enemies:
            if getattr(e, "is_friendly", False): continue
            e.take_damage(100 + (self.damage_level * 75), player=self, game=game)
            e.stun_timer = 0.5
            self.chain_visuals.append((self.pos.copy(), e.pos.copy(), 0.6, "red"))

class StoneBrick(Bullet):
    def __init__(self, pos, vel, game):
        super().__init__(pos, vel, owner="enemy", damage=20, color=(100, 100, 100), radius=15)
        self.break_timer = random.uniform(0.5, 1.5)
        self.game = game

    def update(self, dt):
        super().update(dt)
        self.break_timer -= dt
        if self.break_timer <= 0:
            for _ in range(7):
                angle = random.uniform(0, math.pi * 2)
                f_vel = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * 300
                frag = Bullet(self.pos.copy(), f_vel, owner="enemy", damage=10, color=(120, 120, 120), radius=5)
                self.game.enemy_bullets.append(frag)
            self.kill()

class EnemyBase(pygame.sprite.Sprite):
    def __init__(self, pos, color=RED, radius=16, speed=100, hp=40, score_value=10):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(0, 0)
        self.color = color
        self.radius = radius
        self.speed = speed
        self.hp = hp
        self.max_hp = hp
        self.score_value = score_value
        self.is_friendly = False
        self.target = None
        self.damage_mult = 1.0
        self.history = deque(maxlen=12)
        self.velocity = pygame.math.Vector2(0, 0) # Compatibility with Player attribute
        self.stun_timer = 0.0
        self.flash_timer = 0.0
        self.flash_color = WHITE
    def calculate_health(self): return self.max_hp

    def take_damage(self, amount, enemy_group=None, player=None, game=None, is_crit=False):
        # Prevent damage if the enemy is a boss and the wave hasn't officially started
        if getattr(self, 'is_boss', False):
            # Bosses are invulnerable during their 'entry' state
            if hasattr(self, 'state') and self.state == "entry":
                return False

        rounded_amount = round(amount)
        self.hp -= amount # Keep float for actual HP
        if game:
            # Display damage popup (individual numbers, even within 0.05s)
            color = RED if is_crit else WHITE
            game.damage_popups.append(DamagePopup(self.pos, rounded_amount, color=color, is_crit=is_crit, enemy_id=id(self)))
        if player and player.class_name == "Hero" and player.leech_timer > 0:
            leech_percent = player.calculate_leech_percent()
            heal_amount = amount * leech_percent
            player.health = min(player.calculate_health(), player.health + heal_amount)
        if self.hp <= 0:
            if game:
                game.score += self.score_value
                game.money += self.score_value
            self.kill()
            return True
        return False

    def update(self, dt, current_time=0):
        """Moves enemy according to velocity and keeps them on screen"""
        if self.flash_timer > 0:
            self.flash_timer -= dt
        if self.stun_timer > 0:
            self.stun_timer -= dt
            return
        self.pos += self.vel * dt
        self.velocity = self.vel # Keep velocity synced
        self.history.append((self.pos.copy(), current_time))

        # Screen boundary logic:
        # If they are outside the screen, they should move TOWARD the screen.
        # Once inside, they are clamped to stay inside.
        margin = self.radius + 5
       
        # Check if they are already inside the screen
        is_inside_x = margin <= self.pos.x <= WIDTH - margin
        is_inside_y = margin <= self.pos.y <= HEIGHT - margin
       
        if is_inside_x and is_inside_y or self.is_friendly:
            # Fully inside or Friendly: Clamp to stay inside strictly
            self.pos.x = clamp(self.pos.x, margin, WIDTH - margin)
            self.pos.y = clamp(self.pos.y, margin, HEIGHT - margin)
        else:
            # Outside: If they are moving further away, stop them or redirect them
            if self.pos.x < margin and self.vel.x < 0: self.vel.x = 0
            if self.pos.x > WIDTH - margin and self.vel.x > 0: self.vel.x = 0
            if self.pos.y < margin and self.vel.y < 0: self.vel.y = 0
            if self.pos.y > HEIGHT - margin and self.vel.y > 0: self.vel.y = 0
           
            # Force them toward the screen if they are outside
            if self.pos.x < margin: self.pos.x += abs(self.speed) * 0.5 * dt
            if self.pos.x > WIDTH - margin: self.pos.x -= abs(self.speed) * 0.5 * dt
            if self.pos.y < margin: self.pos.y += abs(self.speed) * 0.5 * dt
            if self.pos.y > HEIGHT - margin: self.pos.y -= abs(self.speed) * 0.5 * dt

    def draw(self, surface):
        color = self.color
        if getattr(self, 'flash_timer', 0) > 0:
            color = getattr(self, 'flash_color', WHITE)
        pygame.draw.circle(surface, color, (int(self.pos.x), int(self.pos.y)), self.radius)

class PredictorBot(EnemyBase):
    def __init__(self, pos, wave=0):
        hp = 60 * (1 + wave * 0.85)
        score = 18 * (1 + wave * 0.2)
        super().__init__(pos, color=ORANGE, radius=16, speed=180, hp=hp, score_value=score)
        self.wave = wave
        self.last_predict_time = -999
        self.predict_interval = max(0.6, 1.4 - 0.1*self.wave)
        self.target_point = self.pos.copy()

    def update_behavior(self, player, current_time, enemies):
        # Target nearest enemy if friendly, otherwise target player or nearest friendly
        target = player
        if getattr(self, "is_friendly", False):
            # Friendly: Target nearest non-friendly enemy
            min_dist = 9999
            for e in enemies:
                if not getattr(e, "is_friendly", False):
                    d = (e.pos - self.pos).length()
                    if d < min_dist:
                        min_dist = d
                        target = e
        else:
            # Hostile: Target player or nearest friendly
            min_dist = (player.pos - self.pos).length()
            for e in enemies:
                if getattr(e, "is_friendly", False):
                    d = (e.pos - self.pos).length()
                    if d < min_dist:
                        min_dist = d
                        target = e

        if (current_time - self.last_predict_time) >= self.predict_interval:
            dist = (target.pos - self.pos).length()
            forward_time = clamp(dist / max(1, self.speed) * 0.75, 0.3, 2.2)
            # Use target's history if it exists, otherwise just its position
            if hasattr(target, "history"):
                self.target_point = predict_future_position(target.history, forward_time)
            else:
                self.target_point = target.pos.copy()
            self.last_predict_time = current_time
        self.vel = normalize_safe(self.target_point - self.pos) * self.speed

class DrifterBot(EnemyBase):
    def __init__(self, pos, wave=0):
        hp = 100 * (1 + wave * 0.85)
        score = 8 * (1 + wave * 0.2)
        super().__init__(pos, color=BLUE, radius=14, speed=90, hp=hp, score_value=score)
        self.wave = wave
        self.change_timer = random.uniform(0.4, 1.5)
        self.dir = vec_from_angle(random.random() * math.pi * 2)

    def update_behavior(self, player, current_time, dt):
        self.change_timer -= dt
        if self.change_timer <= 0:
            self.change_timer = random.uniform(0.6, 3.0)
            # 12% chance to move toward player, else random
            if random.random() < 0.12:
                self.dir = normalize_safe(player.pos - self.pos)
            else:
                self.dir = vec_from_angle(random.random() * math.pi * 2)
        self.vel = self.dir * self.speed

class ShooterBot(EnemyBase):
    def __init__(self, pos, wave=0):
        hp = 120 * (1 + wave * 0.85)
        score = 22 * (1 + wave * 0.2)
        super().__init__(pos, color=YELLOW, radius=16, speed=120, hp=hp, score_value=score)
        self.wave = wave
        self.fire_cooldown = max(0.6, 1.2 - 0.05 * self.wave)
        self.last_shot = -999
        self.desired_distance = 280

    def update_behavior(self, player, current_time, bullets_group):
        to_player = player.pos - self.pos
        dist = to_player.length()
        dir_to_player = normalize_safe(to_player)

        # Maintain distance
        if dist < self.desired_distance - 30:
            self.vel = -dir_to_player * self.speed
        elif dist > self.desired_distance + 30:
            self.vel = dir_to_player * self.speed
        else:
            self.vel = pygame.math.Vector2(0, 0)

        # Fire bullet if cooldown passed
        if (current_time - self.last_shot) >= self.fire_cooldown:
            forward_time = clamp(dist / 350.0, 0.2, 1.5)
            predicted = predict_future_position(player.history, forward_time)
            aim_dir = normalize_safe(predicted - self.pos)
            if aim_dir.length_squared() > 0:
                vel = aim_dir * 430
                b = Bullet(self.pos, vel, owner="enemy")
                bullets_group.append(b)
                self.last_shot = current_time

class TankBot(EnemyBase):
    def __init__(self, pos, wave=0):
        hp = 300 * (1 + wave * 0.85)
        score = 50 * (1 + wave * 0.2)
        super().__init__(pos, color=(150, 80, 200), radius=20, speed=60, hp=hp, score_value=score)
        self.wave = wave
        self.chase_timer = 0
        self.dir = pygame.math.Vector2(0, 0)

    def update_behavior(self, player, current_time, dt):
        self.chase_timer -= dt
        if self.chase_timer <= 0:
            self.chase_timer = random.uniform(0.5, 1.8)
            self.dir = normalize_safe(player.pos - self.pos)
        self.vel = self.dir * self.speed

class MageBot(EnemyBase):
    def __init__(self, pos, wave=0):
        hp = 70 * (1 + wave * 0.85)
        score = 35 * (1 + wave * 0.2)
        super().__init__(pos, color=GREEN, radius=16, speed=100, hp=hp, score_value=score)
        self.wave = wave
        self.last_shot = -999
        self.fire_cooldown = 3.5
        self.warning_time = 1.2
        self.precursor_time = 0.3  # Final flash before shooting
        self.is_charging = False
        self.charge_start = 0
        self.target_line = None

    def update_behavior(self, player, current_time, bullets_group):
        to_player = player.pos - self.pos
        dist = to_player.length()

        if not self.is_charging:
            # Movement: try to stay at a distance
            if dist < 350:
                self.vel = normalize_safe(self.pos - player.pos) * self.speed
            elif dist > 450:
                self.vel = normalize_safe(player.pos - self.pos) * self.speed
            else:
                self.vel = pygame.math.Vector2(0, 0)

            # Start charging shot
            if (current_time - self.last_shot) >= self.fire_cooldown:
                self.is_charging = True
                self.charge_start = current_time
                self.target_line = normalize_safe(player.pos - self.pos)
                self.vel = pygame.math.Vector2(0, 0)  # Stop while charging
        else:
            # Charging logic
            if (current_time - self.charge_start) >= self.warning_time:
                # Shoot lightning bolt
                self.is_charging = False
                self.last_shot = current_time
                # Lightning is a fast, high-damage projectile
                bolt = Bullet(self.pos, self.target_line * 3500, owner="enemy", damage=50 * getattr(self, "damage_mult", 1.0))
                bolt.radius = 8
                bolt.color = (100, 100, 255)  # Blue lightning
                bullets_group.append(bolt)

    def draw(self, surface):
        super().draw(surface)
        if self.is_charging:
            # Draw warning line
            # Use survival_time for consistent timing with game logic
            # We need to pass survival_time to draw or store it in the object
            # For now, let's use a simple timer inside the object updated in update_behavior
            pass

    def draw_warning(self, surface, current_survival_time):
        if self.is_charging:
            time_since_charge = current_survival_time - self.charge_start
            time_remaining = self.warning_time - time_since_charge

            if time_remaining <= self.precursor_time:
                # Precursor: Bright, solid red line
                line_color = (255, 0, 0, 255)
                line_width = 4
            else:
                # Normal warning: Flickering darker red line
                alpha = 100 if (int(time_since_charge * 10) % 2 == 0) else 180
                line_color = (180, 0, 0, alpha)
                line_width = 2

            # Draw a long line in the target direction
            end_pos = self.pos + self.target_line * 2000
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(s, line_color, self.pos, end_pos, line_width)
            surface.blit(s, (0, 0))

class SwarmerBot(EnemyBase):
    def __init__(self, pos, stage=1, wave=0):
        # Stage 1: Big, Stage 2: Medium, Stage 3: Small
        colors = {1: (220, 40, 40), 2: (255, 80, 80), 3: (255, 120, 120)}
        radii = {1: 22, 2: 14, 3: 8}
        hps = {1: 150, 2: 80, 3: 40}
        speeds = {1: 100, 2: 140, 3: 180}
        scores = {1: 20, 2: 10, 3: 5}

        hp = hps[stage] * (1 + wave * 0.85)
        score = scores[stage] * (1 + wave * 0.2)

        super().__init__(pos, color=colors[stage], radius=radii[stage], speed=speeds[stage], hp=hp, score_value=score)
        self.stage = stage
        self.wave = wave

    def update_behavior(self, player):
        self.vel = normalize_safe(player.pos - self.pos) * self.speed

    def take_damage(self, amount, enemy_group=None, player=None, game=None, is_crit=False):
            rounded_amount = round(amount)
            self.hp -= amount
            if game:
                # Display damage popup (individual numbers, even within 0.05s)
                color = RED if is_crit else WHITE
                game.damage_popups.append(DamagePopup(self.pos, rounded_amount, color=color, is_crit=is_crit, enemy_id=id(self)))
            if player and player.class_name == "Hero" and player.leech_timer > 0:
                leech_percent = player.calculate_leech_percent()
                heal_amount = amount * leech_percent
                player.health = min(player.calculate_health(), player.health + heal_amount)
            if self.hp <= 0:
                if game:  # Use the game instance to update score and money
                    game.score += self.score_value
                    game.money += self.score_value
                if self.stage < 3 and enemy_group is not None:
                    # Split into 2
                    for _ in range(2):
                        offset = pygame.math.Vector2(random.uniform(-10, 10), random.uniform(-10, 10))
                        child = SwarmerBot(self.pos + offset, stage=self.stage + 1, wave=self.wave)
                        child.is_friendly = self.is_friendly
                        if child.is_friendly:
                            child.hp *= 0.25
                            child.max_hp *= 0.25
                            child.damage_mult = 2.0
                        enemy_group.append(child)
                self.kill()
                return True
            return False

class AssassinBot(EnemyBase):
    def __init__(self, pos, wave=0):
        hp = 100 * (1 + wave * 0.85)
        score = 100 * (1 + wave * 0.2)
        super().__init__(pos, color=(60, 0, 0), radius=15, speed=220, hp=hp, score_value=score)
        self.wave = wave
        self.blink_timer = 0
        self.is_visible = True
        self.last_damage_time = -999

    def update_behavior(self, player, current_time, dt):
        self.blink_timer -= dt
        if self.blink_timer <= 0:
            self.is_visible = not self.is_visible
            self.blink_timer = random.uniform(0.3, 0.8)

        self.vel = normalize_safe(player.pos - self.pos) * self.speed

    def draw(self, surface):
        if self.is_visible:
            pygame.draw.circle(surface, (30, 0, 0), (int(self.pos.x), int(self.pos.y)), self.radius)
            pygame.draw.circle(surface, (150, 0, 0), (int(self.pos.x), int(self.pos.y)), self.radius, 2)
            super().draw(surface)

class NecromancerBot(EnemyBase):
    def __init__(self, pos, wave=0):
        hp = 200 * (1 + wave * 0.85)
        score = 150 * (1 + wave * 0.2)
        super().__init__(pos, color=(200, 200, 200), radius=18, speed=70, hp=hp, score_value=score)
        self.wave = wave
        self.summon_timer = 5.0

    def update_behavior(self, player, current_time, dt, enemy_group, dead_pool):
        dist = (player.pos - self.pos).length()
        if dist < 300:
            self.vel = normalize_safe(self.pos - player.pos) * self.speed
        elif dist > 500:
            self.vel = normalize_safe(player.pos - self.pos) * self.speed
        else:
            self.vel = pygame.math.Vector2(0, 0)

        self.summon_timer -= dt
        if self.summon_timer <= 0:
            self.summon_timer = 5.0
            for _ in range(5):
                spawn_pos = self.pos + vec_from_angle(random.random() * math.pi * 2) * 50
                etype = random.choice(["predictor", "drifter", "shooter", "tank", "mage", "swarmer", "assassin"])
                if etype == "predictor":
                    e = PredictorBot(spawn_pos, wave=self.wave)
                elif etype == "drifter":
                    e = DrifterBot(spawn_pos, wave=self.wave)
                elif etype == "shooter":
                    e = ShooterBot(spawn_pos, wave=self.wave)
                elif etype == "tank":
                    e = TankBot(spawn_pos, wave=self.wave)
                elif etype == "mage":
                    e = MageBot(spawn_pos, wave=self.wave)
                elif etype == "swarmer":
                    e = SwarmerBot(spawn_pos, stage=1, wave=self.wave)
                elif etype == "assassin":
                    e = AssassinBot(spawn_pos, wave=self.wave)
                else:
                    e = DrifterBot(spawn_pos, wave=self.wave)
                e.is_friendly = self.is_friendly
                if e.is_friendly:
                    e.hp *= 0.25
                    e.max_hp *= 0.25
                e.damage_mult = 2.0
                enemy_group.append(e)

# -----------------------
# Archmage Allies
# -----------------------

class KnightAlly(EnemyBase):
    def __init__(self, pos):
        super().__init__(pos, color=(173, 216, 230), radius=18, speed=160, hp=100, score_value=0) # HP buffed to 100
        self.is_friendly = True
        self.attack_cooldown = 0.3 # Buffed to 0.3s
        self.last_attack = -999
        self.damage = 25 # Damage is 25

    def update_behavior(self, player, current_time, enemies):
        target = None
        min_dist = 9999
        for e in enemies:
            if not getattr(e, "is_friendly", False):
                d = (e.pos - self.pos).length()
                if d < min_dist:
                    min_dist = d
                    target = e
        
        if target:
            if min_dist < 40:
                self.vel = pygame.math.Vector2(0, 0)
                if (current_time - self.last_attack) >= self.attack_cooldown:
                    target.take_damage(self.damage, enemies, player=player, game=getattr(player, 'game_ref', None))
                    self.last_attack = current_time
            else:
                self.vel = normalize_safe(target.pos - self.pos) * self.speed
        else:
            # Follow player if no enemies
            if (player.pos - self.pos).length() > 100:
                self.vel = normalize_safe(player.pos - self.pos) * self.speed
            else:
                self.vel = pygame.math.Vector2(0, 0)

class CrossbowmanAlly(EnemyBase):
    def __init__(self, pos):
        super().__init__(pos, color=(188, 158, 130), radius=15, speed=120, hp=75, score_value=0) # HP buffed to 75
        self.is_friendly = True
        self.attack_cooldown = 0.5 # Buffed to 0.5s
        self.last_attack = -999
        self.damage = 50 # Damage buffed to 50
        self.desired_dist = 250

    def update_behavior(self, player, current_time, enemies, bullets_group):
        target = None
        min_dist = 9999
        for e in enemies:
            if not getattr(e, "is_friendly", False):
                d = (e.pos - self.pos).length()
                if d < min_dist:
                    min_dist = d
                    target = e
        
        if target:
            if min_dist < self.desired_dist - 20:
                self.vel = normalize_safe(self.pos - target.pos) * self.speed
            elif min_dist > self.desired_dist + 20:
                self.vel = normalize_safe(target.pos - self.pos) * self.speed
            else:
                self.vel = pygame.math.Vector2(0, 0)
            
            if (current_time - self.last_attack) >= self.attack_cooldown:
                aim_dir = normalize_safe(target.pos - self.pos)
                if aim_dir.length_squared() > 0:
                    b = Bullet(self.pos, aim_dir * 600, owner="player", damage=self.damage, color=(245, 245, 220))
                    bullets_group.append(b)
                    self.last_attack = current_time
        else:
            if (player.pos - self.pos).length() > 150:
                self.vel = normalize_safe(player.pos - self.pos) * self.speed
            else:
                self.vel = pygame.math.Vector2(0, 0)

class ParagonAlly(EnemyBase):
    def __init__(self, pos):
        super().__init__(pos, color=(255, 215, 0), radius=22, speed=140, hp=250, score_value=0) # HP buffed to 250
        self.is_friendly = True
        self.attack_cooldown = 0.5 # Buffed to 0.5s
        self.last_attack = -999
        self.damage = 100 # Damage is 100
        self.special_cooldown = 5.0
        self.last_special = -999
        self.flash_timer = 0

    def update_behavior(self, player, current_time, enemies, dt):
        self.flash_timer += dt
        # Flash gold/white
        if (int(self.flash_timer * 4) % 2) == 0:
            self.color = (255, 215, 0)
        else:
            self.color = (255, 255, 255)

        target = None
        min_dist = 9999
        for e in enemies:
            if not getattr(e, "is_friendly", False):
                d = (e.pos - self.pos).length()
                if d < min_dist:
                    min_dist = d
                    target = e
        
        if target:
            if min_dist < 50:
                self.vel = pygame.math.Vector2(0, 0)
                if (current_time - self.last_attack) >= self.attack_cooldown:
                    target.take_damage(self.damage, enemies, player=player, game=getattr(player, 'game_ref', None))
                    self.last_attack = current_time
            else:
                self.vel = normalize_safe(target.pos - self.pos) * self.speed
        else:
            if (player.pos - self.pos).length() > 100:
                self.vel = normalize_safe(player.pos - self.pos) * self.speed
            else:
                self.vel = pygame.math.Vector2(0, 0)

        # Golden Cross Attack
        if self.last_special == -999: self.last_special = current_time # Start timer on spawn
        if (current_time - self.last_special) >= self.special_cooldown:
            self.last_special = current_time
            return "golden_cross"
        return None


class AnchorBot(EnemyBase):
    def __init__(self, pos):
        super().__init__(pos, color=DARK_GREEN, radius=22, speed=80, hp=400, score_value=150)
        self.wait_timer = 4.0
        self.tether_timer = 0.0
        self.is_tethering = False

    def update_behavior(self, player, current_time, dt, bullets_group, game):
        if self.is_tethering:
            self.tether_timer -= dt
            self.vel = pygame.math.Vector2(0, 0)
            # Pull player towards anchor
            pull_dir = normalize_safe(self.pos - player.pos)
            dist = (self.pos - player.pos).length()
            
            # Stronger pull if further away
            pull_strength = 150 + (dist * 0.5)
            player.pos += pull_dir * pull_strength * dt
            
            # Restrict player velocity to prevent escaping easily
            if player.velocity.length() > 0:
                # Project velocity onto the perpendicular of the pull direction (allow orbiting but not escaping)
                perp_dir = pygame.math.Vector2(-pull_dir.y, pull_dir.x)
                player.velocity = perp_dir * player.velocity.dot(perp_dir) * 0.5
            
            if self.tether_timer <= 0 or self.hp <= 0:
                self.is_tethering = False
                self.wait_timer = 3.0 # Shorter wait after tether
        else:
            self.wait_timer -= dt
            dist = (player.pos - self.pos).length()
            if dist > 400:
                self.vel = normalize_safe(player.pos - self.pos) * self.speed
            else:
                # Try to maintain a distance to tether
                if dist < 250:
                    self.vel = normalize_safe(self.pos - player.pos) * self.speed
                else:
                    self.vel = pygame.math.Vector2(0, 0)
                
            if self.wait_timer <= 0:
                aim_dir = normalize_safe(player.pos - self.pos)
                # White bullet with a trail effect would be nice, but let's stick to fixing the logic first
                b = TetherBullet(self.pos.copy(), aim_dir * 600, owner="enemy", damage=5, color=(200, 200, 255), radius=12, parent=self)
                bullets_group.append(b)
                self.wait_timer = 5.0 # Cooldown between shots

    def draw(self, surface):
        super().draw(surface)
        if self.is_tethering:
            # Draw tether line with segments for a "chain" look
            start = self.pos
            end = getattr(self, "tether_target_pos", self.pos)
            if isinstance(end, pygame.math.Vector2):
                target_pos = end
            else:
                target_pos = pygame.math.Vector2(end)
                
            dist = (target_pos - start).length()
            if dist > 0:
                num_segments = int(dist / 15)
                for i in range(num_segments):
                    p1 = start + (target_pos - start) * (i / num_segments)
                    p2 = start + (target_pos - start) * ((i + 0.6) / num_segments)
                    pygame.draw.line(surface, (200, 200, 255), p1, p2, 3)
            
            # Pulse effect on anchor
            pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) / 2
            pygame.draw.circle(surface, (100, 100, 255), (int(self.pos.x), int(self.pos.y)), self.radius + 8, 2)
            pygame.draw.circle(surface, (200, 200, 255), (int(self.pos.x), int(self.pos.y)), self.radius + 5, int(2 + pulse * 3))

class GravityCoreBot(EnemyBase):
    def __init__(self, pos):
        super().__init__(pos, color=PALE_PURPLE, radius=25, speed=60, hp=600, score_value=200)
        self.pulse_timer = 0

    def update_behavior(self, player, current_time, dt):
        dist_vec = player.pos - self.pos
        dist = dist_vec.length()
        if dist < 350:
            # Pull strength increases as you get closer
            pull_strength = (1.0 - (dist / 350)) * 180
            player.pos -= normalize_safe(dist_vec) * pull_strength * dt
            # Slow down player movement speed
            player.speed *= 0.4 
            
        self.vel = normalize_safe(player.pos - self.pos) * self.speed
        self.pulse_timer += dt

    def draw(self, surface):
        # Draw pulsing aura
        pulse = (math.sin(self.pulse_timer * 5) + 1) / 2
        aura_radius = 350
        s = pygame.Surface((aura_radius * 2, aura_radius * 2), pygame.SRCALPHA)
        # Fading purple circle
        for r in range(aura_radius, 0, -30):
            alpha = int(30 * (1 - r/aura_radius) * (0.5 + 0.5 * pulse))
            pygame.draw.circle(s, (*PALE_PURPLE, alpha), (aura_radius, aura_radius), r)
        surface.blit(s, (int(self.pos.x - aura_radius), int(self.pos.y - aura_radius)))
        super().draw(surface)

class BossBase(EnemyBase):
    def __init__(self, pos, color, radius, hp, score_value):
        super().__init__(pos, color=color, radius=radius, speed=50, hp=hp, score_value=3000)
        self.is_boss = True
        self.attack_timer = 0
        self.state = "entry"  # Bosses start in 'entry' state (invulnerable)
        self.state_timer = 0

class RedCoreBoss(BossBase):
    def __init__(self, pos, wave):
        # Exponential HP scaling: 1500 * (2 ^ (wave/3 - 1))
        boss_count = (wave // 3) - 1
        hp = 10000 * (3 ** boss_count)
        super().__init__(pos, color=(180, 0, 0), radius=100, hp=hp, score_value=3000)
        self.damage_mult = 1.0 + (boss_count * 1.2)  # 50% more damage each time
        self.target_pos = pygame.math.Vector2(WIDTH//2, 200)
        self.summon_timer = 15.0  # Special summon every 15 seconds
        self.base_color = (180, 0, 0)
        self.wave = wave

    def update_behavior(self, player, current_time, dt, enemy_group, bullets_group):
        # Move to center top, but stay within screen
        self.target_pos.x = clamp(player.pos.x, self.radius, WIDTH - self.radius)
        self.target_pos.y = 150  # Stay at top

        if (self.pos - self.target_pos).length() > 5:
            self.vel = normalize_safe(self.target_pos - self.pos) * self.speed
        else:
            self.vel = pygame.math.Vector2(0, 0)

        self.attack_timer -= dt
        self.summon_timer -= dt

        if self.summon_timer <= 0:
            self.state = "summoning"
            self.state_timer = 2.0  # 2 seconds of pulsing
            self.summon_timer = 15.0
            self.attack_timer = 3.0  # Pause other attacks
        if self.attack_timer <= 0 and self.state == "idle":
            r = random.random()
            if r < 0.4:
                self.state = "normal"
                self.attack_timer = 1.5  # Duration
            elif r < 0.7:
                self.state = "aoe"
                self.state_timer = 0.5  # Windup
                self.attack_timer = 2.5  # Total time
            else:
                self.state = "special"
                self.state_timer = 2.5  # Duration
                self.attack_timer = 3.0  # Total time

        if self.state == "normal":
            # Spiral Barrage: Bullets spiral out with increasing speed
            if int(current_time * 15) % 2 == 0:
                for i in range(3):
                    angle = (current_time * 180) + (i * 120)
                    rad = math.radians(angle)
                    dir_vec = pygame.math.Vector2(math.cos(rad), math.sin(rad))
                    p = Bullet(self.pos, dir_vec * 250, owner="enemy", damage=15 * getattr(self, "damage_mult", 1.0) *
                               self.damage_mult, color=(255, 50, 50), radius=8)
                    bullets_group.append(p)
            if self.attack_timer <= 0:
                self.state = "idle"

        elif self.state == "aoe":
            self.state_timer -= dt
            # Visual charge effect
            self.color = (255, 255, 255) if int(current_time * 20) % 2 == 0 else (180, 0, 0)
            if self.state_timer <= 0:
                # Triple Shock Ring with different speeds
                for speed_mult in [1.0, 1.5, 2.0]:
                    for angle in range(0, 360, 15):
                        rad = math.radians(angle)
                        dir_vec = pygame.math.Vector2(math.cos(rad), math.sin(rad))
                        p = Bullet(self.pos, dir_vec * (200 * speed_mult), owner="enemy", damage=20 *
                                   self.damage_mult, color=(255, 100, 100), radius=int(10 + (speed_mult * 2)))
                        bullets_group.append(p)
                self.color = (180, 0, 0)
                self.state = "idle"

        elif self.state == "special":
            self.state_timer -= dt
            if self.state_timer > 0:
                # Core Overload: Rapid fire aimed at player + random spray
                if int(current_time * 20) % 2 == 0:
                    # Aimed shot
                    aim_dir = normalize_safe(player.pos - self.pos)
                    p1 = Bullet(self.pos, aim_dir * 500, owner="enemy", damage=12 *
                                self.damage_mult, color=(255, 0, 0), radius=10)
                    bullets_group.append(p1)

                    # Random spray
                    angle = random.uniform(0, 360)
                    rad = math.radians(angle)
                    dir_vec = pygame.math.Vector2(math.cos(rad), math.sin(rad))
                    p2 = Bullet(self.pos, dir_vec * random.uniform(200, 600), owner="enemy",
                                damage=8 * self.damage_mult, color=(255, 150, 0), radius=8)
                    bullets_group.append(p2)
            else:
                self.state = "idle"

        elif self.state == "summoning":
            self.state_timer -= dt
            # Pulse visual: Darker red then bright
            if self.state_timer > 1.0:
                # Darken
                t = 2.0 - self.state_timer  # 0 to 1
                self.color = lerp_color(self.base_color, (40, 0, 0), t)
            else:
                # Brighten
                t = 1.0 - self.state_timer  # 0 to 1
                self.color = lerp_color((40, 0, 0), (255, 100, 100), t)

            if self.state_timer <= 0:
                # Spawn 8 spawners
                for i in range(8):
                    angle = i * (360 / 8)
                    rad = math.radians(angle)
                    offset = pygame.math.Vector2(math.cos(rad), math.sin(rad)) * 150
                    spawn_pos = self.pos + offset
                    # Using SwarmerBot as the "spawner" enemy that goes after player
                    s = SwarmerBot(spawn_pos, stage=1, wave=self.wave)
                    enemy_group.append(s)
                self.color = self.base_color
                self.state = "idle"

class OrangeJuggernautBoss(BossBase):
    def __init__(self, pos, wave):
        boss_count = (wave // 3) - 1
        hp = 15000 * (3 ** boss_count)
        super().__init__(pos, color=(255, 140, 0), radius=110, hp=hp, score_value=3000)
        self.damage_mult = 1.0 + (boss_count * 1.2)
        self.speed = 120
        self.base_speed = 120

    def update_behavior(self, player, current_time, dt, bullets_group):
        self.attack_timer -= dt

        # Keep on screen
        self.pos.x = clamp(self.pos.x, self.radius, WIDTH - self.radius)
        self.pos.y = clamp(self.pos.y, self.radius, HEIGHT - self.radius)

        if self.state == "idle":
            self.vel = normalize_safe(player.pos - self.pos) * self.speed
            if self.attack_timer <= 0:
                r = random.random()
                if r < 0.3:
                    self.state = "normal"
                elif r < 0.6:
                    self.state = "aoe"
                elif r < 0.8:
                    self.state = "slam"
                else:
                    self.state = "special"
                self.state_timer = 1.0  # Windup/Duration

        elif self.state == "normal":
            # Heavy Charge: Straight dash with fire trail
            self.state_timer -= dt
            if not hasattr(self, "dash_dir"):
                self.dash_dir = normalize_safe(player.pos - self.pos)

            if self.state_timer > 0:
                self.vel = self.dash_dir * (self.speed * 4)
                # Leave fire trail
                if int(current_time * 30) % 2 == 0:
                    p = Bullet(self.pos, pygame.math.Vector2(0, 0), owner="enemy",
                               damage=10 * self.damage_mult, color=(255, 69, 0), radius=20)
                    p.lifetime = 1.0
                    bullets_group.append(p)
            else:
                if hasattr(self, "dash_dir"):
                    delattr(self, "dash_dir")
                self.state = "idle"
                self.attack_timer = 2.0

        elif self.state == "aoe":
            # Earthquake: Multiple waves of expanding circles
            self.state_timer -= dt
            self.vel = pygame.math.Vector2(0, 0)
            if int(current_time * 10) % 3 == 0:
                for angle in range(0, 360, 30):
                    rad = math.radians(angle + current_time * 50)
                    dir_vec = pygame.math.Vector2(math.cos(rad), math.sin(rad))
                    p = Bullet(self.pos, dir_vec * 300, owner="enemy", damage=25 *
                               self.damage_mult, color=(255, 140, 0), radius=15)
                    bullets_group.append(p)
            if self.state_timer <= 0:
                self.state = "idle"
                self.attack_timer = 3.0

        elif self.state == "special":
            # Meteor Shower: Rain bullets from above
            self.state_timer -= dt
            self.speed = self.base_speed * 0.5  # Slow down while summoning
            self.vel = normalize_safe(player.pos - self.pos) * self.speed
            if int(current_time * 15) % 2 == 0:
                # Spawn meteor at random top position aiming down
                spawn_x = random.uniform(0, WIDTH)
                p = Bullet(pygame.math.Vector2(spawn_x, 0), pygame.math.Vector2(0, 600),
                           owner="enemy", damage=35 * self.damage_mult, color=(255, 50, 0), radius=25)
                bullets_group.append(p)
            if self.state_timer <= -2.0:
                self.speed = self.base_speed
                self.state = "idle"
                self.attack_timer = 4.0

        elif self.state == "slam":
            # Ground Slam: Jump and slam for massive AOE
            self.state_timer -= dt
            if self.state_timer > 0.5:
                # Windup: Move towards player slowly
                self.vel = normalize_safe(player.pos - self.pos) * (self.speed * 0.5)
                # Visual: Pulse orange
                self.color = (255, 255, 255) if int(current_time * 15) % 2 == 0 else (255, 140, 0)
            elif self.state_timer > 0:
                # Jump: Stop moving
                self.vel = pygame.math.Vector2(0, 0)
                self.color = (255, 255, 255)
            else:
                # Slam: Release massive ring of bullets
                for angle in range(0, 360, 10):
                    rad = math.radians(angle)
                    dir_vec = pygame.math.Vector2(math.cos(rad), math.sin(rad))
                    p = Bullet(self.pos, dir_vec * 400, owner="enemy", damage=30 *
                               self.damage_mult, color=(255, 69, 0), radius=25)
                    bullets_group.append(p)
                self.color = (255, 140, 0)
                self.state = "idle"
                self.attack_timer = 3.0

class YellowEyeBoss(BossBase):
    def __init__(self, pos, wave):
        boss_count = (wave // 3) - 1
        hp = 20000 * (3 ** boss_count)
        super().__init__(pos, color=(255, 255, 0), radius=90, hp=hp, score_value=3000)
        self.damage_mult = 1.0 + (boss_count * 1.2)
        self.speed = 80
        self.attack_timer = 2.0

    def update_behavior(self, player, current_time, dt, bullets_group):
        # Movement: Float away
        dist = (player.pos - self.pos).length()
        if dist < 400:
            self.vel = normalize_safe(self.pos - player.pos) * self.speed
        else:
            self.vel = pygame.math.Vector2(0, 0)

        self.attack_timer -= dt
        if self.attack_timer <= 0:
            r = random.random()
            if r < 0.4:
                self.state = "normal"
            elif r < 0.7:
                self.state = "aoe"
            else:
                self.state = "special"
            self.state_timer = 2.0

        if self.state == "normal":
            # Sniper Beam: High speed, high damage aimed shot with warning
            self.state_timer -= dt
            self.vel = pygame.math.Vector2(0, 0)
            if self.state_timer > 0:
                # Flash before firing
                self.color = (255, 255, 255) if int(current_time * 30) % 2 == 0 else (255, 255, 0)
            else:
                aim_dir = normalize_safe(player.pos - self.pos)
                for i in range(5):  # Fire a burst
                    p = Bullet(self.pos, aim_dir * (1000 + i * 100), owner="enemy",
                               damage=30 * self.damage_mult, color=(255, 255, 0), radius=15)
                    bullets_group.append(p)
                self.color = (255, 255, 0)
                self.state = "idle"
                self.attack_timer = 2.0

        elif self.state == "aoe":
            # Solar Flare: Expanding sun-like projectiles
            self.state_timer -= dt
            if int(current_time * 12) % 2 == 0:
                angle_offset = current_time * 100
                for angle in range(0, 360, 30):
                    rad = math.radians(angle + angle_offset)
                    dir_vec = pygame.math.Vector2(math.cos(rad), math.sin(rad))
                    p = Bullet(self.pos, dir_vec * 350, owner="enemy", damage=20 *
                               self.damage_mult, color=(255, 255, 150), radius=12)
                    bullets_group.append(p)
            if self.state_timer <= 0:
                self.state = "idle"
                self.attack_timer = 3.0

        elif self.state == "special":
            # Orbital Strike: Massive shotgun blast
            self.state_timer -= dt
            if int(current_time * 15) % 3 == 0:
                aim_dir = normalize_safe(player.pos - self.pos)
                for spread in range(-20, 21, 10):
                    rad = math.radians(aim_dir.angle_to(pygame.math.Vector2(1, 0)) + spread)
                    dir_vec = pygame.math.Vector2(math.cos(rad), -math.sin(rad))
                    p = Bullet(self.pos, dir_vec * 500, owner="enemy", damage=15 * getattr(self, "damage_mult", 1.0), color=(255, 255, 255), radius=14)
                    bullets_group.append(p)
            if self.state_timer <= 0:
                self.state = "idle"
                self.attack_timer = 4.0

        elif self.state == "minigun":
            # Minigun: Rapid fire, slow bullets
            self.state_timer -= dt
            if int(current_time * 25) % 2 == 0:
                aim_dir = normalize_safe(player.pos - self.pos)
                # Add slight random spread
                spread = random.uniform(-15, 15)
                rad = math.radians(aim_dir.angle_to(pygame.math.Vector2(1, 0)) + spread)
                dir_vec = pygame.math.Vector2(math.cos(rad), -math.sin(rad))
                p = Bullet(self.pos, dir_vec * 250, owner="enemy", damage=8, color=(255, 255, 0), radius=8)
                bullets_group.append(p)
            if self.state_timer <= 0:
                self.state = "idle"
                self.attack_timer = 2.0

class StatusPool(pygame.sprite.Sprite):
    def __init__(self, pos, type):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.type = type  # "poison", "fire", "ice"
        self.radius = 80  # Increased from 60
        self.lifetime = 8.0  # Increased from 7.0
        self.colors = {"poison": (100, 255, 100, 100), "fire": (255, 100, 0, 100), "ice": (100, 200, 255, 100)}
        self.color = self.colors[type]
        self.last_tick = 0
        self.is_landing = True
        self.landing_timer = 1.2  # 1.2 seconds before it "lands" and becomes active

    def update(self, dt, player, current_time):
        if self.is_landing:
            self.landing_timer -= dt
            if self.landing_timer <= 0:
                self.is_landing = False
            return

        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
            return

        dist = (player.pos - self.pos).length()
        if dist <= self.radius + player.radius:
            if self.type == "poison":
                if current_time - self.last_tick >= 1.0:  # Tick every 1s instead of 2s
                    damage = player.calculate_health() * 0.08  # Increased from 5% to 8%
                    player.health -= damage
                    self.last_tick = current_time
            elif self.type == "fire":
                player.health -= 30 * dt  # Doubled damage from 15 to 30
            elif self.type == "ice":
                player.speed_mult = 0.3  # Increased slow from 0.5 to 0.3

    def draw(self, surface):
        if self.is_landing:
            # Draw landing indicator (pulsing circle)
            alpha = int(100 + 155 * (math.sin(pygame.time.get_ticks() * 0.01) + 1) / 2)
            color = (self.color[0], self.color[1], self.color[2], alpha)
            s = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (self.radius, self.radius), self.radius, 2)
            surface.blit(s, (int(self.pos.x - self.radius), int(self.pos.y - self.radius)))
        else:
            s = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
            pygame.draw.circle(s, self.color, (self.radius, self.radius), self.radius)
            surface.blit(s, (int(self.pos.x - self.radius), int(self.pos.y - self.radius)))

class WitchBot(EnemyBase):
    def __init__(self, pos, wave=0):
        hp = 120 * (1 + wave * 0.85)
        score = 40 * (1 + wave * 0.2)
        super().__init__(pos, color=(100, 0, 150), radius=16, speed=110, hp=hp, score_value=score)
        self.wave = wave
        self.throw_timer = random.uniform(2, 4)

    def update_behavior(self, player, current_time, dt, pools_group):
        dist = (player.pos - self.pos).length()
        if dist < 400:
            self.vel = normalize_safe(self.pos - player.pos) * self.speed
        elif dist > 600:
            self.vel = normalize_safe(player.pos - self.pos) * self.speed
        else:
            self.vel = pygame.math.Vector2(0, 0)

        self.throw_timer -= dt
        if self.throw_timer <= 0:
            self.throw_timer = random.uniform(2.5, 4.0)  # Throws more frequently
            # Predict player movement for throwing
            target = player.pos + player.velocity * 0.8 + pygame.math.Vector2(random.uniform(-50, 50), random.uniform(-50, 50))
            type = random.choice(["poison", "fire", "ice"])
            pools_group.append(StatusPool(target, type))

    def draw(self, surface):
        s = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (100, 0, 150, 180), (self.radius, self.radius), self.radius)
        surface.blit(s, (int(self.pos.x - self.radius), int(self.pos.y - self.radius)))

class SniperBot(EnemyBase):
    def __init__(self, pos, wave=0):
        hp = 100 * (1 + wave * 0.85)
        score = 50 * (1 + wave * 0.2)
        super().__init__(pos, color=(0, 150, 100), radius=15, speed=90, hp=hp, score_value=score)
        self.wave = wave
        self.aim_timer = 1.5  # Reduced from 3.0
        self.is_aiming = False
        self.aim_target = pygame.math.Vector2(0, 0)

    def update_behavior(self, player, current_time, dt, bullets_group):
        dist = (player.pos - self.pos).length()
        if dist < 600:  # Increased range
            self.vel = normalize_safe(self.pos - player.pos) * self.speed
        else:
            self.vel = pygame.math.Vector2(0, 0)

        self.aim_timer -= dt
        if self.aim_timer <= 0:
            if not self.is_aiming:
                self.is_aiming = True
                self.aim_timer = 0.8  # Aim for 0.8 seconds (Reduced from 2.0)
                self.aim_target = player.pos.copy()
            else:
                aim_dir = normalize_safe(self.aim_target - self.pos)
                # Increased damage to 40% of player health
                p = Bullet(self.pos, aim_dir * 2000, owner="enemy",
                           damage=player.calculate_health() * 0.40 * getattr(self, "damage_mult", 1.0), color=(0, 255, 200), radius=12)
                bullets_group.append(p)
                self.is_aiming = False
                self.aim_timer = random.uniform(1.5, 2.5)  # Reduced from 3-5s

        if self.is_aiming:
            self.aim_target += (player.pos - self.aim_target) * 0.05

    def draw(self, surface):
        super().draw(surface)
        if self.is_aiming:
            pygame.draw.line(surface, (0, 255, 200, 100), self.pos, self.aim_target, 1)
            pygame.draw.circle(surface, (0, 255, 200), (int(self.aim_target.x), int(self.aim_target.y)), 5, 1)

class ScoreDisplay:
    def __init__(self, font, initial_score=0, pos=(WIDTH-140, 20)):
        self.font = font
        self.score = initial_score
        self.display_score = initial_score
        self.pos = pos
        self.pop_scale = 1.0
        self.last_score = initial_score

    def update(self, new_score, dt):
        # Smooth increase display
        self.display_score += (new_score - self.display_score) * min(10 * dt, 1)

        # Pop effect on score increase
        if new_score > self.last_score:
            self.pop_scale = 1.3  # start bigger
        self.pop_scale = max(1.0, self.pop_scale - dt * 5)  # shrink back to 1.0
        self.last_score = new_score

    def draw(self, surface):
        score_text = f"Score: {int(self.display_score)}"
        text_surf = self.font.render(score_text, True, (255, 255, 255))
        # Scale for pop animation
        w, h = text_surf.get_size()
        scaled_surf = pygame.transform.smoothscale(text_surf, (int(w * self.pop_scale), int(h * self.pop_scale)))
        surface.blit(scaled_surf, (self.pos[0] - scaled_surf.get_width(), self.pos[1]))


class AncientOneBoss(BossBase):
    def __init__(self, pos, wave):
        boss_count = (wave // 3) - 1
        hp = 50000 * (3 ** boss_count)
        super().__init__(pos, color=DARK_GREY, radius=120, hp=hp, score_value=10000)
        self.summon_timer = 4.0
        self.screen_split_timer = 7.0
        self.stone_brick_timer = 2.0
        self.wave = wave
        self.float_offset = 0
        self.aura_particles = []
        self.shake_timer = 0
        self.phase = 1
        self.glitch_timer = 0

    def update_behavior(self, player, current_time, dt, enemy_group, bullets_group, game):
        # Boss entry state handling
        if self.state == "entry":
            target = pygame.math.Vector2(WIDTH//2, HEIGHT//3)
            if (self.pos - target).length() > 5:
                self.vel = normalize_safe(target - self.pos) * self.speed
            else:
                self.vel = pygame.math.Vector2(0, 0)
                self.state = "idle"
                game.screen_shake_timer = 1.0
            return

        # Phase logic
        hp_ratio = self.hp / self.max_hp
        if hp_ratio < 0.4 and self.phase == 1:
            self.phase = 2
            game.screen_shake_timer = 1.5
            self.glitch_timer = 1.0

        # Idle floating movement
        self.float_offset += dt * 2
        float_amp = 30 if self.phase == 1 else 60
        target = pygame.math.Vector2(WIDTH//2, HEIGHT//3 + math.sin(self.float_offset) * float_amp)
        
        if (self.pos - target).length() > 5:
            self.vel = normalize_safe(target - self.pos) * (self.speed * (1 if self.phase == 1 else 1.5))
        else:
            self.vel = pygame.math.Vector2(0, 0)
            
        self.summon_timer -= dt
        self.screen_split_timer -= dt
        self.stone_brick_timer -= dt
        if self.glitch_timer > 0: self.glitch_timer -= dt

        # 1. Summon Mini Bosses
        if self.summon_timer <= 0:
            self.summon_timer = 4.0 if self.phase == 1 else 3.0
            b_type = random.choice(["red_core", "orange_jugg", "yellow_eye"])
            mini = self.create_mini_boss(b_type, self.pos.copy())
            enemy_group.append(mini)

        # 2. Screen Split Attack
        if self.screen_split_timer <= 0:
            self.screen_split_timer = 7.0 if self.phase == 1 else 5.0
            # Guaranteed damage = half of current health
            damage = player.health / 1.5
            game.apply_damage_to_player(damage)
            game.screen_split_effect_timer = 1.0
            game.screen_shake_timer = 0.5
    
        # 3. Stone Brick Attack
        if self.stone_brick_timer <= 0:
            self.stone_brick_timer = 2.0 if self.phase == 1 else 1.2
            # Throw from random edge
            side = random.randint(0, 3)
            if side == 0: start_pos = pygame.math.Vector2(random.randint(0, WIDTH), -50)
            elif side == 1: start_pos = pygame.math.Vector2(random.randint(0, WIDTH), HEIGHT + 50)
            elif side == 2: start_pos = pygame.math.Vector2(-50, random.randint(0, HEIGHT))
            else: start_pos = pygame.math.Vector2(WIDTH + 50, random.randint(0, HEIGHT))
            
            target_pos = pygame.math.Vector2(random.randint(100, WIDTH-100), random.randint(100, HEIGHT-100))
            vel = normalize_safe(target_pos - start_pos) * (450 if self.phase == 1 else 600)
            brick = StoneBrick(start_pos, vel, game)
            bullets_group.append(brick)
            
        # Aura particles update
        if random.random() < 0.3:
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(self.radius, self.radius * 1.5)
            p_pos = self.pos + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * dist
            self.aura_particles.append({
                "pos": p_pos,
                "vel": pygame.math.Vector2(math.cos(angle), math.sin(angle)) * random.uniform(20, 50),
                "life": 1.0,
                "color": random.choice([(40, 40, 40), (20, 20, 20), (100, 0, 255)])
            })
        
        for p in list(self.aura_particles):
            p["pos"] += p["vel"] * dt
            p["life"] -= dt
            if p["life"] <= 0:
                self.aura_particles.remove(p)

    def create_mini_boss(self, b_type, pos):
        if b_type == "red_core": m = RedCoreBoss(pos, self.wave)
        elif b_type == "orange_jugg": m = OrangeJuggernautBoss(pos, self.wave)
        else: m = YellowEyeBoss(pos, self.wave)
        m.max_hp /= 1.5
        m.hp = m.max_hp
        m.radius /= 2
        m.damage_mult = 2
        m.is_boss = False
        m.state = "idle" # Skip entry state for minis
        return m

    def draw(self, surface):
        # Final boss visual effects
        ticks = pygame.time.get_ticks()
        pulse = (math.sin(ticks * 0.005) + 1) / 2
        
        # Glitch effect
        draw_pos = self.pos.copy()
        if self.glitch_timer > 0 or (self.phase == 2 and random.random() < 0.1):
            draw_pos.x += random.uniform(-10, 10)
            draw_pos.y += random.uniform(-10, 10)

        # Dark outer glow with multiple layers
        glow_size = int(self.radius * 3)
        s = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        for r in range(glow_size, self.radius, -10):
            alpha = int(120 * (1 - (r - self.radius) / (glow_size - self.radius)) * pulse)
            color = (10, 10, 15, alpha) if self.phase == 1 else (30, 0, 50, alpha)
            pygame.draw.circle(s, color, (glow_size, glow_size), r)
        surface.blit(s, (int(draw_pos.x - glow_size), int(draw_pos.y - glow_size)))
        
        # Aura particles
        for p in self.aura_particles:
            alpha = int(255 * p["life"])
            p_s = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(p_s, (*p["color"], alpha), (5, 5), 3)
            surface.blit(p_s, (int(p["pos"].x - 5), int(p["pos"].y - 5)))

        # Main body - Void Sphere
        body_color = (20, 20, 25) if self.phase == 1 else (10, 0, 20)
        pygame.draw.circle(surface, body_color, (int(draw_pos.x), int(draw_pos.y)), self.radius)
        
        # Void cracks / energy lines
        for i in range(8):
            angle = (ticks * 0.001 + i * (math.pi / 4))
            crack_color = (100, 100, 255) if self.phase == 1 else (200, 50, 255)
            p1 = draw_pos + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * (self.radius * 0.4)
            p2 = draw_pos + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * (self.radius * 0.9)
            pygame.draw.line(surface, crack_color, p1, p2, 3)

        # Central Core (Replacing eyes)
        core_pulse = (math.sin(ticks * 0.01) + 1) / 2
        core_color = (60, 60, 200) if self.phase == 1 else (150, 0, 255)
        core_radius = 30 + core_pulse * 10
        
        # Core glow
        core_s = pygame.Surface((core_radius * 4, core_radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(core_s, (*core_color, 100), (core_radius * 2, core_radius * 2), core_radius * 2)
        surface.blit(core_s, (int(draw_pos.x - core_radius * 2), int(draw_pos.y - core_radius * 2)))
        
        # Core center
        pygame.draw.circle(surface, core_color, (int(draw_pos.x), int(draw_pos.y)), core_radius)
        pygame.draw.circle(surface, WHITE, (int(draw_pos.x), int(draw_pos.y)), core_radius * 0.6)

class Game:
    MAIN_MENU = 0
    GAME_RUNNING = 1
    LEADERBOARD = 2
    UPGRADE_SCREEN = 4
    CLASS_SELECTION_SCREEN = 5
    ABILITY_SELECTION_SCREEN = 6
    GUIDE = 7
    PLAYABLE_TUTORIAL = 8
    
    def draw_ui_background(self):
        # Dark mysterious background with subtle gradient and particles
        self.screen.fill((10, 10, 20))
        
        # Draw some subtle "mysterious" particles
        if not hasattr(self, 'ui_particles'):
            self.ui_particles = []
            for _ in range(60): # Increased particle count
                self.ui_particles.append({
                    'pos': [random.uniform(0, WIDTH), random.uniform(0, HEIGHT)],
                    'vel': [random.uniform(-15, 15), random.uniform(-15, 15)],
                    'size': random.uniform(1, 4),
                    'alpha': random.uniform(40, 150), # Increased alpha
                    'color': random.choice([(100, 150, 255), (150, 100, 255), (80, 200, 255)]) # Varied mysterious colors
                })
        
        dt = self.clock.get_time() / 1000.0
        timer = pygame.time.get_ticks() * 0.001
        
        # Draw a very subtle radial gradient or glow in the center
        center_glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for r in range(400, 0, -50):
            alpha = int(15 * (1 - r/400))
            pygame.draw.circle(center_glow, (50, 50, 100, alpha), (WIDTH//2, HEIGHT//2), r)
        self.screen.blit(center_glow, (0, 0))
        
        for p in self.ui_particles:
            p['pos'][0] += p['vel'][0] * dt
            p['pos'][1] += p['vel'][1] * dt
            if p['pos'][0] < 0: p['pos'][0] = WIDTH
            if p['pos'][0] > WIDTH: p['pos'][0] = 0
            if p['pos'][1] < 0: p['pos'][1] = HEIGHT
            if p['pos'][1] > HEIGHT: p['pos'][1] = 0
            
            # Subtle pulse based on time
            pulse = (math.sin(timer * 2 + p['pos'][0] * 0.01) + 1) / 2
            current_alpha = int(p['alpha'] * (0.5 + 0.5 * pulse))
            
            s = pygame.Surface((p['size']*4, p['size']*4), pygame.SRCALPHA)
            # Draw a small glow for each particle
            pygame.draw.circle(s, (*p['color'], current_alpha // 2), (p['size']*2, p['size']*2), p['size']*2)
            pygame.draw.circle(s, (*p['color'], current_alpha), (p['size']*2, p['size']*2), p['size'])
            self.screen.blit(s, (int(p['pos'][0] - p['size']*2), int(p['pos'][1] - p['size']*2)))

    def draw_glow_text(self, text, font, color, pos, glow_color=(255, 255, 255), glow_radius=5):
        # Render the glow
        glow_surf = font.render(text, True, glow_color)
        for ox, oy in [(-1,-1), (1,-1), (-1,1), (1,1), (0,-2), (0,2), (-2,0), (2,0)]:
            self.screen.blit(glow_surf, (pos[0] + ox, pos[1] + oy))
        
        # Render the main text
        main_surf = font.render(text, True, color)
        self.screen.blit(main_surf, pos)

    def draw_custom_button(self, label, rect, is_hovered, animation_timer):
        # Clean, mysterious button style
        base_color = (30, 30, 45)
        hover_color = (45, 45, 70)
        border_color = (100, 100, 150)
        glow_color = (150, 150, 255)
        
        if is_hovered:
            # Pulsing glow effect
            glow_amt = (math.sin(animation_timer * 10) + 1) / 2
            current_border = lerp_color(border_color, glow_color, glow_amt)
            current_bg = hover_color
            # Slight expansion
            rect = rect.inflate(4, 4)
        else:
            current_border = border_color
            current_bg = base_color
            
        # Draw button body
        pygame.draw.rect(self.screen, current_bg, rect, border_radius=8)
        pygame.draw.rect(self.screen, current_border, rect, 2, border_radius=8)
        
        # Draw text
        btn_font = pygame.font.SysFont("arial", 24, bold=True)
        text_surf = btn_font.render(label, True, WHITE)
        text_pos = (rect.centerx - text_surf.get_width()//2, rect.centery - text_surf.get_height()//2)
        self.screen.blit(text_surf, text_pos)
        
        return rect

    def draw_main_menu(self):
        self.draw_ui_background()
        
        # Animated Title
        title_font = pygame.font.SysFont("arial", 80, bold=True)
        title_text = "CHALLENGER ARENA"
        
        # Floating effect
        timer = pygame.time.get_ticks() * 0.002
        title_y = 100 + 10 * math.sin(timer)
        
        # Draw title with glow
        title_surf = title_font.render(title_text, True, WHITE)
        title_pos = (WIDTH//2 - title_surf.get_width()//2, title_y)
        
        # Subtle "glitch" or "shimmer" effect on title
        if random.random() < 0.02:
            off_x = random.randint(-2, 2)
            self.draw_glow_text(title_text, title_font, (200, 200, 255), (title_pos[0]+off_x, title_pos[1]), (100, 100, 255))
        else:
            self.draw_glow_text(title_text, title_font, WHITE, title_pos, (50, 50, 150))

        # Draw menu buttons
        self.button_rects = []
        mouse_pos = pygame.mouse.get_pos()
        
        for i, btn in enumerate(self.menu_buttons):
            base_rect = pygame.Rect(WIDTH//2 - 150, 280 + i*70, 300, 50)
            is_hover = base_rect.collidepoint(mouse_pos)
            
            # Entrance animation (slide in)
            if not hasattr(self, 'menu_entrance_timer'): self.menu_entrance_timer = 0
            self.menu_entrance_timer = min(1.0, self.menu_entrance_timer + 0.01)
            
            final_rect = self.draw_custom_button(btn["label"], base_rect, is_hover, timer)
            self.button_rects.append(final_rect)

        # Draw last run stats with a clean "card" look
        if self.last_run_stats:
            stats_rect = pygame.Rect(WIDTH//2 - 200, HEIGHT - 150, 400, 100)
            pygame.draw.rect(self.screen, (20, 20, 35, 150), stats_rect, border_radius=12)
            pygame.draw.rect(self.screen, (80, 80, 120), stats_rect, 1, border_radius=12)
            
            stats_font = pygame.font.SysFont("arial", 20, bold=True)
            go_surf = stats_font.render("PREVIOUS RUN", True, (150, 150, 200))
            self.screen.blit(go_surf, (WIDTH//2 - go_surf.get_width()//2, stats_rect.y + 15))
            
            stats_text = f"Score: {int(self.last_run_stats['score'])}  |  Time: {self.last_run_stats['time']:.1f}s"
            val_surf = stats_font.render(stats_text, True, YELLOW)
            self.screen.blit(val_surf, (WIDTH//2 - val_surf.get_width()//2, stats_rect.y + 50))

        # Draw Effects
        if self.tether_haze_timer > 0:
            self.tether_haze_timer -= dt
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            # Black haze border
            pygame.draw.rect(s, (0, 0, 0, 180), (0, 0, WIDTH, HEIGHT), 60)
            self.screen.blit(s, (0, 0))
            
        if self.screen_split_effect_timer > 0:
            self.screen_split_effect_timer -= dt
            # Red split line
            pygame.draw.line(self.screen, (255, 0, 0), (WIDTH//2, 0), (WIDTH//2, HEIGHT), 15)
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((255, 0, 0, 40))
            self.screen.blit(s, (0, 0))

        pygame.display.flip()

    def draw_leaderboard(self):
        self.draw_ui_background()
        
        title_font = pygame.font.SysFont("arial", 50, bold=True)
        self.draw_glow_text("HALL OF FAME", title_font, WHITE, (WIDTH//2 - 180, 50), (50, 50, 150))
        
        # Leaderboard Container
        container_rect = pygame.Rect(WIDTH//2 - 350, 130, 700, 400)
        pygame.draw.rect(self.screen, (25, 25, 40), container_rect, border_radius=15)
        pygame.draw.rect(self.screen, (60, 60, 90), container_rect, 2, border_radius=15)
        
        # Header
        header_font = pygame.font.SysFont("arial", 20, bold=True)
        headers = ["RANK", "CLASS", "WAVE", "TIME", "SCORE"]
        x_offsets = [50, 150, 300, 450, 600]
        for h, x in zip(headers, x_offsets):
            h_surf = header_font.render(h, True, (150, 150, 200))
            self.screen.blit(h_surf, (container_rect.x + x - h_surf.get_width()//2, container_rect.y + 20))
            
        pygame.draw.line(self.screen, (60, 60, 90), (container_rect.x + 20, container_rect.y + 50), (container_rect.right - 20, container_rect.y + 50), 1)
        
        # Entries
        entry_font = pygame.font.SysFont("arial", 18)
        for idx, entry in enumerate(self.leaderboard[:8]): # Show top 8
            y = container_rect.y + 70 + idx * 40
            
            # Alternating row highlight
            if idx % 2 == 0:
                pygame.draw.rect(self.screen, (35, 35, 55), (container_rect.x + 5, y - 5, container_rect.width - 10, 35), border_radius=5)
            
            # Rank color
            rank_color = WHITE
            if idx == 0: rank_color = (255, 215, 0) # Gold
            elif idx == 1: rank_color = (192, 192, 192) # Silver
            elif idx == 2: rank_color = (205, 127, 50) # Bronze
            
            vals = [
                f"#{idx+1}",
                str(entry.get('class', '???')),
                str(entry.get('wave', 0)),
                f"{int(entry.get('time', 0))}s",
                f"{int(entry.get('score', 0))}"
            ]
            
            for v, x in zip(vals, x_offsets):
                v_surf = entry_font.render(v, True, rank_color if x == 50 else WHITE)
                self.screen.blit(v_surf, (container_rect.x + x - v_surf.get_width()//2, y))

        # Back button
        mouse_pos = pygame.mouse.get_pos()
        back_rect = pygame.Rect(WIDTH//2 - 75, HEIGHT - 100, 150, 45)
        is_hover = back_rect.collidepoint(mouse_pos)
        self.leaderboard_back_rect = self.draw_custom_button("BACK", back_rect, is_hover, pygame.time.get_ticks()*0.002)

        # Draw Effects
        if self.tether_haze_timer > 0:
            self.tether_haze_timer -= dt
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            # Black haze border
            pygame.draw.rect(s, (0, 0, 0, 180), (0, 0, WIDTH, HEIGHT), 60)
            self.screen.blit(s, (0, 0))
            
        if self.screen_split_effect_timer > 0:
            self.screen_split_effect_timer -= dt
            # Red split line
            pygame.draw.line(self.screen, (255, 0, 0), (WIDTH//2, 0), (WIDTH//2, HEIGHT), 15)
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((255, 0, 0, 40))
            self.screen.blit(s, (0, 0))

        pygame.display.flip()

    def draw_tutorial(self):
        self.draw_ui_background()
        
        if self.tutorial_section is None:
            self.draw_tutorial_grid(self.screen)
        else:
            # Content background
            content_rect = pygame.Rect(50, 100, WIDTH - 100, HEIGHT - 200)
            pygame.draw.rect(self.screen, (20, 20, 35), content_rect, border_radius=20)
            pygame.draw.rect(self.screen, (60, 60, 90), content_rect, 2, border_radius=20)
            self.draw_tutorial_content(self.screen)
            
        # Draw Effects
        if self.tether_haze_timer > 0:
            self.tether_haze_timer -= dt
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            # Black haze border
            pygame.draw.rect(s, (0, 0, 0, 180), (0, 0, WIDTH, HEIGHT), 60)
            self.screen.blit(s, (0, 0))
            
        if self.screen_split_effect_timer > 0:
            self.screen_split_effect_timer -= dt
            # Red split line
            pygame.draw.line(self.screen, (255, 0, 0), (WIDTH//2, 0), (WIDTH//2, HEIGHT), 15)
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((255, 0, 0, 40))
            self.screen.blit(s, (0, 0))

        pygame.display.flip()

    def draw_tutorial_grid(self, surf):
        title_font = pygame.font.SysFont("arial", 50, bold=True)
        self.draw_glow_text("ACADEMY GUIDE", title_font, WHITE, (WIDTH//2 - 200, 50), (50, 50, 150))
        
        self.tutorial_buttons = []
        cols, rows = 3, 2
        box_w, box_h = 260, 160
        margin_x, margin_y = 30, 30
        start_x = (WIDTH - (cols * box_w + (cols-1) * margin_x)) // 2
        start_y = 150
        
        mouse_pos = pygame.mouse.get_pos()
        timer = pygame.time.get_ticks() * 0.002
        
        for i, section in enumerate(self.tutorial_sections):
            c, r = i % cols, i // cols
            x = start_x + c * (box_w + margin_x)
            y = start_y + r * (box_h + margin_y)
            
            base_rect = pygame.Rect(x, y, box_w, box_h)
            is_hover = base_rect.collidepoint(mouse_pos)
            
            # Clean card style
            bg_color = (40, 40, 60) if is_hover else (30, 30, 45)
            border_color = (150, 150, 255) if is_hover else (80, 80, 120)
            
            pygame.draw.rect(surf, bg_color, base_rect, border_radius=15)
            pygame.draw.rect(surf, border_color, base_rect, 2 if is_hover else 1, border_radius=15)
            
            # Section Title
            sec_font = pygame.font.SysFont("arial", 28, bold=True)
            text = sec_font.render(section, True, WHITE)
            surf.blit(text, (base_rect.centerx - text.get_width()//2, base_rect.centery - text.get_height()//2))
            
            self.tutorial_buttons.append({"rect": base_rect, "section": section})
            
        # Back button
        back_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT - 80, 200, 45)
        is_hover = back_rect.collidepoint(mouse_pos)
        self.tutorial_back_rect = self.draw_custom_button("MAIN MENU", back_rect, is_hover, timer)
        
    def draw_class_selection_screen(self):
        self.draw_ui_background()
        
        title_font = pygame.font.SysFont("arial", 60, bold=True)
        self.draw_glow_text("CHOOSE YOUR CHALLENGER", title_font, WHITE, (WIDTH // 2 - 350, 40), (50, 50, 150))

        classes = list(CLASS_DATA.keys())
        self.class_buttons = []

        box_width = 260
        box_height = 300
        margin_x = 40
        margin_y = 30
        
        total_grid_width = 2 * box_width + margin_x
        total_grid_height = 2 * box_height + margin_y
        start_x = WIDTH // 2 - total_grid_width // 2
        start_y = 140

        mouse_pos = pygame.mouse.get_pos()
        timer = pygame.time.get_ticks() * 0.002

        for i, class_name in enumerate(classes):
            data = CLASS_DATA[class_name]
            col = i % 2
            row = i // 2
            
            x = start_x + col * (box_width + margin_x)
            y = start_y + row * (box_height + margin_y)
            box_rect = pygame.Rect(x, y, box_width, box_height)
            is_hover = box_rect.collidepoint(mouse_pos)
            
            # Card Style
            bg_color = (40, 40, 65) if is_hover else (30, 30, 50)
            border_color = data["color"] if is_hover else (80, 80, 120)
            
            pygame.draw.rect(self.screen, bg_color, box_rect, border_radius=15)
            pygame.draw.rect(self.screen, border_color, box_rect, 2 if is_hover else 1, border_radius=15)

            # Class Name
            name_font = pygame.font.SysFont("arial", 28, bold=True)
            name_surf = name_font.render(class_name.upper(), True, WHITE)
            self.screen.blit(name_surf, (box_rect.centerx - name_surf.get_width() // 2, box_rect.y + 15))

            # Sprite Preview
            try:
                sprite_path = f"down_{data['sprite_prefix']}.png"
                try:
                    sprite_img = pygame.image.load(sprite_path).convert_alpha()
                except:
                    sprite_img = pygame.image.load(f"{data['sprite_prefix']}_down.png").convert_alpha()
                sprite_size = 80
                sprite_img = pygame.transform.smoothscale(sprite_img, (sprite_size, sprite_size))
                # Floating effect for sprite
                s_bob = 5 * math.sin(timer * 3 + i)
                self.screen.blit(sprite_img, (box_rect.centerx - sprite_size // 2, box_rect.y + 60 + s_bob))
            except:
                pygame.draw.circle(self.screen, data["color"], (box_rect.centerx, box_rect.y + 100), 35)

            # Description
            desc_font = pygame.font.SysFont("arial", 16)
            desc_text = data["description"]
            words = desc_text.split()
            current_line = ""
            line_y = box_rect.y + 150
            for word in words:
                if desc_font.size(current_line + word)[0] < box_width - 40:
                    current_line += word + " "
                else:
                    desc_surf = desc_font.render(current_line, True, (200, 200, 220))
                    self.screen.blit(desc_surf, (box_rect.x + 20, line_y))
                    line_y += 20
                    current_line = word + " "
            desc_surf = desc_font.render(current_line, True, (200, 200, 220))
            self.screen.blit(desc_surf, (box_rect.x + 20, line_y))

            # Select Button
            btn_rect = pygame.Rect(box_rect.centerx - 70, box_rect.bottom - 50, 140, 35)
            btn_hover = btn_rect.collidepoint(mouse_pos)
            final_btn_rect = self.draw_custom_button("SELECT", btn_rect, btn_hover, timer)
            self.class_buttons.append({"rect": final_btn_rect, "class": class_name})

        # Draw Effects
        if self.tether_haze_timer > 0:
            self.tether_haze_timer -= dt
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            # Black haze border
            pygame.draw.rect(s, (0, 0, 0, 180), (0, 0, WIDTH, HEIGHT), 60)
            self.screen.blit(s, (0, 0))
            
        if self.screen_split_effect_timer > 0:
            self.screen_split_effect_timer -= dt
            # Red split line
            pygame.draw.line(self.screen, (255, 0, 0), (WIDTH//2, 0), (WIDTH//2, HEIGHT), 15)
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((255, 0, 0, 40))
            self.screen.blit(s, (0, 0))

        pygame.display.flip()

    def draw_ability_selection_screen(self):
        self.draw_ui_background()
        
        title_font = pygame.font.SysFont("arial", 50, bold=True)
        self.draw_glow_text("CHOOSE YOUR ABILITY", title_font, WHITE, (WIDTH // 2 - 250, 80), (50, 50, 150))
        
        sub_font = pygame.font.SysFont("arial", 20)
        sub_surf = sub_font.render("Press [SHIFT] to use in-game", True, (150, 150, 200))
        self.screen.blit(sub_surf, (WIDTH // 2 - sub_surf.get_width() // 2, 140))

        self.ability_buttons = []
        box_width = 320
        box_height = 280
        mouse_pos = pygame.mouse.get_pos()
        timer = pygame.time.get_ticks() * 0.002

        for i, ability in enumerate(self.ability_options):
            x = WIDTH // 2 + (i - 0.5) * (box_width + 80) - box_width / 2
            y = HEIGHT // 2 - 50
            box_rect = pygame.Rect(x, y, box_width, box_height)
            is_hover = box_rect.collidepoint(mouse_pos)
            
            # Card Style
            bg_color = (45, 45, 75) if is_hover else (35, 35, 55)
            border_color = YELLOW if is_hover else (100, 100, 150)
            
            pygame.draw.rect(self.screen, bg_color, box_rect, border_radius=20)
            pygame.draw.rect(self.screen, border_color, box_rect, 2 if is_hover else 1, border_radius=20)

            # Ability Name
            name_font = pygame.font.SysFont("arial", 32, bold=True)
            name_surf = name_font.render(ability["name"], True, YELLOW)
            self.screen.blit(name_surf, (box_rect.centerx - name_surf.get_width() // 2, box_rect.y + 30))

            # Description
            desc_font = pygame.font.SysFont("arial", 18)
            words = ability["desc"].split()
            line = ""
            line_y = box_rect.y + 90
            for word in words:
                if desc_font.size(line + word)[0] < box_width - 50:
                    line += word + " "
                else:
                    surf = desc_font.render(line, True, WHITE)
                    self.screen.blit(surf, (box_rect.x + 25, line_y))
                    line_y += 25
                    line = word + " "
            surf = desc_font.render(line, True, WHITE)
            self.screen.blit(surf, (box_rect.x + 25, line_y))

            # Select Button
            btn_rect = pygame.Rect(box_rect.centerx - 80, box_rect.bottom - 60, 160, 40)
            btn_hover = btn_rect.collidepoint(mouse_pos)
            final_btn_rect = self.draw_custom_button("SELECT", btn_rect, btn_hover, timer)
            self.ability_buttons.append({"rect": final_btn_rect, "ability": ability["name"]})

        # Draw Effects
        if self.tether_haze_timer > 0:
            self.tether_haze_timer -= dt
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            # Black haze border
            pygame.draw.rect(s, (0, 0, 0, 180), (0, 0, WIDTH, HEIGHT), 60)
            self.screen.blit(s, (0, 0))
            
        if self.screen_split_effect_timer > 0:
            self.screen_split_effect_timer -= dt
            # Red split line
            pygame.draw.line(self.screen, (255, 0, 0), (WIDTH//2, 0), (WIDTH//2, HEIGHT), 15)
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((255, 0, 0, 40))
            self.screen.blit(s, (0, 0))

        pygame.display.flip()

    def draw_upgrade_screen(self):
        self.draw_ui_background()
        
        # Title & Money
        title_font = pygame.font.SysFont("arial", 50, bold=True)
        self.draw_glow_text("ARSENAL UPGRADE", title_font, WHITE, (WIDTH // 2 - 220, 40), (50, 50, 150))
        
        money_font = pygame.font.SysFont("arial", 32, bold=True)
        money_surf = money_font.render(f"CREDITS: ${int(self.money)}", True, YELLOW)
        self.screen.blit(money_surf, (WIDTH // 2 - money_surf.get_width() // 2, 100))

        # Container
        container_rect = pygame.Rect(80, 150, WIDTH - 160, 420)
        pygame.draw.rect(self.screen, (25, 25, 45), container_rect, border_radius=20)
        pygame.draw.rect(self.screen, (70, 70, 110), container_rect, 2, border_radius=20)

        # Headers
        header_font = pygame.font.SysFont("arial", 20, bold=True)
        cols = [("STAT", 120), ("LVL", 320), ("CURRENT", 450), ("NEXT", 620), ("UPGRADE", 800)]
        for h, x in cols:
            h_surf = header_font.render(h, True, (150, 150, 200))
            self.screen.blit(h_surf, (x, container_rect.y + 20))
            
        pygame.draw.line(self.screen, (70, 70, 110), (container_rect.x + 20, container_rect.y + 50), (container_rect.right - 20, container_rect.y + 50), 1)

        stats_info = [
            ("Health", self.player.health_level, self.player.calculate_health, ""),
            ("Speed", self.player.speed_level, self.player.calculate_speed, "px/s"),
            ("Fire Rate", self.player.firerate_level, self.player.calculate_fire_rate, "s"),
            ("Regen", self.player.regen_level, self.player.calculate_regen_rate, "hp/s"),
            ("Damage", self.player.damage_level, self.player.calculate_damage, "dmg"),
            ("Cooldown", self.player.cooldown_level, self.player.calculate_cooldown_reduction, "%"),
            ("Ability", self.player.ability_level, self.player.calculate_ability_scaling, "x"),
        ]

        self.upgrade_buttons = []
        self.prestige_buttons = []
        stat_font = pygame.font.SysFont("arial", 20)
        mouse_pos = pygame.mouse.get_pos()
        timer = pygame.time.get_ticks() * 0.002

        for i, (name, level, calc_func, unit) in enumerate(stats_info):
            y = container_rect.y + 75 + i * 45
            stat_key = name.lower().replace(" ", "_")
            p_level = self.player.prestige.get(stat_key, 0)
            
            # Row highlight
            if i % 2 == 0:
                pygame.draw.rect(self.screen, (35, 35, 60), (container_rect.x + 10, y - 8, container_rect.width - 20, 40), border_radius=8)

            # Stat Name
            name_surf = stat_font.render(name, True, WHITE)
            self.screen.blit(name_surf, (120, y))
            
            # Level
            lvl_color = GREEN if p_level > 0 else WHITE
            lvl_text = f"{level}" + (" [P]" if p_level > 0 else "")
            lvl_surf = stat_font.render(lvl_text, True, lvl_color)
            self.screen.blit(lvl_surf, (320, y))

            # Values
            curr_val = calc_func()
            
            # Calculate next value
            # Save original level
            orig_lvl = level
            if stat_key == "health": self.player.health_level += 1
            elif stat_key == "speed": self.player.speed_level += 1
            elif stat_key == "fire_rate": self.player.firerate_level += 1
            elif stat_key == "regen": self.player.regen_level += 1
            elif stat_key == "damage": self.player.damage_level += 1
            elif stat_key == "cooldown": self.player.cooldown_level += 1
            elif stat_key == "ability": 
                self.player.ability_level += 1
                self.player.range_level += 1
            
            next_val = calc_func()
            
            # Restore original level
            if stat_key == "health": self.player.health_level = orig_lvl
            elif stat_key == "speed": self.player.speed_level = orig_lvl
            elif stat_key == "fire_rate": self.player.firerate_level = orig_lvl
            elif stat_key == "regen": self.player.regen_level = orig_lvl
            elif stat_key == "damage": self.player.damage_level = orig_lvl
            elif stat_key == "cooldown": self.player.cooldown_level = orig_lvl
            elif stat_key == "ability": 
                self.player.ability_level = orig_lvl
                self.player.range_level = orig_lvl
            
            curr_display = f"{curr_val:.1f}{unit}" if unit != "%" else f"{curr_val*100:.0f}%"
            curr_surf = stat_font.render(curr_display, True, (200, 200, 220))
            self.screen.blit(curr_surf, (450, y))
            
            next_display = f"{next_val:.1f}{unit}" if unit != "%" else f"{next_val*100:.0f}%"
            next_surf = stat_font.render(next_display, True, YELLOW)
            self.screen.blit(next_surf, (620, y))

            # Upgrade Button
            cost = self.player.get_upgrade_cost(level)
            can_afford = self.money >= cost
            btn_rect = pygame.Rect(800, y - 5, 100, 32)
            btn_hover = btn_rect.collidepoint(mouse_pos)
            
            btn_color = (50, 180, 100) if can_afford else (80, 80, 80)
            pygame.draw.rect(self.screen, btn_color, btn_rect, border_radius=6)
            if btn_hover and can_afford:
                pygame.draw.rect(self.screen, WHITE, btn_rect, 2, border_radius=6)
            
            cost_surf = stat_font.render(f"${int(cost)}", True, WHITE)
            self.screen.blit(cost_surf, (btn_rect.centerx - cost_surf.get_width()//2, btn_rect.centery - cost_surf.get_height()//2))
            self.upgrade_buttons.append({"rect": btn_rect, "stat": stat_key, "cost": cost, "can_afford": can_afford})

            # Prestige Button
            if level >= PRESTIGE_LEVEL_REQ and p_level < 1:
                p_rect = pygame.Rect(910, y - 5, 40, 32)
                p_hover = p_rect.collidepoint(mouse_pos)
                pygame.draw.rect(self.screen, ORANGE, p_rect, border_radius=6)
                p_surf = stat_font.render("P", True, WHITE)
                self.screen.blit(p_surf, (p_rect.centerx - p_surf.get_width()//2, p_rect.centery - p_surf.get_height()//2))
                self.prestige_buttons.append({"rect": p_rect, "stat": stat_key})

        # Ready Button
        ready_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 80, 200, 50)
        r_hover = ready_rect.collidepoint(mouse_pos)
        self.ready_button_rect = self.draw_custom_button("READY", ready_rect, r_hover, timer)

        # Draw Effects
        if self.tether_haze_timer > 0:
            self.tether_haze_timer -= dt
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            # Black haze border
            pygame.draw.rect(s, (0, 0, 0, 180), (0, 0, WIDTH, HEIGHT), 60)
            self.screen.blit(s, (0, 0))
            
        if self.screen_split_effect_timer > 0:
            self.screen_split_effect_timer -= dt
            # Red split line
            pygame.draw.line(self.screen, (255, 0, 0), (WIDTH//2, 0), (WIDTH//2, HEIGHT), 15)
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((255, 0, 0, 40))
            self.screen.blit(s, (0, 0))

        pygame.display.flip()
    def __init__(self):
        pygame.init()
        self.score_display = ScoreDisplay(pygame.font.SysFont("arial", 24, bold=True))
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Predictive Bots Arena")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 18)
        self.bigfont = pygame.font.SysFont("arial", 36)
        self.running = True
        self.last_run_stats = None
        self.player = None  # Player is created after class selection
        Player.game_ref = self
        self.enemy_group = []
        self.player_bullets = []
        self.enemy_bullets = []
        self.status_pools = []

        self.in_intermission = False
        self.intermission_timer = 0.0
        self.wave = 0
        self.wave_announcement = f"Wave {self.wave}"
        self.wave_announcement_timer = 0.0

        self.survival_time = 0.0
        self.current_time = 0.0
        self.start_time = 0.0
        self.score = 0
        self.player_class = None  # To store the selected class
        self.selected_ability = "Dash"  # Default ability
        self.ability_options = []  # For wave zero selection
        self.money = 0  # Money earned from killing enemies
        self.wave_active = True
        self.max_enemies = 8
        self.wave_start_time = 0.0  # Track when current wave started
        self.leaderboard = []

        # HERO PRIMARY MELEE TIMER
        self.primary_melee_timer = 0.0
        self.current_boss = None
        self.dead_enemy_pool = []
        self.damage_popups = []
        self.pending_splits = []
        self.tether_haze_timer = 0.0
        self.screen_split_effect_timer = 0.0
        self.screen_shake_timer = 0.0
        self.screen_shake_intensity = 5.0

        self.state = self.MAIN_MENU
        self.start_time = self.current_time
        self.menu_buttons = [
            {"label": "Play", "action": lambda: self.start_game()},
            {"label": "Tutorial", "action": self.go_playable_tutorial},
            {"label": "Guide", "action": self.go_guide},
            {"label": "Leaderboard", "action": self.go_leaderboard}
        ]
        self.button_rects = []
        self.tutorial_page = 0
        self.tutorial_section = None # None means grid view, otherwise the section name
        self.tutorial_sections = ["Classes", "Enemies", "Abilities", "Bosses", "Basic Info", "Prestige & Shop"]
        self.tutorial_alpha = 0
        self.tutorial_target_alpha = 255
        self.tutorial_anim_timer = 0.0
        self.tutorial_text_timer = 0.0
        self.tutorial_hover_scales = [1.0] * len(self.tutorial_sections)
        self.tutorial_transition_timer = 0.0
        self.tutorial_prev_page = 0
        self.tutorial_page_alpha = 255
        self.tutorial_buttons = []
        self.tutorial_nav_buttons = []
        self.tutorial_content = {
            "Classes": [
                {
                    "lines": ["HERO", "Close range brawler. High damage and health.", "Special: LEECH (draws health from enemies).", "Survivable but struggles in late game."],
                    "type": "class", "data": "Hero"
                },
                {
                    "lines": ["ARCHMAGE", "Ranged specialist. Shoots piercing light beam.", "Special: SUMMON (allies like Knights/Paladins).", "Hard start but one of the strongest late game."],
                    "type": "class", "data": "Archmage"
                },
                {
                    "lines": ["SPACEMAN", "Hits multiple enemies at once with chain shock.", "Special: SHOCKWAVE (hits every visible enemy).", "Struggles against bosses due to subpar damage."],
                    "type": "class", "data": "Electrician"
                },
                {
                    "lines": ["WIZARD", "Jack of all trades. Balanced stats.", "Special: CROSS ATTACK (massive cross damage).", "Great against bosses and late game."],
                    "type": "class", "data": "Wizard"
                }
            ],
            "Enemies": [
                {
                    "lines": ["BASIC ENEMIES", "Blue: Random pattern, low health.", "Tank (Purple): Very slow, high health.", "Tracker (Orange): Follows the player.", "Archer (Yellow): Ranged, predicts movement."],
                    "type": "enemy_group", "data": ["drifter", "tank", "predictor", "shooter"]
                },
                {
                    "lines": ["ADVANCED ENEMIES", "Mage (Green): Fast critical shots.", "Splitter (Red): Splits into 8 miniatures.", "Stay moving to avoid being targeted."],
                    "type": "enemy_group", "data": ["mage", "swarmer"]
                },
                {
                    "lines": ["ELITE ENEMIES", "Sniper: Near instantaneous hit with high damage.", "Witch: Slows, burns, or poisons with potions.", "Necromancer: Summons enemies every 5 seconds.", "Assassin: Instant kill contact damage."],
                    "type": "enemy_group", "data": ["sniper", "witch", "necromancer", "assassin"]
                }
            ],
            "Abilities": [
                {
                    "lines": ["MOVEMENT ABILITIES", "Dash: Quick burst (take damage if hitting enemies).", "Blink Step: Instant teleport (no damage taken).", "Essential for dodging boss attacks."],
                    "type": "ability", "data": "Dash"
                },
                {
                    "lines": ["OFFENSIVE ABILITIES", "Burning Garden: AoE circle (200 DPS).", "Quick Bomb: Massive damage explosive behind you.", "Great for clearing groups of basic enemies."],
                    "type": "ability", "data": "Burning Garden"
                },
                {
                    "lines": ["DEFENSIVE ABILITIES", "Force Push: Pushes enemies away from you.", "Wall Arc: Blocks enemies and projectiles.", "Small Heal: Restores a portion of your HP."],
                    "type": "ability", "data": "Small Heal"
                }
            ],
            "Bosses": [
                {
                    "lines": ["RED CORE", "4 Stages: Spawn, Minigun, AoE, Beyblade.", "Each phase requires different movement tactics.", "Stay at a distance during the Beyblade phase."],
                    "type": "boss", "data": "core"
                },
                {
                    "lines": ["ORANGE JUGGERNAUT", "Close range bruiser that follows you.", "Leaves a trail and can dash suddenly.", "Keep moving in large circles."],
                    "type": "boss", "data": "juggernaut"
                },
                {
                    "lines": ["YELLOW EYE", "Ranged boss. Attacks after 5 seconds.", "High fire rate and tracking projectiles.", "The ultimate test of survival."],
                    "type": "boss", "data": "eye"
                }
            ],
            "Basic Info": [
                {
                    "lines": ["CONTROLS", "WASD: Movement", "Space: Class Ability", "Shift: Chosen Ability", "Left Click: Basic Attack"],
                    "type": "text_only", "data": None
                },
                {
                    "lines": ["GAMEPLAY LOOP", "Kill enemies to earn money.", "Survive waves to reach the Intermission.", "Buy upgrades and prepare for Bosses every 3 waves."],
                    "type": "text_only", "data": None
                }
            ],
            "Prestige & Shop": [
                {
                    "lines": ["THE SHOP", "Upgrade stats using money from kills.", "Health, Speed, Fire Rate, Regen, Damage.", "Cooldown and Ability stats are vital."],
                    "type": "text_only", "data": None
                },
                {
                    "lines": ["PRESTIGE (Level 15)", "Health: Heal 5% on kill.", "Speed: 15% Dodge chance.", "Regen: Overheal to 130% HP.", "Damage: 10% Crit chance (4x dmg)."],
                    "type": "text_only", "data": None
                },
                {
                    "lines": ["CLASS PRESTIGE", "Wizard: Twin shots.", "Hero: Short range slash on attack.", "Archmage: Laser damage ramps up to 4x.", "Spaceman: Double hit with yellow flash."],
                    "type": "text_only", "data": None
                }
            ]
        }

    def draw_tutorial_preview(self, v_type, v_data, rect, surf):
        center = rect.center
        if v_type == "text_only" or v_data is None:
            return

        # Add a subtle bobbing effect to all previews
        bob = 10 * math.sin(self.tutorial_anim_timer * 2)
        draw_center = (center[0], center[1] + bob)

        if v_type == "class":
            data = CLASS_DATA.get(v_data)
            if data:
                try:
                    sprite_path = f"down_{data['sprite_prefix']}.png"
                    try:
                        img = pygame.image.load(sprite_path).convert_alpha()
                    except:
                        img = pygame.image.load(f"{data['sprite_prefix']}_down.png").convert_alpha()
                    img = pygame.transform.smoothscale(img, (80, 80))
                    surf.blit(img, (draw_center[0] - 40, draw_center[1] - 40))
                except:
                    pygame.draw.circle(surf, data['color'], draw_center, 35)
                    pygame.draw.circle(surf, WHITE, draw_center, 35, 2)
        
        elif v_type == "enemy":
            pos = pygame.math.Vector2(draw_center)
            e = None
            if v_data == "drifter": e = DrifterBot(pos)
            elif v_data == "tank": e = TankBot(pos)
            elif v_data == "predictor": e = PredictorBot(pos)
            elif v_data == "shooter": e = ShooterBot(pos)
            elif v_data == "mage": e = MageBot(pos)
            elif v_data == "swarmer": e = SwarmerBot(pos, stage=1)
            elif v_data == "assassin": e = AssassinBot(pos)
            elif v_data == "necromancer": e = NecromancerBot(pos)
            elif v_data == "witch": e = WitchBot(pos)
            elif v_data == "sniper": e = SniperBot(pos)
            if e:
                e.pos = pos
                e.draw(surf)
                
        elif v_type == "enemy_group":
            count = len(v_data)
            spacing = rect.width // (count + 1)
            for i, etype in enumerate(v_data):
                pos = pygame.math.Vector2(rect.left + spacing * (i + 1), draw_center[1])
                e = None
                if etype == "drifter": e = DrifterBot(pos)
                elif etype == "tank": e = TankBot(pos)
                elif etype == "predictor": e = PredictorBot(pos)
                elif etype == "shooter": e = ShooterBot(pos)
                elif etype == "witch": e = WitchBot(pos)
                elif etype == "necromancer": e = NecromancerBot(pos)
                elif etype == "assassin": e = AssassinBot(pos)
                elif etype == "sniper": e = SniperBot(pos)
                if e:
                    e.pos = pos
                    e.draw(surf)

        elif v_type == "boss":
            pos = pygame.math.Vector2(draw_center)
            if v_data == "core": b = RedCoreBoss(pos, 3)
            elif v_data == "juggernaut": b = OrangeJuggernautBoss(pos, 6)
            else: b = YellowEyeBoss(pos, 9)
            b.pos = pos
            old_r = b.radius
            b.radius = 45 # Standardize for preview
            b.draw(surf)
            b.radius = old_r

        elif v_type == "ability":
            if v_data == "Dash":
                pygame.draw.line(surf, WHITE, (draw_center[0]-40, draw_center[1]), (draw_center[0]+20, draw_center[1]), 5)
                pygame.draw.polygon(surf, WHITE, [(draw_center[0]+20, draw_center[1]-10), (draw_center[0]+45, draw_center[1]), (draw_center[0]+20, draw_center[1]+10)])
            elif v_data == "Burning Garden":
                pygame.draw.circle(surf, ORANGE, draw_center, 40, 3)
                pygame.draw.circle(surf, RED, draw_center, 20)
            elif v_data == "Small Heal":
                pygame.draw.rect(surf, GREEN, (draw_center[0]-10, draw_center[1]-25, 20, 50))
                pygame.draw.rect(surf, GREEN, (draw_center[0]-25, draw_center[1]-10, 50, 20))

    def draw_tutorial_content(self, surf):
        if self.tutorial_section not in self.tutorial_content:
            self.tutorial_section = None
            return

        # Title with subtle float
        float_y = 5 * math.sin(self.tutorial_anim_timer * 2)
        title_font = pygame.font.SysFont("arial", 48, bold=True)
        title_surf = title_font.render(self.tutorial_section.upper(), True, YELLOW)
        surf.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, 40 + float_y))

        content_list = self.tutorial_content[self.tutorial_section]
        self.tutorial_page = max(0, min(self.tutorial_page, len(content_list) - 1))
        page = content_list[self.tutorial_page]

        if isinstance(page, str):
            lines_to_draw = [page]
            v_type = "text_only"
            v_data = None
        else:
            lines_to_draw = page.get("lines", [])
            v_type = page.get("type", "text_only")
            v_data = page.get("data", None)

        # Content surface for page transitions
        content_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        
        text_box = pygame.Rect(WIDTH//2 - 400, 110, 800, 220)
        pygame.draw.rect(content_surf, (30, 30, 50), text_box, border_radius=15)
        pygame.draw.rect(content_surf, BLUE, text_box, 2, border_radius=15)

        text_font = pygame.font.SysFont("arial", 24)
        total_chars_shown = int(self.tutorial_text_timer)
        chars_counter = 0
        
        for idx, text_line in enumerate(lines_to_draw):
            color = WHITE if idx > 0 else YELLOW
            
            # Typing effect
            if chars_counter < total_chars_shown:
                visible_text = text_line[:total_chars_shown - chars_counter]
                line_surf = text_font.render(visible_text, True, color)
                content_surf.blit(line_surf, (WIDTH//2 - line_surf.get_width()//2, 130 + idx * 35))
            chars_counter += len(text_line)

        preview_rect = pygame.Rect(WIDTH//2 - 200, 350, 400, 200)
        # Subtle pulse for preview box
        preview_pulse = 1 + 0.01 * math.sin(self.tutorial_anim_timer * 4)
        p_draw_rect = preview_rect.copy()
        p_draw_rect.width *= preview_pulse
        p_draw_rect.height *= preview_pulse
        p_draw_rect.center = preview_rect.center
        
        pygame.draw.rect(content_surf, (20, 20, 40), p_draw_rect, border_radius=15)
        pygame.draw.rect(content_surf, GREY, p_draw_rect, 1, border_radius=15)
        
        # Draw preview on content_surf
        self.draw_tutorial_preview(v_type, v_data, p_draw_rect, content_surf)

        # Apply page transition alpha
        content_surf.set_alpha(int(self.tutorial_page_alpha))
        surf.blit(content_surf, (0, 0))

        # Navigation buttons
        nav_y = HEIGHT - 80
        self.tutorial_nav_buttons = []
        mouse_pos = pygame.mouse.get_pos()

        # Back to grid button
        grid_text = self.font.render("BACK TO GRID", True, WHITE)
        grid_rect = grid_text.get_rect(center=(WIDTH//2, nav_y))
        bg_rect = grid_rect.inflate(30, 15)
        is_hover = bg_rect.collidepoint(mouse_pos)
        
        bg_color = (80, 80, 100) if is_hover else (60, 60, 80)
        pygame.draw.rect(surf, bg_color, bg_rect, border_radius=8)
        if is_hover:
            pygame.draw.rect(surf, YELLOW, bg_rect, 2, border_radius=8)
        surf.blit(grid_text, grid_rect)
        self.tutorial_nav_buttons.append({"rect": bg_rect, "action": "grid"})

        if len(content_list) > 1:
            # Prev button
            p_color = WHITE if self.tutorial_page > 0 else (100, 100, 100)
            prev_text = self.font.render("< PREV", True, p_color)
            prev_rect = prev_text.get_rect(center=(WIDTH//2 - 200, nav_y))
            p_bg = prev_rect.inflate(30, 15)
            p_hover = p_bg.collidepoint(mouse_pos) and self.tutorial_page > 0
            
            p_bg_color = (60, 60, 80) if p_hover else (40, 40, 60)
            pygame.draw.rect(surf, p_bg_color, p_bg, border_radius=8)
            if p_hover:
                pygame.draw.rect(surf, WHITE, p_bg, 2, border_radius=8)
            surf.blit(prev_text, prev_rect)
            if self.tutorial_page > 0:
                self.tutorial_nav_buttons.append({"rect": p_bg, "action": "prev"})

            # Next button
            n_color = WHITE if self.tutorial_page < len(content_list)-1 else (100, 100, 100)
            next_text = self.font.render("NEXT >", True, n_color)
            next_rect = next_text.get_rect(center=(WIDTH//2 + 200, nav_y))
            n_bg = next_rect.inflate(30, 15)
            n_hover = n_bg.collidepoint(mouse_pos) and self.tutorial_page < len(content_list)-1
            
            n_bg_color = (60, 60, 80) if n_hover else (40, 40, 60)
            pygame.draw.rect(surf, n_bg_color, n_bg, border_radius=8)
            if n_hover:
                pygame.draw.rect(surf, WHITE, n_bg, 2, border_radius=8)
            surf.blit(next_text, next_rect)
            if self.tutorial_page < len(content_list)-1:
                self.tutorial_nav_buttons.append({"rect": n_bg, "action": "next"})

            page_text = self.font.render(f"{self.tutorial_page + 1} / {len(content_list)}", True, GREY)
            surf.blit(page_text, (WIDTH//2 - page_text.get_width()//2, nav_y - 40))
    

    def handle_tutorial_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.tutorial_section is None:
                if hasattr(self, "tutorial_back_rect") and self.tutorial_back_rect.collidepoint(mouse_pos):
                    self.state = self.MAIN_MENU
                for btn in self.tutorial_buttons:
                    if btn["rect"].collidepoint(mouse_pos):
                        self.tutorial_section = btn["section"]
                        self.tutorial_page = 0
                        self.tutorial_text_timer = 0.0
                        self.tutorial_page_alpha = 0
            else:
                for btn in self.tutorial_nav_buttons:
                    if btn["rect"].collidepoint(mouse_pos):
                        if btn["action"] == "grid":
                            self.tutorial_section = None
                            self.tutorial_anim_timer = 0.0 # Reset for grid entrance
                        elif btn["action"] == "prev":
                            self.tutorial_page -= 1
                            self.tutorial_text_timer = 0.0
                            self.tutorial_page_alpha = 0
                        elif btn["action"] == "next":
                            self.tutorial_page += 1
                            self.tutorial_text_timer = 0.0
                            self.tutorial_page_alpha = 0

    def handle_leaderboard_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if hasattr(self, "leaderboard_back_rect") and self.leaderboard_back_rect.collidepoint(mouse_pos):
                self.state = self.MAIN_MENU

    def update_tutorial_animations(self, dt):
        # Fade in/out
        self.tutorial_alpha += (self.tutorial_target_alpha - self.tutorial_alpha) * min(10 * dt, 1)
        
        # General animation timer
        self.tutorial_anim_timer += dt
        
        # Text typing effect timer
        self.tutorial_text_timer += dt * 30 # 30 chars per second
        
        # Hover scales
        mouse_pos = pygame.mouse.get_pos()
        if self.tutorial_section is None:
            for i, btn in enumerate(self.tutorial_buttons):
                target = 1.05 if btn["rect"].collidepoint(mouse_pos) else 1.0
                self.tutorial_hover_scales[i] += (target - self.tutorial_hover_scales[i]) * min(15 * dt, 1)
        
        # Page transition alpha
        self.tutorial_page_alpha += (255 - self.tutorial_page_alpha) * min(12 * dt, 1)

    def go_guide(self):
        self.state = self.GUIDE
        self.tutorial_section = None
        self.tutorial_alpha = 0
        self.tutorial_target_alpha = 255
        self.tutorial_anim_timer = 0.0
        self.tutorial_text_timer = 0.0
        self.tutorial_page_alpha = 255

    def go_playable_tutorial(self):
        self.state = self.PLAYABLE_TUTORIAL
        self.init_playable_tutorial()

    def go_leaderboard(self):
        self.state = self.LEADERBOARD

    def set_state(self, new_state):
        self.state = new_state

    

    def handle_class_selection_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for btn in self.class_buttons:
                if btn["rect"].collidepoint(mouse_pos):
                    self.select_class(btn["class"])
                    break

    def select_class(self, class_name):
        self.player_class = class_name
        # Create the player instance with the selected class
        self.player = Player((WIDTH//2, HEIGHT//2), self.player_class)

        # UPDATE GLOBAL HEALTH CONSTANT FOR UI
        global PLAYER_MAX_HEALTH
        PLAYER_MAX_HEALTH = int(self.player.calculate_health())
        self.player.health = PLAYER_MAX_HEALTH

        # Proceed to ability selection (Wave 0)
        self.setup_ability_selection()

    def setup_ability_selection(self):
        # Assign class-specific intrinsic abilities
        if self.player_class == "Hero":
            self.player.intrinsic_ability = "Leech"
        elif self.player_class == "Wizard":
            self.player.intrinsic_ability = "Cross Attack"
        elif self.player_class == "Archmage":
            self.player.intrinsic_ability = "Summon"

        # Restore secondary ability selection
        all_abilities = [
            {"name": "Quick Bomb", "desc": "Toss a small explosive that deals minor AoE damage."},
            {"name": "Dash", "desc": "Short movement burst in the input direction."},
            {"name": "Blink Step", "desc": "Very short-range instant teleport."},
            {"name": "Small Heal", "desc": "Restore a small amount of HP on use."},
            {"name": "Force Push", "desc": "Pushes back enemies in a small radius around you."},
            {"name": "Burning Garden", "desc": "Deploy an orange circle that burns enemies for 200 DPS. Stacks."},
            {"name": "Defiance", "desc": "Become invulnerable to all attacks for 2 seconds."},
            {"name": "Wall Arc", "desc": "Deploy a dark grey arc wall that blocks enemies and projectiles."}
        ]
        self.ability_options = random.sample(all_abilities, 2)
        self.state = self.ABILITY_SELECTION_SCREEN
        self.wave_announcement = "CHOOSE ABILITY"
        self.wave_announcement_timer = 0.0

    

    def handle_ability_selection_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for btn in self.ability_buttons:
                if btn["rect"].collidepoint(mouse_pos):
                    self.selected_ability = btn["ability"]
                    self.player.secondary_ability = self.selected_ability
                    # After ability selection, go to upgrade screen
                    self.state = self.UPGRADE_SCREEN
                    self.wave_announcement = "UPGRADE TIME"
                    self.wave_announcement_timer = 0.0
                    break

    

    def handle_upgrade_screen_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            # Ready Button
            if hasattr(self, "ready_button_rect") and self.ready_button_rect.collidepoint(mouse_pos):
                self.start_next_wave()

            # Upgrade Buttons
            for btn in self.upgrade_buttons:
                if btn["rect"].collidepoint(mouse_pos) and btn["can_afford"]:
                    self.apply_upgrade(btn["stat"], btn["cost"])
                    return

            # Prestige Buttons
            for btn in self.prestige_buttons:
                if btn["rect"].collidepoint(mouse_pos):
                    self.apply_prestige(btn["stat"])
                    return

    def apply_upgrade(self, stat_name, cost):
        if self.money < cost:
            return

        self.money -= cost

        if stat_name == "health":
            self.player.health_level += 1
            new_max_health = self.player.calculate_health()
            global PLAYER_MAX_HEALTH
            PLAYER_MAX_HEALTH = int(new_max_health)
            self.player.health = min(PLAYER_MAX_HEALTH, self.player.health)
        elif stat_name == "speed":
            self.player.speed_level += 1
        elif stat_name == "fire_rate":
            self.player.firerate_level += 1
        elif stat_name == "regen":
            self.player.regen_level += 1
            global PLAYER_HEALTH_REGEN_RATE
            PLAYER_HEALTH_REGEN_RATE = self.player.calculate_regen_rate()
        elif stat_name == "damage":
            self.player.damage_level += 1
        elif stat_name == "cooldown":
            self.player.cooldown_level += 1
        elif stat_name == "ability":
            self.player.ability_level += 1
            self.player.range_level += 1

        # Re-draw the screen to show the changes immediately
        self.draw_upgrade_screen()

    def apply_prestige(self, stat_name):
        if stat_name in self.player.prestige:
            self.player.prestige[stat_name] = 1
            # Reset level to 0
            if stat_name == "health":
                self.player.health_level = 0
            elif stat_name == "speed":
                self.player.speed_level = 0
            elif stat_name == "fire_rate":
                self.player.firerate_level = 0
            elif stat_name == "regen":
                self.player.regen_level = 0
            elif stat_name == "damage":
                self.player.damage_level = 0
            elif stat_name == "cooldown":
                self.player.cooldown_level = 0
            elif stat_name == "ability":
                self.player.ability_level = 0

            # Re-draw the screen
            self.draw_upgrade_screen()

    def start_next_wave(self):
        # This function will replace the logic in the old intermission
        self.wave += 1  # Increment wave (0 -> 1, 1 -> 2, etc.)
        
        # Reset Player Health and Cooldowns for the new round
        new_max_health = self.player.calculate_health()
        global PLAYER_MAX_HEALTH
        PLAYER_MAX_HEALTH = int(new_max_health)
        self.player.health = PLAYER_MAX_HEALTH
        
        self.player.last_melee = -999
        self.player.last_dash = -999
        self.player.last_summon_time = -999
        self.player.ability_charges = self.player.max_ability_charges
        
        # Clear temporary abilities
        if hasattr(self, "walls"): self.walls.clear()
        if hasattr(self, "burning_gardens"): self.burning_gardens.clear()
        
        self.spawn_wave(self.wave)
        self.wave_active = True
        self.in_intermission = True  # Use intermission for the countdown
        self.wave_countdown = 5.0  # Intermission duration
        self.wave_announcement = f"ROUND {self.wave} starts in {int(self.wave_countdown) + 1}..."
        self.wave_announcement_timer = 0.0
        self.state = self.GAME_RUNNING

    def current_wave_duration(self):
        """Returns duration of current wave in seconds."""
        if self.wave % 3 == 0:
            return 99999  # Boss waves end when boss dies
        return 30  # All other waves last 30 seconds

    def start_game(self):
        self.reset_game()
        self.wave = 0  # Start at wave 0
        self.state = self.CLASS_SELECTION_SCREEN  # New state for class selection
        self.wave_announcement = "CHOOSE YOUR CHALLENGER"
        self.wave_announcement_timer = 0.0

    def handle_main_menu_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for idx, rect in enumerate(self.button_rects):
                if rect.collidepoint(mouse_pos):
                    self.menu_buttons[idx]["action"]()

    

    def spawn_position_offscreen(self):
        side = random.choice(["left", "right", "top", "bottom"])
        if side == "left":
            return (-ENEMY_SPAWN_PADDING, random.uniform(0, HEIGHT))
        if side == "right":
            return (WIDTH + ENEMY_SPAWN_PADDING, random.uniform(0, HEIGHT))
        if side == "top":
            return (random.uniform(0, WIDTH), -ENEMY_SPAWN_PADDING)
        return (random.uniform(0, WIDTH), HEIGHT + ENEMY_SPAWN_PADDING)

    def spawn_enemy(self, etype=None):
        pos = self.spawn_position_offscreen()
        if etype is None:
            # Tiered Spawning Logic
            # Waves 1-2: Basic enemies only
            # Wave 3: Boss (Red Core)
            # Waves 4-5: Basic + Advanced enemies
            # Wave 6: Boss (Orange Juggernaut)
            # Waves 7-8: Basic + Advanced + Elite enemies
            # Wave 9: Boss (Yellow Eye)
            
            basic = ["drifter", "tank", "predictor"]
            advanced = ["shooter", "mage", "swarmer"]
            elite = ["assassin", "necromancer", "witch", "sniper"]
            
            if self.wave <= 2:
                etype = random.choice(basic)
            elif self.wave == 4 or self.wave == 5:
                if random.random() < 0.7:
                    etype = random.choice(basic)
                else:
                    etype = random.choice(advanced)
            elif self.wave == 7 or self.wave == 8:
                r = random.random()
                if r < 0.5:
                    etype = random.choice(basic)
                elif r < 0.8:
                    etype = random.choice(advanced)
                else:
                    etype = random.choice(elite)
            else:
                # Waves 10+: Include Special Enemies
                r = random.random()
                if self.wave >= 10:
                    if r < 0.15: etype = "anchor"
                    elif r < 0.30: etype = "gravity_core"
                    elif r < 0.55: etype = random.choice(basic)
                    elif r < 0.80: etype = random.choice(advanced)
                    else: etype = random.choice(elite)
                else:
                    # Fallback for waves beyond 9 but before 10 (if any)
                    if r < 0.4: etype = random.choice(basic)
                    elif r < 0.7: etype = random.choice(advanced)
                    else: etype = random.choice(elite)

        if etype == "predictor":
            e = PredictorBot(pos, wave=self.wave)
        elif etype == "drifter":
            e = DrifterBot(pos, wave=self.wave)
        elif etype == "shooter":
            e = ShooterBot(pos, wave=self.wave)
        elif etype == "tank":
            e = TankBot(pos, wave=self.wave)
        elif etype == "mage":
            e = MageBot(pos, wave=self.wave)
        elif etype == "swarmer":
            e = SwarmerBot(pos, stage=1, wave=self.wave)
        elif etype == "assassin":
            e = AssassinBot(pos, wave=self.wave)
        elif etype == "necromancer":
            e = NecromancerBot(pos, wave=self.wave)
        elif etype == "witch":
            e = WitchBot(pos, wave=self.wave)
        elif etype == "sniper":
            e = SniperBot(pos, wave=self.wave)
        elif etype == "anchor":
            e = AnchorBot(pos)
            # High health as requested
            e.max_hp = 1500 + (self.wave * 100)
            e.hp = e.max_hp
        elif etype == "gravity_core":
            e = GravityCoreBot(pos)
            # High health as requested
            e.max_hp = 2000 + (self.wave * 120)
            e.hp = e.max_hp
        else:
            e = DrifterBot(pos, wave=self.wave)

        e.is_friendly = False
        self.enemy_group.append(e)

    def spawn_wave(self, wave_number):
        # Clear existing enemies and bullets before starting a new wave
        self.enemy_group.clear()
        self.enemy_bullets.clear()

        if wave_number % 3 == 0:
            # Boss Wave
            self.spawn_boss(wave_number)
            self.max_enemies = 1  # Only the boss
        else:
            # Normal Wave
            num = min(6 + wave_number*2, 40)
            for _ in range(num):
                self.spawn_enemy()
            self.max_enemies = max(6, min(12 + wave_number*2, 50))

        self.wave_active = True

    def spawn_boss(self, wave_number):
        pos = (WIDTH // 2, 100)  # Spawn at top center instead of offscreen

        if wave_number == 12:
            boss = AncientOneBoss(pos, wave_number)
            boss_type = "ancient_one"
        else:
            # Use a cycling system based on wave number to ensure 100% equal distribution
            # Wave 3 = core, Wave 6 = juggernaut, Wave 9 = eye
            boss_index = (wave_number // 3 - 1) % 3
            boss_types = ["core", "juggernaut", "eye"]
            boss_type = boss_types[boss_index]

            if boss_type == "core":
                boss = RedCoreBoss(pos, wave_number)
            elif boss_type == "juggernaut":
                boss = OrangeJuggernautBoss(pos, wave_number)
            else:
                boss = YellowEyeBoss(pos, wave_number)

        self.current_boss = boss
        self.enemy_group.append(boss)
        print(f"DEBUG: Spawned boss {boss_type} at {pos}")  # Add debug print to console

    def perform_archmage_beam(self):
        mouse_pos = pygame.mouse.get_pos()
        beam_dir = normalize_safe(pygame.math.Vector2(mouse_pos) - self.player.pos)
        if beam_dir.length_squared() == 0:
            beam_dir = pygame.math.Vector2(1, 0)

        # Beam settings
        beam_width = 6
        damage = self.player.damage
        
        # Archmage Prestige: Ramp up damage
        if self.player.prestige["fire_rate"] >= 1:
            damage *= self.player.archmage_ramp

        # Visual effect timer
        self.archmage_beam_timer = 0.1
        self.archmage_beam_start = self.player.pos.copy()
        self.archmage_beam_end = self.player.pos + beam_dir * 2000 # Piercing to end of map

        # Damage enemies in the line
        contact_made = False
        for e in list(self.enemy_group):
            if getattr(e, "is_friendly", False):
                continue
            
            A = self.player.pos
            D = beam_dir
            V = e.pos - A
            t = V.dot(D)
            
            if t < 0: continue # Enemy is behind the player
            
            p_closest = A + D * t
            dist = (e.pos - p_closest).length()
            
            if dist <= (beam_width / 2) + e.radius:
                contact_made = True
                died = e.take_damage(damage, self.enemy_group, player=self.player, game=self)
                if died:
                    self.enemy_group.remove(e)
        
        if contact_made:
            self.player.archmage_contact = True

    def perform_hero_slash(self):
        # Settings for the slash
        # Hero's primary melee attack has 5x damage of normal attack
        damage = self.player.damage * 3.0

        # Range scales with melee_radius (which is updated by ability level)
        slash_range = self.player.melee_radius 

        # ARC ANGLE in DEGREES
        arc_angle_degrees = 160

        mouse_pos = pygame.mouse.get_pos()
        slash_dir = normalize_safe(pygame.math.Vector2(mouse_pos) - self.player.pos)

        # Create a visual effect timer (0.15 seconds)
        self.primary_melee_timer = 0.15

        for e in list(self.enemy_group):
            # Friendly fire protection: Hero slash doesn't hit friendly summons
            if getattr(e, "is_friendly", False):
                continue
            enemy_vec = e.pos - self.player.pos
            dist = enemy_vec.length()
            if dist == 0:
                continue

            # Precision Strike Settings
            precision_range = slash_range * 1.5  # 50% longer
            precision_arc = 30  # Narrow 30-degree cone
            angle_diff = slash_dir.angle_to(enemy_vec)

            is_hit = False
            final_damage = damage

            # 1. Check Precision Strike (Narrow cone, longer range, extra damage)
            if abs(angle_diff) <= precision_arc / 2:
                if dist <= precision_range + e.radius:
                    is_hit = True
                    final_damage *= 2  # 50% extra damage in precision zone

            # 2. Check Normal Slash (Wide arc, normal range)
            if not is_hit and abs(angle_diff) <= arc_angle_degrees / 2:
                if dist <= slash_range + e.radius:
                    is_hit = True

            if is_hit:
                died = e.take_damage(final_damage, self.enemy_group, player=self.player, game=self)
                if died:
                    self.enemy_group.remove(e)

    def apply_damage_to_player(self, damage):
        if self.player.defiance_timer > 0:
            return

        # Ability Prestige Shield
        if hasattr(self.player, "ability_shield_hp") and self.player.ability_shield_hp > 0:
            self.player.ability_shield_hp -= damage
            if self.player.ability_shield_hp < 0:
                damage = abs(self.player.ability_shield_hp)
                self.player.ability_shield_hp = 0
            else:
                damage = 0

        # Speed Prestige: Dodge Chance (15%)
        if self.player.prestige["speed"] >= 1:
            if random.random() < 0.15:
                # Show dodge message
                self.damage_popups.append(DamagePopup(self.player.pos, "DODGE"))
                return

        if damage > 0:
            self.player.health -= damage
            self.player.last_damage_time = self.survival_time

    def handle_collisions(self):
        dt = self.clock.get_time() / 1000.0
        # Update Burning Gardens
        if hasattr(self, "burning_gardens"):
            for bg in list(self.burning_gardens):
                bg.update(dt, self.enemy_group, self.player)
                if bg.timer <= 0:
                    self.burning_gardens.remove(bg)

        # Update Walls
        if hasattr(self, "walls"):
            for w in list(self.walls):
                if w.hp <= 0:
                    self.walls.remove(w)
                    continue
                
                # Block enemies
                for e in self.enemy_group:
                    if not getattr(e, "is_friendly", False):
                        dist = (e.pos - w.pos).length()
                        if dist <= w.radius + e.radius and dist >= w.radius - w.thickness - e.radius:
                            angle_to_enemy = math.degrees(math.atan2(e.pos.y - w.pos.y, e.pos.x - w.pos.x))
                            diff = (angle_to_enemy - w.angle + 180) % 360 - 180
                            if abs(diff) <= w.arc_width / 2:
                                push_dir = normalize_safe(e.pos - w.pos)
                                e.pos = w.pos + push_dir * (w.radius + e.radius + 2)
                                w.take_damage(dt * 50)
                
                # Block projectiles
                for b in list(self.enemy_bullets):
                    dist = (b.pos - w.pos).length()
                    if dist <= w.radius + b.radius and dist >= w.radius - w.thickness - b.radius:
                        angle_to_bullet = math.degrees(math.atan2(b.pos.y - w.pos.y, b.pos.x - w.pos.x))
                        diff = (angle_to_bullet - w.angle + 180) % 360 - 180
                        if abs(diff) <= w.arc_width / 2:
                            w.take_damage(b.damage)
                            if b in self.enemy_bullets: self.enemy_bullets.remove(b)

                # Block player
                dist = (self.player.pos - w.pos).length()
                if dist <= w.radius + self.player.radius and dist >= w.radius - w.thickness - self.player.radius:
                    angle_to_player = math.degrees(math.atan2(self.player.pos.y - w.pos.y, self.player.pos.x - w.pos.x))
                    diff = (angle_to_player - w.angle + 180) % 360 - 180
                    if abs(diff) <= w.arc_width / 2:
                        push_dir = normalize_safe(self.player.pos - w.pos)
                        self.player.pos = w.pos + push_dir * (w.radius + self.player.radius + 2)

        # 1. Player Bullets vs Enemies
        for b in list(self.player_bullets):
            for e in list(self.enemy_group):
                

                # Optimization: Skip damage if in intermission (prep phase)
                if self.in_intermission:
                    continue
                
                # Friendly fire protection: Player bullets don't hit friendly summons
                if getattr(e, "is_friendly", False):
                    continue

                dist_sq = (b.pos.x - e.pos.x)**2 + (b.pos.y - e.pos.y)**2
                if dist_sq <= (b.radius + e.radius)**2:
                    if id(e) in b.hit_enemies:
                        continue
                    b.hit_enemies.add(id(e))
                    final_damage = b.damage

                    # Damage Prestige: Critical Chance of 10%
                    is_crit = False
                    if self.player.prestige["damage"] >= 1:
                        if random.random() < 0.10:
                            final_damage *= 4.0
                            is_crit = True

                    dead = e.take_damage(final_damage, self.enemy_group, player=self.player, game=self, is_crit=is_crit)
                    
                    # Handle special bullet effects on hit
                    if isinstance(b, TriSplitBullet):
                        b.on_hit(self, enemy_hit=e)

                    if dead:
                        etype = "drifter"
                        if isinstance(e, PredictorBot):
                            etype = "predictor"
                        elif isinstance(e, ShooterBot):
                            etype = "shooter"
                        elif isinstance(e, TankBot):
                            etype = "tank"
                        elif isinstance(e, MageBot):
                            etype = "mage"
                        elif isinstance(e, SwarmerBot):
                            etype = "swarmer"

                        if not hasattr(e, "is_boss") or not e.is_boss:
                            self.dead_enemy_pool.append(etype)
                            if len(self.dead_enemy_pool) > 20:
                                self.dead_enemy_pool.pop(0)

                        # Health Prestige: Every kill enemy you heal 5% of hp
                        if self.player.prestige["health"] >= 1:
                            heal_amount = self.player.calculate_health() * 0.05
                            self.player.health = min(self.player.calculate_health() * (1.3 if self.player.prestige["regen"] >= 1 else 1.0), self.player.health + heal_amount)

                        # Cooldown Prestige: every kill 5% of your cooldown time left
                        if self.player.prestige["cooldown"] >= 1:
                            # Reduce remaining cooldowns by 5%
                            current_time = self.survival_time
                            
                            # For intrinsic ability
                            intrinsic_cooldown = 2.0 # Default
                            if self.player.intrinsic_ability == "Summon": intrinsic_cooldown = 15.0
                            elif self.player.intrinsic_ability == "Red Lightning": intrinsic_cooldown = 10.0
                            elif self.player.intrinsic_ability == "Cross Attack": intrinsic_cooldown = 8.0
                            elif self.player.intrinsic_ability == "Leech": intrinsic_cooldown = 15.0
                            
                            time_passed = current_time - self.player.last_melee
                            if time_passed < intrinsic_cooldown:
                                remaining = intrinsic_cooldown - time_passed
                                self.player.last_melee -= remaining * 0.05

                            # For secondary ability
                            if self.player.secondary_ability:
                                # This is a bit complex due to charges, but we can simplify by reducing last_dash
                                # which is used for charge regeneration.
                                pass # Simplified for now

                        self.enemy_group.remove(e)

                    if not getattr(b, "piercing", False):
                        self.player_bullets.remove(b)
                        break

        # 2. Enemy Bullets vs Player/Shield
        for b in list(self.enemy_bullets):
            # Wizard stationary shield removed

            # Check Player collision
            dist_sq = (b.pos.x - self.player.pos.x)**2 + (b.pos.y - self.player.pos.y)**2
            if dist_sq <= (b.radius + self.player.radius)**2:
                if isinstance(b, TetherBullet):
                    b.on_hit_player(self.player, self)
                else:
                    self.apply_damage_to_player(b.damage)
                self.enemy_bullets.remove(b)
                continue
            
            # Check Friendly Summons collision
            for e in self.enemy_group:
                if getattr(e, "is_friendly", False):
                    dist_sq = (b.pos.x - e.pos.x)**2 + (b.pos.y - e.pos.y)**2
                    if dist_sq <= (b.radius + e.radius)**2:
                        e.take_damage(b.damage, self.enemy_group)
                        if b in self.enemy_bullets:
                            self.enemy_bullets.remove(b)
                        break

        # 3. Enemy Body vs Player/Shield (Invulnerability logic)
        self.player.cleanup_invulnerability(self.survival_time)
        for e in list(self.enemy_group):
            enemy_id = id(e)
            
            # Friendly summons interaction
            if getattr(e, "is_friendly", False):
                # Update behavior for dedicated allies
                if isinstance(e, KnightAlly):
                    e.update_behavior(self.player, self.survival_time, self.enemy_group)
                elif isinstance(e, CrossbowmanAlly):
                    e.update_behavior(self.player, self.survival_time, self.enemy_group, self.player_bullets)
                elif isinstance(e, ParagonAlly):
                    res = e.update_behavior(self.player, self.survival_time, self.enemy_group, self.clock.get_time() / 1000.0)
                    if res == "golden_cross":
                        # Golden Cross Attack: 500 damage to all enemies in cross
                        for other_e in list(self.enemy_group):
                            if not getattr(other_e, "is_friendly", False):
                                # Check if enemy is in the cross (horizontal or vertical line)
                                if abs(other_e.pos.x - e.pos.x) < other_e.radius + 10 or abs(other_e.pos.y - e.pos.y) < other_e.radius + 10:
                                    died = other_e.take_damage(500, self.enemy_group, player=self.player, game=self)
                                    if died:
                                        self.enemy_group.remove(other_e)

                        # Visual effect handled in draw
                        if not hasattr(self, "paragon_cross_effects"): self.paragon_cross_effects = []
                        self.paragon_cross_effects.append({"pos": e.pos.copy(), "timer": 0.3})

                for other_e in list(self.enemy_group):
                    if not getattr(other_e, "is_friendly", False):
                        dist_sq = (e.pos.x - other_e.pos.x)**2 + (e.pos.y - other_e.pos.y)**2
                        if dist_sq <= (e.radius + other_e.radius)**2:
                            # Use a small cooldown for physical damage to prevent instant death
                            enemy_id = id(other_e)
                            if not hasattr(e, 'contact_cooldowns'): e.contact_cooldowns = {}
                            if enemy_id not in e.contact_cooldowns or self.survival_time > e.contact_cooldowns[enemy_id]:
                                # Friendly summons deal damage to enemies
                                other_e.take_damage(10 * getattr(e, "damage_mult", 1.0), self.enemy_group, player=self.player, game=self)
                                # Enemies deal damage back to friendly summons
                                e.take_damage(10, self.enemy_group)
                                e.contact_cooldowns[enemy_id] = self.survival_time + 0.5
            # Wizard stationary shield removed
            dist_sq = (e.pos.x - self.player.pos.x)**2 + (e.pos.y - self.player.pos.y)**2
            if dist_sq <= (e.radius + self.player.radius)**2:
                if isinstance(e, AssassinBot):
                    if self.survival_time - e.last_damage_time >= 5.0:
                        damage = self.player.calculate_health() * 0.15
                        self.apply_damage_to_player(damage)
                        e.last_damage_time = self.survival_time
                    continue

                if enemy_id not in self.player.invulnerable_enemies:
                    damage = clamp(int(e.radius * 0.5), 4, 24)
                    self.apply_damage_to_player(damage)
                    # Set invulnerability for this enemy for 0.2 seconds
                    self.player.invulnerable_enemies[enemy_id] = self.survival_time + 0.2

        # 4. Spacebar Melee (AOE Slam)
        if self.melee_just_used:
            ability_melee_damage = self.player.damage * 5
            for e in list(self.enemy_group):
                

                # Friendly fire protection: Melee doesn't hit friendly summons
                if getattr(e, "is_friendly", False):
                    continue
                # Check for collision with the melee radius
                if (e.pos - self.player.pos).length() <= self.player.melee_radius + e.radius:
                    died = e.take_damage(ability_melee_damage, self.enemy_group, player=self.player, game=self)
                    if died:
                        self.enemy_group.remove(e)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        # Track survival time while wave is active
        if self.state == self.GAME_RUNNING and self.wave_active:
            self.survival_time += dt

        # Update Screen Shake
        if hasattr(self, "screen_shake_timer") and self.screen_shake_timer > 0:
            self.screen_shake_timer -= dt

        # Player update (moved before intermission check to allow movement during intermission)
        self.player.speed_mult = 1.0  # Reset speed mult
        for p in list(self.status_pools):
            p.update(dt, self.player, self.survival_time)
            if p.lifetime <= 0:
                self.status_pools.remove(p)

        self.player.game_ref = self
        self.player.game_ref_enemies = self.enemy_group
        self.player.update(dt, keys, mouse_pos, self.survival_time)

        # Update damage popups
        for popup in list(self.damage_popups):
            popup.update(dt)
            if popup.lifetime <= 0:
                self.damage_popups.remove(popup)

        if self.player.class_name == "Electrician":
            if self.player.can_shoot(self.survival_time):
                self.player.last_shot = self.survival_time
                self.player.perform_chain_attack(mouse_pos, self.enemy_group, game=self)
            if getattr(self.player, "red_lightning_requested", False):
                self.player.perform_red_ability(self.enemy_group, game=self)
                self.player.red_lightning_requested = False

        # Health Regeneration
        # Regen Prestige: Overheal. You can overheal to 130% of your hp.
        max_h = self.player.calculate_health()
        if self.player.prestige["regen"] >= 1:
            max_h *= 1.30

        if self.player.health < max_h:
            regen_rate = PLAYER_HEALTH_REGEN_RATE
            regen_amount = regen_rate * dt
            self.player.health = min(max_h, self.player.health + regen_amount)

        # Update Score Display
        self.score_display.update(self.score, dt)

        # Decrement visual timer for Hero slash
        if self.primary_melee_timer > 0:
            self.primary_melee_timer -= dt
        
        # Decrement visual timer for Archmage beam
        if hasattr(self, "archmage_beam_timer") and self.archmage_beam_timer > 0:
            self.archmage_beam_timer -= dt
        
        # Decrement visual timer for Summoning Circle
        if hasattr(self, "summoning_circle_timer") and self.summoning_circle_timer > 0:
            self.summoning_circle_timer -= dt
        
        # Decrement Paragon Cross effects
        if hasattr(self, "paragon_cross_effects"):
            for effect in list(self.paragon_cross_effects):
                effect["timer"] -= dt
                if effect["timer"] <= 0:
                    self.paragon_cross_effects.remove(effect)

        # Decrement Wizard Cross effects
        if hasattr(self, "wizard_cross_effects"):
            for effect in list(self.wizard_cross_effects):
                effect["timer"] -= dt
                if effect["timer"] <= 0:
                    self.wizard_cross_effects.remove(effect)

        # Decrement ability effect timers
        if self.player.blink_effect_timer > 0:
            self.player.blink_effect_timer -= dt
        if self.player.heal_effect_timer > 0:
            self.player.heal_effect_timer -= dt
        if self.player.push_effect_timer > 0:
            self.player.push_effect_timer -= dt
        
        if self.player.defiance_timer > 0:
            self.player.defiance_timer -= dt
        
        # Ability Prestige: using an ability grants you a 10% temporary shield for 2 seconds.
        if hasattr(self.player, "ability_shield_timer") and self.player.ability_shield_timer > 0:
            self.player.ability_shield_timer -= dt
            if self.player.ability_shield_timer <= 0:
                self.player.ability_shield_hp = 0

        # Handle Ability Requests
        # Hero Fire Rate Prestige: short range slash
        if getattr(self.player, "hero_prestige_slash_requested", False):
            self.player.hero_prestige_slash_requested = False
            mouse_pos = pygame.mouse.get_pos()
            slash_dir = normalize_safe(pygame.math.Vector2(mouse_pos) - self.player.pos)
            # Create a visual effect for the prestige slash
            if not hasattr(self, "hero_prestige_slashes"): self.hero_prestige_slashes = []
            self.hero_prestige_slashes.append({"pos": self.player.pos.copy(), "dir": slash_dir, "timer": 0.2})
            # Damage enemies in range
            for e in list(self.enemy_group):
                

                if getattr(e, "is_friendly", False): continue
                diff = e.pos - self.player.pos
                dist = diff.length()
                if dist <= 100 + e.radius:
                    # Check if enemy is in front of player (roughly)
                    if slash_dir.dot(normalize_safe(diff)) > 0.5:
                        e.take_damage(self.player.damage * 2, self.enemy_group, player=self.player, game=self)

        if not hasattr(self, "burning_gardens"): self.burning_gardens = []
        if self.player.burning_garden_requested:
            self.player.burning_garden_requested = False
            radius = 150 * self.player.calculate_ability_scaling()
            self.burning_gardens.append(BurningGarden(self.player.pos.copy(), radius))

        if not hasattr(self, "walls"): self.walls = []
        if self.player.wall_requested:
            self.player.wall_requested = False
            mouse_pos = pygame.mouse.get_pos()
            angle = math.degrees(math.atan2(mouse_pos[1] - self.player.pos.y, mouse_pos[0] - self.player.pos.x))
            wall_hp = 150 * self.player.calculate_ability_scaling()
            spawn_pos = self.player.pos + normalize_safe(pygame.math.Vector2(mouse_pos) - self.player.pos) * 80
            self.walls.append(Wall(spawn_pos, angle, hp=wall_hp))

        if hasattr(self.player, "summon_requested") and self.player.summon_requested:
            self.player.summon_requested = False
            self.summoning_circle_timer = 0.5
            # Start at 3 and get +1 every 5 levels
            num_summons = 3 + (self.player.ability_level // 5)
            
            # Create a pool to ensure fair distribution in each summon batch
            # 70% Knight, 20% Crossbowman, 10% Paragon
            spawn_pool = []
            for _ in range(num_summons):
                r = random.random()
                if r < 0.7: spawn_pool.append("knight")
                elif r < 0.9: spawn_pool.append("crossbowman")
                else: spawn_pool.append("paragon")
            
            # Shuffle the pool to keep it random but statistically consistent
            random.shuffle(spawn_pool)
            
            for etype in spawn_pool:
                spawn_pos = self.player.pos + pygame.math.Vector2(random.uniform(-60, 60), random.uniform(-60, 60))
                if etype == "knight":
                    e = KnightAlly(spawn_pos)
                elif etype == "crossbowman":
                    e = CrossbowmanAlly(spawn_pos)
                else:
                    e = ParagonAlly(spawn_pos)
                
                self.enemy_group.append(e)

        if self.player.bomb_requested:
            self.player.bomb_requested = False
            # Scale bomb damage
            bomb_damage = self.player.damage * 100 * self.player.calculate_ability_scaling()
            bomb = Bomb(self.player.pos, damage=bomb_damage, player=self.player)
            self.player_bullets.append(bomb)

        if self.player.cross_attack_requested:
            self.player.cross_attack_requested = False
            damage = self.player.calculate_cross_damage()
            # Purple Cross Attack: damage to all enemies in cross centered on player
            # Hit area: 80 pixels wide cross (40 each side)
            cross_width = 40
            for other_e in list(self.enemy_group):
                if not getattr(other_e, "is_friendly", False):
                    # Check if enemy is in the cross (horizontal or vertical line)
                    in_horizontal = abs(other_e.pos.y - self.player.pos.y) < (other_e.radius + cross_width)
                    in_vertical = abs(other_e.pos.x - self.player.pos.x) < (other_e.radius + cross_width)
                    
                    if in_horizontal or in_vertical:
                        died = other_e.take_damage(damage, self.enemy_group, player=self.player, game=self)
                        if died:
                            self.enemy_group.remove(other_e)

            # Visual effect handled in draw
            if not hasattr(self, "wizard_cross_effects"): self.wizard_cross_effects = []
            self.wizard_cross_effects.append({"pos": self.player.pos.copy(), "timer": 0.4})

        if self.player.push_requested:
            self.player.push_requested = False
            # Store initial enemy positions for gradual pushing
            for e in self.enemy_group:
                diff = e.pos - self.player.pos
                dist = diff.length()
                if dist <= self.player.push_effect_max_radius + e.radius:
                    # Store enemy data for gradual push: (enemy, initial_distance, push_direction)
                    push_dir = normalize_safe(diff)
                    if not hasattr(self.player, 'push_targets'):
                        self.player.push_targets = []
                    self.player.push_targets.append((e, dist, push_dir))
                    e.take_damage(10, self.enemy_group, player=self.player, game=self)  # Minor damage from push

        # Handle gradual force push expansion
        if self.player.push_effect_timer > 0:
            # Calculate current radius based on timer
            progress = 1 - (self.player.push_effect_timer / self.player.push_effect_duration)
            current_radius = progress * self.player.push_effect_max_radius

            if hasattr(self.player, 'push_targets'):
                for enemy, initial_dist, push_dir in self.player.push_targets:
                    if enemy in self.enemy_group:  # Check if enemy still exists
                        # Push enemy if the expanding wave reaches them
                        if current_radius >= initial_dist:
                            # Set enemy position to exactly the current radius of the expansion
                            enemy.pos = self.player.pos + push_dir * current_radius

                # Clear targets when effect ends
                if self.player.push_effect_timer <= dt:
                    self.player.push_targets = []

        # Shooting (allowed during intermission)
        if mouse_pressed[0] and self.player.can_shoot(self.survival_time):
            attack_result = self.player.shoot(mouse_pos, self.survival_time)

            if isinstance(attack_result, Bullet):
                self.player_bullets.append(attack_result)
            elif isinstance(attack_result, list):
                for b in attack_result:
                    self.player_bullets.append(b)
            elif attack_result == "primary_melee":
                # Only trigger slash ONCE when cooldown is ready
                self.perform_hero_slash()
            elif attack_result == "piercing_beam":
                self.perform_archmage_beam()

        # Melee (allowed during intermission)
        self.melee_just_used = False
        # Only trigger standard melee if NOT an Archmage (Archmage uses Space for Summon)
        if self.player.class_name != "Archmage":
            if keys[pygame.K_SPACE] and self.player.can_melee(self.survival_time):
                self.player.melee(self.survival_time)
                self.melee_just_used = True

        # Handle Intermission (only for countdown after upgrade screen)
        if self.in_intermission:
            self.wave_countdown -= dt

            # Update announcement timer
            self.wave_announcement_timer += dt

            # Set announcement text
            self.wave_announcement = f"ROUND {self.wave} starts in {max(0, int(self.wave_countdown) + 1)}..."

            # self.enemy_group.clear() # REMOVED: This was clearing the boss instantly
            # self.enemy_bullets.clear()
            # Freeze enemies and bullets
            for e in self.enemy_group:
                e.freeze = True
            for b in self.enemy_bullets:
                b.freeze = True

            # Update player bullets during intermission so they can move
            for b in self.player_bullets:
                if isinstance(b, Bomb):
                    b.update(dt, self.enemy_group)
                elif isinstance(b, HomingOrb):
                    b.update(dt, self.enemy_group)
                else:
                    b.update(dt)

            # Handle Tri-Split logic
            for b in list(self.pending_splits):
                b.split_timer -= dt
                if b.split_timer <= 0:
                    # Split into 10 homing orbs
                    # Each orb deals 25% of the big orb's damage (which is 50% of normal orb damage)
                    for i in range(10):
                        # Find a target for each orb
                        target = None
                        if self.enemy_group:
                            enemies_not_friendly = [en for en in self.enemy_group if not getattr(en, "is_friendly", False)]
                            if enemies_not_friendly:
                                target = random.choice(enemies_not_friendly)
                        
                        orb = HomingOrb(b.hit_enemy_pos, owner="player", damage=b.damage * 0.4, target_enemy=target, color=NEON_GREEN)
                        # Explode outwards in all directions
                        angle = (i * 36) + random.uniform(-10, 10)
                        rad = math.radians(angle)
                        orb.vel = pygame.math.Vector2(math.cos(rad), math.sin(rad)) * (PLAYER_BULLET_SPEED * 0.6)
                        self.player_bullets.append(orb)
                    self.pending_splits.remove(b)

            if self.wave_countdown <= 0:
                self.in_intermission = False
                self.wave_announcement = None
                self.wave_announcement_timer = 0.0
                self.wave_start_time = self.survival_time  # Record when this wave started
                # Activate bosses when the wave officially starts
                for e in self.enemy_group:
                    if getattr(e, 'is_boss', False) and getattr(e, 'state', None) == "entry":
                        e.state = "idle"
            return  # Skip normal updates during intermission

         # Update enemies
        if self.wave_active:
            for e in list(self.enemy_group):
                

                if hasattr(e, "update_behavior"):
                    # Determine target: Allies target enemies, Enemies target player or allies
                    potential_targets = []
                    if e.is_friendly:
                        potential_targets = [en for en in self.enemy_group if not en.is_friendly]
                    else:
                        potential_targets = [self.player] + [en for en in self.enemy_group if en.is_friendly]
                    
                    # Find nearest target
                    best_target = None
                    min_dist = 99999
                    for t in potential_targets:
                        d = (t.pos - e.pos).length()
                        if d < min_dist:
                            min_dist = d
                            best_target = t
                    
                    target_to_use = best_target if best_target else self.player

                    if isinstance(e, PredictorBot):
                        e.update_behavior(target_to_use, self.survival_time, self.enemy_group)
                    elif isinstance(e, DrifterBot):
                        e.update_behavior(target_to_use, self.survival_time, dt)
                    elif isinstance(e, ShooterBot):
                        # Friendly shooters add to player_bullets, enemies to enemy_bullets
                        target_bullets = self.player_bullets if e.is_friendly else self.enemy_bullets
                        e.update_behavior(target_to_use, self.survival_time, target_bullets)
                    elif isinstance(e, TankBot):
                        e.update_behavior(target_to_use, self.survival_time, dt)
                    elif isinstance(e, MageBot):
                        target_bullets = self.player_bullets if e.is_friendly else self.enemy_bullets
                        e.update_behavior(target_to_use, self.survival_time, target_bullets)
                    elif isinstance(e, SwarmerBot):
                        e.update_behavior(target_to_use)
                    elif isinstance(e, AssassinBot):
                        e.update_behavior(target_to_use, self.survival_time, dt)
                    elif isinstance(e, NecromancerBot):
                        e.update_behavior(target_to_use, self.survival_time, dt, self.enemy_group, self.dead_enemy_pool)
                    elif isinstance(e, AnchorBot):
                        e.update_behavior(self.player, self.survival_time, dt, self.enemy_bullets, self)
                    elif isinstance(e, GravityCoreBot):
                        e.update_behavior(self.player, self.survival_time, dt)
                    elif isinstance(e, AncientOneBoss):
                        e.update_behavior(self.player, self.survival_time, dt, self.enemy_group, self.enemy_bullets, self)
                    elif isinstance(e, RedCoreBoss):
                        e.update_behavior(self.player, self.survival_time, dt, self.enemy_group, self.enemy_bullets)
                    elif isinstance(e, OrangeJuggernautBoss):
                        e.update_behavior(self.player, self.survival_time, dt, self.enemy_bullets)
                    elif isinstance(e, YellowEyeBoss):
                        e.update_behavior(self.player, self.survival_time, dt, self.enemy_bullets)
                    elif isinstance(e, WitchBot):
                        e.update_behavior(target_to_use, self.survival_time, dt, self.status_pools)
                    elif isinstance(e, SniperBot):
                        target_bullets = self.player_bullets if e.is_friendly else self.enemy_bullets
                        e.update_behavior(target_to_use, self.survival_time, dt, target_bullets)

                e.update(dt, self.survival_time)  # base movement update

            # Update bullets (Optimization: Limit total bullets)
            if len(self.player_bullets) > 150:
                self.player_bullets = self.player_bullets[-150:]
            if len(self.enemy_bullets) > 150:
                self.enemy_bullets = self.enemy_bullets[-150:]

            for b in self.player_bullets:
                if isinstance(b, Bomb):
                    b.update(dt, self.enemy_group)
                elif isinstance(b, HomingOrb):
                    b.update(dt, self.enemy_group)
                else:
                    b.update(dt)

            # Handle Tri-Split logic
            for b in list(self.pending_splits):
                b.split_timer -= dt
                if b.split_timer <= 0:
                    # Split into 10 homing orbs
                    # Each orb deals 25% of the big orb's damage (which is 50% of normal orb damage)
                    for i in range(10):
                        # Find a target for each orb
                        target = None
                        if self.enemy_group:
                            enemies_not_friendly = [en for en in self.enemy_group if not getattr(en, "is_friendly", False)]
                            if enemies_not_friendly:
                                target = random.choice(enemies_not_friendly)
                        
                        orb = HomingOrb(b.hit_enemy_pos, owner="player", damage=b.damage * 0.25, target_enemy=target, color=NEON_GREEN)
                        # Explode outwards in all directions
                        angle = (i * 36) + random.uniform(-10, 10)
                        rad = math.radians(angle)
                        orb.vel = pygame.math.Vector2(math.cos(rad), math.sin(rad)) * (PLAYER_BULLET_SPEED * 0.6)
                        self.player_bullets.append(orb)
                    self.pending_splits.remove(b)
            for b in self.enemy_bullets:
                b.update(dt)

            # Handle collisions
            self.handle_collisions()
            
            # Enemy/Ally Cleanup: Remove any that have 0 or less HP
            self.enemy_group = [e for e in self.enemy_group if e.hp > 0]

            # Bullet Cleanup (Optimization: Check every 0.1s)
            if self.survival_time % 0.1 < dt:
                # Keep bombs even if they are slightly offscreen, or just don't filter them by position
                self.player_bullets = [b for b in self.player_bullets if isinstance(
                    b, Bomb) or (0 <= b.pos.x <= WIDTH and 0 <= b.pos.y <= HEIGHT)]
                self.enemy_bullets = [b for b in self.enemy_bullets if 0 <= b.pos.x <= WIDTH and 0 <= b.pos.y <= HEIGHT]

            # Reset melee trigger
            if self.player.melee_just_used:
                self.perform_hero_slash()
                self.player.melee_just_used = False

            # Spawn extra enemies if under max (but not during boss waves)
            if self.wave % 3 != 0 and len(self.enemy_group) < self.max_enemies:
                # Spawn faster as waves progress
                spawn_chance = 0.05 + 0.005 * self.wave  # 0.05 → ~3 spawns/sec at 60 FPS
                if random.random() < spawn_chance:
                    self.spawn_enemy()

            # Check if wave finished
            if self.wave > 0 and self.wave % 3 == 0:
                # Boss Wave: Finished ONLY when boss dies
                # We check if the boss is in the enemy group
                boss_exists = any(isinstance(e, BossBase) for e in self.enemy_group)
                if not boss_exists:
                    # Double check if we actually spawned a boss this wave
                    # (current_boss is set in spawn_boss)
                    if self.current_boss is not None:
                        self.wave_active = False
                        self.current_boss = None
                        self.dead_enemy_pool = []  # Clear souls after boss
                        self.state = self.UPGRADE_SCREEN
                        self.wave_announcement = "BOSS DEFEATED!"
                        self.wave_announcement_timer = 0.0
            else:
                # Normal Wave: Time-based
                wave_elapsed = self.survival_time - self.wave_start_time
                if wave_elapsed >= self.current_wave_duration():
                    self.wave_active = False
                    self.dead_enemy_pool = []  # Clear souls after wave
                    self.state = self.UPGRADE_SCREEN
                    self.wave_announcement = "UPGRADE TIME"
                    self.wave_announcement_timer = 0.0

        # Player death / game over
        if self.player.health <= 0 and self.state == self.GAME_RUNNING:
            self.last_run_stats = {"score": round(self.score), "time": self.survival_time}
            self.leaderboard.append({"score": round(self.score), "time": self.survival_time,
                                    "class": self.player.class_name, "wave": self.wave})
            self.leaderboard = sorted(self.leaderboard, key=lambda x: x["score"], reverse=True)[:10]
            self.state = self.MAIN_MENU

        # Draw Effects
        if self.tether_haze_timer > 0:
            self.tether_haze_timer -= dt
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            # Black haze border
            pygame.draw.rect(s, (0, 0, 0, 180), (0, 0, WIDTH, HEIGHT), 60)
            self.screen.blit(s, (0, 0))
            
        if self.screen_split_effect_timer > 0:
            self.screen_split_effect_timer -= dt
            # Red split line
            pygame.draw.line(self.screen, (255, 0, 0), (WIDTH//2, 0), (WIDTH//2, HEIGHT), 15)
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((255, 0, 0, 40))
            self.screen.blit(s, (0, 0))

        pygame.display.flip()

    def draw_ui(self):
        # Score
        self.score_display.draw(self.screen)

        # Player health
        draw_health_bar(self.screen, 20, 20, self.player.health, PLAYER_MAX_HEALTH, self.clock.get_time() / 1000)

        # Cooldowns (Only using the visual bar display)
        # Ability Cooldown
        # Ability Cooldowns Data
        ability_cooldowns = {
            "Dash": 2.0, "Blink Step": 3.0, "Quick Bomb": 4.0, "Small Heal": 10.0, "Force Push": 5.0, "Melee": 1.5, "Cross Attack": 8.0, "Leech": 12.0, "Summon": 15.0,
            "Burning Garden": 8.0, "Defiance": 7.0, "Wall Arc": 8.0, "Red Lightning": 10.0
        }

        # Intrinsic Ability Cooldown (Space)
        intrinsic_name = self.player.intrinsic_ability
        intrinsic_base = ability_cooldowns.get(intrinsic_name, 2.0)
        intrinsic_cd = intrinsic_base * (1 - self.player.cooldown_reduction)
        
        # Use last_melee for all intrinsic abilities for consistency
        last_used_time = self.player.last_melee
        
        draw_cooldown_bar(
            self.screen, 20, 50,
            max(0.0, intrinsic_cd - (self.survival_time - last_used_time)),
            intrinsic_cd,
            f"{intrinsic_name} (Space)"
        )

        # Secondary Ability Cooldown (Shift)
        secondary_name = self.player.secondary_ability
        secondary_base = ability_cooldowns.get(secondary_name, 2.0)
        secondary_cd = secondary_base * (1 - self.player.cooldown_reduction)
        
        # Calculate remaining cooldown for secondary ability
        if self.player.ability_charges >= self.player.max_ability_charges:
            cd_left = 0.0
        else:
            # If last_dash is -999 but charges aren't full, something is wrong, 
            # but we'll treat it as 0 to avoid crashes.
            if self.player.last_dash == -999:
                cd_left = 0.0
            else:
                cd_left = max(0.0, secondary_cd - (self.survival_time - self.player.last_dash))

        # Show charges in the label
        charge_text = f" [{self.player.ability_charges}/{self.player.max_ability_charges}]" if self.player.max_ability_charges > 1 else ""
        draw_cooldown_bar(
            self.screen, 20, 80,
            cd_left,
            secondary_cd,
            f"{secondary_name}{charge_text} (Shift)"
        )

        # Survival time display
        font = pygame.font.SysFont("arial", 24)
        time_surf = font.render(f"Time Survived: {int(self.survival_time)}s", True, WHITE)
        # Moved from Y=20 to Y=50 to avoid score overlap # Moved from Y=20 to Y=50 to avoid score overlap
        self.screen.blit(time_surf, (WIDTH - 220, 50))

        # Wave / intermission announcement
        if self.in_intermission and self.wave_announcement:
            font = pygame.font.SysFont("arial", 48, bold=True)
            text_surf = font.render(self.wave_announcement, True, WHITE)
            rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.screen.blit(text_surf, rect)
        self.score_display.draw(self.screen)

    def draw(self, dt):
        # Apply screen shake offset
        shake_offset = pygame.math.Vector2(0, 0)
        if hasattr(self, "screen_shake_timer") and self.screen_shake_timer > 0:
            shake_offset.x = random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity)
            shake_offset.y = random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity)

        # Create a temporary surface for the game world to apply shake
        world_surf = pygame.Surface((WIDTH, HEIGHT))
        world_surf.fill((10, 10, 24))

        for b in self.player_bullets:
            pygame.draw.circle(world_surf, YELLOW, (int(b.pos.x), int(b.pos.y)), b.radius)
        for b in self.enemy_bullets:
            pygame.draw.circle(world_surf, GREY, (int(b.pos.x), int(b.pos.y)), b.radius)

        for p in self.status_pools:
            p.draw(world_surf)

        for e in self.enemy_group:
            e.draw(world_surf)

            # Draw Mage warning lines
            if isinstance(e, MageBot):
                e.draw_warning(world_surf, self.survival_time)

            if isinstance(e, WitchBot):
                pass  # Witch has custom draw

            if isinstance(e, SniperBot):
                pass  # Sniper has custom draw

            if hasattr(e, "is_boss") and e.is_boss:
                # Custom Boss Health Bar
                is_ancient = isinstance(e, AncientOneBoss)
                bar_w = 700 if is_ancient else 600
                bar_h = 25 if is_ancient else 20
                bar_x = (WIDTH - bar_w) // 2
                bar_y = HEIGHT - 70
                
                # Background
                pygame.draw.rect(world_surf, (20, 20, 20), (bar_x - 4, bar_y - 4, bar_w + 8, bar_h + 8), border_radius=8)
                
                hp_ratio = clamp(e.hp / e.max_hp, 0, 1)
                
                # Health bar color
                if is_ancient:
                    # Pulsing purple/blue for Ancient One
                    pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) / 2
                    hp_color = lerp_color((100, 0, 200), (50, 0, 100), pulse)
                    # Add a "shield" or "void" effect to the bar
                    pygame.draw.rect(world_surf, (40, 0, 60), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
                else:
                    hp_color = (200, 0, 0)
                
                pygame.draw.rect(world_surf, hp_color, (bar_x, bar_y, bar_w * hp_ratio, bar_h), border_radius=6)
                
                # Boss Name with glow
                boss_name = "THE ANCIENT ONE" if is_ancient else "The Red Core" if isinstance(e, RedCoreBoss) else "The Orange Juggernaut" if isinstance(
                    e, OrangeJuggernautBoss) else "The Yellow Eye"
                
                name_font = pygame.font.SysFont("arial", 40, bold=True) if is_ancient else self.bigfont
                name_surf = name_font.render(boss_name, True, WHITE)
                
                if is_ancient:
                    # Draw glow for Ancient One name
                    glow_surf = name_font.render(boss_name, True, (150, 0, 255))
                    for ox, oy in [(-2,-2), (2,-2), (-2,2), (2,2)]:
                        world_surf.blit(glow_surf, (WIDTH // 2 - name_surf.get_width() // 2 + ox, bar_y - 45 + oy))
                
                world_surf.blit(name_surf, (WIDTH // 2 - name_surf.get_width() // 2, bar_y - 45))
            else:
                hp_w = e.radius * 2
                hp_h = 4
                hp_x = e.pos.x - e.radius
                hp_y = e.pos.y - e.radius - 8
                pygame.draw.rect(world_surf, (60, 60, 60), (hp_x, hp_y, hp_w, hp_h))
                hp_ratio = clamp(e.hp / e.max_hp, 0, 1)
                pygame.draw.rect(world_surf, (40, 220, 40), (hp_x, hp_y, hp_w*hp_ratio, hp_h))

        # Draw damage popups
        popup_font = pygame.font.SysFont("arial", 20, bold=True)
        crit_font = pygame.font.SysFont("arial", 28, bold=True)
        for popup in self.damage_popups:
            popup.draw(world_surf, popup_font, crit_font)

        # Draw player and abilities if player exists
        if self.player:
            # Draw Wizard's Cross Effects
            if hasattr(self, "wizard_cross_effects"):
                for effect in self.wizard_cross_effects:
                    alpha = int(255 * (effect["timer"] / 0.4))
                    color = (160, 32, 240, alpha) # Purple
                    # Draw horizontal and vertical lines for the cross
                    s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    pygame.draw.line(s, color, (0, effect["pos"].y), (WIDTH, effect["pos"].y), 30)
                    pygame.draw.line(s, color, (effect["pos"].x, 0), (effect["pos"].x, HEIGHT), 30)
                    world_surf.blit(s, (0, 0))

            # Draw Spaceman (Electrician) lightning effects
            if self.player.class_name == "Electrician":
                for start_pos, end_pos, timer, color_name in self.player.chain_visuals:
                    color = (255, 255, 0) if color_name == "yellow" else (255, 50, 50)
                    thickness = 3 if color_name == "red" else 2
                    draw_jagged_lightning(world_surf, start_pos, end_pos, color, thickness)

            # Draw wizard sprite centered on player
            sprite_rect = self.player.current_sprite.get_rect(center=(int(self.player.pos.x), int(self.player.pos.y)))
            world_surf.blit(self.player.current_sprite, sprite_rect)

            # Blit world to screen with shake
            self.screen.blit(world_surf, (shake_offset.x, shake_offset.y))

            # Draw Archmage Beam
            if hasattr(self, "archmage_beam_timer") and self.archmage_beam_timer > 0:
                # Pulsating effect
                pulse = (math.sin(pygame.time.get_ticks() * 0.05) + 1) / 2
                
                # Archmage Prestige: Color change from blue to red
                if self.player.prestige["fire_rate"] >= 1:
                    # ramp is 1.0 to 4.0
                    t = (self.player.archmage_ramp - 1.0) / 3.0
                    # Gradient from blue (60, 160, 220) to red (220, 60, 60)
                    base_color = lerp_color((60, 160, 220), (220, 60, 60), t)
                    color = lerp_color(base_color, (255, 255, 255), pulse * 0.3)
                else:
                    color = lerp_color((60, 160, 220), (200, 240, 255), pulse)
                
                width = 4 + int(4 * pulse)
                pygame.draw.line(self.screen, color, self.archmage_beam_start, self.archmage_beam_end, width)

            # Draw Hero Prestige Slashes
            if hasattr(self, "hero_prestige_slashes"):
                for slash in list(self.hero_prestige_slashes):
                    alpha = int(255 * (slash["timer"] / 0.2))
                    s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    # Draw a short arc or line for the slash
                    end_pos = slash["pos"] + slash["dir"] * 100
                    pygame.draw.line(s, (255, 255, 255, alpha), slash["pos"], end_pos, 5)
                    self.screen.blit(s, (0, 0))
                    slash["timer"] -= dt
                    if slash["timer"] <= 0:
                        self.hero_prestige_slashes.remove(slash)

            # Draw Paragon Cross Effects
            if hasattr(self, "paragon_cross_effects"):
                for effect in self.paragon_cross_effects:
                    alpha = int(255 * (effect["timer"] / 0.3))
                    s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    pos = effect["pos"]
                    pygame.draw.line(s, (255, 215, 0, alpha), (pos.x, 0), (pos.x, HEIGHT), 10)
                    pygame.draw.line(s, (255, 215, 0, alpha), (0, pos.y), (WIDTH, pos.y), 10)
                    pygame.draw.line(s, (255, 255, 255, alpha), (pos.x, 0), (pos.x, HEIGHT), 2)
                    pygame.draw.line(s, (255, 255, 255, alpha), (0, pos.y), (WIDTH, pos.y), 2)
                    self.screen.blit(s, (0, 0))
            
            # Draw Burning Gardens
            if hasattr(self, "burning_gardens"):
                for bg in self.burning_gardens:
                    bg.draw(self.screen)

            # Draw Walls
            if hasattr(self, "walls"):
                for w in self.walls:
                    w.draw(self.screen)

            # Draw Defiance Effect
            if self.player.defiance_timer > 0:
                s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                pygame.draw.circle(s, (150, 150, 150, 100), (int(self.player.pos.x), int(self.player.pos.y)), self.player.radius + 10)
                self.screen.blit(s, (0, 0))

            # Draw Summoning Circle
            if hasattr(self, "summoning_circle_timer") and self.summoning_circle_timer > 0:
                try:
                    circle_img = pygame.image.load("summoning_circle.png").convert_alpha()
                    # Scale based on timer
                    scale = 1.0 + (0.5 * (1.0 - self.summoning_circle_timer / 0.5))
                    size = int(120 * scale)
                    circle_img = pygame.transform.smoothscale(circle_img, (size, size))
                    # Rotate
                    circle_img = pygame.transform.rotate(circle_img, pygame.time.get_ticks() * 0.5)
                    rect = circle_img.get_rect(center=(int(self.player.pos.x), int(self.player.pos.y)))
                    self.screen.blit(circle_img, rect)
                except:
                    # Fallback if image missing
                    pygame.draw.circle(self.screen, (100, 100, 255), (int(self.player.pos.x), int(self.player.pos.y)), 60, 3)

            # Draw Ability Visual Effects
            if self.player.blink_effect_timer > 0:
                # Draw a trail or ghost effect
                alpha = int(255 * (self.player.blink_effect_timer / 0.2))
                pygame.draw.circle(self.screen, (100, 200, 255, alpha), (int(self.player.pos.x),
                                   int(self.player.pos.y)), self.player.radius + 10, 2)

            if self.player.heal_effect_timer > 0:
                # Draw green pulse
                alpha = int(150 * (self.player.heal_effect_timer / 0.4))
                s = pygame.Surface((self.player.radius*4, self.player.radius*4), pygame.SRCALPHA)
                pygame.draw.circle(s, (0, 255, 0, alpha), (self.player.radius*2,
                                   self.player.radius*2), self.player.radius*2)
                self.screen.blit(s, (int(self.player.pos.x - self.player.radius*2),
                                 int(self.player.pos.y - self.player.radius*2)))

            if self.player.push_effect_timer > 0:
                # Draw expanding shockwave
                progress = 1 - (self.player.push_effect_timer / self.player.push_effect_duration)
                radius = int(self.player.push_effect_max_radius * progress)
                alpha = int(200 * (self.player.push_effect_timer / self.player.push_effect_duration))
                pygame.draw.circle(self.screen, (200, 200, 255, alpha), (int(
                    self.player.pos.x), int(self.player.pos.y)), radius, 3)

            # Draw Hero's primary melee slash indicator
            if self.player.class_name == "Hero" and self.primary_melee_timer > 0:
                primary_melee_range = self.player.melee_radius

                mouse_pos = pygame.mouse.get_pos()
                # Calculate angle to mouse in radians using atan2
                dx = mouse_pos[0] - self.player.pos.x
                dy = mouse_pos[1] - self.player.pos.y
                center_angle = math.atan2(dy, dx)

                # Arc settings
                arc_deg = 240 if self.player.prestige["fire_rate"] >= 1 else 160
                arc_width_radians = math.radians(arc_deg)
                start_angle = center_angle - arc_width_radians / 2

                # Create a temporary surface for transparency
                slash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

                # 1. Draw Normal Slash Arc
                points = [self.player.pos]
                num_segments = 20
                for i in range(num_segments + 1):
                    theta = start_angle + (arc_width_radians * i / num_segments)
                    x = self.player.pos.x + primary_melee_range * math.cos(theta)
                    y = self.player.pos.y + primary_melee_range * math.sin(theta)
                    points.append((x, y))

                translucent_yellow = (230, 210, 80, 140)
                pygame.draw.polygon(slash_surf, translucent_yellow, points)
                pygame.draw.polygon(slash_surf, (255, 255, 255, 180), points, 2)

                # 2. Draw Precision Strike Extension (Brighter, longer cone)
                precision_range = primary_melee_range * 1.4
                precision_arc_rad = math.radians(30)
                p_start_angle = center_angle - precision_arc_rad / 2

                p_points = [self.player.pos]
                for i in range(6):
                    theta = p_start_angle + (precision_arc_rad * i / 5)
                    x = self.player.pos.x + precision_range * math.cos(theta)
                    y = self.player.pos.y + precision_range * math.sin(theta)
                    p_points.append((x, y))

                bright_yellow = (255, 255, 150, 200)
                pygame.draw.polygon(slash_surf, bright_yellow, p_points)
                pygame.draw.polygon(slash_surf, (255, 255, 255, 255), p_points, 2)

                self.screen.blit(slash_surf, (0, 0))

            # Draw spacebar melee indicator if recently used (for a single frame)
            # The visual effect is now tied to the melee_just_used flag which is set in Game.update
            if self.melee_just_used:
                pygame.draw.circle(self.screen, WHITE, (int(self.player.pos.x), int(self.player.pos.y)),
                                   self.player.melee_radius, 1)  # 1px wide circle as requested

        # Draw UI
        self.draw_ui()

        # Wave announcement
        if self.wave_announcement:
            # Fade out over 2 seconds
            fade_duration = 2.0
            alpha = max(0, 255 * (1 - self.wave_announcement_timer / fade_duration))

            if alpha > 0:
                # Create text surface
                font = pygame.font.SysFont("arial", 48, bold=True)
                text_surf = font.render(self.wave_announcement, True, (255, 255, 255))
                text_surf.set_alpha(int(alpha))

                # Center on screen
                rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                self.screen.blit(text_surf, rect)  # use self.screen, not screen
            else:
                # Fade finished
                self.wave_announcement = None

        # Draw Effects
        if self.tether_haze_timer > 0:
            self.tether_haze_timer -= dt
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            # Black haze border
            pygame.draw.rect(s, (0, 0, 0, 180), (0, 0, WIDTH, HEIGHT), 60)
            self.screen.blit(s, (0, 0))
            
        if self.screen_split_effect_timer > 0:
            self.screen_split_effect_timer -= dt
            # Red split line
            pygame.draw.line(self.screen, (255, 0, 0), (WIDTH//2, 0), (WIDTH//2, HEIGHT), 15)
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((255, 0, 0, 40))
            self.screen.blit(s, (0, 0))

        pygame.display.flip()

    def reset_game(self):
        self.player = None  # Player is created after class selection
        Player.game_ref = self
        self.player_class = None  # Reset class selection
        self.enemy_group = []
        self.player_bullets = []
        self.enemy_bullets = []
        self.score = 0
        self.money = 0
        self.survival_time = 0.0
        self.wave = 0
        self.wave_active = False
        self.in_intermission = False
        self.wave_announcement = None
        self.wave_announcement_timer = 0.0
        self.score_display = ScoreDisplay(pygame.font.SysFont("arial", 24, bold=True))
        # Reset global constants that were modified by upgrades
        global PLAYER_MAX_HEALTH
        PLAYER_MAX_HEALTH = 100
        global PLAYER_HEALTH_REGEN_RATE
        PLAYER_HEALTH_REGEN_RATE = 1.0





    def init_playable_tutorial(self):
        self.player = Player(WIDTH // 2, HEIGHT // 2, "Wizard")
        self.player.selected_ability = "Dash"
        self.enemy_group = []
        self.player_bullets = []
        self.enemy_bullets = []
        self.damage_popups = []
        self.tutorial_step = 0
        self.tutorial_timer = 0.0
        self.tutorial_message = "Welcome to the Arena! Use WASD to move around."
        self.tutorial_sub_message = "Get a feel for your character's movement."
        self.tutorial_complete = False
        self.tutorial_fade = 0
        self.tut_moved = False
        self.tut_shot = False
        self.tut_dashed = False
        self.tut_ability = False
        self.tut_enemies_killed = 0
        self.tut_practice_spawned = False

    def update_playable_tutorial(self, dt):
        self.tutorial_timer += dt
        self.tutorial_fade = min(255, self.tutorial_fade + 5)
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        self.player.game_ref = self
        self.player.game_ref_enemies = self.enemy_group
        self.player.update(dt, keys, mouse_pos, self.tutorial_timer)
        if getattr(self.player, "cross_attack_requested", False):
            self.player.cross_attack_requested = False
            self.player.perform_cross_attack(self.enemy_group, game=self)
        if hasattr(self, "wizard_cross_effects"):
            for effect in list(self.wizard_cross_effects):
                effect["timer"] -= dt
                if effect["timer"] <= 0: self.wizard_cross_effects.remove(effect)
        for b in self.player_bullets[:]:
            b.update(dt)
            if b.pos.x < 0 or b.pos.x > WIDTH or b.pos.y < 0 or b.pos.y > HEIGHT: self.player_bullets.remove(b)
        for e in self.enemy_group[:]:
            e.update(dt, self.player)
            for b in self.player_bullets[:]:
                if (e.pos - b.pos).length() < e.radius + b.radius:
                    e.take_damage(self.player.calculate_damage())
                    if b in self.player_bullets: self.player_bullets.remove(b)
            if e.hp <= 0:
                if e in self.enemy_group: self.enemy_group.remove(e)
                self.tut_enemies_killed += 1
                self.damage_popups.append(DamagePopup(e.pos, "KILLED!", YELLOW))
        for p in self.damage_popups[:]:
            p.update(dt)
            if p.lifetime <= 0: self.damage_popups.remove(p)
        if self.tutorial_step == 0:
            if keys[pygame.K_w] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d]: self.tut_moved = True
            if self.tut_moved and self.tutorial_timer > 2.0:
                self.advance_tutorial_step("Great! Now use LEFT CLICK to shoot.", "Aim with your mouse and fire at the center.")
        elif self.tutorial_step == 1:
            if pygame.mouse.get_pressed()[0]: self.tut_shot = True
            if self.tut_shot and self.tutorial_timer > 2.0:
                self.advance_tutorial_step("Nice shot! Press SPACE for your Class Ability.", "The Wizard uses a powerful Cross Attack.")
        elif self.tutorial_step == 2:
            if keys[pygame.K_SPACE]: self.tut_ability = True
            if self.tut_ability and self.tutorial_timer > 2.0:
                self.advance_tutorial_step("Powerful! Press L-SHIFT to Dash.", "Dashing makes you move fast and dodge attacks.")
        elif self.tutorial_step == 3:
            if keys[pygame.K_LSHIFT]: self.tut_dashed = True
            if self.tut_dashed and self.tutorial_timer > 2.0:
                self.advance_tutorial_step("Perfect. Now, destroy these practice bots!", "Use everything you've learned.")
                if not self.tut_practice_spawned:
                    self.tut_practice_spawned = True
                    for _ in range(3):
                        pos = pygame.math.Vector2(random.uniform(100, WIDTH-100), random.uniform(100, HEIGHT-100))
                        while (pos - self.player.pos).length() < 200:
                            pos = pygame.math.Vector2(random.uniform(100, WIDTH-100), random.uniform(100, HEIGHT-100))
                        self.enemy_group.append(DrifterBot(pos))
        elif self.tutorial_step == 4:
            if self.tut_enemies_killed >= 3:
                self.advance_tutorial_step("Tutorial Complete!", "You are ready for the Arena. Press ESC to return.")
                self.tutorial_complete = True

    def advance_tutorial_step(self, msg, sub_msg):
        self.tutorial_step += 1
        self.tutorial_timer = 0.0
        self.tutorial_message = msg
        self.tutorial_sub_message = sub_msg
        self.tutorial_fade = 0



    def draw_playable_tutorial(self):
        self.draw_ui_background()
        if hasattr(self, "wizard_cross_effects"):
            for effect in self.wizard_cross_effects:
                color = (150, 50, 255, int(255 * (effect["timer"] / 0.4)))
                s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                pygame.draw.rect(s, color, (0, effect["pos"].y - 20, WIDTH, 40))
                pygame.draw.rect(s, color, (effect["pos"].x - 20, 0, 40, HEIGHT))
                self.screen.blit(s, (0, 0))
        self.player.draw(self.screen)
        for b in self.player_bullets: b.draw(self.screen)
        for e in self.enemy_group: e.draw(self.screen)
        for p in self.damage_popups: p.draw(self.screen)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        msg_bg = pygame.Rect(WIDTH//2 - 350, 50, 700, 100)
        pygame.draw.rect(overlay, (20, 20, 40, 200), msg_bg, border_radius=15)
        pygame.draw.rect(overlay, (100, 100, 255, self.tutorial_fade), msg_bg, 2, border_radius=15)
        title_font = pygame.font.SysFont("arial", 32, bold=True)
        sub_font = pygame.font.SysFont("arial", 20)
        t_surf = title_font.render(self.tutorial_message, True, WHITE)
        s_surf = sub_font.render(self.tutorial_sub_message, True, YELLOW)
        t_surf.set_alpha(self.tutorial_fade)
        s_surf.set_alpha(self.tutorial_fade)
        overlay.blit(t_surf, (WIDTH//2 - t_surf.get_width()//2, 70))
        overlay.blit(s_surf, (WIDTH//2 - s_surf.get_width()//2, 110))
        hint_font = pygame.font.SysFont("arial", 18)
        hint_text = "WASD: Move | Mouse: Aim | Left Click: Shoot | Space: Special | Shift: Dash | ESC: Quit"
        h_surf = hint_font.render(hint_text, True, GREY)
        overlay.blit(h_surf, (WIDTH//2 - h_surf.get_width()//2, HEIGHT - 40))
        self.screen.blit(overlay, (0, 0))
        pygame.display.flip()

    def handle_playable_tutorial_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: self.state = self.MAIN_MENU
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos())
                dir_vec = normalize_safe(mouse_pos - self.player.pos)
                self.player_bullets.append(Bullet(self.player.pos.copy(), dir_vec, self.player.calculate_damage(), True))
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE: self.player.cross_attack_requested = True

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.current_time += dt
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if self.state == self.MAIN_MENU:
                    self.handle_main_menu_events(event)
                elif self.state == self.GUIDE:
                    self.handle_tutorial_events(event)
                elif self.state == self.PLAYABLE_TUTORIAL:
                    self.handle_playable_tutorial_events(event)
                elif self.state == self.LEADERBOARD:
                    self.handle_leaderboard_events(event)
                elif self.state == self.CLASS_SELECTION_SCREEN:
                    self.handle_class_selection_events(event)
                elif self.state == self.ABILITY_SELECTION_SCREEN:
                    self.handle_ability_selection_events(event)
                elif self.state == self.UPGRADE_SCREEN:
                    self.handle_upgrade_screen_events(event)

            if self.state == self.GAME_RUNNING:
                self.update(dt)
                self.draw(dt)
            elif self.state == self.MAIN_MENU:
                self.draw_main_menu()
            elif self.state == self.GUIDE:
                self.update_tutorial_animations(dt)
                self.draw_tutorial()
            elif self.state == self.PLAYABLE_TUTORIAL:
                self.update_playable_tutorial(dt)
                self.draw_playable_tutorial()
            elif self.state == self.LEADERBOARD:
                self.draw_leaderboard()
            elif self.state == self.UPGRADE_SCREEN:
                self.draw_upgrade_screen()
            elif self.state == self.CLASS_SELECTION_SCREEN:
                self.draw_class_selection_screen()
            elif self.state == self.ABILITY_SELECTION_SCREEN:
                self.draw_ability_selection_screen()
        pygame.quit()
if __name__ == "__main__":
    game = Game() 
    game.run()