# These methods should be added to the Game class in game.py
# Add them after the start_game method

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
