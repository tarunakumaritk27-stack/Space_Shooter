import pygame
import math
import random

COLOR_CYAN = (0, 240, 255)
COLOR_NEON_PINK = (255, 0, 110)
COLOR_NEON_GREEN = (0, 255, 140)
COLOR_CORE_WHITE = (240, 250, 255)
COLOR_DARK_STEEL = (30, 35, 50)
COLOR_PANEL_BG = (10, 14, 28, 200)

class Boss:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.target_y = 180.0
        self.max_hp = 500
        self.hp = 500
        self.radius = 65
        self.angle = 0.0
        self.vx = 2.5
        self.active = True
        self.phase = 1
        self.last_shot_time = 0
        self.shoot_cooldown = 1200  # ms between boss bullet waves

    def update(self, now, width):
        # Entry animation
        if self.y < self.target_y:
            self.y += 1.5

        # Horizontal sweeping movement
        self.x += self.vx
        if self.x - self.radius < 20 or self.x + self.radius > width - 20:
            self.vx *= -1

        # Rotation effect
        self.angle += 0.02

        # Phase logic based on health
        if self.hp < self.max_hp * 0.4:
            self.phase = 3
            self.shoot_cooldown = 600
        elif self.hp < self.max_hp * 0.7:
            self.phase = 2
            self.shoot_cooldown = 900

    def draw(self, surface):
        bx, by = int(self.x), int(self.y)

        # Pulsing Core Glow
        pulse = math.sin(self.angle * 3) * 6
        glow_color = COLOR_NEON_PINK if self.phase == 3 else (COLOR_CYAN if self.phase == 1 else COLOR_NEON_GREEN)
        
        glow_surf = pygame.Surface((180, 180), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*glow_color, 40), (90, 90), int(75 + pulse))
        pygame.draw.circle(glow_surf, (*glow_color, 90), (90, 90), int(50 + pulse * 0.5))
        surface.blit(glow_surf, (bx - 90, by - 90))

        # Main Hull Geometry (3D Hexagon structure)
        pts_outer = []
        for i in range(6):
            a = self.angle + (i * math.pi / 3)
            r = self.radius + (math.sin(self.angle * 2 + i) * 4)
            pts_outer.append((bx + math.cos(a) * r, by + math.sin(a) * r))

        pygame.draw.polygon(surface, COLOR_DARK_STEEL, pts_outer)
        pygame.draw.polygon(surface, glow_color, pts_outer, width=3)

        # Inner Glowing Core
        pygame.draw.circle(surface, COLOR_CORE_WHITE, (bx, by), int(20 + pulse * 0.3))
        pygame.draw.circle(surface, glow_color, (bx, by), 12)

        # Side Wing Cannons
        pygame.draw.circle(surface, COLOR_DARK_STEEL, (bx - 70, by + 10), 14)
        pygame.draw.circle(surface, glow_color, (bx - 70, by + 10), 14, width=2)
        pygame.draw.circle(surface, COLOR_DARK_STEEL, (bx + 70, by + 10), 14)
        pygame.draw.circle(surface, glow_color, (bx + 70, by + 10), 14, width=2)

    def draw_health_bar(self, surface, width):
        bar_w = 400
        bar_h = 16
        bar_x = (width - bar_w) // 2
        bar_y = 80

        # Health bar glass frame
        frame = pygame.Surface((bar_w + 8, bar_h + 8), pygame.SRCALPHA)
        pygame.draw.rect(frame, COLOR_PANEL_BG, (0, 0, bar_w + 8, bar_h + 8), border_radius=6)
        pygame.draw.rect(frame, COLOR_NEON_PINK, (0, 0, bar_w + 8, bar_h + 8), width=2, border_radius=6)
        surface.blit(frame, (bar_x - 4, bar_y - 4))

        # Fill percentage
        fill_pct = max(0, self.hp / self.max_hp)
        fill_w = int(bar_w * fill_pct)
        if fill_w > 0:
            fill_color = COLOR_NEON_GREEN if fill_pct > 0.5 else (COLOR_CYAN if fill_pct > 0.25 else COLOR_NEON_PINK)
            pygame.draw.rect(surface, fill_color, (bar_x, bar_y, fill_w, bar_h), border_radius=4)
