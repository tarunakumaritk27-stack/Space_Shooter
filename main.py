import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import cv2
import pygame
import sys
import random
import math
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from asteroid import generate_3d_asteroid, render_3d_asteroid
from spaceship import draw_3d_ship, draw_glow_bullet

def run_game():
    pygame.init()
    WIDTH, HEIGHT = 700, 900
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ASTEROIDS 3D // HAND GESTURE EDITION")
    clock = pygame.time.Clock()

    try:
        font_title = pygame.font.SysFont("Trebuchet MS", 42, bold=True)
        font_hud = pygame.font.SysFont("Consolas", 24, bold=True)
        font_small = pygame.font.SysFont("Trebuchet MS", 14, bold=True)
    except:
        font_title = pygame.font.Font(None, 48)
        font_hud = pygame.font.Font(None, 28)
        font_small = pygame.font.Font(None, 18)

    model_path = 'hand_landmarker.task'
    if not os.path.exists(model_path):
        print(f"ERROR: '{model_path}' not found! Place it in the project folder.")
        sys.exit()

    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=1,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )
    detector = vision.HandLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)

    COLOR_BG = (4, 6, 14)
    COLOR_CYAN = (0, 240, 255)
    COLOR_CORE_WHITE = (240, 250, 255)
    COLOR_NEON_PINK = (255, 0, 110)
    COLOR_NEON_GREEN = (0, 255, 140)
    COLOR_PANEL_BG = (10, 14, 28, 190)
    COLOR_BORDER = (0, 180, 220, 120)

    stars = []
    for _ in range(120):
        z = random.uniform(0.15, 1.0)
        stars.append({
            "x": random.randint(0, WIDTH), "y": random.randint(0, HEIGHT),
            "z": z, "speed": z * 3.5,
            "color": (int(120 * z), int(200 * z), int(255 * z))
        })

    particles = []
    thrust_particles = []
    floating_texts = []

    BULLET_RADIUS = 6
    SHOOT_COOLDOWN_MS = 160
    PINCH_THRESHOLD = 0.065
    SMOOTHING_FACTOR = 0.22
    BASE_ENEMY_SPEED = 3.6
    BASE_SPAWN_INTERVAL_MS = 950
    MIN_SPAWN_INTERVAL_MS = 240
    PLAYER_LIVES = 3

    def draw_glass_panel(surface, rect, border_color=COLOR_BORDER):
        panel = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        pygame.draw.rect(panel, COLOR_PANEL_BG, (0, 0, rect[2], rect[3]), border_radius=12)
        pygame.draw.rect(panel, border_color, (0, 0, rect[2], rect[3]), width=2, border_radius=12)
        surface.blit(panel, (rect[0], rect[1]))

    def add_floating_text(text, x, y, color=COLOR_CYAN):
        floating_texts.append({"text": text, "x": x, "y": y, "color": color, "life": 1.0, "vy": -2.0})

    def create_explosion_3d(x, y, color=COLOR_CYAN, count=25):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 7)
            particles.append({
                "x": x, "y": y,
                "vx": math.cos(angle) * speed, "vy": math.sin(angle) * speed,
                "radius": random.randint(2, 5), "color": color, "life": 1.0
            })

    def new_game_state():
        return {
            "target_x": WIDTH // 2, "target_y": HEIGHT - 120,
            "player_x": float(WIDTH // 2), "player_y": float(HEIGHT - 120),
            "player_vx": 0.0, "bullets": [], "enemies": [],
            "score": 0, "lives": PLAYER_LIVES,
            "last_shot_time": 0, "spawn_interval": BASE_SPAWN_INTERVAL_MS,
            "invuln_until": 0,
        }

    state = new_game_state()
    game_over = False

    SPAWN_ENEMY = pygame.USEREVENT + 1
    pygame.time.set_timer(SPAWN_ENEMY, state["spawn_interval"])

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
                    state = new_game_state()
                    game_over = False
                    particles.clear()
                    thrust_particles.clear()
                    floating_texts.clear()
                    pygame.time.set_timer(SPAWN_ENEMY, state["spawn_interval"])
            elif event.type == SPAWN_ENEMY and not game_over:
                rad = random.randint(26, 42)
                nodes, faces = generate_3d_asteroid(rad)
                state["enemies"].append({
                    "x": random.randint(50, WIDTH - 50), "y": -rad * 2,
                    "radius": rad, "speed": BASE_ENEMY_SPEED * random.uniform(0.85, 1.25),
                    "rot_x": random.uniform(0, 3.14), "rot_y": random.uniform(0, 3.14), "rot_z": random.uniform(0, 3.14),
                    "rx_speed": random.uniform(-0.04, 0.04), "ry_speed": random.uniform(-0.04, 0.04), "rz_speed": random.uniform(-0.04, 0.04),
                    "nodes": nodes, "faces": faces
                })

        pinch_detected = False
        hand_tracking_active = False

        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                
                detection_result = detector.detect(mp_image)

                if detection_result.hand_landmarks and not game_over:
                    hand_tracking_active = True
                    landmarks = detection_result.hand_landmarks[0]
                    index_tip, thumb_tip = landmarks[8], landmarks[4]

                    state["target_x"] = max(35, min(WIDTH - 35, index_tip.x * WIDTH))
                    state["target_y"] = max(80, min(HEIGHT - 45, index_tip.y * HEIGHT))

                    pinch_dist = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
                    pinch_detected = pinch_dist < PINCH_THRESHOLD

        if not game_over:
            prev_x = state["player_x"]
            state["player_x"] += (state["target_x"] - state["player_x"]) * SMOOTHING_FACTOR
            state["player_y"] += (state["target_y"] - state["player_y"]) * SMOOTHING_FACTOR
            state["player_vx"] = state["player_x"] - prev_x

            if pinch_detected and now - state["last_shot_time"] > SHOOT_COOLDOWN_MS:
                state["bullets"].append([state["player_x"], state["player_y"] - 28])
                state["last_shot_time"] = now

            for bullet in state["bullets"][:]:
                bullet[1] -= 17
                if bullet[1] < -20:
                    state["bullets"].remove(bullet)

            player_rect = pygame.Rect(state["player_x"] - 22, state["player_y"] - 22, 44, 44)

            for enemy in state["enemies"][:]:
                enemy["y"] += enemy["speed"]
                enemy["rot_x"] += enemy["rx_speed"]
                enemy["rot_y"] += enemy["ry_speed"]
                enemy["rot_z"] += enemy["rz_speed"]

                if enemy["y"] > HEIGHT + 60:
                    state["enemies"].remove(enemy)
                    continue

                hit = False
                for bullet in state["bullets"][:]:
                    if math.hypot(bullet[0] - enemy["x"], bullet[1] - enemy["y"]) < enemy["radius"] + BULLET_RADIUS:
                        create_explosion_3d(enemy["x"], enemy["y"], color=COLOR_CYAN)
                        add_floating_text("+100", enemy["x"], enemy["y"])
                        if enemy in state["enemies"]: state["enemies"].remove(enemy)
                        if bullet in state["bullets"]: state["bullets"].remove(bullet)
                        state["score"] += 100
                        hit = True
                        break
                if hit: continue

                enemy_rect = pygame.Rect(enemy["x"] - enemy["radius"], enemy["y"] - enemy["radius"], enemy["radius"]*2, enemy["radius"]*2)
                if now > state["invuln_until"] and player_rect.colliderect(enemy_rect):
                    create_explosion_3d(enemy["x"], enemy["y"], color=COLOR_NEON_PINK, count=40)
                    create_explosion_3d(state["player_x"], state["player_y"], color=COLOR_CYAN, count=40)
                    add_floating_text("HULL CRITICAL!", state["player_x"], state["player_y"] - 30, color=COLOR_NEON_PINK)
                    state["enemies"].remove(enemy)
                    state["lives"] -= 1
                    state["invuln_until"] = now + 1600
                    if state["lives"] <= 0:
                        game_over = True

            target_interval = max(MIN_SPAWN_INTERVAL_MS, BASE_SPAWN_INTERVAL_MS - (state["score"] // 8))
            if target_interval != state["spawn_interval"]:
                state["spawn_interval"] = target_interval
                pygame.time.set_timer(SPAWN_ENEMY, state["spawn_interval"])

        for star in stars:
            star["y"] += star["speed"]
            if star["y"] > HEIGHT:
                star["y"] = 0
                star["x"] = random.randint(0, WIDTH)

        for p in particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 0.035
            if p["life"] <= 0: particles.remove(p)

        for tp in thrust_particles[:]:
            tp["y"] += tp["vy"]
            tp["life"] -= 0.08
            if tp["life"] <= 0: thrust_particles.remove(tp)

        for ft in floating_texts[:]:
            ft["y"] += ft["vy"]
            ft["life"] -= 0.025
            if ft["life"] <= 0: floating_texts.remove(ft)

        screen.fill(COLOR_BG)

        for star in stars:
            pygame.draw.circle(screen, star["color"], (int(star["x"]), int(star["y"])), int(star["z"] * 3) + 1)

        for tp in thrust_particles:
            alpha = int(220 * tp["life"])
            surf = pygame.Surface((tp["radius"] * 2, tp["radius"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*COLOR_CYAN, alpha), (tp["radius"], tp["radius"]), tp["radius"])
            screen.blit(surf, (tp["x"] - tp["radius"], tp["y"] - tp["radius"]))

        for p in particles:
            alpha = int(255 * p["life"])
            surf = pygame.Surface((p["radius"] * 2, p["radius"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p["color"], alpha), (p["radius"], p["radius"]), p["radius"])
            screen.blit(surf, (p["x"] - p["radius"], p["y"] - p["radius"]))

        for bullet in state["bullets"]:
            draw_glow_bullet(screen, bullet[0], bullet[1])

        for enemy in state["enemies"]:
            render_3d_asteroid(screen, enemy)

        if game_over or now > state["invuln_until"] or (now // 100) % 2 == 0:
            draw_3d_ship(screen, state["player_x"], state["player_y"], state["player_vx"], thrust_particles)

        for ft in floating_texts:
            txt_surf = font_small.render(ft["text"], True, ft["color"])
            txt_surf.set_alpha(int(255 * ft["life"]))
            screen.blit(txt_surf, (ft["x"] - txt_surf.get_width() // 2, ft["y"]))

        draw_glass_panel(screen, (15, 12, WIDTH - 30, 60))

        score_lbl = font_small.render("SCORE", True, (140, 160, 190))
        score_val = font_hud.render(f"{state['score']:06d}", True, COLOR_CYAN)
        screen.blit(score_lbl, (30, 18))
        screen.blit(score_val, (30, 34))

        sensor_x = WIDTH // 2 - 70
        if hand_tracking_active:
            status_color = COLOR_NEON_GREEN if not pinch_detected else COLOR_NEON_PINK
            status_txt = "FIRING" if pinch_detected else "TRACKING HAND"
        else:
            status_color = (200, 80, 80)
            status_txt = "NO HAND DETECTED"

        pygame.draw.circle(screen, status_color, (sensor_x, 42), 6)
        sensor_lbl = font_small.render(f"INPUT: {status_txt}", True, status_color)
        screen.blit(sensor_lbl, (sensor_x + 14, 34))

        hull_lbl = font_small.render("HULL INTEGRITY", True, (140, 160, 190))
        screen.blit(hull_lbl, (WIDTH - 160, 18))
        for i in range(PLAYER_LIVES):
            icon_x = WIDTH - 155 + (i * 32)
            icon_y = 48
            color = COLOR_CYAN if i < state["lives"] else (40, 50, 70)
            pygame.draw.polygon(screen, color, [(icon_x, icon_y - 8), (icon_x - 8, icon_y + 6), (icon_x + 8, icon_y + 6)])

        if game_over:
            modal_w, modal_h = 420, 260
            modal_x, modal_y = (WIDTH - modal_w) // 2, (HEIGHT - modal_h) // 2
            draw_glass_panel(screen, (modal_x, modal_y, modal_w, modal_h), border_color=COLOR_NEON_PINK)

            title_txt = font_title.render("SYSTEM CRITICAL", True, COLOR_NEON_PINK)
            screen.blit(title_txt, (WIDTH // 2 - title_txt.get_width() // 2, modal_y + 25))

            sub_txt = font_hud.render(f"FINAL SCORE: {state['score']}", True, COLOR_CYAN)
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
