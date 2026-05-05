import pygame
import math
import random
from collections import deque
from constants import *
from utils import *
from entities import *

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
        if class_name == "Hero":
            self.intrinsic_ability = "Leech"
        elif class_name == "Wizard":
            self.intrinsic_ability = "Cross Attack"
        elif class_name == "Archmage":
            self.intrinsic_ability = "Summon"
        elif class_name == "Electrician":
            self.intrinsic_ability = "Red Lightning"
        else:
            self.intrinsic_ability = None
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
        self.defiance_duration = 1.0
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
        
        # Class specific health increments
        if self.class_name == "Hero":
            percent_per_upgrade = 0.15
        elif self.class_name == "Electrician":
            percent_per_upgrade = 0.10
        elif self.class_name == "Wizard":
            percent_per_upgrade = 0.08
        elif self.class_name == "Archmage":
            percent_per_upgrade = 0.065
        else:
            percent_per_upgrade = 0.10 # Default
            
        total_increase = self.health_level * percent_per_upgrade * self.base_health
        return self.base_health + total_increase

    def calculate_speed(self):
        """Calculate current speed based on upgrade level"""
        if self.speed_level == 0:
            return PLAYER_SPEED
        
        # Class specific speed increments
        if self.class_name == "Hero":
            increment = 10.0
        elif self.class_name == "Electrician":
            # Speed same (original was 5 then 10)
            total_increase = 0
            for i in range(1, self.speed_level + 1):
                if i <= 10: total_increase += 5.0
                else: total_increase += 10.0
            return PLAYER_SPEED + total_increase
        elif self.class_name == "Wizard":
            increment = 3.0
        elif self.class_name == "Archmage":
            increment = 3.0
        else:
            increment = 5.0 # Default
            
        return PLAYER_SPEED + (self.speed_level * increment)

    def calculate_fire_rate(self):
        """Calculate current fire rate based on upgrade level and class base"""
        if self.firerate_level == 0:
            return self.base_fire_rate
        
        # Fire rate stays the same for all classes per prompt ("fire rate the same")
        # When it says the same it means it should remain the same boundaries it already was
        if self.class_name == "Archmage":
            # For Archmage, each upgrade halves the fire rate (0.01 -> 0.005 -> 0.0025...)
            return self.base_fire_rate * (0.5 ** self.firerate_level)
        else:
            total_decrease = 0
            for i in range(1, self.firerate_level + 1):
                if i <= 5:
                    total_decrease += 0.025
                else:
                    total_decrease += 0.04
            return max(0.1, self.base_fire_rate - total_decrease)

    def calculate_regen_rate(self):
        """Calculate current regen rate based on upgrade level"""
        # Base regen is 1.0
        if self.regen_level == 0:
            return 1.0
        
        # Class specific regen increments
        if self.class_name == "Hero":
            increment = 1.0
        elif self.class_name == "Electrician":
            increment = 1.0
        elif self.class_name == "Wizard":
            # Regen same
            total_increase = 0
            for i in range(1, self.regen_level + 1):
                if i <= 9: total_increase += 0.5
                else: total_increase += 1.0
            return 1.0 + total_increase
        elif self.class_name == "Archmage":
            increment = 0.5
        else:
            increment = 0.5 # Default
            
        return 1.0 + (self.regen_level * increment)

    def calculate_damage(self):
        """Calculate current damage based on upgrade level"""
        # Base damage setup
        if self.class_name == "Archmage":
            base_dmg = 1
        elif self.class_name == "Electrician":
            base_dmg = 30
        else:
            base_dmg = 25
            
        if self.damage_level == 0:
            return base_dmg
            
        # Class specific damage increments
        if self.class_name == "Hero":
            increment = 7.0
        elif self.class_name == "Electrician":
            increment = 5.0
        elif self.class_name == "Wizard":
            # Damage same
            increment = 3.0
        elif self.class_name == "Archmage":
            increment = 1.5
        else:
            increment = 3.0 # Default
            
        return base_dmg + (self.damage_level * increment)

    def calculate_cooldown_reduction(self):
        """Calculate current cooldown reduction based on upgrade level"""
        # "cooldown the same" for all
        # Starts at 0%, adds 3% (0.03) per upgrade. Capped at 65%.
        return min(0.65, self.cooldown_level * 0.03)

    def calculate_range(self):
        """Calculate current range based on upgrade level"""
        if self.class_name == "Wizard":
            return 1500  # Screen is 1000x700, 1500 covers all
        if self.class_name == "Hero":
            return 75
        # Starts at 75, adds 3 per upgrade.
        r = 75 + (self.range_level * 3)
        return r

    def calculate_ability_scaling(self):
        """Calculate current ability scaling based on upgrade level (7% per level)"""
        # "ability the same" for all
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

    def update(self, dt, keys, mouse_pos, current_time):
        # Handle leech timer
        if self.leech_timer > 0:
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

        # Movement
        if self.dashing:
            self.dash_time -= dt
            if self.dash_time <= 0:
                self.dashing = False
        else:
            self.velocity = dir_vec * self.speed

        self.pos += self.velocity * dt

        # Screen boundary
        self.pos.x = max(self.radius, min(WIDTH - self.radius, self.pos.x))
        self.pos.y = max(self.radius, min(HEIGHT - self.radius, self.pos.y))

        # Update rect for collision
        self.rect = self.current_sprite.get_rect(center=self.pos)

        # Health regen
        regen_rate = self.calculate_regen_rate()
        self.health = min(self.calculate_health(), self.health + regen_rate * dt)

        # Ability Shield decay
        if self.ability_shield_hp > 0:
            self.ability_shield_hp -= 5.0 * dt # Lose 5 HP per second
            if self.ability_shield_hp < 0: self.ability_shield_hp = 0

        # Ability charges regeneration
        if self.ability_charges < self.max_ability_charges:
            # Recharges based on cooldown reduction
            charge_rate = 0.1 * (1.0 + self.cooldown_reduction) 
            # (Just a placeholder logic, usually charges have fixed CD)

        # History for dash/trail
        self.history.append((self.pos.copy(), current_time))

        # Archmage Ramp Logic
        if self.class_name == "Archmage":
            if getattr(self, "archmage_contact", False):
                # Ramp up when hitting
                self.archmage_ramp = min(4.0, self.archmage_ramp + 1.5 * dt)
                self.archmage_contact = False # Reset for next frame
            else:
                # Decay when not hitting
                self.archmage_ramp = max(1.0, self.archmage_ramp - 2.0 * dt)

        # Handle invulnerability cleanup
        self.cleanup_invulnerability(current_time)

    def take_damage(self, amount):
        if self.ability_shield_hp > 0:
            self.ability_shield_hp -= amount
            if self.ability_shield_hp < 0:
                remaining = abs(self.ability_shield_hp)
                self.ability_shield_hp = 0
                self.health -= remaining
        else:
            self.health -= amount
        return self.health <= 0

    def can_shoot(self, current_time):
        return (current_time - self.last_shot) >= self.fire_rate

    def shoot(self, mouse_pos, current_time, enemies=None):
        self.last_shot = current_time
        self.shot_count += 1
        
        # Calculate direction
        target_pos = pygame.math.Vector2(mouse_pos)
        
        # Spaceman (Electrician) logic: shoot at nearest enemy
        if self.class_name == "Electrician" and enemies:
            nearest_enemy = None
            min_dist = float('inf')
            for e in enemies:
                if not getattr(e, "is_friendly", False):
                    dist = self.pos.distance_to(e.pos)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_enemy = e
            if nearest_enemy:
                target_pos = nearest_enemy.pos

        dir_vec = normalize_safe(target_pos - self.pos)
        if dir_vec.length_squared() == 0:
            dir_vec = pygame.math.Vector2(1, 0)
            
        # Class specific shooting logic
        if self.class_name == "Hero":
            return "primary_melee"
        elif self.class_name == "Archmage":
            return "piercing_beam"
        elif self.class_name == "Wizard":
            # Wizard attack pattern
            pattern = self.wizard_attack_pattern[self.wizard_pattern_index]
            self.wizard_pattern_index = (self.wizard_pattern_index + 1) % len(self.wizard_attack_pattern)
            
            if pattern == "tri-split":
                return TriSplitBullet(self.pos.copy(), dir_vec * PLAYER_BULLET_SPEED, "player", damage=self.calculate_damage())
            else:
                return Bullet(self.pos.copy(), dir_vec * PLAYER_BULLET_SPEED, "player", damage=self.calculate_damage())
        elif self.class_name == "Electrician":
            return "chain_lightning"
        else:
            # Default
            return Bullet(self.pos.copy(), dir_vec * PLAYER_BULLET_SPEED, "player", damage=self.calculate_damage())

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

    def perform_beam_attack(self, mouse_pos, enemies, game=None):
        aim_dir = normalize_safe(pygame.math.Vector2(mouse_pos) - self.pos)
        if aim_dir.length_squared() == 0:
            aim_dir = pygame.math.Vector2(1, 0)

        # Beam settings
        beam_width = 6
        damage = self.calculate_damage()
        
        # Archmage Prestige: Ramp up damage
        if self.prestige["fire_rate"] >= 1:
            damage *= self.archmage_ramp

        # Visual effect timer (in Game class)
        if game:
            game.archmage_beam_timer = 0.1
            game.archmage_beam_start = self.pos.copy()
            game.archmage_beam_end = self.pos + aim_dir * 2000 # Piercing to end of map

        # Damage enemies in the line
        contact_made = False
        for e in list(enemies):
            if getattr(e, "is_friendly", False):
                continue
            
            # Distance from point (enemy.pos) to line (self.pos + aim_dir * t)
            A = self.pos
            D = aim_dir
            V = e.pos - A
            t = V.dot(D)
            
            # Project enemy onto the line
            if t < 0:
                p_closest = A
            else:
                p_closest = A + D * t
                
            dist = (e.pos - p_closest).length()
            
            if dist <= (beam_width / 2) + e.radius:
                contact_made = True
                died = e.take_damage(damage, enemies, player=self, game=game)
                if died and enemies is not None:
                    if isinstance(enemies, list):
                        if e in enemies: enemies.remove(e)
                    elif isinstance(enemies, pygame.sprite.Group):
                        enemies.remove(e)
        
        if contact_made:
            self.archmage_contact = True

    def perform_chain_attack(self, mouse_pos, enemies, game=None):
        aim_dir = normalize_safe(pygame.math.Vector2(mouse_pos) - self.pos)
        best_enemy = None
        min_dist = 999999
        
        # Check for enemies directly under or very near the mouse pointer
        for e in enemies:
            if getattr(e, "is_friendly", False): continue
            dist_to_mouse = (pygame.math.Vector2(mouse_pos) - e.pos).length()
            if dist_to_mouse <= e.radius + 10:
                best_enemy = e
                break
        
        # If no enemy under mouse, look for the one closest to the aim line
        if not best_enemy:
            for e in enemies:
                if getattr(e, "is_friendly", False): continue
                to_enemy = e.pos - self.pos
                dist = to_enemy.length()
                if dist == 0: continue
                dot = aim_dir.dot(to_enemy.normalize())
                # Narrower cone (0.9 instead of 0.5) for more precise aiming
                if dot > 0.9:
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

    def use_ability(self, ability_name, current_time, dir_vec, mouse_pos):
        # Ability Cooldowns (Base values from endlessrunner.py)
        ability_cooldowns = {
            "Dash": 2.0,
            "Blink Step": 3.0,
            "Quick Bomb": 4.0,
            "Small Heal": 10.0,
            "Force Push": 5.0,
            "Burning Garden": 8.0,
            "Defiance": 7.0,
            "Wall Arc": 8.0,
            "Melee": 1.5,
            "Cross Attack": 8.0,
            "Summon": 15.0,
            "Leech": 15.0,
            "Red Lightning": 10.0
        }

        # Apply cooldown reduction
        for k in ability_cooldowns:
            ability_cooldowns[k] *= (1 - self.cooldown_reduction)

        scaling = self.calculate_ability_scaling()

        # Ability Prestige: using an ability grants you a 10% temporary shield for 2 seconds.
        if self.prestige["ability"] >= 1:
            self.ability_shield_timer = 2.0
            # 10% of max health as shield
            self.ability_shield_hp = self.calculate_health() * 0.10

        if ability_name == "Dash":
            dash_dir = dir_vec if dir_vec.length_squared() > 0 else normalize_safe(pygame.math.Vector2(mouse_pos) - self.pos)
            if dash_dir.length_squared() > 0:
                self.dashing = True
                self.dash_time = DASH_DURATION
                # Scale dash distance (speed * duration)
                self.velocity = dash_dir * (DASH_SPEED * scaling)

        elif ability_name == "Blink Step":
            blink_dir = dir_vec if dir_vec.length_squared() > 0 else normalize_safe(pygame.math.Vector2(mouse_pos) - self.pos)
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
            # Archmage's intrinsic ability: Summon friendly enemies
            self.summon_requested = True
        
        return None

    def get_ability_cooldown(self, ability_name):
        ability_cooldowns = {
            "Dash": 2.0, "Blink Step": 3.0, "Quick Bomb": 4.0, "Small Heal": 10.0,
            "Force Push": 5.0, "Burning Garden": 8.0, "Defiance": 7.0, "Wall Arc": 8.0,
            "Melee": 1.5, "Cross Attack": 8.0, "Summon": 15.0, "Leech": 15.0, "Red Lightning": 10.0
        }
        base_cd = ability_cooldowns.get(ability_name, 2.0)
        return base_cd * (1 - self.cooldown_reduction)
