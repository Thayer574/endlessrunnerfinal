import pygame
import math
import random
from constants import *
from utils_enhanced import *

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
        self.scale = 1.5 if is_crit else 1.0

    def update(self, dt):
        self.lifetime -= dt
        self.pos += self.vel * dt
        # Add slight scale animation
        self.scale *= 0.98

    def draw(self, surface, font, crit_font):
        if self.lifetime <= 0: return
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        # Use larger font for crits
        use_font = crit_font if self.is_crit else font
        text_surf = use_font.render(str(self.amount), True, self.color)
        
        # Scale the text
        if self.is_crit:
            scaled_size = int(text_surf.get_width() * self.scale)
            text_surf = pygame.transform.scale(text_surf, (scaled_size, int(text_surf.get_height() * self.scale)))
        
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
        
        # Trail particles
        self.trail_particles = []
        self.trail_timer = 0
        self.trail_interval = 0.02

    def update(self, dt):
        self.pos += self.vel * dt
        self.velocity = self.vel # Keep velocity synced
        self.lifetime -= dt
        
        # Update trail
        self.trail_timer += dt
        if self.trail_timer >= self.trail_interval:
            self.trail_timer = 0
            trail = create_trail_particles(self.pos, self.color, self.vel * 0.5, count=2)
            self.trail_particles.extend(trail)
        
        # Update trail particles
        draw_particle_field(pygame.Surface((1, 1)), self.trail_particles, dt)
        
        if (self.pos.x < -100 or self.pos.x > WIDTH+100 or self.pos.y < -100 or self.pos.y > HEIGHT+100 or self.lifetime <= 0):
            self.kill()

    def draw(self, surface):
        # Draw trail particles
        for particle in self.trail_particles:
            alpha = int(particle['alpha'] * (particle['lifetime'] / particle['max_lifetime']))
            size = particle['size']
            s = pygame.Surface((int(size * 2), int(size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*particle['color'], alpha), (int(size), int(size)), int(size))
            surface.blit(s, (int(particle['pos'].x - size), int(particle['pos'].y - size)))
        
        # Draw a small glow for special bullets
        if self.color != YELLOW and self.color != GREY:
            glow_surf = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color, 120), (self.radius * 2, self.radius * 2), self.radius * 2.5)
            pygame.draw.circle(glow_surf, (*self.color, 80), (self.radius * 2, self.radius * 2), self.radius * 3)
            surface.blit(glow_surf, (int(self.pos.x - self.radius * 2), int(self.pos.y - self.radius * 2)))
        
        # Draw main bullet with enhanced glow
        glow_surf = pygame.Surface((self.radius * 3, self.radius * 3), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color, 100), (self.radius * 1.5, self.radius * 1.5), self.radius * 1.5)
        surface.blit(glow_surf, (int(self.pos.x - self.radius * 1.5), int(self.pos.y - self.radius * 1.5)))
        
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
        # Wizard BIG shot: Purple/Pink theme to match Wizard
        super().__init__(pos, vel, owner, damage * 2.0, color=(255, 50, 255), radius=16)
        self.has_split = False
        self.split_delay = 0.5
        self.split_timer = 0
        self.hit_enemy_pos = None
        self.pulse_timer = 0
        self.rotation = 0

    def update(self, dt):
        self.pulse_timer += dt
        self.rotation += dt * 10
        super().update(dt)
        # Add special trail for BIG shot
        if random.random() < 0.3:
            trail_color = random.choice([(255, 100, 255), (200, 50, 255), (255, 255, 255)])
            self.trail_particles.extend(create_trail_particles(self.pos, trail_color, -self.vel * 0.2, count=1))

    def on_hit(self, game, enemy_hit):
        if not self.has_split:
            self.has_split = True
            self.hit_enemy_pos = enemy_hit.pos.copy()
            self.split_timer = self.split_delay
            if hasattr(game, "pending_splits"):
                game.pending_splits.append(self)
            self.kill()

    def draw(self, surface):
        # Pulsing effect
        pulse = (math.sin(self.pulse_timer * 8) + 1) / 2
        current_radius = self.radius * (1.0 + 0.2 * pulse)
        
        # Draw multiple layers of glow for "BIG" feel
        for i in range(3):
            glow_radius = current_radius * (1.5 + i * 0.5)
            glow_surf = pygame.Surface((int(glow_radius * 2), int(glow_radius * 2)), pygame.SRCALPHA)
            alpha = int(100 / (i + 1))
            pygame.draw.circle(glow_surf, (*self.color, alpha), (int(glow_radius), int(glow_radius)), int(glow_radius))
            surface.blit(glow_surf, (int(self.pos.x - glow_radius), int(self.pos.y - glow_radius)))
        
        # Draw spinning core
        draw_spinning_rings(surface, self.pos, (255, 255, 255), current_radius * 0.8, self.rotation, num_rings=2)
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), int(current_radius))
        pygame.draw.circle(surface, (255, 200, 255), (int(self.pos.x), int(self.pos.y)), int(current_radius * 0.6))

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
        pygame.draw.circle(surface, (255, 255, 255), (int(self.pos.x), int(self.pos.y)), int(current_radius * 0.5))

class BoomerangBullet(Bullet):
    def __init__(self, pos, vel, owner, damage=25, player=None):
        super().__init__(pos, vel, owner, damage, color=BRIGHT_ORANGE, radius=7)
        self.player = player
        self.start_pos = pygame.math.Vector2(pos)
        self.returning = False
        self.max_dist = 500
        self.piercing = True
        self.rotation = 0

    def update(self, dt):
        self.rotation += dt * 15
        
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

    def draw(self, surface):
        # Draw rotating boomerang
        glow_surf = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.color, 100), (self.radius * 2, self.radius * 2), self.radius * 2.5)
        surface.blit(glow_surf, (int(self.pos.x - self.radius * 2), int(self.pos.y - self.radius * 2)))
        
        # Draw spinning effect
        draw_spinning_rings(surface, self.pos, self.color, 10, self.rotation, num_rings=2)
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)

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
        self.pulse_timer = 0
        self.impact_particles = []

    def update(self, dt, enemies):
        self.pulse_timer += dt
        
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
            
            # Update impact particles
            draw_particle_field(pygame.Surface((1, 1)), self.impact_particles, dt)

    def explode(self, enemies):
        self.exploded = True
        self.impact_particles = create_explosion_particles(self.pos, BRIGHT_ORANGE, count=20, speed_range=(150, 350))
        
        for e in enemies:
            # Friendly fire protection: Bombs don't hit friendly summons
            if getattr(e, "is_friendly", False):
                continue
            if (e.pos - self.pos).length() <= self.explosion_radius + e.radius:
                e.take_damage(self.damage, None, player=self.player, game=getattr(self.player, 'game_ref', None))

    def draw(self, surface):
        if not self.exploded:
            # Pulsing effect
            pulse = (math.sin(self.pulse_timer * 3) + 1) / 2
            current_radius = self.radius * (0.9 + 0.1 * pulse)
            
            # Draw glow
            glow_surf = pygame.Surface((int(current_radius * 4), int(current_radius * 4)), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 150, 0, 100), (int(current_radius * 2), int(current_radius * 2)), int(current_radius * 2.5))
            surface.blit(glow_surf, (int(self.pos.x - current_radius * 2), int(self.pos.y - current_radius * 2)))
            
            # Draw white outline circle (explosion radius)
            pygame.draw.circle(surface, WHITE, (int(self.pos.x), int(self.pos.y)), self.explosion_radius, 2)
            # Draw yellow bomb
            pygame.draw.circle(surface, YELLOW, (int(self.pos.x), int(self.pos.y)), int(current_radius))
        else:
            # Draw explosion with particles
            alpha = int(255 * (self.explosion_timer / 0.2))
            s = pygame.Surface((self.explosion_radius*2, self.explosion_radius*2), pygame.SRCALPHA)
            
            # Multiple explosion rings
            pygame.draw.circle(s, (255, 150, 0, alpha), (self.explosion_radius, self.explosion_radius), self.explosion_radius)
            pygame.draw.circle(s, (255, 200, 0, alpha), (self.explosion_radius, self.explosion_radius), int(self.explosion_radius * 0.7))
            
            surface.blit(s, (int(self.pos.x - self.explosion_radius), int(self.pos.y - self.explosion_radius)))
            
            # Draw impact particles
            for particle in self.impact_particles:
                p_alpha = int(particle['alpha'] * (particle['lifetime'] / particle['max_lifetime']))
                size = particle['size']
                ps = pygame.Surface((int(size * 2), int(size * 2)), pygame.SRCALPHA)
                pygame.draw.circle(ps, (*particle['color'], p_alpha), (int(size), int(size)), int(size))
                surface.blit(ps, (int(particle['pos'].x - size), int(particle['pos'].y - size)))

class BurningGarden(pygame.sprite.Sprite):
    def __init__(self, pos, radius, duration=5.0):
        super().__init__()
        self.pos = pygame.math.Vector2(pos)
        self.radius = radius
        self.duration = duration
        self.timer = duration
        self.damage_tick_timer = 0.0
        self.damage_interval = 0.01
        self.damage_per_tick = 2.0**(radius/150)
        self.pulse_timer = 0
        self.impact_particles = []

    def update(self, dt, enemies, player):
        self.timer -= dt
        self.pulse_timer += dt
        
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
        
        # Update particles
        draw_particle_field(pygame.Surface((1, 1)), self.impact_particles, dt)

    def draw(self, surface):
        # Draw semi-opulent orange circle with animation
        alpha = int(120 * (self.timer / self.duration))
        
        # Pulsing effect
        pulse = (math.sin(self.pulse_timer * 3) + 1) / 2
        current_radius = self.radius * (0.95 + 0.05 * pulse)
        
        s = pygame.Surface((int(current_radius * 2), int(current_radius * 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 140, 0, alpha), (int(current_radius), int(current_radius)), int(current_radius))
        # Draw border
        pygame.draw.circle(s, (255, 69, 0, alpha + 30), (int(current_radius), int(current_radius)), int(current_radius), 3)
        surface.blit(s, (int(self.pos.x - current_radius), int(self.pos.y - current_radius)))
        
        # Draw inner glow
        inner_alpha = int(80 * (self.timer / self.duration))
        pygame.draw.circle(s, (255, 200, 0, inner_alpha), (int(current_radius), int(current_radius)), int(current_radius // 2))
        surface.blit(s, (int(self.pos.x - current_radius), int(self.pos.y - current_radius)))

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
        self.pulse_timer = 0
        self.hit_flash_timer = 0

    def take_damage(self, amount):
        self.hp -= amount
        self.hit_flash_timer = 0.2
        if self.hp <= 0:
            self.kill()
            return True
        return False

    def draw(self, surface):
        # Pulsing effect
        self.pulse_timer += 0.016  # Approximate dt
        pulse = (math.sin(self.pulse_timer * 2) + 1) / 2
        current_thickness = self.thickness * (0.9 + 0.1 * pulse)
        
        # Draw dark grey arc
        rect = pygame.Rect(self.pos.x - self.radius, self.pos.y - self.radius, self.radius * 2, self.radius * 2)
        start_angle = math.radians(self.angle - self.arc_width / 2)
        end_angle = math.radians(self.angle + self.arc_width / 2)
        
        # Pygame draw.arc uses a different coordinate system (0 is right, goes counter-clockwise)
        # Our angle is 0 is right, goes clockwise. Need to adjust.
        # Actually pygame.draw.arc(surface, color, rect, start_angle, stop_angle, width)
        # angles are in radians.
        
        # Draw glow
        if self.hit_flash_timer > 0:
            glow_color = (255, 255, 255)
            self.hit_flash_timer -= 0.016
        else:
            glow_color = (100, 100, 100)
        
        pygame.draw.arc(surface, glow_color, rect, -end_angle, -start_angle, int(current_thickness) + 2)
        pygame.draw.arc(surface, (60, 60, 60), rect, -end_angle, -start_angle, int(current_thickness))
        
        # Draw small health bar
        bar_width = 40
        bar_height = 5
        bar_x = self.pos.x - bar_width / 2
        bar_y = self.pos.y - self.radius - 10
        pygame.draw.rect(surface, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, (200, 60, 60), (bar_x, bar_y, bar_width * (self.hp / self.max_hp), bar_height))

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
                # Import BossProjectile inside to avoid circular import if needed, 
                # but since we are in entities.py and enemies.py imports entities, 
                # we should check where BossProjectile is defined.
                # Actually, I'll just use a special color/glow for these fragments to make them unique.
                frag = Bullet(self.pos.copy(), f_vel, owner="enemy", damage=10, color=(150, 0, 255), radius=7)
                self.game.enemy_bullets.append(frag)
            self.kill()
