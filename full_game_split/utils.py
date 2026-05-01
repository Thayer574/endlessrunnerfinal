import pygame
import math
import random
from constants import *

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

# -----------------------
# NEW ENHANCED EFFECTS
# -----------------------

def draw_impact_burst(surface, pos, color, radius, intensity=1.0):
    """Draw an expanding burst effect for impacts."""
    s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    
    # Outer glow
    alpha = int(150 * intensity)
    pygame.draw.circle(s, (*color, alpha), (radius, radius), radius)
    
    # Inner bright core
    inner_alpha = int(255 * intensity)
    pygame.draw.circle(s, (*color, inner_alpha), (radius, radius), radius // 2)
    
    surface.blit(s, (int(pos.x - radius), int(pos.y - radius)))

def draw_projectile_trail(surface, pos, color, length=15, thickness=2):
    """Draw a trail behind a projectile."""
    s = pygame.Surface((length * 2, length * 2), pygame.SRCALPHA)
    
    # Gradient trail
    for i in range(length):
        alpha = int(200 * (1 - i / length))
        size = max(1, thickness * (1 - i / length))
        pygame.draw.circle(s, (*color, alpha), (length, length), size)
    
    surface.blit(s, (int(pos.x - length), int(pos.y - length)))

def draw_aura(surface, pos, color, radius, intensity=1.0, pulse_time=0):
    """Draw a pulsing aura around an entity."""
    s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    
    # Pulsing effect
    pulse = (math.sin(pulse_time * 4) + 1) / 2
    current_radius = radius * (0.8 + 0.2 * pulse)
    
    # Outer glow
    alpha = int(100 * intensity * pulse)
    pygame.draw.circle(s, (*color, alpha), (radius, radius), int(current_radius), 3)
    
    # Inner glow
    inner_alpha = int(150 * intensity)
    pygame.draw.circle(s, (*color, inner_alpha), (radius, radius), int(current_radius // 2), 2)
    
    surface.blit(s, (int(pos.x - radius), int(pos.y - radius)))

def draw_charge_effect(surface, pos, color, radius, charge_amount):
    """Draw a charging effect (0.0 to 1.0)."""
    s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    
    # Background ring
    pygame.draw.circle(s, (*color, 80), (radius, radius), radius, 2)
    
    # Charge arc
    angle = charge_amount * math.pi * 2
    start_angle = -math.pi / 2
    end_angle = start_angle + angle
    
    # Draw filled arc using polygon
    points = [(radius, radius)]
    num_points = max(3, int(charge_amount * 20))
    for i in range(num_points + 1):
        t = i / max(1, num_points)
        a = start_angle + (end_angle - start_angle) * t
        x = radius + radius * math.cos(a)
        y = radius + radius * math.sin(a)
        points.append((x, y))
    
    if len(points) > 2:
        pygame.draw.polygon(s, (*color, 200), points)
    
    surface.blit(s, (int(pos.x - radius), int(pos.y - radius)))

def draw_hit_flash(surface, pos, radius, intensity=1.0):
    """Draw a white flash effect for hits."""
    s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    alpha = int(255 * intensity)
    pygame.draw.circle(s, (255, 255, 255, alpha), (radius, radius), radius)
    surface.blit(s, (int(pos.x - radius), int(pos.y - radius)))

def draw_spinning_rings(surface, pos, color, radius, rotation, num_rings=3):
    """Draw spinning rings around an entity."""
    s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    
    for i in range(num_rings):
        ring_radius = radius * (0.3 + 0.35 * i)
        alpha = int(150 * (1 - i / num_rings))
        
        # Calculate rotated position
        angle = rotation + (i * math.pi * 2 / num_rings)
        
        # Draw ring segments
        for j in range(8):
            seg_angle = angle + (j * math.pi * 2 / 8)
            x = radius + ring_radius * math.cos(seg_angle)
            y = radius + ring_radius * math.sin(seg_angle)
            pygame.draw.circle(s, (*color, alpha), (int(x), int(y)), 2)
    
    surface.blit(s, (int(pos.x - radius), int(pos.y - radius)))

def draw_energy_wave(surface, pos, color, radius, wave_time):
    """Draw an expanding energy wave."""
    s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    
    # Multiple expanding rings
    wave_pos = (wave_time % 1.0) * radius
    thickness = 3
    
    for i in range(3):
        ring_pos = wave_pos - i * (radius / 3)
        if 0 <= ring_pos <= radius:
            alpha = int(200 * (1 - i / 3) * (1 - ring_pos / radius))
            pygame.draw.circle(s, (*color, alpha), (radius, radius), int(ring_pos), thickness)
    
    surface.blit(s, (int(pos.x - radius), int(pos.y - radius)))

def draw_particle_field(surface, particles, dt):
    """Draw and update a list of particles."""
    for particle in particles[:]:
        particle['lifetime'] -= dt
        particle['pos'] += particle['vel'] * dt
        
        if particle['lifetime'] <= 0:
            particles.remove(particle)
            continue
        
        alpha = int(particle['alpha'] * (particle['lifetime'] / particle['max_lifetime']))
        size = particle['size'] * (particle['lifetime'] / particle['max_lifetime'])
        
        s = pygame.Surface((int(size * 2), int(size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*particle['color'], alpha), (int(size), int(size)), int(size))
        surface.blit(s, (int(particle['pos'].x - size), int(particle['pos'].y - size)))

def create_impact_particles(pos, color, count=8, speed_range=(100, 300)):
    """Create particles for an impact effect."""
    particles = []
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(speed_range[0], speed_range[1])
        vel = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * speed
        
        particles.append({
            'pos': pygame.math.Vector2(pos),
            'vel': vel,
            'lifetime': random.uniform(0.3, 0.6),
            'max_lifetime': 0.6,
            'size': random.uniform(2, 5),
            'color': color,
            'alpha': 200
        })
    return particles

def create_trail_particles(pos, color, vel, count=3):
    """Create particles for a trail effect."""
    particles = []
    for _ in range(count):
        angle_offset = random.uniform(-0.3, 0.3)
        speed_mult = random.uniform(0.5, 1.0)
        
        particles.append({
            'pos': pygame.math.Vector2(pos),
            'vel': vel * speed_mult + pygame.math.Vector2(math.cos(angle_offset), math.sin(angle_offset)) * 50,
            'lifetime': 0.4,
            'max_lifetime': 0.4,
            'size': random.uniform(1, 3),
            'color': color,
            'alpha': 150
        })
    return particles

def create_explosion_particles(pos, color, count=16, speed_range=(200, 400)):
    """Create particles for an explosion effect."""
    particles = []
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(speed_range[0], speed_range[1])
        vel = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * speed
        
        particles.append({
            'pos': pygame.math.Vector2(pos),
            'vel': vel,
            'lifetime': random.uniform(0.4, 0.8),
            'max_lifetime': 0.8,
            'size': random.uniform(2, 6),
            'color': color,
            'alpha': 220
        })
    return particles

def draw_screen_shake_offset(intensity):
    """Calculate screen shake offset."""
    return (random.randint(-int(intensity), int(intensity)), 
            random.randint(-int(intensity), int(intensity)))

def draw_vignette(surface, intensity=0.3):
    """Draw a vignette effect (darkening edges)."""
    s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    
    # Create radial gradient vignette
    for r in range(int(WIDTH * 0.7), 0, -50):
        alpha = int(150 * intensity * (1 - r / (WIDTH * 0.7)))
        pygame.draw.circle(s, (0, 0, 0, alpha), (WIDTH // 2, HEIGHT // 2), r)
    
    surface.blit(s, (0, 0))

def draw_screen_flash(surface, color, intensity):
    """Draw a full screen flash."""
    s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    alpha = int(255 * intensity)
    s.fill((*color, alpha))
    surface.blit(s, (0, 0))
