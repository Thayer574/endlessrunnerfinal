import pygame
import random
import math
from constants import *
from utils import *
from entities import Bullet, DamagePopup
from player import Player
from enemies import DrifterBot

class TutorialModule:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.player = Player((WIDTH // 2, HEIGHT // 2), "Wizard")
        self.player.game_ref = self.game
        self.enemy_group = []
        self.player_bullets = []
        self.damage_popups = []
        self.step = 0
        self.timer = 0.0
        self.message = "Welcome to the Arena! Use WASD to move around."
        self.sub_message = "Get a feel for your character's movement."
        self.fade = 0
        self.complete = False
        
        self.tut_moved = False
        self.tut_shot = False
        self.tut_ability = False
        self.tut_dashed = False
        self.enemies_killed = 0
        self.practice_spawned = False

        # Initialize fonts for damage popups
        self.popup_font = pygame.font.SysFont("arial", 20, bold=True)
        self.popup_crit_font = pygame.font.SysFont("arial", 26, bold=True)

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.state = self.game.MAIN_MENU
            if event.key == pygame.K_SPACE:
                self.player.cross_attack_requested = True
                self.tut_ability = True
            if event.key == pygame.K_LSHIFT:
                self.player.dashing = True
                self.player.dash_time = DASH_DURATION
                self.tut_dashed = True
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if self.player.can_shoot(self.timer):
                    attack_result = self.player.shoot(mouse_pos, self.timer)
                    if isinstance(attack_result, Bullet):
                        self.player_bullets.append(attack_result)
                    elif isinstance(attack_result, list):
                        for b in attack_result:
                            self.player_bullets.append(b)
                    self.tut_shot = True

    def update(self, dt):
        self.timer += dt
        self.fade = min(255, self.fade + 5)
        
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        self.player.update(dt, keys, mouse_pos, self.timer)
        
        if keys[pygame.K_w] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d]:
            self.tut_moved = True

        # Update bullets
        for b in self.player_bullets[:]:
            b.update(dt)
            if b.pos.x < 0 or b.pos.x > WIDTH or b.pos.y < 0 or b.pos.y > HEIGHT:
                self.player_bullets.remove(b)
            
        # Update enemies
        for e in self.enemy_group[:]:
            e.update(dt, self.timer)
            for b in self.player_bullets[:]:
                if (e.pos - b.pos).length() < e.radius + b.radius:
                    e.hp -= b.damage
                    self.damage_popups.append(DamagePopup(e.pos, b.damage))
                    if b in self.player_bullets: self.player_bullets.remove(b)
            if e.hp <= 0:
                self.enemy_group.remove(e)
                self.enemies_killed += 1

        # Update popups
        for p in self.damage_popups[:]:
            p.update(dt)
            if p.lifetime <= 0: self.damage_popups.remove(p)

        # Tutorial Logic Steps
        if self.step == 0 and self.tut_moved and self.timer > 2.0:
            self.advance("Great! Now use LEFT CLICK to shoot.", "Aim with your mouse and fire at the center.")
        elif self.step == 1 and self.tut_shot and self.timer > 2.0:
            self.advance("Nice shot! Press SPACE for your Class Ability.", "The Wizard uses a powerful Cross Attack.")
        elif self.step == 2 and self.tut_ability and self.timer > 2.0:
            self.advance("Powerful! Press L-SHIFT to Dash.", "Dashing makes you move fast and dodge attacks.")
        elif self.step == 3 and self.tut_dashed and self.timer > 2.0:
            self.advance("Perfect. Now, destroy these practice bots!", "Use everything you've learned.")
            if not self.practice_spawned:
                self.practice_spawned = True
                for _ in range(3):
                    pos = pygame.math.Vector2(random.uniform(100, WIDTH-100), random.uniform(100, HEIGHT-100))
                    while (pos - self.player.pos).length() < 200:
                        pos = pygame.math.Vector2(random.uniform(100, WIDTH-100), random.uniform(100, HEIGHT-100))
                    self.enemy_group.append(DrifterBot(pos))
        elif self.step == 4 and self.enemies_killed >= 3:
            self.message = "Tutorial Complete!"
            self.sub_message = "You are ready for the Arena. Press ESC to return."
            self.complete = True

    def advance(self, msg, sub):
        self.step += 1
        self.timer = 0.0
        self.message = msg
        self.sub_message = sub
        self.fade = 0

    def draw(self):
        self.game.draw_ui_background()
        
        # Draw Wizard Cross Attack visual if requested
        if self.player.cross_attack_requested:
            self.player.cross_attack_requested = False
            # Visual only for tutorial
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            color = (150, 50, 255, 180)
            pygame.draw.rect(s, color, (0, self.player.pos.y - 20, WIDTH, 40))
            pygame.draw.rect(s, color, (self.player.pos.x - 20, 0, 40, HEIGHT))
            self.screen.blit(s, (0, 0))
            # Damage nearby enemies
            for e in self.enemy_group:
                if abs(e.pos.x - self.player.pos.x) < 40 or abs(e.pos.y - self.player.pos.y) < 40:
                    e.hp -= 500
                    self.damage_popups.append(DamagePopup(e.pos, 500, color=PURPLE, is_crit=True))

        # Fix: Manually draw the player sprite since Player object has no draw() method
        sprite_rect = self.player.current_sprite.get_rect(center=(int(self.player.pos.x), int(self.player.pos.y)))
        self.screen.blit(self.player.current_sprite, sprite_rect)

        for b in self.player_bullets: b.draw(self.screen)
        for e in self.enemy_group: e.draw(self.screen)
        
        # Fix: Correct DamagePopup.draw calls by providing required font arguments
        for p in self.damage_popups:
            p.draw(self.screen, self.popup_font, self.popup_crit_font)
        
        # Use game's fonts if available, otherwise fallback
        font = pygame.font.SysFont("arial", 32, bold=True)
        sub_font = pygame.font.SysFont("arial", 20)
        
        # UI Overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        msg_bg = pygame.Rect(WIDTH//2 - 350, 50, 700, 100)
        pygame.draw.rect(overlay, (20, 20, 40, 200), msg_bg, border_radius=15)
        pygame.draw.rect(overlay, (100, 100, 255, self.fade), msg_bg, 2, border_radius=15)
        
        t_surf = font.render(self.message, True, WHITE)
        s_surf = sub_font.render(self.sub_message, True, YELLOW)
        t_surf.set_alpha(self.fade)
        s_surf.set_alpha(self.fade)
        
        overlay.blit(t_surf, (WIDTH//2 - t_surf.get_width()//2, 70))
        overlay.blit(s_surf, (WIDTH//2 - s_surf.get_width()//2, 110))
        
        # Hint bar
        hint_font = pygame.font.SysFont("arial", 18)
        hint_text = "WASD: Move | Mouse: Aim | Left Click: Shoot | Space: Special | Shift: Dash | ESC: Quit"
        h_surf = hint_font.render(hint_text, True, GREY)
        overlay.blit(h_surf, (WIDTH//2 - h_surf.get_width()//2, HEIGHT - 40))
        
        self.screen.blit(overlay, (0, 0))
        pygame.display.flip()
