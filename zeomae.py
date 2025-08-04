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

# 플레이어 설정
player_size = 40
player_x = 100
player_y = 300
player_speed_y = 0
gravity = 0.9
jump_power = -14
on_ground = False

angle_amplitude = 5      # 최대 기울기 각도 (5도)
angle_speed = 0.3       # 기울기 변화 속도
angle_time = 0           # 시간 변수
angle_amplitude = 3.5      
angle_speed = 0.005       
scale_amplitude = 0.02   
scale_base = 0.8         
angle_time = 0
bg_scroll_x = 0
bg_scroll_speed = -0.3  # 적당한 속도로

# 위치 저장 리스트
triangle_positions = []        # 보통 삼각형 (^)
thin_triangle_positions = []   # 얇은 삼각형 (`)
spike_tile_positions = []      # 자잘한 가시 (*)
half_block_positions = []      # 반블록 (~)

# 충돌용 리스트 (좌표 저장)
blocks_list = []   # (x, y, width, height)

# 트리거 위치
u_positions = []
d_positions = []
clear_positions = []

# ✅ 로고 이미지
start_image = pygame.image.load("_geometryrising.png")
orig_width, orig_height = start_image.get_size()
scale = 0.45
new_size = (int(orig_width * scale), int(orig_height * scale))
logo_image = pygame.transform.scale(start_image, new_size)
logo_rect = logo_image.get_rect(center=(400, 170))

# ✅ 버튼 이미지
button_image = pygame.image.load("logo.png").convert_alpha()
button_image = pygame.transform.scale(button_image, (160, 160))
button_rect = button_image.get_rect(center=(screen_width // 2, screen_height // 2 + 50))
button_image_hover = pygame.transform.scale(button_image, (176, 176))

# ✅배경이미지
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
                # 반블록: 위쪽 절반에 생성
                half_block_positions.append((x, y))
                blocks_list.append((x, y, TILE_SIZE, TILE_SIZE // 2))
            elif char == 'u':
                u_positions.append(x)
            elif char == 'd':
                d_positions.append(x)
            elif char == '$':              # 추가: 클리어 구역 위치 저장
                clear_positions.append((x, y))

    return blocks

def draw_scrolling_background(x_offset):
    rel_x = x_offset % screen_width
    screen.blit(background_image, (rel_x - screen_width, 0))
    screen.blit(background_image, (rel_x, 0))

# ✅ 게임 리셋
def reset_game():
    global player, velocity_y, on_ground, player_angle, scroll_x
    player = pygame.Rect(100, -150, player_size, player_size)
    velocity_y = 0
    on_ground = False
    player_angle = 0
    scroll_x = 0

# 맵 로딩
map_blocks = load_map("map.txt")

# 스크롤 변수
scroll_x = 0
scroll_y = 0
game_speed = 7.468
#game_speed=15

# 게임 루프
running = False
clear = False
waiting = True

while True:
    while running:
        dt = clock.tick(60)
        screen.fill(COLOR_BG)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()


        # 플레이어 입력
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and on_ground:
            player_speed_y = jump_power
            on_ground = False
        if keys[pygame.K_t]:
            time.sleep(5)


        # 중력 적용
        player_speed_y += gravity

        # 이전 y 저장
        previous_y = player_y
        # Y 이동
        player_y += player_speed_y

        # 플레이어 rect
        player_rect = pygame.Rect(player_x, player_y, player_size, player_size)
        on_ground = False

        # 충돌 검사 (블록 + 반블록)
        for bx, by, bw, bh in blocks_list:
            adj = pygame.Rect(bx - scroll_x, by - scroll_y, bw, bh)
            if player_rect.colliderect(adj):
                # 위에서 내려올 때만 착지 (5px 토러런스)
                if previous_y + player_size <= adj.top + 5:
                    player_y = adj.top - player_size
                    player_speed_y = 0
                    on_ground = True

        for clear_x, clear_y in clear_positions:
            clear_rect = pygame.Rect(clear_x - scroll_x, clear_y, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, COLOR_CLEAR, clear_rect)
            if player_rect.colliderect(clear_rect):
                clear = True
                running = False


        # 바닥 충돌
        if player_y + player_size >= screen_height - 50:
            player_y = screen_height - 50 - player_size
            player_speed_y = 0
            on_ground = True

        # 스크롤 업데이트
        scroll_x += game_speed
        player_map_x = player_x + scroll_x
        for ux in u_positions:
            if abs(player_map_x - ux) < 10:
                scroll_y -= 10
                player_y+=5
        for dx in d_positions:
            if abs(player_map_x - dx) < 10:
                scroll_y += 10
                player_y-=5

        # 블록 그리기
        for block in map_blocks:
            screen.blit(block.image, (block.rect.x - scroll_x, block.rect.y - scroll_y))

        # 삼각형 그리기 (^, `, *)
        for tx, ty in triangle_positions:
            p1 = (tx - scroll_x + TILE_SIZE//2, ty - scroll_y)
            p2 = (tx - scroll_x, ty + TILE_SIZE - scroll_y)
            p3 = (tx - scroll_x + TILE_SIZE, ty + TILE_SIZE - scroll_y)
            pygame.draw.polygon(screen, COLOR_TRIANGLE, [p1,p2,p3])
        for tx, ty in thin_triangle_positions:
            h = TILE_SIZE // 3
            by = ty + TILE_SIZE - h
            p1 = (tx - scroll_x + TILE_SIZE//2, by - scroll_y)
            p2 = (tx - scroll_x, by + h - scroll_y)
            p3 = (tx - scroll_x + TILE_SIZE, by + h - scroll_y)
            pygame.draw.polygon(screen, COLOR_THIN_TRIANGLE, [p1,p2,p3])
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
                pygame.draw.polygon(screen, COLOR_SPIKES, [p1,p2,p3])

        # 반블록 그리기 (위쪽 절반)
        for hx, hy in half_block_positions:
            rect = pygame.Rect(hx - scroll_x, hy - scroll_y, TILE_SIZE, TILE_SIZE//2)
            pygame.draw.rect(screen, COLOR_BLOCK, rect)

        for clear_x, clear_y in clear_positions:
            clear_rect = pygame.Rect(clear_x - scroll_x, clear_y, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, COLOR_CLEAR, clear_rect)

        # 플레이어 그리기
        pygame.draw.rect(screen, COLOR_PLAYER, player_rect)

        pygame.display.flip()

    while clear:
        screen.fill(COLOR_BG)
        clear_font = pygame.font.SysFont(None, 72)
        clear_text = clear_font.render("Clear!", True, (200, 150, 255))
        clear_rect = clear_text.get_rect(center=(screen_width//2, screen_height//2))
        screen.blit(clear_text, clear_rect)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                clear = False
                waiting = True
                reset_game()

        pygame.display.flip()
        clock.tick(FPS)

    while waiting:
        bg_scroll_x += bg_scroll_speed
        # draw_scrolling_background2(bg_scroll_x,angle_time)
        draw_scrolling_background(bg_scroll_x)

        # 사인 함수로 자연스러운 각도와 스케일 변화 계산
        angle = angle_amplitude * math.sin(angle_time)
        scale = scale_base + scale_amplitude * math.sin(angle_time)
        angle_time += angle_speed

        angle_time += angle_speed

        # 로고 이미지 크기 변경
        new_width = int(orig_width * scale * scale)
        new_height = int(orig_height * scale * scale)
        scaled_logo = pygame.transform.smoothscale(start_image, (new_width, new_height))

        # 회전
        rotated_logo = pygame.transform.rotate(scaled_logo, angle)
        rotated_rect = rotated_logo.get_rect(center=logo_rect.center)

        screen.blit(rotated_logo, rotated_rect)

        # 버튼 흔들림 (기존 코드)
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
    


pygame.quit()
sys.exit()
