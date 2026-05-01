import pygame
import math
from constants import *
from utils import *

class GuideModule:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.section = None
        self.page = 0
        self.sections = ["Classes", "Enemies", "Abilities", "Bosses", "Basic Info", "Prestige & Shop"]
        self.hover_scales = [1.0] * len(self.sections)
        self.alpha = 0
        self.target_alpha = 255
        self.anim_timer = 0.0
        
        # Content definitions
        self.content = {
            "Classes": [
                {"title": "WIZARD", "desc": "Ranged specialist. Powerful Cross Attack.", "details": "Great for clearing screens and boss damage.", "color": (100, 50, 150)},
                {"title": "HERO", "desc": "Melee brawler. High HP and Leech ability.", "details": "Tough to kill, excels in close combat.", "color": (50, 100, 150)},
                {"title": "ARCHMAGE", "desc": "Arcane master. Piercing beams and summons.", "details": "Weak early, unstoppable late game.", "color": (60, 160, 220)},
                {"title": "ELECTRICIAN", "desc": "Chain lightning specialist.", "details": "Hits multiple enemies, great crowd control.", "color": (184, 134, 11)}
            ],
            "Enemies": [
                {"title": "DRIFTER", "desc": "Basic red enemy.", "details": "Moves directly toward you. Low health."},
                {"title": "TANK", "desc": "Slow purple behemoth.", "details": "High health, hard to knock back."},
                {"title": "PREDICTOR", "desc": "Orange tracker.", "details": "Predicts your movement to intercept you."}
            ],
            "Abilities": [
                {"title": "DASH", "desc": "Quick burst of speed.", "details": "Use Shift to dodge through projectiles."},
                {"title": "CROSS ATTACK", "desc": "Wizard's signature move.", "details": "Deals massive damage in a cross pattern."},
                {"title": "LEECH", "desc": "Hero's survival tool.", "details": "Heal by dealing damage to enemies."}
            ],
            "Bosses": [
                {"title": "RED CORE", "desc": "Wave 3 Boss.", "details": "Fires complex patterns and splits on death."},
                {"title": "ORANGE JUGGERNAUT", "desc": "Wave 6 Boss.", "details": "Massive health and heavy fire."},
                {"title": "YELLOW EYE", "desc": "Wave 9 Boss.", "details": "Precise laser attacks and high speed."}
            ],
            "Basic Info": [
                {"title": "CONTROLS", "desc": "WASD: Move | Mouse: Aim", "details": "Left Click: Shoot | Space: Special | Shift: Dash"},
                {"title": "OBJECTIVE", "desc": "Survive waves of enemies.", "details": "Collect credits to upgrade your stats."}
            ],
            "Prestige & Shop": [
                {"title": "UPGRADES", "desc": "Buy stats in the shop.", "details": "Health, Speed, Damage, and more."},
                {"title": "PRESTIGE", "desc": "Reach Level 15 in a stat.", "details": "Unlock powerful unique perks for that stat."}
            ]
        }

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.section: self.section = None
                else: self.game.state = self.game.MAIN_MENU
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if not self.section:
                # Check grid clicks
                for i, s in enumerate(self.sections):
                    rect = pygame.Rect(100 + (i % 3) * 300, 200 + (i // 3) * 250, 250, 200)
                    if rect.collidepoint(mouse_pos):
                        self.section = s
                        self.page = 0
                
                # Back button in grid view
                back_rect = pygame.Rect(WIDTH//2 - 75, HEIGHT - 80, 150, 45)
                if back_rect.collidepoint(mouse_pos):
                    self.game.state = self.game.MAIN_MENU
            else:
                # Back button in section view
                back_rect = pygame.Rect(50, 50, 120, 45)
                if back_rect.collidepoint(mouse_pos):
                    self.section = None

    def update(self, dt):
        self.anim_timer += dt
        self.alpha += (self.target_alpha - self.alpha) * min(10 * dt, 1)
        
        mouse_pos = pygame.mouse.get_pos()
        if not self.section:
            for i, s in enumerate(self.sections):
                rect = pygame.Rect(100 + (i % 3) * 300, 200 + (i // 3) * 250, 250, 200)
                target = 1.05 if rect.collidepoint(mouse_pos) else 1.0
                self.hover_scales[i] += (target - self.hover_scales[i]) * min(15 * dt, 1)

    def draw(self):
        self.game.draw_ui_background()
        title_font = pygame.font.SysFont("arial", 60, bold=True)
        section_font = pygame.font.SysFont("arial", 32, bold=True)
        text_font = pygame.font.SysFont("arial", 22)
        
        if not self.section:
            self.game.draw_glow_text("ACADEMY GUIDE", title_font, WHITE, (WIDTH//2 - 220, 60), (50, 50, 150))
            
            for i, s in enumerate(self.sections):
                base_rect = pygame.Rect(100 + (i % 3) * 300, 200 + (i // 3) * 250, 250, 200)
                scale = self.hover_scales[i]
                rect = base_rect.inflate(base_rect.width * (scale-1), base_rect.height * (scale-1))
                
                color = (40, 40, 70) if scale > 1.01 else (25, 25, 40)
                pygame.draw.rect(self.screen, color, rect, border_radius=15)
                pygame.draw.rect(self.screen, (100, 100, 200), rect, 2, border_radius=15)
                
                s_text = section_font.render(s, True, WHITE)
                self.screen.blit(s_text, (rect.centerx - s_text.get_width()//2, rect.centery - s_text.get_height()//2))
            
            # Back to Menu button
            back_rect = pygame.Rect(WIDTH//2 - 75, HEIGHT - 80, 150, 45)
            self.game.draw_custom_button("BACK", back_rect, back_rect.collidepoint(pygame.mouse.get_pos()), self.anim_timer)
        else:
            # Section View
            self.game.draw_glow_text(self.section.upper(), section_font, YELLOW, (WIDTH//2 - 100, 60), (100, 100, 0))
            
            back_rect = pygame.Rect(50, 50, 120, 45)
            self.game.draw_custom_button("< BACK", back_rect, back_rect.collidepoint(pygame.mouse.get_pos()), self.anim_timer)
            
            items = self.content.get(self.section, [])
            for i, item in enumerate(items):
                y_off = 150 + i * 140
                card_rect = pygame.Rect(100, y_off, WIDTH - 200, 120)
                pygame.draw.rect(self.screen, (30, 30, 50), card_rect, border_radius=10)
                pygame.draw.rect(self.screen, (80, 80, 120), card_rect, 1, border_radius=10)
                
                t_surf = section_font.render(item["title"], True, item.get("color", WHITE))
                d_surf = text_font.render(item["desc"], True, (200, 200, 200))
                det_surf = text_font.render(item["details"], True, GREY)
                
                self.screen.blit(t_surf, (card_rect.x + 20, card_rect.y + 15))
                self.screen.blit(d_surf, (card_rect.x + 20, card_rect.y + 55))
                self.screen.blit(det_surf, (card_rect.x + 20, card_rect.y + 85))
        
        pygame.display.flip()
