import pygame
import math
import random
import time
import json
import os
from collections import deque
from constants import *
from utils import *
from entities import *
from player import *
from enemies import *
from guide_module import GuideModule
from tutorial_module import TutorialModule

class Game:
    MAIN_MENU = 0
    GAME_RUNNING = 1
    LEADERBOARD = 2
    UPGRADE_SCREEN = 4
    CLASS_SELECTION_SCREEN = 5
    ABILITY_SELECTION_SCREEN = 6
    TUTORIAL = 7
    GUIDE = 8
    
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
        self.draw_glow_text("ACADEMY", title_font, WHITE, (WIDTH//2 - 100, 50), (50, 50, 150))
        
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
            is_maxed = (stat_key == "cooldown" and self.player.calculate_cooldown_reduction() >= 0.65)
            can_afford = self.money >= cost and not is_maxed
            btn_rect = pygame.Rect(800, y - 5, 100, 32)
            btn_hover = btn_rect.collidepoint(mouse_pos)
            
            if is_maxed:
                btn_color = (150, 50, 50) # Reddish for maxed
                pygame.draw.rect(self.screen, btn_color, btn_rect, border_radius=6)
                btn_text = "MAX"
            else:
                btn_color = (50, 180, 100) if can_afford else (80, 80, 80)
                pygame.draw.rect(self.screen, btn_color, btn_rect, border_radius=6)
                if btn_hover and can_afford:
                    pygame.draw.rect(self.screen, WHITE, btn_rect, 2, border_radius=6)
                btn_text = f"${int(cost)}"
            
            cost_surf = stat_font.render(btn_text, True, WHITE)
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
        self.melee_just_used = False
        self.current_boss = None
        self.dead_enemy_pool = []
        self.damage_popups = []
        self.pending_splits = []
        self.tether_haze_timer = 0.0
        self.screen_split_effect_timer = 0.0
        self.screen_shake_timer = 0.0
        self.screen_shake_intensity = 5.0
        
        # Enhanced visual effects
        self.global_particles = []  # Global particle system
        self.impact_effects = []  # Impact burst effects
        self.screen_flash_timer = 0.0
        self.screen_flash_color = WHITE
        self.vignette_intensity = 0.0
        self.hit_indicators = []  # For visual hit feedback
        self.enemy_hit_flashes = {}  # Track hit flash timers for enemies
        self.player_hit_flash_timer = 0.0
        self.screen_shake_offset = (0, 0)

        self.state = self.MAIN_MENU
        self.start_time = self.current_time
        self.guide_module = GuideModule(self)
        self.tutorial_module = None
        self.menu_buttons = [
            {"label": "Play", "action": lambda: self.start_game()},
            {"label": "Leaderboard", "action": self.go_leaderboard},
            {"label": "Guide", "action": self.go_guide},
            {"label": "Tutorial", "action": self.go_tutorial}
        ]
        self.button_rects = []
        self.tutorial_page = 0
        self.tutorial_section = None # None means grid view, otherwise the section name
        self.tutorial_sections = ["Classes", "Enemies", "Special Enemies", "Abilities", "Bosses", "Basic Info", "Advanced Info"]
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
                    "lines": ["THE SHOP", "Upgrade stats using money from kills.", "Health, Speed, Fire Rate, Regen, Damage.", "Cooldown and Ability stats are vital."],
                    "type": "text_only", "data": None
                }
            ],
            
            "Special Enemies": [
                {
                    "name": "Anchor",
                    "color": (0, 100, 0),
                    "description": "A dark green enemy that waits 4s then fires a tether. If hit, you are pulled for 1.5s. Movement locked but firing allowed."
                },
                {
                    "name": "Gravity Core",
                    "color": (174, 164, 191),
                    "description": "A pale purple core that pulses and pulls nearby players in, slowing them down and making them easier targets."
                },
                {
                    "name": "Ancient One",
                    "color": (60, 60, 60),
                    "description": "The Wave 12 Boss. Summons mini-bosses, splits the screen for massive damage, and throws breaking stone bricks."
                }
            ],
            "Advanced Info": [
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

    def go_tutorial(self):
        self.tutorial_module = TutorialModule(self)
        self.state = self.TUTORIAL

    def go_guide(self):
        self.state = self.GUIDE

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
            if self.player.calculate_cooldown_reduction() < 0.65:
                self.player.cooldown_level += 1
            else:
                # Refund money if somehow clicked when capped
                self.money += cost
                return
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
        beam_width = 10 # Slightly wider
        damage = self.player.damage
        
        # Archmage Prestige: Ramp up damage
        if self.player.prestige["fire_rate"] >= 1:
            damage *= self.player.archmage_ramp

        # Visual effect timer
        self.archmage_beam_timer = 0.1
        self.archmage_beam_start = self.player.pos.copy()
        self.archmage_beam_end = self.player.pos + beam_dir * 2000 # Piercing to end of map
        
        # Visual effect handled in draw loop

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

            # 1. Check Precision Zone (Inner 40% of range, focused arc)
            if abs(angle_diff) <= (arc_angle_degrees / 4):
                if dist <= (slash_range * 0.4) + e.radius:
                    is_hit = True
                    final_damage *= 3  # High DPS in the focused center zone where swords cross

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
                    e.update_behavior(self.player, self.survival_time, self.enemy_group, dt)
                elif isinstance(e, CrossbowmanAlly):
                    e.update_behavior(self.player, self.survival_time, self.enemy_group, self.player_bullets, dt)
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

        # Update Boss Screen Effects
        if self.wave_active and self.current_boss:
            # Subtle vignette pulse for bosses
            self.vignette_intensity = max(self.vignette_intensity, 0.4 + 0.1 * math.sin(self.survival_time * 2))
            
            # Special effects for specific bosses
            if isinstance(self.current_boss, AncientOneBoss):
                # Glitch intensity increases with boss phase
                glitch_chance = 0.05 if self.current_boss.phase == 1 else 0.15
                if random.random() < glitch_chance:
                    self.screen_shake_timer = max(self.screen_shake_timer, 0.1)
                    self.screen_shake_intensity = 8.0 if self.current_boss.phase == 2 else 4.0
                
                # Darken the screen as the Ancient One takes damage
                hp_ratio = self.current_boss.hp / self.current_boss.max_hp
                self.vignette_intensity = max(self.vignette_intensity, 0.8 - (hp_ratio * 0.4))
            
            elif isinstance(self.current_boss, RedCoreBoss):
                # Pulsing red flash for Red Core
                if int(self.survival_time * 2) % 2 == 0:
                    self.vignette_intensity = max(self.vignette_intensity, 0.5)
            
            elif isinstance(self.current_boss, OrangeJuggernautBoss):
                # Shake screen when Juggernaut is in special/slam states
                if self.current_boss.state in ["slam", "special"]:
                    self.screen_shake_timer = max(self.screen_shake_timer, 0.1)
                    self.screen_shake_intensity = 5.0
        else:
            # Decay effects when no boss
            self.vignette_intensity = max(0, self.vignette_intensity - dt)

        # Player update (moved before intermission check to allow movement during intermission)
        self.player.speed_mult = 1.0  # Reset speed mult
        for p in list(self.status_pools):
            p.update(dt, self.player, self.survival_time)
            if p.lifetime <= 0:
                self.status_pools.remove(p)

        self.player.game_ref = self
        self.player.game_ref_enemies = self.enemy_group
        # Calculate dir_vec for player movement and abilities
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

        self.player.update(dt, keys, mouse_pos, self.survival_time)

        # Update damage popups
        for popup in list(self.damage_popups):
            popup.update(dt)
            if popup.lifetime <= 0:
                self.damage_popups.remove(popup)

        # Update global particles
        if hasattr(self, "global_particles"):
            for p in list(self.global_particles):
                p["pos"][0] += p["vel"][0] * dt
                p["pos"][1] += p["vel"][1] * dt
                p["lifetime"] -= dt
                if p["lifetime"] <= 0:
                    self.global_particles.remove(p)

        if self.player.class_name == "Electrician":
            # Auto-fire removed: now handled in the mouse click block below
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
            # Hit area: 60 pixels wide cross (30 each side)
            cross_width = 30
            for other_e in list(self.enemy_group):
                if not getattr(other_e, "is_friendly", False):
                    # Check if enemy is in the cross (horizontal or vertical line)
                    in_horizontal = abs(other_e.pos.y - self.player.pos.y) < (other_e.radius + cross_width)
                    in_vertical = abs(other_e.pos.x - self.player.pos.x) < (other_e.radius + cross_width)
                    
                    if in_horizontal or in_vertical:
                        # Damage is 15x base attack (calculated in player.py)
                        died = other_e.take_damage(damage, self.enemy_group, player=self.player, game=self)
                        if died:
                            self.enemy_group.remove(other_e)

            # Visual effect handled in draw
            if not hasattr(self, "wizard_cross_effects"): self.wizard_cross_effects = []
            self.wizard_cross_effects.append({"pos": self.player.pos.copy(), "timer": 0.5, "max_timer": 0.5})
            
            # Add some screen effects for impact
            if hasattr(self, "screen_shake"):
                self.screen_shake(intensity=6.0, duration=0.3)
            if hasattr(self, "screen_flash"):
                self.screen_flash(color=(160, 32, 240), duration=0.1)

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
            attack_result = self.player.shoot(mouse_pos, self.survival_time, enemies=self.enemy_group)

            if isinstance(attack_result, Bullet):
                self.player_bullets.append(attack_result)
            elif isinstance(attack_result, list):
                for b in attack_result:
                    self.player_bullets.append(b)
            elif attack_result == "primary_melee":
                self.player.melee_just_used = True
            elif attack_result == "piercing_beam":
                # Archmage beam logic
                self.player.perform_beam_attack(mouse_pos, self.enemy_group, game=self)
            elif attack_result == "chain_lightning":
                # Electrician chain lightning (only on click)
                self.player.perform_chain_attack(mouse_pos, self.enemy_group, game=self)#ntrinsic Ability (Space key) ---
        intrinsic_cooldown = self.player.get_ability_cooldown(self.player.intrinsic_ability)
        if keys[pygame.K_SPACE] and (self.survival_time - self.player.last_melee) >= intrinsic_cooldown:
            result = self.player.use_ability(self.player.intrinsic_ability, self.survival_time, dir_vec if 'dir_vec' in locals() else pygame.math.Vector2(0,0), mouse_pos)
            self.player.last_melee = self.survival_time
            self.melee_just_used = True # Trigger visual feedback in draw()
            if self.player.class_name == "Archmage":
                self.player.last_summon_time = self.survival_time

        # --- Handle Secondary Ability (Shift key) ---
        secondary_cooldown = self.player.get_ability_cooldown(self.player.secondary_ability)
        # Charge regeneration
        if self.player.ability_charges < self.player.max_ability_charges:
            if (self.survival_time - self.player.last_dash) >= secondary_cooldown:
                self.player.ability_charges += 1
                if self.player.ability_charges < self.player.max_ability_charges:
                    self.player.last_dash = self.survival_time
                else:
                    self.player.last_dash = -999

        if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and self.player.ability_charges > 0:
            self.player.use_ability(self.player.secondary_ability, self.survival_time, dir_vec if 'dir_vec' in locals() else pygame.math.Vector2(0,0), mouse_pos)
            self.player.ability_charges -= 1
            if self.player.ability_charges < self.player.max_ability_charges:
                if self.player.last_dash == -999:
                    self.player.last_dash = self.survival_time

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

            # Trigger hero slash if requested
            if self.player.melee_just_used:
                self.perform_hero_slash()
                self.melee_just_used = True # Sync with game's visual flag
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
        if self.player.secondary_ability:
            secondary_name = self.player.secondary_ability
            secondary_base = ability_cooldowns.get(secondary_name, 2.0)
            secondary_cd = secondary_base * (1 - self.player.cooldown_reduction)
            
            # Calculate remaining cooldown for secondary ability
            if self.player.ability_charges >= self.player.max_ability_charges:
                cd_left = 0.0
            else:
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
        
        # Ancient One Glitch Effect
        if self.current_boss and isinstance(self.current_boss, AncientOneBoss):
            if self.current_boss.glitch_timer > 0 or (self.current_boss.phase == 2 and random.random() < 0.05):
                shake_offset.x += random.uniform(-15, 15)
                shake_offset.y += random.uniform(-15, 15)

        # Create a temporary surface for the game world to apply shake
        world_surf = pygame.Surface((WIDTH, HEIGHT))
        
        # --- Background Rendering ---
        bg_timer = pygame.time.get_ticks() * 0.001
        
        if self.current_boss:
            # BOSS BACKGROUND: Intense, darker, with boss-specific tint
            bg_color_base = (5, 5, 10)
            if isinstance(self.current_boss, RedCoreBoss): tint = (40, 0, 0)
            elif isinstance(self.current_boss, OrangeJuggernautBoss): tint = (40, 20, 0)
            elif isinstance(self.current_boss, YellowEyeBoss): tint = (30, 30, 0)
            elif isinstance(self.current_boss, AncientOneBoss): tint = (20, 0, 40)
            else: tint = (20, 20, 20)
            
            # Pulse the tint
            pulse = (math.sin(bg_timer * 1.5) + 1) / 2
            bg_color = (
                int(bg_color_base[0] + tint[0] * pulse),
                int(bg_color_base[1] + tint[1] * pulse),
                int(bg_color_base[2] + tint[2] * pulse)
            )
            world_surf.fill(bg_color)
            
            # Boss particles: Faster, more chaotic, matching tint
            if not hasattr(self, "boss_bg_particles"):
                self.boss_bg_particles = []
                for _ in range(80):
                    self.boss_bg_particles.append({
                        "pos": [random.uniform(0, WIDTH), random.uniform(0, HEIGHT)],
                        "vel": [random.uniform(-20, 20), random.uniform(30, 60)],
                        "size": random.uniform(1, 4),
                        "alpha": random.randint(40, 100)
                    })
            
            for p in self.boss_bg_particles:
                p["pos"][0] += p["vel"][0] * dt
                p["pos"][1] += p["vel"][1] * dt
                if p["pos"][1] > HEIGHT: p["pos"][1] = 0; p["pos"][0] = random.uniform(0, WIDTH)
                if p["pos"][0] < 0: p["pos"][0] = WIDTH
                if p["pos"][0] > WIDTH: p["pos"][0] = 0
                
                p_pulse = (math.sin(bg_timer * 3 + p["pos"][0]) + 1) / 2
                p_alpha = int(p["alpha"] * (0.6 + 0.4 * p_pulse))
                
                s = pygame.Surface((int(p["size"]*2), int(p["size"]*2)), pygame.SRCALPHA)
                pygame.draw.circle(s, (*tint, p_alpha), (int(p["size"]), int(p["size"])), int(p["size"]))
                world_surf.blit(s, (int(p["pos"][0]), int(p["pos"][1])))
        else:
            # NORMAL ARENA BACKGROUND: Calm, mysterious
            bg_color_base = (10, 10, 24)
            pulse = (math.sin(bg_timer * 0.5) + 1) / 2
            bg_color = (
                int(bg_color_base[0] + 5 * pulse),
                int(bg_color_base[1] + 5 * pulse),
                int(bg_color_base[2] + 10 * pulse)
            )
            world_surf.fill(bg_color)
            
            if not hasattr(self, "bg_particles"):
                self.bg_particles = []
                for _ in range(50):
                    self.bg_particles.append({
                        "pos": [random.uniform(0, WIDTH), random.uniform(0, HEIGHT)],
                        "speed": random.uniform(5, 15),
                        "size": random.uniform(1, 3),
                        "alpha": random.randint(20, 60)
                    })
            
            for p in self.bg_particles:
                p["pos"][1] += p["speed"] * dt
                if p["pos"][1] > HEIGHT: p["pos"][1] = 0; p["pos"][0] = random.uniform(0, WIDTH)
                
                p_pulse = (math.sin(bg_timer * 2 + p["pos"][0]) + 1) / 2
                p_alpha = int(p["alpha"] * (0.5 + 0.5 * p_pulse))
                
                s = pygame.Surface((int(p["size"]*2), int(p["size"]*2)), pygame.SRCALPHA)
                pygame.draw.circle(s, (100, 100, 255, p_alpha), (int(p["size"]), int(p["size"])), int(p["size"]))
                world_surf.blit(s, (int(p["pos"][0]), int(p["pos"][1])))

        for b in self.player_bullets:
            if hasattr(b, 'draw'):
                b.draw(world_surf)
            else:
                pygame.draw.circle(world_surf, YELLOW, (int(b.pos.x), int(b.pos.y)), b.radius)
        for b in self.enemy_bullets:
            if hasattr(b, 'draw'):
                b.draw(world_surf)
            else:
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

        # Draw global particles
        if hasattr(self, "global_particles"):
            for p in self.global_particles:
                alpha = int(p["alpha"] * (p["lifetime"] / p["max_lifetime"]))
                s = pygame.Surface((int(p["size"]*2), int(p["size"]*2)), pygame.SRCALPHA)
                pygame.draw.circle(s, (*p["color"][:3], alpha), (int(p["size"]), int(p["size"])), int(p["size"]))
                world_surf.blit(s, (int(p["pos"][0] - p["size"]), int(p["pos"][1] - p["size"])))

        # Draw Vignette / Screen Effects
        if self.vignette_intensity > 0:
            vignette_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            color = (0, 0, 0)
            if self.current_boss:
                if isinstance(self.current_boss, RedCoreBoss): color = (50, 0, 0)
                elif isinstance(self.current_boss, OrangeJuggernautBoss): color = (50, 25, 0)
                elif isinstance(self.current_boss, YellowEyeBoss): color = (40, 40, 0)
                elif isinstance(self.current_boss, AncientOneBoss): color = (20, 0, 40)
            
            alpha = int(255 * self.vignette_intensity)
            # Draw a radial gradient for vignette
            for i in range(4):
                r_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
                pygame.draw.rect(vignette_surf, (*color, alpha // (4 - i)), r_rect.inflate(-i * 100, -i * 100), 100)
            world_surf.blit(vignette_surf, (0, 0))

        # Draw player and abilities if player exists
        if self.player:
            # Draw Wizard's Cross Effects
            if hasattr(self, "wizard_cross_effects"):
                for effect in self.wizard_cross_effects:
                    progress = 1.0 - (effect["timer"] / effect["max_timer"])
                    alpha = int(255 * (effect["timer"] / effect["max_timer"]))
                    
                    # Core beam (white/bright purple)
                    core_width = int(40 * (1.0 - progress))
                    glow_width = int(80 * (1.0 - progress))
                    
                    s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    
                    # Draw glow lines
                    glow_color = (160, 32, 240, alpha // 2)
                    pygame.draw.line(s, glow_color, (0, effect["pos"].y), (WIDTH, effect["pos"].y), glow_width)
                    pygame.draw.line(s, glow_color, (effect["pos"].x, 0), (effect["pos"].x, HEIGHT), glow_width)
                    
                    # Draw core lines
                    core_color = (230, 180, 255, alpha)
                    pygame.draw.line(s, core_color, (0, effect["pos"].y), (WIDTH, effect["pos"].y), core_width)
                    pygame.draw.line(s, core_color, (effect["pos"].x, 0), (effect["pos"].x, HEIGHT), core_width)
                    
                    # Add some "energy particles" along the cross
                    for i in range(10):
                        # Horizontal particles
                        hx = random.uniform(0, WIDTH)
                        hy = effect["pos"].y + random.uniform(-glow_width//2, glow_width//2)
                        pygame.draw.circle(s, (255, 255, 255, alpha), (int(hx), int(hy)), random.randint(1, 3))
                        
                        # Vertical particles
                        vx = effect["pos"].x + random.uniform(-glow_width//2, glow_width//2)
                        vy = random.uniform(0, HEIGHT)
                        pygame.draw.circle(s, (255, 255, 255, alpha), (int(vx), int(vy)), random.randint(1, 3))
                        
                    world_surf.blit(s, (0, 0))

            # Draw Spaceman (Electrician) lightning effects
            if self.player.class_name == "Electrician":
                for i in range(len(self.player.chain_visuals) - 1, -1, -1):
                    start_pos, end_pos, timer, color_name = self.player.chain_visuals[i]
                    color = (255, 255, 0) if color_name == "yellow" else (255, 50, 50)
                    thickness = 3 if color_name == "red" else 2
                    draw_jagged_lightning(world_surf, start_pos, end_pos, color, thickness)
                    
                    # IMPACT ANIMATION: Show shock effect at the end of the lightning
                    # Only draw if the timer is fresh (just hit)
                    if timer > 0.1:
                        shock_color = (255, 255, 200) if color_name == "yellow" else (255, 200, 200)
                        # Draw a bright burst at the target position
                        draw_impact_burst(world_surf, end_pos, shock_color, radius=20, intensity=0.8)
                        # Add some electric particles
                        if not hasattr(self, "global_particles"): self.global_particles = []
                        for _ in range(3):
                            self.global_particles.append({
                                "pos": list(end_pos),
                                "vel": [random.uniform(-100, 100), random.uniform(-100, 100)],
                                "size": random.uniform(2, 4),
                                "color": shock_color,
                                "alpha": 255,
                                "lifetime": 0.3,
                                "max_lifetime": 0.3
                            })
                    
                    # Update timer and remove if expired
                    self.player.chain_visuals[i] = (start_pos, end_pos, timer - dt, color_name)
                    if timer - dt <= 0:
                        self.player.chain_visuals.pop(i)

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
                # Draw outer glow
                glow_color = (*color[:3], 100)
                glow_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                pygame.draw.line(glow_surf, glow_color, self.archmage_beam_start, self.archmage_beam_end, width + 10)
                self.screen.blit(glow_surf, (0, 0))
                # Draw main beam
                pygame.draw.line(self.screen, color, self.archmage_beam_start, self.archmage_beam_end, width)
                # Draw core beam
                pygame.draw.line(self.screen, (255, 255, 255), self.archmage_beam_start, self.archmage_beam_end, max(1, width // 3))

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
                inner_radius = primary_melee_range * 0.4 # Focused high DPS zone

                mouse_pos = pygame.mouse.get_pos()
                dx = mouse_pos[0] - self.player.pos.x
                dy = mouse_pos[1] - self.player.pos.y
                center_angle = math.atan2(dy, dx)

                # Arc settings
                arc_deg = 240 if self.player.prestige["fire_rate"] >= 1 else 160
                arc_width_radians = math.radians(arc_deg)
                
                # ANIMATION: Slashing from edge to center
                # progress goes from 0 to 1
                progress = 1.0 - (self.primary_melee_timer / 0.2)
                
                # 1. OUTER SLASHES (Normal Damage)
                # Two slashes coming from the edges of the arc towards the center
                s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                
                # Left slash
                left_angle = center_angle - (arc_width_radians / 2) * (1.0 - progress)
                left_pos = self.player.pos + pygame.math.Vector2(math.cos(left_angle), math.sin(left_angle)) * primary_melee_range
                
                # Right slash
                right_angle = center_angle + (arc_width_radians / 2) * (1.0 - progress)
                right_pos = self.player.pos + pygame.math.Vector2(math.cos(right_angle), math.sin(right_angle)) * primary_melee_range
                
                # Draw the slash lines
                alpha = int(255 * (self.primary_melee_timer / 0.2))
                pygame.draw.line(s, (200, 200, 255, alpha), self.player.pos + (left_pos - self.player.pos) * 0.8, left_pos, 3)
                pygame.draw.line(s, (200, 200, 255, alpha), self.player.pos + (right_pos - self.player.pos) * 0.8, right_pos, 3)
                
                # 2. INNER FOCUSED ZONE (High DPS)
                # When slashes cross in the center (near the end of animation)
                if progress > 0.7:
                    cross_alpha = int(255 * ((progress - 0.7) / 0.3) * (self.primary_melee_timer / 0.2))
                    # Draw a bright X or cross in the inner radius
                    p1 = self.player.pos + pygame.math.Vector2(math.cos(center_angle - 0.4), math.sin(center_angle - 0.4)) * inner_radius
                    p2 = self.player.pos + pygame.math.Vector2(math.cos(center_angle + 0.4), math.sin(center_angle + 0.4)) * inner_radius
                    pygame.draw.line(s, (255, 255, 255, cross_alpha), self.player.pos, p1, 5)
                    pygame.draw.line(s, (255, 255, 255, cross_alpha), self.player.pos, p2, 5)
                    # Add a glow at the center
                    pygame.draw.circle(s, (255, 255, 255, cross_alpha // 2), (int(self.player.pos.x), int(self.player.pos.y)), int(inner_radius), 0)

                world_surf.blit(s, (0, 0))
                
                # Original arc indicator (more subtle now)
                # Create a temporary surface for transparency
                slash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

                # 1. Draw Normal Slash Arc
                points = [self.player.pos]
                num_segments = 20
                start_angle = center_angle - arc_width_radians / 2
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

                # Add some "swing particles"
                for _ in range(3):
                    p_angle = center_angle + random.uniform(-arc_width_radians/2, arc_width_radians/2)
                    p_dist = random.uniform(20, primary_melee_range)
                    px = self.player.pos.x + p_dist * math.cos(p_angle)
                    py = self.player.pos.y + p_dist * math.sin(p_angle)
                    pygame.draw.circle(slash_surf, (255, 255, 200, 150), (int(px), int(py)), random.randint(1, 3))

                self.screen.blit(slash_surf, (0, 0))

            # Draw spacebar melee indicator if recently used (for a single frame)
            # The visual effect is now tied to the melee_just_used flag which is set in Game.update
            if self.melee_just_used:
                pygame.draw.circle(self.screen, WHITE, (int(self.player.pos.x), int(self.player.pos.y)),
                                   self.player.melee_radius, 1)  # 1px wide circle as requested
                self.melee_just_used = False

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

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.current_time += dt
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if self.state == self.MAIN_MENU:
                    self.handle_main_menu_events(event)
                elif self.state == self.TUTORIAL:
                    self.tutorial_module.handle_events(event)
                elif self.state == self.GUIDE:
                    self.guide_module.handle_events(event)
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
            elif self.state == self.TUTORIAL:
                self.tutorial_module.update(dt)
                self.tutorial_module.draw()
            elif self.state == self.GUIDE:
                self.guide_module.update(dt)
                self.guide_module.draw()
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