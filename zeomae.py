# 기존 코드와 통합한 전체 코드 (Ship 모드 포함)

import pygame
import sys
import time
import random
import math

# 초기화
pygame.init()
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
clock = pygame.time.Clock()
FPS = 60

# 타일 크기
TILE_SIZE = 50

# 색
COLOR_BG = (30, 30, 30)
COLOR_BLOCK = (200, 50, 50)
COLOR_TRIANGLE = (50, 200, 200)
COLOR_THIN_TRIANGLE = (255, 255, 0)
COLOR_SPIKES = (255, 255, 255)
COLOR_PLAYER = (0, 150, 255)
COLOR_CLEAR = (150, 0, 200)
BLUE = (50, 150, 255)

# 플레이어 설정
player_size = 40
player_x = 100
player_y = 300
player_speed_y = 0
gravity = 0.9
jump_power = -14
on_ground = False
ship_mode = False  # Ship 모드 상태
player_angle = 0

def draw_rotated_player(surface, rect, angle):
    surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, BLUE, (0, 0, rect.width, rect.height))
    rotated_surf = pygame.transform.rotate(surf, angle)
    new_rect = rotated_surf.get_rect(center=rect.center)
    surface.blit(rotated_surf, new_rect.topleft)

# 배경
angle_amplitude = 3.5
angle_speed = 0.005
scale_amplitude = 0.02
scale_base = 0.8
angle_time = 0
bg_scroll_x = 0
bg_scroll_speed = -0.3

# 위치 저장 리스트
triangle_positions = []
thin_triangle_positions = []
spike_tile_positions = []
half_block_positions = []
blocks_list = []
u_positions = []
d_positions = []
clear_positions = []
ship_trigger_positions = []  # ship 모드 전환용

# 로고 이미지
start_image = pygame.image.load("_geometryrising.png")
orig_width, orig_height = start_image.get_size()
scale = 0.45
new_size = (int(orig_width * scale), int(orig_height * scale))
logo_image = pygame.transform.scale(start_image, new_size)
logo_rect = logo_image.get_rect(center=(400, 170))

# 버튼 이미지
button_image = pygame.image.load("logo.png").convert_alpha()
button_image = pygame.transform.scale(button_image, (160, 160))
button_rect = button_image.get_rect(center=(screen_width // 2, screen_height // 2 + 50))
button_image_hover = pygame.transform.scale(button_image, (176, 176))

# 배경 이미지
background_image = pygame.image.load("bg1.png").convert()
background_image = pygame.transform.scale(background_image, (screen_width, screen_height))

# 블록 클래스
class Block(pygame.sprite.Sprite):
    def __init__(self, x, y, height=TILE_SIZE):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, height))
        self.image.fill(COLOR_BLOCK)
        self.rect = self.image.get_rect(topleft=(x, y))

# 맵 불러오기
def load_map(filename):
    blocks = pygame.sprite.Group()
    with open(filename, 'r') as f:
        lines = f.readlines()

    for row_idx, line in enumerate(lines):
        for col_idx, char in enumerate(line.strip()):
            x = col_idx * TILE_SIZE
            y = row_idx * TILE_SIZE

            if char == '#':
                block = Block(x, y)
                blocks.add(block)
                blocks_list.append((x, y, TILE_SIZE, TILE_SIZE))
            elif char == '^':
                triangle_positions.append((x, y))
            elif char == '`':
                thin_triangle_positions.append((x, y))
            elif char == '*':
                spike_tile_positions.append((x, y))
            elif char == '~':
                half_block_positions.append((x, y))
                blocks_list.append((x, y, TILE_SIZE, TILE_SIZE // 2))
            elif char == 'u':
                u_positions.append(x)
            elif char == 'd':
                d_positions.append(x)
            elif char == '$':
                clear_positions.append((x, y))
            elif char == 's':
                ship_trigger_positions.append(x)

    return blocks

def draw_scrolling_background(x_offset):
    rel_x = x_offset % screen_width
    screen.blit(background_image, (rel_x - screen_width, 0))
    screen.blit(background_image, (rel_x, 0))
def draw_map():
    screen.fill(COLOR_BG)
    for block in map_blocks:
        block_rect = block.rect.move(-scroll_x, 0)
        screen.blit(block.image, block_rect.topleft)
    for tri_x, tri_y in triangle_positions:
        p1 = (tri_x - scroll_x + TILE_SIZE // 2, tri_y)
        p2 = (tri_x - scroll_x, tri_y + TILE_SIZE)
        p3 = (tri_x - scroll_x + TILE_SIZE, tri_y + TILE_SIZE)
        pygame.draw.polygon(screen, COLOR_TRIANGLE, [p1, p2, p3])
    for tri_x, tri_y in thin_triangle_positions:
        height = TILE_SIZE // 3
        base_y = tri_y + TILE_SIZE - height
        p1 = (tri_x - scroll_x + TILE_SIZE // 2, base_y)
        p2 = (tri_x - scroll_x, base_y + height)
        p3 = (tri_x - scroll_x + TILE_SIZE, base_y + height)
        pygame.draw.polygon(screen, COLOR_THIN_TRIANGLE, [p1, p2, p3])
    for spike_x, spike_y in spike_tile_positions:
        num_spikes = 6
        spike_width = TILE_SIZE // num_spikes
        spike_height = TILE_SIZE // 2
        for i in range(num_spikes):
            left = spike_x - scroll_x + i * spike_width
            top = spike_y + TILE_SIZE - spike_height
            p1 = (left + spike_width // 2, top)
            p2 = (left, spike_y + TILE_SIZE)
            p3 = (left + spike_width, spike_y + TILE_SIZE)
            pygame.draw.polygon(screen, COLOR_SPIKES, [p1, p2, p3])
    # 클리어 영역 그리기
    for clear_x, clear_y in clear_positions:
        clear_rect = pygame.Rect(clear_x - scroll_x, clear_y, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(screen, COLOR_CLEAR, clear_rect)
        
class Particle:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(random.uniform(-5, 5), random.uniform(-5, 5))
        self.radius = random.randint(3, 6)
        self.color = (0,100,0)
        self.lifetime = random.randint(20, 40)
    def update(self):
        self.pos += self.vel
        self.vel.y += 0.3
        self.lifetime -= 1
    def draw(self, surface):
        if self.lifetime > 0:
            pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
# 게임 리셋
def reset_game():
    global player_y, player_speed_y, on_ground, scroll_x, ship_mode
    player_y = 300
    player_speed_y = 0
    on_ground = False
    scroll_x = 0
    ship_mode = False
def explode_particles(center):
    particles = [Particle(center[0], center[1]) for _ in range(30)]
    for _ in range(30):
        draw_map()   # 맵만 그림
        for p in particles:
            p.update()
            p.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

def game_over():
    global game_speed
    saved_speed = game_speed
    game_speed = 0
    explode_particles(player_rect.center)  # 💥 파티클만 보여줌 (플레이어는 X)
    game_speed = saved_speed
    reset_game()

def draw_rotated_player(surface, rect, angle):
    surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, COLOR_PLAYER, (0, 0, rect.width, rect.height))
    rotated_surf = pygame.transform.rotate(surf, angle)
    new_rect = rotated_surf.get_rect(center=rect.center)
    surface.blit(rotated_surf, new_rect.topleft)

# 기존 플레이어 그리기 코드 대신 아래로 교체

map_blocks = load_map("map.txt")
scroll_x = 0
scroll_y = 0
game_speed = 7.468
running = False
clear = False
waiting = True

while True:
    # ... (생략) 기존 코드

    while running:
        dt = clock.tick(FPS)
        screen.fill(COLOR_BG)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and on_ground and not ship_mode:
            player_speed_y = jump_power
            on_ground = False
        if ship_mode and keys[pygame.K_SPACE]:
            player_speed_y += -0.7

        player_speed_y += gravity
        previous_y = player_y
        player_y += player_speed_y
        player_rect = pygame.Rect(player_x, player_y, player_size, player_size)
        on_ground = False

        # --- 충돌 검사 ---

        # 블록 충돌
        for bx, by, bw, bh in blocks_list:
            block_rect = pygame.Rect(bx - scroll_x, by - scroll_y, bw, bh)
            if player_rect.colliderect(block_rect):
                # 착지 충돌 (플레이어 아래가 블록 위에 닿는 경우)
                if previous_y + player_size <= block_rect.top + 5 and player_speed_y >= 0:
                    player_y = block_rect.top - player_size
                    player_speed_y = 0
                    on_ground = True
                else:
                    game_over()
                    running = False
                    waiting = True
                    break
        if not running:
            continue

        # 삼각형 충돌
        for tx, ty in triangle_positions + thin_triangle_positions + spike_tile_positions:
            tri_rect = pygame.Rect(tx - scroll_x, ty - scroll_y, TILE_SIZE, TILE_SIZE)
            if player_rect.colliderect(tri_rect):
                game_over()
                running = False
                waiting = True
                break
        if not running:
            continue

        # 클리어 위치 검사
        for clear_x, clear_y in clear_positions:
            clear_rect = pygame.Rect(clear_x - scroll_x, clear_y, TILE_SIZE, TILE_SIZE)
            if player_rect.colliderect(clear_rect):
                clear = True
                running = False
                break

        # 플레이어 위치 제한(바닥)
        if player_y + player_size >= screen_height:
            player_y = screen_height - player_size
            player_speed_y = 0
            on_ground = True

        scroll_x += game_speed

        # --- 그리기 ---

        # 맵 그리기 (블록, 삼각형, 가시 등)
        for bx, by, bw, bh in blocks_list:
            block_rect = pygame.Rect(bx - scroll_x, by - scroll_y, bw, bh)
            pygame.draw.rect(screen, COLOR_BLOCK, block_rect)
        for tx, ty in triangle_positions:
            p1 = (tx - scroll_x + TILE_SIZE//2, ty - scroll_y)
            p2 = (tx - scroll_x, ty + TILE_SIZE - scroll_y)
            p3 = (tx - scroll_x + TILE_SIZE, ty + TILE_SIZE - scroll_y)
            pygame.draw.polygon(screen, COLOR_TRIANGLE, [p1, p2, p3])
        for tx, ty in thin_triangle_positions:
            h = TILE_SIZE // 3
            by = ty + TILE_SIZE - h
            p1 = (tx - scroll_x + TILE_SIZE//2, by - scroll_y)
            p2 = (tx - scroll_x, by + h - scroll_y)
            p3 = (tx - scroll_x + TILE_SIZE, by + h - scroll_y)
            pygame.draw.polygon(screen, COLOR_THIN_TRIANGLE, [p1, p2, p3])
        for sx, sy in spike_tile_positions:
            num = 6
            w = TILE_SIZE // num
            h = TILE_SIZE // 2
            for i in range(num):
                l = sx - scroll_x + i*w
                t = sy + TILE_SIZE - h - scroll_y
                p1 = (l + w//2, t)
                p2 = (l, sy + TILE_SIZE - scroll_y)
                p3 = (l + w, sy + TILE_SIZE - scroll_y)
                pygame.draw.polygon(screen, COLOR_SPIKES, [p1, p2, p3])

        for clear_x, clear_y in clear_positions:
            clear_rect = pygame.Rect(clear_x - scroll_x, clear_y, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, COLOR_CLEAR, clear_rect)

        # 플레이어 그리기
        if not on_ground:
            player_angle -= 5
            player_angle %= 360
        else:
            player_angle = 0

        # 🎨 플레이어 그리기 (살아 있을 때만)
        draw_rotated_player(screen, player_rect, player_angle)

        pygame.display.flip()

    # ... 이하 생략 (clear 화면, waiting 루프 등)


    while waiting:
        bg_scroll_x += bg_scroll_speed
        draw_scrolling_background(bg_scroll_x)

        angle = angle_amplitude * math.sin(angle_time)
        scale = scale_base + scale_amplitude * math.sin(angle_time)
        angle_time += angle_speed

        new_width = int(orig_width * scale * scale)
        new_height = int(orig_height * scale * scale)
        scaled_logo = pygame.transform.smoothscale(start_image, (new_width, new_height))
        rotated_logo = pygame.transform.rotate(scaled_logo, angle)
        rotated_rect = rotated_logo.get_rect(center=logo_rect.center)
        screen.blit(rotated_logo, rotated_rect)

        mouse_pos = pygame.mouse.get_pos()
        shake_range = 2
        if button_rect.collidepoint(mouse_pos):
            shake_x = random.randint(-shake_range, shake_range)
            shake_y = random.randint(-shake_range, shake_range)
            hover_rect = button_image_hover.get_rect(center=(button_rect.centerx + shake_x, button_rect.centery + shake_y))
            screen.blit(button_image_hover, hover_rect)
        else:
            screen.blit(button_image, button_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(mouse_pos):
                    waiting = False
                    running = True
