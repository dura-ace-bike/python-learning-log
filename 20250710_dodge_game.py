import pygame
import random
import sys
import time
import math

# 初期化
pygame.init()

# 画面サイズ
WIDTH = 480
HEIGHT = 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("障害物避けゲーム")

# フォント
font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 54)
small_font = pygame.font.SysFont(None, 24)

# 色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
RED   = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
BLUE  = (0, 0, 255)
LIGHT_GRAY = (180, 180, 180)

# プレイヤー設定
player_radius_large = 30
player_radius_middle = 20
player_radius_small = 10
player_x = WIDTH // 2
player_y = HEIGHT - player_radius_large * 2
player_speed = 5

# 障害物設定
obstacle_radius = 25
base_obstacle_speed = 5 * 1.6
speedup_increment = 3 * 1.1
obstacle_speed = base_obstacle_speed

obstacles = []
num_obstacles = 3

# スコアとタイマー
score = 0
game_duration = 15
game_over = False
game_clear = False
paused = False
speedup_triggered = False
speedup_flash = True
speedup_flash_timer = 0
speedup_soon_flash = True
speedup_soon_flash_timer = 0

# READY モード
ready = True
start_time = None
end_time = None

clock = pygame.time.Clock()
running = True

def circle_collision(x1, y1, r1, x2, y2, r2):
    distance = math.hypot(x1 - x2, y1 - y2)
    return distance <= (r1 + r2)

def reset_game():
    global player_x, obstacles, obstacle_speed, speedup_triggered, speedup_flash_timer
    global speedup_soon_flash_timer, score, game_over, paused, ready, game_clear, end_time
    player_x = WIDTH // 2
    obstacles = []
    obstacle_speed = base_obstacle_speed
    speedup_triggered = False
    speedup_flash_timer = 0
    speedup_soon_flash_timer = 0
    score = 0
    game_over = False
    game_clear = False
    paused = False
    ready = True
    end_time = None

while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_SPACE:
                if not ready and not game_over and not game_clear:
                    paused = not paused
                if game_over or game_clear:
                    reset_game()
            if ready:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    ready = False
                    start_time = time.time()
                    obstacles = []
                    obstacle_speed = base_obstacle_speed
                    for i in range(num_obstacles):
                        x = random.randint(obstacle_radius, WIDTH - obstacle_radius)
                        y = random.randint(-300, -obstacle_radius)
                        obstacles.append([x, y])

    if not ready and not game_over and not game_clear and not paused:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player_x -= player_speed
        if keys[pygame.K_RIGHT]:
            player_x += player_speed

        if player_x < player_radius_large:
            player_x = player_radius_large
        if player_x > WIDTH - player_radius_large:
            player_x = WIDTH - player_radius_large

        elapsed_time = time.time() - start_time
        remaining_time = max(0, game_duration - elapsed_time)

        speedup_soon = False
        if 7 < remaining_time <= 10:
            speedup_soon = True

        if remaining_time <= 7 and not speedup_triggered:
            for i in range(2):
                x = random.randint(obstacle_radius, WIDTH - obstacle_radius)
                y = random.randint(-300, -obstacle_radius)
                obstacles.append([x, y])
            obstacle_speed += speedup_increment
            speedup_triggered = True

        for obstacle in obstacles:
            obstacle[1] += obstacle_speed
            if obstacle[1] > HEIGHT + obstacle_radius:
                obstacle[1] = random.randint(-300, -obstacle_radius)
                obstacle[0] = random.randint(obstacle_radius, WIDTH - obstacle_radius)

        for obstacle in obstacles:
            if circle_collision(player_x, player_y, player_radius_large, obstacle[0], obstacle[1], obstacle_radius):
                game_over = True
                end_time = time.time()

        score = int(elapsed_time * 10)

        if remaining_time <= 0:
            game_clear = True
            end_time = time.time()

    screen.fill(BLACK)

    if ready:
        ready_text = big_font.render("READY?", True, GREEN)
        screen.blit(ready_text, (WIDTH // 2 - ready_text.get_width() // 2, HEIGHT // 2 - ready_text.get_height() // 2 - 40))
        arrow_text = font.render("Press LEFT or RIGHT to START", True, GREEN)
        screen.blit(arrow_text, (WIDTH // 2 - arrow_text.get_width() // 2, HEIGHT // 2 + 20))
    else:
        pygame.draw.circle(screen, RED, (player_x, player_y), player_radius_large)
        pygame.draw.circle(screen, WHITE, (player_x, player_y), player_radius_middle)

        # 青い目の形を分岐
        if game_over:
            eye_rect = pygame.Rect(player_x - 5, player_y - 2, 10, 4)
            pygame.draw.rect(screen, BLUE, eye_rect)
        else:
            # プレイ中・クリア時は同じ！
            pygame.draw.circle(screen, BLUE, (player_x - 5, player_y - 5), player_radius_small)

        for obstacle in obstacles:
            pygame.draw.circle(screen, GRAY, (obstacle[0], obstacle[1]), obstacle_radius)

        score_text = font.render(f"Score: {score}", True, GREEN)
        screen.blit(score_text, (10, 10))

        if not game_over and not game_clear:
            remaining_time = max(0, game_duration - (time.time() - start_time))
            time_text = font.render(f"Time: {remaining_time:.1f}s", True, GREEN)
            screen.blit(time_text, (WIDTH - 200, 10))

            pause_hint = small_font.render("Press SPACE to Pause", True, LIGHT_GRAY)
            screen.blit(pause_hint, (WIDTH - 220, HEIGHT - 30))

        if speedup_soon and not speedup_triggered:
            speedup_soon_flash_timer += 1
            if speedup_soon_flash_timer % 30 == 0:
                speedup_soon_flash = not speedup_soon_flash
            if speedup_soon_flash:
                soon_text = big_font.render("SPEED UP SOON!", True, ORANGE)
                screen.blit(soon_text, (WIDTH // 2 - soon_text.get_width() // 2, 50))

        if speedup_triggered and not game_over and not game_clear:
            speedup_flash_timer += 1
            if speedup_flash_timer % 30 == 0:
                speedup_flash = not speedup_flash
            if speedup_flash:
                speedup_text = big_font.render("SPEED UP!", True, YELLOW)
                screen.blit(speedup_text, (WIDTH // 2 - speedup_text.get_width() // 2, 100))

        if game_over:
            over_text = big_font.render("GAME OVER!", True, GREEN)
            restart_text = font.render("Press SPACE to Restart", True, GREEN)
            rem_time = font.render(f"Time Left: {remaining_time:.1f}s", True, GREEN)
            screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 2 - over_text.get_height()))
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 10))
            screen.blit(rem_time, (WIDTH // 2 - rem_time.get_width() // 2, HEIGHT // 2 + 50))

        if game_clear:
            clear_text = big_font.render("CLEAR!", True, GREEN)
            restart_text = font.render("Press SPACE to Restart", True, GREEN)
            screen.blit(clear_text, (WIDTH // 2 - clear_text.get_width() // 2, HEIGHT // 2 - clear_text.get_height()))
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 10))
            if time.time() - end_time > 5:
                reset_game()

        if paused and not game_over and not game_clear:
            pause_text = big_font.render("PAUSE", True, GREEN)
            screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - pause_text.get_height() // 2))

    pygame.display.flip()

pygame.quit()
sys.exit()
import pygame
import random
import sys
import time
import math

# 初期化
pygame.init()

# 画面サイズ
WIDTH = 480
HEIGHT = 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("障害物避けゲーム")

# フォント
font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 54)
small_font = pygame.font.SysFont(None, 24)

# 色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
RED   = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
BLUE  = (0, 0, 255)
LIGHT_GRAY = (180, 180, 180)

# プレイヤー設定
player_radius_large = 30
player_radius_middle = 20
player_radius_small = 10
player_x = WIDTH // 2
player_y = HEIGHT - player_radius_large * 2
player_speed = 5

# 障害物設定
obstacle_radius = 25
base_obstacle_speed = 5 * 1.6
speedup_increment = 3 * 1.1
obstacle_speed = base_obstacle_speed

obstacles = []
num_obstacles = 3

# スコアとタイマー
score = 0
game_duration = 15
game_over = False
game_clear = False
paused = False
speedup_triggered = False
speedup_flash = True
speedup_flash_timer = 0
speedup_soon_flash = True
speedup_soon_flash_timer = 0

# READY モード
ready = True
start_time = None
end_time = None

clock = pygame.time.Clock()
running = True

def circle_collision(x1, y1, r1, x2, y2, r2):
    distance = math.hypot(x1 - x2, y1 - y2)
    return distance <= (r1 + r2)

def reset_game():
    global player_x, obstacles, obstacle_speed, speedup_triggered, speedup_flash_timer
    global speedup_soon_flash_timer, score, game_over, paused, ready, game_clear, end_time
    player_x = WIDTH // 2
    obstacles = []
    obstacle_speed = base_obstacle_speed
    speedup_triggered = False
    speedup_flash_timer = 0
    speedup_soon_flash_timer = 0
    score = 0
    game_over = False
    game_clear = False
    paused = False
    ready = True
    end_time = None

while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_SPACE:
                if not ready and not game_over and not game_clear:
                    paused = not paused
                if game_over:
                    reset_game()
                if game_clear:
                    running = False  # CLEAR画面でSPACEを押しても終了
            if ready:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    ready = False
                    start_time = time.time()
                    obstacles = []
                    obstacle_speed = base_obstacle_speed
                    for i in range(num_obstacles):
                        x = random.randint(obstacle_radius, WIDTH - obstacle_radius)
                        y = random.randint(-300, -obstacle_radius)
                        obstacles.append([x, y])

    if not ready and not game_over and not game_clear and not paused:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player_x -= player_speed
        if keys[pygame.K_RIGHT]:
            player_x += player_speed

        if player_x < player_radius_large:
            player_x = player_radius_large
        if player_x > WIDTH - player_radius_large:
            player_x = WIDTH - player_radius_large

        elapsed_time = time.time() - start_time
        remaining_time = max(0, game_duration - elapsed_time)

        speedup_soon = False
        if 7 < remaining_time <= 10:
            speedup_soon = True

        if remaining_time <= 7 and not speedup_triggered:
            for i in range(2):
                x = random.randint(obstacle_radius, WIDTH - obstacle_radius)
                y = random.randint(-300, -obstacle_radius)
                obstacles.append([x, y])
            obstacle_speed += speedup_increment
            speedup_triggered = True

        for obstacle in obstacles:
            obstacle[1] += obstacle_speed
            if obstacle[1] > HEIGHT + obstacle_radius:
                obstacle[1] = random.randint(-300, -obstacle_radius)
                obstacle[0] = random.randint(obstacle_radius, WIDTH - obstacle_radius)

        for obstacle in obstacles:
            if circle_collision(player_x, player_y, player_radius_large, obstacle[0], obstacle[1], obstacle_radius):
                game_over = True
                end_time = time.time()

        score = int(elapsed_time * 10)

        if remaining_time <= 0:
            game_clear = True
            end_time = time.time()

    screen.fill(BLACK)

    if ready:
        ready_text = big_font.render("READY?", True, GREEN)
        screen.blit(ready_text, (WIDTH // 2 - ready_text.get_width() // 2, HEIGHT // 2 - ready_text.get_height() // 2 - 40))
        arrow_text = font.render("Press LEFT or RIGHT to START", True, GREEN)
        screen.blit(arrow_text, (WIDTH // 2 - arrow_text.get_width() // 2, HEIGHT // 2 + 20))
    else:
        pygame.draw.circle(screen, RED, (player_x, player_y), player_radius_large)
        pygame.draw.circle(screen, WHITE, (player_x, player_y), player_radius_middle)

        if game_over:
            eye_rect = pygame.Rect(player_x - 5, player_y - 2, 10, 4)
            pygame.draw.rect(screen, BLUE, eye_rect)
        else:
            pygame.draw.circle(screen, BLUE, (player_x - 5, player_y - 5), player_radius_small)

        for obstacle in obstacles:
            pygame.draw.circle(screen, GRAY, (obstacle[0], obstacle[1]), obstacle_radius)

        score_text = font.render(f"Score: {score}", True, GREEN)
        screen.blit(score_text, (10, 10))

        if not game_over and not game_clear:
            remaining_time = max(0, game_duration - (time.time() - start_time))
            time_text = font.render(f"Time: {remaining_time:.1f}s", True, GREEN)
            screen.blit(time_text, (WIDTH - 200, 10))

            pause_hint = small_font.render("Press SPACE to Pause", True, LIGHT_GRAY)
            screen.blit(pause_hint, (WIDTH - 220, HEIGHT - 30))

        if speedup_soon and not speedup_triggered:
            speedup_soon_flash_timer += 1
            if speedup_soon_flash_timer % 30 == 0:
                speedup_soon_flash = not speedup_soon_flash
            if speedup_soon_flash:
                soon_text = big_font.render("SPEED UP SOON!", True, ORANGE)
                screen.blit(soon_text, (WIDTH // 2 - soon_text.get_width() // 2, 50))

        if speedup_triggered and not game_over and not game_clear:
            speedup_flash_timer += 1
            if speedup_flash_timer % 30 == 0:
                speedup_flash = not speedup_flash
            if speedup_flash:
                speedup_text = big_font.render("SPEED UP!", True, YELLOW)
                screen.blit(speedup_text, (WIDTH // 2 - speedup_text.get_width() // 2, 100))

        if game_over:
            over_text = big_font.render("GAME OVER!", True, GREEN)
            restart_text = font.render("Press SPACE to Restart", True, GREEN)
            rem_time = font.render(f"Time Left: {remaining_time:.1f}s", True, GREEN)
            screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 2 - over_text.get_height()))
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 10))
            screen.blit(rem_time, (WIDTH // 2 - rem_time.get_width() // 2, HEIGHT // 2 + 50))

        if game_clear:
            clear_text = big_font.render("CLEAR!", True, GREEN)
            restart_text = font.render("Press SPACE to Exit", True, GREEN)
            screen.blit(clear_text, (WIDTH // 2 - clear_text.get_width() // 2, HEIGHT // 2 - clear_text.get_height()))
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 10))
            if time.time() - end_time > 5:
                running = False  # 一定時間経過後に終了

        if paused and not game_over and not game_clear:
            pause_text = big_font.render("PAUSE", True, GREEN)
            screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - pause_text.get_height() // 2))

    pygame.display.flip()

pygame.quit()
sys.exit()
