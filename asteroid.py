import pygame
import math
import random

class Asteroid:
    def __init__(self, x, y, radius, speed):
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = speed
        self.rot_x = random.uniform(0, 3.14)
        self.rot_y = random.uniform(0, 3.14)
        self.rot_z = random.uniform(0, 3.14)
        self.rx_speed = random.uniform(-0.04, 0.04)
        self.ry_speed = random.uniform(-0.04, 0.04)
        self.rz_speed = random.uniform(-0.04, 0.04)
        self.nodes, self.faces = self._generate_mesh(radius)

    def _generate_mesh(self, radius):
        nodes, faces = [], []
        num_lat, num_lon = 5, 7
        for i in range(num_lat):
            lat = (i / (num_lat - 1)) * math.pi - (math.pi / 2)
            for j in range(num_lon):
                lon = (j / num_lon) * 2 * math.pi
                r = radius * random.uniform(0.75, 1.25)
                nodes.append([r * math.cos(lat) * math.cos(lon), r * math.cos(lat) * math.sin(lon), r * math.sin(lat)])
        for i in range(num_lat - 1):
            for j in range(num_lon):
                next_j = (j + 1) % num_lon
                faces.append([i * num_lon + j, i * num_lon + next_j, (i + 1) * num_lon + next_j, (i + 1) * num_lon + j])
        return nodes, faces

    def update(self):
        self.y += self.speed
        self.rot_x += self.rx_speed
        self.rot_y += self.ry_speed
        self.rot_z += self.rz_speed

    def draw(self, surface):
        ex, ey = self.x, self.y
        ax, ay, az = self.rot_x, self.rot_y, self.rot_z
        cx, sx = math.cos(ax), math.sin(ax)
        cy, sy = math.cos(ay), math.sin(ay)
        cz, sz = math.cos(az), math.sin(az)

        rotated_nodes = []
        for nx, ny, nz in self.nodes:
            y1 = ny * cx - nz * sx
            z1 = ny * sx + nz * cx
            x2 = nx * cy + z1 * sy
            z2 = -nx * sy + z1 * cy
            x3 = x2 * cz - y1 * sz
            y3 = x2 * sz + y1 * cz
            rotated_nodes.append((x3, y3, z2))

        light_dir = (0.5, -0.7, 0.5)
        projected_faces = []

        for face in self.faces:
            pts = [rotated_nodes[idx] for idx in face]
            avg_z = sum(p[2] for p in pts) / len(pts)
            v1 = (pts[1][0] - pts[0][0], pts[1][1] - pts[0][1], pts[1][2] - pts[0][2])
            v2 = (pts[2][0] - pts[0][0], pts[2][1] - pts[0][1], pts[2][2] - pts[0][2])
            normal = (v1[1]*v2[2] - v1[2]*v2[1], v1[2]*v2[0] - v1[0]*v2[2], v1[0]*v2[1] - v1[1]*v2[0])
            n_len = math.hypot(normal[0], normal[1], normal[2]) + 0.0001
            dot = max(0.12, (normal[0]/n_len)*light_dir[0] + (normal[1]/n_len)*light_dir[1] + (normal[2]/n_len)*light_dir[2])
            
            shade = int(220 * dot)
            color = (shade, shade, int(shade * 1.15))
            screen_pts = [(int(p[0] + ex), int(p[1] + ey)) for p in pts]
            projected_faces.append((avg_z, screen_pts, color))

        projected_faces.sort(key=lambda f: f[0])
        for _, pts, color in projected_faces:
            pygame.draw.polygon(surface, color, pts)
            pygame.draw.polygon(surface, (color[0]//2, color[1]//2, color[2]//2), pts, width=1)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)