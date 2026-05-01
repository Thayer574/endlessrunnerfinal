import pygame
import math
import random
from collections import deque
from constants import *
from utils import *
from entities import *

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
        self.slash_timer = 0
        self.slash_dir = pygame.math.Vector2(1, 0)

    def update_behavior(self, player, current_time, enemies, dt):
        if self.slash_timer > 0:
            self.slash_timer -= dt

        target = None
        min_dist = 9999
        for e in enemies:
            if not getattr(e, "is_friendly", False):
                d = (e.pos - self.pos).length()
                if d < min_dist:
                    min_dist = d
                    target = e
        
        if target:
            if min_dist < 45:
                self.vel = pygame.math.Vector2(0, 0)
                if (current_time - self.last_attack) >= self.attack_cooldown:
                    self.slash_dir = normalize_safe(target.pos - self.pos)
                    target.take_damage(self.damage, enemies, player=player, game=getattr(player, 'game_ref', None))
                    self.last_attack = current_time
                    self.slash_timer = 0.15
            else:
                self.vel = normalize_safe(target.pos - self.pos) * self.speed
        else:
            # Follow player if no enemies
            if (player.pos - self.pos).length() > 100:
                self.vel = normalize_safe(player.pos - self.pos) * self.speed
            else:
                self.vel = pygame.math.Vector2(0, 0)

    def draw(self, surface):
        super().draw(surface)
        if self.slash_timer > 0:
            # Draw a quick slash arc
            angle = math.degrees(math.atan2(-self.slash_dir.y, self.slash_dir.x))
            slash_surf = pygame.Surface((self.radius * 6, self.radius * 6), pygame.SRCALPHA)
            rect = pygame.Rect(0, 0, self.radius * 6, self.radius * 6)
            start_angle = math.radians(-angle - 60)
            end_angle = math.radians(-angle + 60)
            pygame.draw.arc(slash_surf, (200, 230, 255, 180), rect, start_angle, end_angle, 5)
            surface.blit(slash_surf, (int(self.pos.x - self.radius * 3), int(self.pos.y - self.radius * 3)))

class CrossbowmanAlly(EnemyBase):
    def __init__(self, pos):
        super().__init__(pos, color=(188, 158, 130), radius=15, speed=120, hp=75, score_value=0) # HP buffed to 75
        self.is_friendly = True
        self.attack_cooldown = 0.5 # Buffed to 0.5s
        self.last_attack = -999
        self.damage = 50 # Damage buffed to 50
        self.desired_dist = 250
        self.muzzle_flash = 0

    def update_behavior(self, player, current_time, enemies, bullets_group, dt):
        if self.muzzle_flash > 0:
            self.muzzle_flash -= dt

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
                    # Fix: Use owner="player" but ensure the bullet is added to player_bullets in game.py
                    # Actually, the bug is that it's added to the WRONG group in game.py or Bullet class doesn't handle owner correctly.
                    # Based on game.py:1641, enemy_bullets are checked against player.
                    # CrossbowmanAlly was adding to bullets_group which is self.player_bullets in game.py:1675.
                    # Wait, if it's in player_bullets, it shouldn't hit the player.
                    # Let's re-check game.py collision logic.
                    b = Bullet(self.pos, aim_dir * 800, owner="player", damage=self.damage, color=(255, 255, 200), radius=7)
                    b.piercing = True # Give them piercing for more "oomph"
                    bullets_group.append(b)
                    self.last_attack = current_time
                    self.muzzle_flash = 0.1 # 100ms flash
        else:
            if (player.pos - self.pos).length() > 150:
                self.vel = normalize_safe(player.pos - self.pos) * self.speed
            else:
                self.vel = pygame.math.Vector2(0, 0)

    def draw(self, surface):
        super().draw(surface)
        if self.muzzle_flash > 0:
            # Draw a bright muzzle flash
            flash_size = int(self.radius * 1.5)
            flash_surf = pygame.Surface((flash_size * 2, flash_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (255, 255, 200, 180), (flash_size, flash_size), flash_size)
            surface.blit(flash_surf, (int(self.pos.x - flash_size), int(self.pos.y - flash_size)))

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
        self.aura_timer = 0

    def update_behavior(self, player, current_time, enemies, dt):
        self.flash_timer += dt
        self.aura_timer += dt
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
            if min_dist < 60:
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

    def draw(self, surface):
        # Draw a golden aura
        aura_radius = self.radius + 5 + math.sin(self.aura_timer * 5) * 3
        aura_surf = pygame.Surface((aura_radius * 2.5, aura_radius * 2.5), pygame.SRCALPHA)
        pygame.draw.circle(aura_surf, (255, 215, 0, 80), (int(aura_radius * 1.25), int(aura_radius * 1.25)), int(aura_radius))
        surface.blit(aura_surf, (int(self.pos.x - aura_radius * 1.25), int(self.pos.y - aura_radius * 1.25)))
        super().draw(surface)


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

