import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import cv2
import mediapipe as mp
import pygame
import sys
import random
import math

from spaceship import Spaceship
from boss import FinalBoss
from asteroid import Asteroid

# Color Definitions
COLOR_BG = (4, 6, 14)
COLOR_CYAN = (0, 240, 255)
COLOR_CORE_WHITE = (240, 250, 255)
COLOR_NEON_PINK = (255, 0, 110)
COLOR_NEON_GREEN = (0, 255, 140)
COLOR_PANEL_BG = (10, 14, 28, 190)
COLOR_BORDER = (0, 180, 220, 120)

particles = []
floating_texts = []

def draw_glass_panel(surface, rect, border_color=COLOR_BORDER):
    panel = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(panel, COLOR_PANEL_BG, (0, 0, rect[2], rect[3]), border_radius=12)
    pygame.draw.rect(panel, border_color, (0, 0, rect[2], rect[3]), width=2, border_radius=12)
    surface.blit(panel, (rect[0], rect[1]))

def add_floating_text(text, x, y, color=COLOR_CYAN):
    floating_texts.append({
        "text": text, "x": x, "y": y,
        "color": color, "life": 1.0, "vy": -2.0
    })

def create_explosion_3d(x, y, color=COLOR_CYAN, count=25):
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2, 7)
        particles.append({
            "x": x, "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "radius": random.randint(2, 5),
            "color": color,
            "life": 1.0
        })

def run_game():
    pygame.init()
    WIDTH, HEIGHT = 700, 900
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ASTEROIDS 3D // WORLD EDITION")
    clock = pygame.time.Clock()

    try:
        font_title = pygame.font.SysFont("Trebuchet MS", 42, bold=True)
        font_hud = pygame.font.SysFont("Consolas", 24, bold=True)
        font_small = pygame.font.SysFont("Trebuchet MS", 14, bold=True)
    except:
        font_title = pygame.font.Font(None, 48)
        font_hud = pygame.font.Font(None, 28)
        font_small = pygame.font.Font(None, 18)

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)

    stars = []
    for _ in range(120):
        z = random.uniform(0.15, 1.0)
        stars.append({
            "x": random.randint(0, WIDTH), "y": random.randint(0, HEIGHT),
            "z": z, "speed": z * 3.5, "color": (int(120 * z), int(200 * z), int(255 * z))
        })

    ship = Spaceship(WIDTH // 2, HEIGHT - 120)
    boss = FinalBoss(WIDTH)
    asteroids = []

    score = 0
    game_over = False
    spawn_interval = 950

    SPAWN_ENEMY = pygame.USEREVENT + 1
    pygame.time.set_timer(SPAWN_ENEMY, spawn_interval)

    running = True
    while running:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_r and game_over:
                    ship = Spaceship(WIDTH // 2, HEIGHT - 120)
                    boss = FinalBoss(WIDTH)
                    asteroids.clear()
                    particles.clear()
                    floating_texts.clear()
                    score = 0
                    game_over = False
                    spawn_interval = 950
                    pygame.time.set_timer(SPAWN_ENEMY, spawn_interval)
            elif event.type == SPAWN_ENEMY and not game_over and not boss.active:
                rad = random.randint(26, 42)
                asteroids.append(Asteroid(
                    random.randint(50, WIDTH - 50), -rad * 2, rad, 3.6 * random.uniform(0.85, 1.25)
                ))

        # Mouse & Hand Inputs
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()[0]
        pinch_detected = False
        hand_tracking_active = False

        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                frame = cv2.flip(frame, 1)
                results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                if results.multi_hand_landmarks and not game_over:
                    hand_tracking_active = True
                    lm = results.multi_hand_landmarks[0].landmark
                    ship.target_x = max(35, min(WIDTH - 35, lm[8].x * WIDTH))
                    ship.target_y = max(80, min(HEIGHT - 45, lm[8].y * HEIGHT))
                    pinch_detected = math.hypot(lm[4].x - lm[5].x, lm[4].y - lm[5].y) < 0.055
            else:
                ship.target_x, ship.target_y = max(35, min(WIDTH - 35, mouse_x)), max(80, min(HEIGHT - 45, mouse_y))
                pinch_detected = mouse_click
        else:
            ship.target_x, ship.target_y = max(35, min(WIDTH - 35, mouse_x)), max(80, min(HEIGHT - 45, mouse_y))
            pinch_detected = mouse_click

        if not game_over:
            ship.update(now)
            if pinch_detected:
                ship.shoot(now)

            # Boss Logic Trigger
            if score >= 1500 and not boss.active:
                boss.spawn()
                asteroids.clear()

            if boss.active:
                boss.update(now)
                for bullet in ship.bullets[:]:
                    if boss.get_rect().collidepoint(bullet[0], bullet[1]):
                        boss.hp -= 2
                        create_explosion_3d(bullet[0], bullet[1], color=COLOR_NEON_PINK, count=8)
                        ship.bullets.remove(bullet)
                        if boss.hp <= 0:
                            boss.active = False
                            create_explosion_3d(boss.x, boss.y, color=COLOR_CYAN, count=60)
                            add_floating_text("+2000 BOSS DEFEATED", boss.x, boss.y)
                            score += 2000

                for b in boss.bullets[:]:
                    if now > ship.invuln_until and ship.get_rect().collidepoint(b["x"], b["y"]):
                        ship.lives -= 1
                        ship.invuln_until = now + 1600
                        boss.bullets.remove(b)
                        create_explosion_3d(ship.x, ship.y, color=COLOR_NEON_PINK, count=30)
                        if ship.lives <= 0:
                            game_over = True

            # Asteroid Mechanics
            for ast in asteroids[:]:
                ast.update()
                if ast.y > HEIGHT + 60:
                    asteroids.remove(ast)
                    continue

                for bullet in ship.bullets[:]:
                    if math.hypot(bullet[0] - ast.x, bullet[1] - ast.y) < ast.radius + 6:
                        create_explosion_3d(ast.x, ast.y, color=COLOR_CYAN)
                        add_floating_text("+100", ast.x, ast.y)
                        if ast in asteroids: asteroids.remove(ast)
                        if bullet in ship.bullets: ship.bullets.remove(bullet)
                        score += 100
                        break

                if now > ship.invuln_until and ship.get_rect().colliderect(ast.get_rect()):
                    create_explosion_3d(ast.x, ast.y, color=COLOR_NEON_PINK, count=40)
                    create_explosion_3d(ship.x, ship.y, color=COLOR_CYAN, count=40)
                    add_floating_text("HULL CRITICAL!", ship.x, ship.y - 30, color=COLOR_NEON_PINK)
                    asteroids.remove(ast)
                    ship.lives -= 1
                    ship.invuln_until = now + 1600
                    if ship.lives <= 0:
                        game_over = True

            target_interval = max(240, 950 - (score // 8))
            if target_interval != spawn_interval:
                spawn_interval = target_interval
                pygame.time.set_timer(SPAWN_ENEMY, spawn_interval)

        # Star Field
        for star in stars:
            star["y"] += star["speed"]
            if star["y"] > HEIGHT:
                star["y"] = 0
                star["x"] = random.randint(0, WIDTH)

        # Particles & Text Updates
        for p in particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 0.035
            if p["life"] <= 0: particles.remove(p)

        for ft in floating_texts[:]:
            ft["y"] += ft["vy"]
            ft["life"] -= 0.025
            if ft["life"] <= 0: floating_texts.remove(ft)

        # Render Scene
        screen.fill(COLOR_BG)

        for star in stars:
            pygame.draw.circle(screen, star["color"], (int(star["x"]), int(star["y"])), int(star["z"] * 3) + 1)

        for p in particles:
            alpha = int(255 * p["life"])
            surf = pygame.Surface((p["radius"] * 2, p["radius"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p["color"], alpha), (p["radius"], p["radius"]), p["radius"])
            screen.blit(surf, (p["x"] - p["radius"], p["y"] - p["radius"]))

        for ast in asteroids:
            ast.draw(screen)

        boss.draw(screen)
        ship.draw(screen, now)

        for ft in floating_texts:
            txt_surf = font_small.render(ft["text"], True, ft["color"])
            txt_surf.set_alpha(int(255 * ft["life"]))
            screen.blit(txt_surf, (ft["x"] - txt_surf.get_width() // 2, ft["y"]))

        # HUD Panel
        draw_glass_panel(screen, (15, 12, WIDTH - 30, 60))
        score_lbl = font_small.render("SCORE", True, (140, 160, 190))
        score_val = font_hud.render(f"{score:06d}", True, COLOR_CYAN)
        screen.blit(score_lbl, (30, 18))
        screen.blit(score_val, (30, 34))

        sensor_x = WIDTH // 2 - 70
        if hand_tracking_active:
            status_color = COLOR_NEON_GREEN if not pinch_detected else COLOR_NEON_PINK
            status_txt = "FIRING" if pinch_detected else "TRACKING"
        else:
            status_color = (180, 140, 40)
            status_txt = "MOUSE MODE"

        pygame.draw.circle(screen, status_color, (sensor_x, 42), 6)
        sensor_lbl = font_small.render(f"INPUT: {status_txt}", True, status_color)
        screen.blit(sensor_lbl, (sensor_x + 14, 34))

        hull_lbl = font_small.render("HULL INTEGRITY", True, (140, 160, 190))
        screen.blit(hull_lbl, (WIDTH - 160, 18))
        for i in range(ship.max_lives):
            icon_x = WIDTH - 155 + (i * 32)
            icon_y = 48
            color = COLOR_CYAN if i < ship.lives else (40, 50, 70)
            pygame.draw.polygon(screen, color, [(icon_x, icon_y - 8), (icon_x - 8, icon_y + 6), (icon_x + 8, icon_y + 6)])

        # Game Over Screen Modal
        if game_over:
            modal_w, modal_h = 420, 260
            modal_x, modal_y = (WIDTH - modal_w) // 2, (HEIGHT - modal_h) // 2
            draw_glass_panel(screen, (modal_x, modal_y, modal_w, modal_h), border_color=COLOR_NEON_PINK)

            title_txt = font_title.render("SYSTEM CRITICAL", True, COLOR_NEON_PINK)
            screen.blit(title_txt, (WIDTH // 2 - title_txt.get_width() // 2, modal_y + 25))

            sub_txt = font_hud.render(f"FINAL SCORE: {score}", True, COLOR_CYAN)
            screen.blit(sub_txt, (WIDTH // 2 - sub_txt.get_width() // 2, modal_y + 90))

            btn_surf = font_small.render("PRESS 'R' TO REBOOT MISSION", True, COLOR_CORE_WHITE)
            screen.blit(btn_surf, (WIDTH // 2 - btn_surf.get_width() // 2, modal_y + 155))

            quit_surf = font_small.render("PRESS 'Q' TO QUIT TO DESKTOP", True, (130, 140, 160))
            screen.blit(quit_surf, (WIDTH // 2 - quit_surf.get_width() // 2, modal_y + 190))

        pygame.display.flip()
        clock.tick(60)

    if cap is not None and cap.isOpened():
        cap.release()
    cv2.destroyAllWindows()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    run_game()