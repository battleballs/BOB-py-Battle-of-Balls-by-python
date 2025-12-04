import pygame
import random
import math
from BOB_param import SCREEN_WIDTH, SCREEN_HEIGHT, MAP_SIZE, FOOD_COUNT, AI_COUNT, WHITE, BLACK, RED, MIN_SPLIT_RADIUS, MIN_EJECT_RADIUS, GAME_FPS
from BOB_lib import Ball, Player


# --- 3. 游戏初始化 ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Ball Eater Clone (Single Player)")
pygame.display.flip()  # 强制刷新显示
pygame.event.set_grab(False)  # 确保不抓取鼠标
clock = pygame.time.Clock()

# --- 4. 对象生成函数 ---
def create_random_ball(min_radius, max_radius, ball_class="food"):
    radius = random.randint(min_radius, max_radius)
    x = random.randint(-MAP_SIZE // 2, MAP_SIZE // 2)
    y = random.randint(-MAP_SIZE // 2, MAP_SIZE // 2)
    color = (random.randint(50, 155), random.randint(50, 155), random.randint(50, 155))
    return Ball(x, y, radius, color, ball_class)

# 初始化玩家 (使用一个列表来支持分裂)
player = Player()

# 初始化食物
food_list = [create_random_ball(2, 4, ball_class="food") for _ in range(FOOD_COUNT)]
spore_list = []

# 初始化 AI 球
ai_list = [create_random_ball(10, 30, ball_class="ai") for _ in range(AI_COUNT)]

# --- 游戏逻辑函数 ---

def handle_game_logic():
    global food_list, ai_list, player, spore_list
    
    # 所有活动球列表 (玩家分身 + AI)
    active_balls = player.balls + ai_list

    eatable_balls = food_list + spore_list
    
    # --- 1. 吞噬检测 (玩家/AI 吞噬 食物/彼此) ---
    eaters_to_update = []
    eaten_balls = []
    
    # 检查所有活动球对食物的吞噬
    for eater in active_balls:
        food_to_remove = []
        for food in eatable_balls:#food_list + spore_list:
            collision = eater.check_collision(food)
            if collision == "EAT_OTHER":
                eaters_to_update.append((eater, food.mass))
                food_to_remove.append(food)
        
        for food in food_to_remove:
            if food in food_list:
                food_list.remove(food)
            if food in spore_list:
                spore_list.remove(food)

    # 检查活动球之间的吞噬
    for i in range(len(player.balls)):
        for j in range(len(ai_list)):
            ball_a = player.balls[i]
            ball_b = ai_list[j]
            
            # 检查 A 是否吞噬 B
            if ball_a.check_collision(ball_b) == "EAT_OTHER":
                eaters_to_update.append((ball_a, ball_b.mass))
                eaten_balls.append(ball_b)
            # 检查 B 是否吞噬 A
            elif ball_b.check_collision(ball_a) == "EAT_OTHER":
                eaters_to_update.append((ball_b, ball_a.mass))
                eaten_balls.append(ball_a)   
    # --- 2. 更新质量 ---
    for eater, mass_gained in eaters_to_update:
        eater.update_mass(mass_gained)

    # --- 3. 移除被吞噬的球并再生 ---
    new_ai_count = 0
    player_died = False
    
    for ball in set(eaten_balls):
        if ball.ball_class == "player":
            if ball in player.balls:
                player.balls.remove(ball)
                if not player.balls: # 所有分身都被吞噬
                    player_died = True
        else: # AI 被吞噬
            if ball in ai_list:
                ai_list.remove(ball)
                new_ai_count += 1
                
    # 重新生成食物和 AI 球
    for _ in range(FOOD_COUNT - len(food_list)):
        food_list.append(create_random_ball(2, 4))
        
    for _ in range(new_ai_count):
        ai_list.append(create_random_ball(10, 30, ball_class="ai"))
    # print("num ai",len(ai_list))
    return not player_died # 返回玩家是否存活


def update_camera(balls):
    if not balls:
        return 0, 0, 1.0 # 玩家死亡，相机静止
    camera_x = sum(ball.x for ball in balls) / len(balls)
    camera_y = sum(ball.y for ball in balls) / len(balls)

    
    # 缩放：以所有分身球的总质量或最大半径来决定视野
    max_radius = max(ball.radius for ball in balls)
    
    # 基础缩放 1.0 (半径 15 的时候)根据球的大小缩放
    base_radius = 15
    re_scale = max_radius / base_radius
    scale = 1 * (100/(100 + re_scale))#
    
    # 找到边界点（近似方法）根据分身分布缩放
    min_x = min(ball.x for ball in balls)
    max_x = max(ball.x for ball in balls)
    min_y = min(ball.y for ball in balls)
    max_y = max(ball.y for ball in balls)

    rate_x = (max_x - min_x)/SCREEN_WIDTH
    rate_y = (max_y - min_y)/SCREEN_HEIGHT
    rate_for_scale = max(rate_x, rate_y)

    scale = scale * 4/(4 + rate_for_scale)
    # 限制最小缩放，防止画面过小
    scale = max(0.1, scale) 
    # print(scale)
    
    return camera_x, camera_y, scale



# --- 7. 游戏主循环 ---
running = True
game_over = False

cam_scale = 1.0
while running:
    # 缓存鼠标位置，用于移动和操作
    mouse_pos = pygame.mouse.get_pos()     
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if not game_over:
            # 处理分身（空格键）
            player.handle_split(event)
    if not game_over:
        # 处理吐球（W键
        player.handle_eject(spore_list)
        # 1. 处理移动
        player.handle_movement(mouse_pos[0], mouse_pos[1])
        for spore in spore_list:
            spore.update_position()
        # 2. 更新摄像头
        camera_x, camera_y, scale = update_camera(player.balls)
        cam_scale = scale * 0.3 + cam_scale * 0.7
        # 3. 游戏逻辑（碰撞检测和吞噬）
        if not handle_game_logic():
            game_over = True
        
        # 4. 渲染
        screen.fill(WHITE)

        # 绘制背景网格 (省略，保持代码简洁)

        # 绘制食物、AI 球和玩家球 (混合在一起绘制)
        for ball in food_list + ai_list + spore_list:
            ball.draw(screen, camera_x, camera_y, cam_scale)
            
        player.draw_balls(screen, camera_x, camera_y, cam_scale, mouse_pos)

        # 6. 渲染玩家信息
        font = pygame.font.Font(None, 36)
        total_mass = sum(ball.mass for ball in player.balls)
        text = font.render(f"Mass: {total_mass:.0f} | Splits: {len(player.balls)}", True, BLACK)
        screen.blit(text, (10, 10))

        # if camera_x < -MAP_SIZE//2 + SCREEN_WIDTH // 2:
        #     pygame.draw.line(screen, RED, (SCREEN_WIDTH // 2 - camera_x - MAP_SIZE//2, SCREEN_HEIGHT // 2 - camera_y - MAP_SIZE//2), (SCREEN_WIDTH // 2 - camera_x - MAP_SIZE//2, SCREEN_HEIGHT // 2 - camera_y + MAP_SIZE//2), 3)
        # elif camera_x > MAP_SIZE//2 - SCREEN_WIDTH // 2:
        #     pygame.draw.line(screen, RED, (SCREEN_WIDTH // 2 - camera_x + MAP_SIZE//2, SCREEN_HEIGHT // 2 - camera_y - MAP_SIZE//2), (SCREEN_WIDTH // 2 - camera_x + MAP_SIZE//2, SCREEN_HEIGHT // 2 - camera_y + MAP_SIZE//2), 3)

        # if camera_y < -MAP_SIZE//2 + SCREEN_HEIGHT // 2:   
        #     pygame.draw.line(screen, RED, (SCREEN_WIDTH // 2 - camera_x - MAP_SIZE//2, SCREEN_HEIGHT // 2 - camera_y - MAP_SIZE//2), (SCREEN_WIDTH // 2 - camera_x + MAP_SIZE//2, SCREEN_HEIGHT // 2 - camera_y - MAP_SIZE//2), 3)
        # elif camera_y > MAP_SIZE//2 - SCREEN_HEIGHT // 2:
        #     pygame.draw.line(screen, RED, (SCREEN_WIDTH // 2 - camera_x - MAP_SIZE//2, SCREEN_HEIGHT // 2 - camera_y + MAP_SIZE//2), (SCREEN_WIDTH // 2 - camera_x + MAP_SIZE//2, SCREEN_HEIGHT // 2 - camera_y + MAP_SIZE//2), 3)

        # 绘制完整的地图边界框
        left_boundary   = SCREEN_WIDTH  // 2 - (camera_x + MAP_SIZE//2)*cam_scale
        right_boundary  = SCREEN_WIDTH  // 2 - (camera_x - MAP_SIZE//2)*cam_scale
        top_boundary    = SCREEN_HEIGHT // 2 - (camera_y + MAP_SIZE//2)*cam_scale
        bottom_boundary = SCREEN_HEIGHT // 2 - (camera_y - MAP_SIZE//2)*cam_scale

        # 绘制四条边界线
        pygame.draw.line(screen, RED, (left_boundary, top_boundary), (left_boundary, bottom_boundary), 1)
        pygame.draw.line(screen, RED, (right_boundary, top_boundary), (right_boundary, bottom_boundary), 1)
        pygame.draw.line(screen, RED, (left_boundary, top_boundary), (right_boundary, top_boundary), 1)
        pygame.draw.line(screen, RED, (left_boundary, bottom_boundary), (right_boundary, bottom_boundary), 1)
        # print("pos",camera_x,camera_y)
        # 更新屏幕显示
        pygame.display.flip()
        
    else:
        # 游戏结束画面 (略)
        screen.fill((200, 200, 255))
        font = pygame.font.Font(None, 74)
        text = font.render("GAME OVER", True, BLACK)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(text, text_rect)
        
        small_font = pygame.font.Font(None, 36)
        restart_text = small_font.render("Press ESC to Exit", True, BLACK)
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False


    clock.tick(GAME_FPS) # 限制帧率为 60 FPS

pygame.quit()