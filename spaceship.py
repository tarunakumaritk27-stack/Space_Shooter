import pygame
import random

COLOR_CORE_WHITE = (240, 250, 255)
COLOR_ACCENT_ORANGE = (255, 110, 20)
COLOR_CYAN = (0, 240, 255)
COLOR_BLUE_GLOW = (0, 110, 255)

def draw_3d_ship(surface, x, y, tilt, thrust_particles):
    px, py = int(x), int(y)
    roll = max(-0.6, min(0.6, tilt * 0.05))
    w_off = roll * 14

    thrust_particles.append({
        "x": px + random.uniform(-4, 4), "y": py + 22,
        "vy": random.uniform(4, 9), "radius": random.randint(3, 7), "life": 1.0
    })

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

def draw_glow_bullet(surface, x, y):
    glow = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*COLOR_CYAN, 70), (16, 16), 14)
    pygame.draw.circle(glow, (*COLOR_BLUE_GLOW, 160), (16, 16), 8)
    pygame.draw.circle(glow, COLOR_CORE_WHITE, (16, 16), 4)
    surface.blit(glow, (x - 16, y - 16))
