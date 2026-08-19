import pygame
import math

class FinalBoss:
    def __init__(self, screen_width):
        self.screen_width = screen_width
        self.x = float(screen_width // 2)
        self.y = -120.0
        self.target_y = 150.0
        self.max_hp = 100
        self.hp = 100
        self.active = False
        self.move_dir = 1
        self.bullets = []
        self.last_shot_time = 0

    def spawn(self):
        self.active = True
        self.hp = self.max_hp
        self.y = -120.0

    def update(self, now):
        if not self.active:
            return

        if self.y < self.target_y:
            self.y += 2.0
        else:
            self.x += 2.5 * self.move_dir
            if self.x < 100 or self.x > self.screen_width - 100:
                self.move_dir *= -1

        if now - self.last_shot_time > 800:
            self.last_shot_time = now
            for angle in [-0.3, 0, 0.3]:
                self.bullets.append({
                    "x": self.x, "y": self.y + 40,
                    "vx": math.sin(angle) * 6,
                    "vy": math.cos(angle) * 6
                })

        for b in self.bullets[:]:
            b["x"] += b["vx"]
            b["y"] += b["vy"]
            if b["y"] > 1000 or b["x"] < -20 or b["x"] > self.screen_width + 20:
                self.bullets.remove(b)

    def draw(self, surface):
        if not self.active:
            return

        bx, by = int(self.x), int(self.y)

        pygame.draw.polygon(surface, (255, 0, 110), [(bx, by + 50), (bx - 70, by - 30), (bx + 70, by - 30)])
        pygame.draw.polygon(surface, (40, 10, 30), [(bx, by + 30), (bx - 50, by - 20), (bx + 50, by - 20)])
        pygame.draw.circle(surface, (255, 0, 110), (bx, by), 20)
        pygame.draw.circle(surface, (255, 255, 255), (bx, by), 10)

        # Health Bar
        bar_w, bar_h = 200, 12
        bar_x, bar_y = bx - bar_w // 2, by - 60
        pct = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surface, (40, 10, 20), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
        pygame.draw.rect(surface, (255, 0, 110), (bar_x, bar_y, int(bar_w * pct), bar_h), border_radius=6)
        pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), width=2, border_radius=6)

        for b in self.bullets:
            pygame.draw.circle(surface, (255, 0, 110), (int(b["x"]), int(b["y"])), 8)
            pygame.draw.circle(surface, (255, 255, 255), (int(b["x"]), int(b["y"])), 4)

    def get_rect(self):
        return pygame.Rect(self.x - 65, self.y - 35, 130, 70)