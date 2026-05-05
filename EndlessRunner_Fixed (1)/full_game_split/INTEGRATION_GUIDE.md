# Visual Effects Integration Guide

This guide explains how to integrate the enhanced visual effects into your game.

## Files Updated

### 1. **utils.py** - Enhanced with new effect drawing functions
- `draw_impact_burst()` - Expanding impact effect
- `draw_projectile_trail()` - Trail behind projectiles
- `draw_aura()` - Pulsing aura around entities
- `draw_charge_effect()` - Charging visual indicator
- `draw_hit_flash()` - White flash on hit
- `draw_spinning_rings()` - Rotating rings effect
- `draw_energy_wave()` - Expanding wave effect
- `draw_particle_field()` - Update and draw particle systems
- `create_impact_particles()` - Generate impact particles
- `create_trail_particles()` - Generate trail particles
- `create_explosion_particles()` - Generate explosion particles
- `draw_screen_shake_offset()` - Calculate screen shake
- `draw_vignette()` - Darkening edges effect
- `draw_screen_flash()` - Full screen flash

### 2. **entities.py** - Enhanced with particle effects
- **DamagePopup**: Added scaling animation for crits
- **Bullet**: Added trail particles and enhanced glow
- **TriSplitBullet**: Added pulsing effect
- **HomingOrb**: Added spiral trail effect
- **BoomerangBullet**: Added rotating effect
- **Bomb**: Added pulsing effect and explosion particles
- **BurningGarden**: Added pulsing animation
- **Wall**: Added pulsing effect and hit flash

### 3. **game.py** - Add these methods and integrations

#### Step 1: Import new functions in game.py
Add to imports at the top:
```python
from utils_enhanced import (
    draw_impact_burst, draw_screen_shake_offset, draw_screen_flash, 
    draw_vignette, create_impact_particles, create_explosion_particles,
    create_trail_particles, draw_particle_field
)
```

#### Step 2: Add visual effects methods to Game class
Add these methods after `start_game()`:

```python
def add_impact_effect(self, pos, color, radius=30, intensity=1.0):
    """Add an impact burst effect at the given position."""
    self.impact_effects.append({
        'pos': pygame.math.Vector2(pos),
        'color': color,
        'radius': radius,
        'max_radius': radius,
        'lifetime': 0.3,
        'max_lifetime': 0.3,
        'intensity': intensity
    })

def add_global_particles(self, particles):
    """Add particles to the global particle system."""
    self.global_particles.extend(particles)

def screen_flash(self, color=WHITE, duration=0.1):
    """Create a screen flash effect."""
    self.screen_flash_timer = duration
    self.screen_flash_color = color

def screen_shake(self, intensity=5.0, duration=0.2):
    """Create a screen shake effect."""
    self.screen_shake_timer = duration
    self.screen_shake_intensity = intensity

def update_visual_effects(self, dt):
    """Update all visual effects."""
    # Update impact effects
    for effect in self.impact_effects[:]:
        effect['lifetime'] -= dt
        effect['radius'] = effect['max_radius'] * (1 - effect['lifetime'] / effect['max_lifetime'])
        
        if effect['lifetime'] <= 0:
            self.impact_effects.remove(effect)
    
    # Update screen flash
    if self.screen_flash_timer > 0:
        self.screen_flash_timer -= dt
    
    # Update screen shake
    if self.screen_shake_timer > 0:
        self.screen_shake_timer -= dt
        intensity_factor = self.screen_shake_timer / max(0.001, self.screen_shake_timer + dt)
        self.screen_shake_offset = draw_screen_shake_offset(self.screen_shake_intensity * intensity_factor)
    else:
        self.screen_shake_offset = (0, 0)
    
    # Update vignette
    self.vignette_intensity = max(0, self.vignette_intensity - dt * 2)

def draw_visual_effects(self, dt):
    """Draw all visual effects."""
    # Draw impact effects
    for effect in self.impact_effects:
        intensity = effect['lifetime'] / effect['max_lifetime']
        draw_impact_burst(self.screen, effect['pos'], effect['color'], int(effect['radius']), intensity)
    
    # Draw global particles
    for particle in self.global_particles[:]:
        particle['lifetime'] -= dt
        particle['pos'] += particle['vel'] * dt
        
        if particle['lifetime'] <= 0:
            self.global_particles.remove(particle)
            continue
        
        alpha = int(particle['alpha'] * (particle['lifetime'] / particle['max_lifetime']))
        size = particle['size']
        s = pygame.Surface((int(size * 2), int(size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*particle['color'], alpha), (int(size), int(size)), int(size))
        self.screen.blit(s, (int(particle['pos'].x - size), int(particle['pos'].y - size)))
    
    # Draw screen flash
    if self.screen_flash_timer > 0:
        intensity = self.screen_flash_timer / 0.1
        draw_screen_flash(self.screen, self.screen_flash_color, intensity * 0.3)
    
    # Draw vignette
    if self.vignette_intensity > 0:
        draw_vignette(self.screen, self.vignette_intensity)
```

#### Step 3: Update the update() method
In the `update()` method, add after updating enemies (around line 2150):
```python
# Update visual effects
self.update_visual_effects(dt)
```

#### Step 4: Update the draw() method
In the `draw()` method, add after drawing UI (around line 2220):
```python
# Draw visual effects
self.draw_visual_effects(dt)
```

#### Step 5: Add effects to bullet collisions
In `handle_collisions()`, in the player bullet vs enemy section (around line 1584), add after damage is applied:
```python
# Add impact effect
self.add_impact_effect(b.pos, b.color, radius=20, intensity=0.8)
# Add particles
particles = create_impact_particles(b.pos, b.color, count=6)
self.add_global_particles(particles)
# Screen flash for player hits (30% chance)
if random.random() < 0.3:
    self.screen_flash(b.color, duration=0.05)
```

#### Step 6: Add effects to enemy death
In `handle_collisions()`, when an enemy dies (around line 1636), add:
```python
# Add death effects
particles = create_explosion_particles(e.pos, e.color, count=12)
self.add_global_particles(particles)
self.add_impact_effect(e.pos, e.color, radius=40, intensity=1.0)
self.screen_shake(intensity=2.0, duration=0.15)
```

#### Step 7: Add effects to player damage
In `apply_damage_to_player()` (around line 1507), add:
```python
# Add hit effects
self.player_hit_flash_timer = 0.2
self.screen_flash((255, 0, 0), duration=0.1)
self.vignette_intensity = 0.5
particles = create_impact_particles(self.player.pos, (255, 100, 100), count=8)
self.add_global_particles(particles)
```

#### Step 8: Add effects to abilities
In the ability handling section (around line 1932-1945), add:

For **Force Push**:
```python
if self.player.push_requested:
    self.player.push_requested = False
    # ... existing code ...
    # Add screen shake and particles
    self.screen_shake(intensity=3.0, duration=0.2)
    particles = create_impact_particles(self.player.pos, (100, 200, 255), count=20)
    self.add_global_particles(particles)
```

For **Burning Garden** (when created):
```python
if self.player.burning_garden_requested:
    # ... existing code ...
    # Add particles
    particles = create_explosion_particles(ability_pos, ORANGE, count=15)
    self.add_global_particles(particles)
```

For **Dash** (in player update):
```python
if self.player.dashing:
    # Add trail particles
    for i in range(3):
        offset = self.player.velocity.normalize() * i * 10 if self.player.velocity.length() > 0 else pygame.math.Vector2(0, 0)
        particles = create_trail_particles(self.player.pos + offset, self.player.class_data['color'], self.player.velocity, count=2)
        self.add_global_particles(particles)
```

## Visual Effects Summary

### Particle Systems
- **Impact Particles**: Burst outward on bullet hits
- **Trail Particles**: Follow projectiles
- **Explosion Particles**: Burst on enemy death or bomb explosion

### Screen Effects
- **Screen Shake**: Triggered on major events (enemy death, big hits)
- **Screen Flash**: Color flash on impacts
- **Vignette**: Darkening edges when player takes damage

### Entity Effects
- **Pulsing Auras**: Around enemies and abilities
- **Charge Effects**: Visual feedback for charging abilities
- **Hit Flashes**: White flash on impact
- **Spinning Rings**: Decorative effect for homing orbs
- **Energy Waves**: Expanding wave effect

### Projectile Effects
- **Glows**: Enhanced glow around projectiles
- **Trails**: Particle trails following projectiles
- **Spinning**: Boomerang and homing orbs spin

## Performance Considerations

The particle system is optimized for performance:
- Particles are removed when lifetime expires
- Maximum particles are managed by the global list
- Drawing uses efficient pygame Surface operations
- Effects scale with intensity for better visuals

## Testing

After integration, test:
1. Bullet impacts create particle bursts
2. Enemy deaths create explosions
3. Screen shakes on major events
4. Player damage shows red flash and vignette
5. Abilities create appropriate effects
6. Performance remains smooth at 60 FPS

## Customization

You can adjust effects by modifying:
- Particle count in `create_*_particles()` functions
- Colors in effect calls
- Duration and intensity values
- Radius and scale values
