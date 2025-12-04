import pygame
import random
import math
from BOB_param import SCREEN_WIDTH, SCREEN_HEIGHT, MAP_SIZE, FOOD_COUNT, AI_COUNT, MIN_SPLIT_MASS, MIN_EJECT_MASS, WHITE, BLACK, RED, FUSE_COOLDOWN_TIME, GAME_FPS, EJECT_FPS
# --- 2. Ball 类 (游戏对象) ---
class Ball:
    def __init__(self, x, y, radius, color, ball_class="food"):
        self.x = x
        self.y = y

        self.screen_x = x
        self.screen_y = y

        self.radius = radius
        self.screen_radius = radius
        self.color = color
        self.ball_class = ball_class # "food"星星 "player"玩家 "spore"孢子 "thorn"刺
        self.mass = math.pi * (radius ** 2)
        # 针对分裂/吐球后短暂的运动惯性
        self.vel_x_iner = 0
        self.vel_y_iner = 0
        # 玩家控制速度
        self.vel_x_ctrl = 0
        self.vel_y_ctrl = 0
        # 玩家控制速度_last
        self.vel_x_ctrl_last = 0
        self.vel_y_ctrl_last = 0
        

    def draw(self, screen, camera_x, camera_y, scale):
        # 将地图坐标转换为屏幕坐标
        self.screen_x = int((self.x - camera_x) * scale + SCREEN_WIDTH / 2)
        self.screen_y = int((self.y - camera_y) * scale + SCREEN_HEIGHT / 2)
        if self.ball_class == "food":
            self.screen_radius = 2
        else:
            self.screen_radius = self.radius * scale * 0.2 + self.screen_radius * 0.8

        # 只绘制在屏幕范围内的球
        if self.screen_x + self.screen_radius > 0 and self.screen_x - self.screen_radius < SCREEN_WIDTH and \
           self.screen_y + self.screen_radius > 0 and self.screen_y - self.screen_radius < SCREEN_HEIGHT and \
           self.screen_radius > 1: # 避免绘制过小的球
            
            # 绘制球体
            pygame.draw.circle(screen, self.color, (self.screen_x, self.screen_y), self.screen_radius)
            # 绘制轮廓
            pygame.draw.circle(screen, BLACK, (self.screen_x, self.screen_y), self.screen_radius, 1)

    def update_mass(self, mass_gained):
        self.mass += mass_gained
        self.radius = math.sqrt(self.mass / math.pi)

    def update_position(self):
        # 更新位置（处理惯性）
        self.x += self.vel_x_iner
        self.y += self.vel_y_iner
  
        # 更新玩家球的位置（处理控制速度）
        self.x += self.vel_x_ctrl
        self.y += self.vel_y_ctrl
        
        # 衰减惯性速度  吐球或分身用
        self.vel_x_iner *= 0.9
        self.vel_y_iner *= 0.9
        
        # 速度过小时归零
        if abs(self.vel_x_iner) < 0.1: self.vel_x_iner = 0
        if abs(self.vel_y_iner) < 0.1: self.vel_y_iner = 0
        
        # 限制在地图边界内
        self.x = max(-MAP_SIZE // 2, min(MAP_SIZE // 2, self.x))
        self.y = max(-MAP_SIZE // 2, min(MAP_SIZE // 2, self.y))
        


    def check_collision(self, other_ball):
        distance = math.sqrt((self.x - other_ball.x)**2 + (self.y - other_ball.y)**2)
        
        # 吞噬检测：如果球体重叠
        if distance < (self.radius + other_ball.radius):
            # 吞噬逻辑：自己的半径大于对方半径的 1.1 倍 且 小球大部分被大球压着 才能吞噬
            if self.radius > other_ball.radius * 1.1 and distance < self.radius  - other_ball.radius*0.9:
                return "EAT_OTHER"
            elif other_ball.radius > self.radius * 1.1 and distance < other_ball.radius  - self.radius*0.9:
                return "BE_EATEN"
        return None
    def check_fusion(self, other_ball):
        distance = math.sqrt((self.x - other_ball.x)**2 + (self.y - other_ball.y)**2)
        
        # 融合检测：如果球体重叠
        if distance < (self.radius + other_ball.radius):
            # 融合逻辑：自己的半径大于对方半径 且 小球大部分被大球压着 才能融合
            if self.radius > other_ball.radius and distance < self.radius  - other_ball.radius*0.8:
                return "EAT_OTHER"
            elif other_ball.radius > self.radius and distance < other_ball.radius  - self.radius*0.8:
                return "BE_EATEN"
        return None
# --- 4. 对象生成函数 ---
def create_random_ball(min_radius, max_radius, ball_class="food"):
    radius = random.randint(min_radius, max_radius)
    x = random.randint(-MAP_SIZE // 2, MAP_SIZE // 2)
    y = random.randint(-MAP_SIZE // 2, MAP_SIZE // 2)
    color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
    return Ball(x, y, radius, color, ball_class)

class Player:
    def __init__(self):
        # 初始化玩家球列表
        self.balls = []
        
        self.radius = 25
        x = random.randint(-MAP_SIZE // 2, MAP_SIZE // 2)
        y = random.randint(-MAP_SIZE // 2, MAP_SIZE // 2)
        color = (255, 0, 0)  # 玩家球设为红色#(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        init_ball =  Ball(x, y, self.radius, color, "player")

        self.balls.append(init_ball)
        
        # 添加融合冷却时间属性
        self.fuse_cooldown = 0
        self.FUSE_COOLDOWN_TIME = FUSE_COOLDOWN_TIME
        self.eject_count = 0
        self.MAX_EJECT_COUNT = GAME_FPS / EJECT_FPS
    
    def add_ball(self, ball):
        """添加新球到玩家"""
        self.balls.append(ball)
    
    def remove_ball(self, ball):
        """从玩家中移除球"""
        if ball in self.balls:
            self.balls.remove(ball)
    
    def get_total_mass(self):
        """获取玩家总质量"""
        return sum(ball.mass for ball in self.balls)
    
    def get_geometric_center(self):
        """获取所有球的几何中心"""
        if not self.balls:
            return 0, 0
        center_x = sum(ball.x for ball in self.balls) / len(self.balls)
        center_y = sum(ball.y for ball in self.balls) / len(self.balls)
        return center_x, center_y
    
    def get_max_radius(self):
        """获取玩家球的最大半径"""
        if not self.balls:
            return 0
        return max(ball.radius for ball in self.balls)
    
    def update_all_balls(self):
        """更新所有球的位置和状态"""
        for ball in self.balls:
            ball.update_position()
    
    def find_smallest_ball(self):
        """找到最小的球"""
        if not self.balls:
            return None
        return min(self.balls, key=lambda b: b.radius)
    def handle_movement(self, mouse_x, mouse_y):
        """处理玩家球的移动"""
        if self.fuse_cooldown > -1:
            self.fuse_cooldown -= 1
        # 检查是否有融合
        if len(self.balls) > 1:#检查是否有分身
            # print("self.fuse_cooldown",self.fuse_cooldown)
            if self.fuse_cooldown <= 0:
                # 找到最小的玩家球
                min_ball = min(self.balls, key=lambda b: b.radius)
                
                # 检查是否可以与其他球融合
                for ball_fuse in self.balls:
                    if ball_fuse != min_ball:
                        collision = min_ball.check_fusion(ball_fuse)
                        if collision == "EAT_OTHER":
                            min_ball.x = (min_ball.x * min_ball.mass + ball_fuse.x * ball_fuse.mass) / (ball_fuse.mass + min_ball.mass)
                            min_ball.y = (min_ball.y * min_ball.mass + ball_fuse.y * ball_fuse.mass) / (ball_fuse.mass + min_ball.mass)
                            min_ball.update_mass(ball_fuse.mass)
                            self.balls.remove(ball_fuse)
                            self.fuse_cooldown = self.FUSE_COOLDOWN_TIME
                            break
                        elif collision == "BE_EATEN":
                            ball_fuse.x = (min_ball.x * min_ball.mass + ball_fuse.x * ball_fuse.mass) / (ball_fuse.mass + min_ball.mass)
                            ball_fuse.y = (min_ball.y * min_ball.mass + ball_fuse.y * ball_fuse.mass) / (ball_fuse.mass + min_ball.mass)
                            ball_fuse.update_mass(min_ball.mass)
                            self.balls.remove(min_ball)
                            self.fuse_cooldown = self.FUSE_COOLDOWN_TIME
                            break
        # for ball in self.balls:
        for i in range(len(self.balls)):
            ball = self.balls[i]
            # 计算玩家球中心点到鼠标点的向量
            dx = mouse_x - ball.screen_x
            dy = mouse_y - ball.screen_y
            
            distance = math.sqrt(dx**2 + dy**2)
            if distance == 0:
                ball.vel_x_ctrl = 0
                ball.vel_y_ctrl = 0
            else:
                # 归一化方向向量
                dir_x = dx / distance
                dir_y = dy / distance

                distance = min(150, distance)
                
                # 基础移动速度，受球的大小影响 (大球慢)
                MAX_SPEED = 3
                speed_factor = max(1, ball.radius / 25)
                move_speed = MAX_SPEED * 1 / (speed_factor + 2) * distance / 50

                ball.vel_x_ctrl = dir_x * move_speed
                ball.vel_y_ctrl = dir_y * move_speed

            if len(self.balls) > 1:#检查是否有分身
                if self.fuse_cooldown > 0: # 冷却时间 不允许重合
                    # 检查自己球之间的碰撞
                    for j in range(i + 1, len(self.balls)):
                        other_ball = self.balls[j]
                        # 碰撞检测：
                        distance = math.sqrt((ball.x - other_ball.x)**2 + (ball.y - other_ball.y)**2)
                        # if distance < (ball.radius + other_ball.radius - 1):#有碰撞，同化碰撞方向速度
                        #     dis = ball.radius + other_ball.radius - 1 - distance
                        #     angle = math.atan2(other_ball.y - ball.y, other_ball.x - ball.x)
                        #     # print("angle",angle)
                        #     vel_x_ball = ball.vel_x_ctrl * math.cos(angle) + ball.vel_y_ctrl * math.sin(angle)
                        #     vel_y_ball = - ball.vel_x_ctrl * math.sin(angle) + ball.vel_y_ctrl * math.cos(angle)
                            
                        #     vel_x_other_ball = other_ball.vel_x_ctrl * math.cos(angle) + other_ball.vel_y_ctrl * math.sin(angle)
                        #     vel_y_other_ball = - other_ball.vel_x_ctrl * math.sin(angle) + other_ball.vel_y_ctrl * math.cos(angle)

                        #     vel_x = (vel_x_ball * ball.mass + vel_x_other_ball * other_ball.mass)/(ball.mass + other_ball.mass)

                        #     k_avoid = 0.1

                        #     ball.vel_x_ctrl = (vel_x - dis * k_avoid) * math.cos(angle) - vel_y_ball * math.sin(angle)
                        #     ball.vel_y_ctrl = (vel_x - dis * k_avoid) * math.sin(angle) + vel_y_ball * math.cos(angle)
                        #     other_ball.vel_x_ctrl = (vel_x + dis * k_avoid) * math.cos(angle) - vel_y_other_ball * math.sin(angle)
                        #     other_ball.vel_y_ctrl = (vel_x + dis * k_avoid) * math.sin(angle) + vel_y_other_ball * math.cos(angle)
                        if distance < (ball.radius + other_ball.radius - 1):#有碰撞，同化碰撞方向速度
                            dis = ball.radius + other_ball.radius - 1 - distance
                            angle = math.atan2(other_ball.y - ball.y, other_ball.x - ball.x)

                            vel_x_ball = ball.vel_x_ctrl * math.cos(angle) + ball.vel_y_ctrl * math.sin(angle)
                            vel_y_ball = - ball.vel_x_ctrl * math.sin(angle) + ball.vel_y_ctrl * math.cos(angle)
                            
                            vel_x_other_ball = other_ball.vel_x_ctrl * math.cos(angle) + other_ball.vel_y_ctrl * math.sin(angle)
                            vel_y_other_ball = - other_ball.vel_x_ctrl * math.sin(angle) + other_ball.vel_y_ctrl * math.cos(angle)
                            
                            k_avoid = 0.1
                            k1 = ball.mass /(ball.mass + other_ball.mass)
                            k2 = other_ball.mass /(ball.mass + other_ball.mass)
                            if ball.radius > other_ball.radius:
                                ball.vel_x_ctrl = (vel_x_ball - dis * k_avoid*k1) * math.cos(angle) - vel_y_ball * math.sin(angle)
                                ball.vel_y_ctrl = (vel_x_ball - dis * k_avoid*k1) * math.sin(angle) + vel_y_ball * math.cos(angle)

                                other_ball.vel_x_ctrl = (vel_x_ball + dis * k_avoid * k2) * math.cos(angle) - vel_y_other_ball * math.sin(angle)
                                other_ball.vel_y_ctrl = (vel_x_ball + dis * k_avoid * k2) * math.sin(angle) + vel_y_other_ball * math.cos(angle)
                            else:
                                ball.vel_x_ctrl = (vel_x_other_ball - dis * k_avoid * k1) * math.cos(angle) - vel_y_ball * math.sin(angle)
                                ball.vel_y_ctrl = (vel_x_other_ball - dis * k_avoid * k1) * math.sin(angle) + vel_y_ball * math.cos(angle)

                                other_ball.vel_x_ctrl = (vel_x_other_ball + dis * k_avoid*k2) * math.cos(angle) - vel_y_other_ball * math.sin(angle)
                                other_ball.vel_y_ctrl = (vel_x_other_ball + dis * k_avoid*k2) * math.sin(angle) + vel_y_other_ball * math.cos(angle)
        for ball in self.balls:
            # ball.vel_x_ctrl = ball.vel_x_ctrl * 0.2 + ball.vel_x_ctrl_last * 0.8
            # ball.vel_y_ctrl = ball.vel_y_ctrl * 0.2 + ball.vel_y_ctrl_last * 0.8

            ball.vel_x_ctrl_last = ball.vel_x_ctrl
            ball.vel_y_ctrl_last = ball.vel_y_ctrl
            # 更新位置
            ball.update_position()
    
    def handle_eject(self, food_list):
        """处理吐球"""
        # 获取鼠标位置和方向
        mouse_x, mouse_y = pygame.mouse.get_pos()     
        # --- W键：吐球（喷射）---
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            # print("检测到W键被按下")
            self.eject_count = self.eject_count + 1
            if self.eject_count >= self.MAX_EJECT_COUNT:
                self.eject_count = 0
        
                for ball in self.balls:
                    if ball.mass >= MIN_EJECT_MASS:
                        dx = mouse_x - ball.screen_x
                        dy = mouse_y - ball.screen_y
                        
                        if dx == 0 and dy == 0:
                            return # 鼠标在中心，不执行操作

                        distance = math.sqrt(dx**2 + dy**2)
                        dir_x = dx / distance
                        dir_y = dy / distance
                        # 吐出质量314食物球
                        eject_mass = 314
                        
                        # 扣除质量
                        ball.update_mass(-eject_mass) 
                        
                        # 吐出球的半径 (假设吐球的半径是固定的较小值)
                        eject_radius = 10
                        
                        # 计算吐球的初始位置 (在球的外围)
                        eject_x = ball.x + (ball.radius + eject_radius + 50) * dir_x
                        eject_y = ball.y + (ball.radius + eject_radius + 50) * dir_y
                        
                        new_eject_ball = Ball(eject_x, eject_y, eject_radius, ball.color, "spore")
                        new_eject_ball.mass = eject_mass
                        
                        # 赋予初始速度，使其飞出去
                        EJECT_SPEED = 7
                        new_eject_ball.vel_x_iner = dir_x * EJECT_SPEED
                        new_eject_ball.vel_y_iner = dir_y * EJECT_SPEED
                        
                        # 将吐出的球添加到食物列表，等待被吞噬
                        food_list.append(new_eject_ball)
                        # print("split")

    def handle_split(self, event):
        """处理分身"""
        # 获取鼠标位置和方向
        mouse_x, mouse_y = pygame.mouse.get_pos()     
        # --- 空格键：分身（分裂）---
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            new_split_balls = []
            for ball in self.balls:
                if ball.mass >= MIN_SPLIT_MASS and len(self.balls) < 16: # 限制分裂次数
                    dx = mouse_x - ball.screen_x
                    dy = mouse_y - ball.screen_y
                    
                    if dx == 0 and dy == 0:
                        return # 鼠标在中心，不执行操作

                    distance = math.sqrt(dx**2 + dy**2)
                    dir_x = dx / distance
                    dir_y = dy / distance
                    # 分裂后质量减半
                    split_mass = ball.mass / 2
                    ball.update_mass(-split_mass)
                    
                    # 创建一个新的分身球
                    new_ball = Ball(ball.x, ball.y, ball.radius, ball.color, ball_class="player")
                    new_ball.mass = split_mass
                    
                    # 赋予初始速度，使其飞出去
                    SPLIT_SPEED = 20
                    new_ball.vel_x_iner = dir_x * SPLIT_SPEED
                    new_ball.vel_y_iner = dir_y * SPLIT_SPEED
                    
                    new_split_balls.append(new_ball)

            self.balls.extend(new_split_balls)
            
            # 分身后进入冷却期
            self.fuse_cooldown = self.FUSE_COOLDOWN_TIME
    def draw_balls(self, screen, camera_x, camera_y, scale, mouse_pos):
        """绘制所有玩家球"""
        for ball in self.balls:
            # 绘制球
            ball.draw(screen, camera_x, camera_y, scale)
            # 绘制移动方向指示箭头
            center_x = SCREEN_WIDTH // 2
            center_y = SCREEN_HEIGHT // 2
            mouse_x, mouse_y = mouse_pos
            
            dx = mouse_x - ball.screen_x
            dy = mouse_y - ball.screen_y
            
            # 只有鼠标不在中心时才绘制箭头
            if abs(dx) > 1 or abs(dy) > 1:
                distance = math.sqrt(dx**2 + dy**2)
                
                # 箭头基点 (球中心)
                start_pos = (ball.screen_x, ball.screen_y)
                
                triangle_hight = 6 * ball.screen_radius / 15
                # 箭头终点 (指向鼠标方向，长度固定)
                INDICATOR_LENGTH = ball.screen_radius * 0.75 + triangle_hight
                dir_x = dx / distance
                dir_y = dy / distance
                end_pos = (ball.screen_x + dir_x * INDICATOR_LENGTH, ball.screen_y + dir_y * INDICATOR_LENGTH)
                
                # 绘制主线
                # pygame.draw.line(screen, BLACK, start_pos, end_pos, 3)
                
                # 绘制箭头尖端 (简单三角形)
                point_a = end_pos
                angle = math.atan2(dy, dx)
                # 偏移 135度和 -135度来计算两个侧边点
                angle_arrow = 1.0
                arrow_size = triangle_hight / math.cos(angle_arrow)
                point_b = (end_pos[0] - arrow_size * math.cos(angle - angle_arrow), 
                        end_pos[1] - arrow_size * math.sin(angle - angle_arrow)) # 0.785 约等于 45度
                point_c = (end_pos[0] - arrow_size * math.cos(angle + angle_arrow), 
                        end_pos[1] - arrow_size * math.sin(angle + angle_arrow))
                
                pygame.draw.polygon(screen, BLACK, [point_a, point_b, point_c])

    
    def is_alive(self):
        """检查玩家是否还活着"""
        return len(self.balls) > 0