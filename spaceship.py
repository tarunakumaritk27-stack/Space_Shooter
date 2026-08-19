import pygame
import random
import math

COLOR_CYAN = (0, 240, 255)
COLOR_BLUE_GLOW = (0, 110, 255)
COLOR_CORE_WHITE = (240, 250, 255)
COLOR_ACCENT_ORANGE = (255, 110, 20)

class Spaceship:
    def __init__(self, x, y, max_lives=3):
        self.x = float(x)
        self.y = float(y)
        self.target_x = float(x)
        self.target_y = float(y)
        self.vx = 0.0
        self.lives = max_lives
        self.max_lives = max_lives
        self.invuln_until = 0
        self.last_shot_time = 0
        self.bullets = []
        self.thrust_particles = []

    def update(self, now, smoothing=0.22):
        prev_x = self.x
        self.x += (self.target_x - self.x) * smoothing
        self.y += (self.target_y - self.y) * smoothing
        self.vx = self.x - prev_x

        # Bullets Movement
        for bullet in self.bullets[:]:
            bullet[1] -= 17
            if bullet[1] < -20:
                self.bullets.remove(bullet)

        # Thrust Particles Update
        for tp in self.thrust_particles[:]:
            tp["y"] += tp["vy"]
            tp["life"] -= 0.08
            if tp["life"] <= 0:
                self.thrust_particles.remove(tp)

    def shoot(self, now, cooldown=160):
        if now - self.last_shot_time > cooldown:
            self.bullets.append([self.x, self.y - 28])
            self.last_shot_time = now

    def draw(self, surface, now):
        # Flashing effect during invulnerability
        if now < self.invuln_until and (now // 100) % 2 == 0:
            return

        px, py = int(self.x), int(self.y)
        roll = max(-0.6, min(0.6, self.vx * 0.05))
        w_off = roll * 14

        # Add thrust effect
        self.thrust_particles.append({
            "x": px + random.uniform(-4, 4), "y": py + 22,
            "vy": random.uniform(4, 9), "radius": random.randint(3, 7), "life": 1.0
        })

        # Draw Thrust Particles
        for tp in self.thrust_particles:
            alpha = int(220 * tp["life"])
            surf = pygame.Surface((tp["radius"] * 2, tp["radius"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*COLOR_CYAN, alpha), (tp["radius"], tp["radius"]), tp["radius"])
            surface.blit(surf, (tp["x"] - tp["radius"], tp["y"] - tp["radius"]))

        # Geometry
        wing_l = (px - 32 + w_off * 1.4, py + 20)
        wing_r = (px + 32 + w_off * 1.4, py + 20)
        nose = (px + w_off * 0.5, py - 30)
        tail_l = (px - 10 + w_off, py + 16)
        tail_r = (px + 10 + w_off, py + 16)
        body_mid = (px, py - 8)

        pygame.draw.polygon(surface, (160, 170, 190), [wing_l, (px - 10, py + 2), tail_l])
        pygame.draw.polygon(surface, COLOR_CORE_WHITE, [wing_r, (px + 10, py + 2), tail_r])
        pygame.draw.polygon(surface, COLOR_ACCENT_ORANGE, [wing_l, (px - 22, py + 20), (px - 12, py + 8)])
        pygame.draw.polygon(surface, COLOR_ACCENT_ORANGE, [wing_r, (px + 22, py + 20), (px + 12, py + 8)])
        pygame.draw.polygon(surface, (200, 210, 230), [nose, tail_l, body_mid])
        pygame.draw.polygon(surface, COLOR_CORE_WHITE, [nose, tail_r, body_mid])

        cockpit = [(px, py - 14), (px - 5, py - 2), (px, py + 2), (px + 5, py - 2)]
        pygame.draw.polygon(surface, COLOR_CYAN, cockpit)
        pygame.draw.polygon(surface, COLOR_CORE_WHITE, cockpit, width=1)

        # Bullets
        for bx, by in self.bullets:
            glow = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*COLOR_CYAN, 70), (16, 16), 14)
            pygame.draw.circle(glow, (*COLOR_BLUE_GLOW, 160), (16, 16), 8)
            pygame.draw.circle(glow, COLOR_CORE_WHITE, (16, 16), 4)
            surface.blit(glow, (bx - 16, by - 16))

    def get_rect(self):
        return pygame.Rect(self.x - 22, self.y - 22, 44, 44)