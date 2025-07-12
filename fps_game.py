import pyxel
import math
import random

class FPSGame:
    def __init__(self):
        pyxel.init(160, 120, title="FPS Zombie Game")
        pyxel.mouse(True)
        
        # プレイヤー
        self.player_x = 2.0
        self.player_y = 7.0
        self.player_angle = math.pi  # 180度（ゴール方向）
        
        # マップ（1=壁、0=空間）
        self.map_width = 20
        self.map_height = 15
        self.world_map = [[1 if x == 0 or x == 19 or y == 0 or y == 14 or (y < 4 or y > 10) else 0 
                          for x in range(self.map_width)] for y in range(self.map_height)]
        
        # 出口
        for y in range(4, 11):
            self.world_map[y][19] = 0
        
        # ゾンビ
        self.zombies = []
        for i in range(5):
            self.zombies.append({
                'x': 5.0 + i * 3,
                'y': 7.5,
                'hp': 3,
                'alive': True
            })
        
        # ゲーム状態
        self.game_clear = False
        self.last_mouse_x = pyxel.mouse_x
        self.step_timer = 0
        self.explosions = []
        
        # サウンド設定
        pyxel.sounds[0].set("c1", "n", "2", "f", 5)  # 歩行音
        pyxel.sounds[1].set("c2e1", "n", "31", "f", 8)  # 銃声
        pyxel.sounds[2].set("c4", "t", "1", "f", 3)  # 移動音
        pyxel.sounds[3].set("e3", "n", "3", "f", 5)  # ヒット音
        pyxel.sounds[4].set("c3e3g3c4", "t", "7654", "f", 20)  # クリアジングル
        
        pyxel.run(self.update, self.draw)
    
    def update(self):
        if self.game_clear:
            if pyxel.btnp(pyxel.KEY_R):
                self.__init__()
            return
        
        # マウス視点操作
        mouse_dx = pyxel.mouse_x - self.last_mouse_x
        self.player_angle += mouse_dx * 0.08
        self.last_mouse_x = pyxel.mouse_x
        
        # WASD移動
        speed = 0.2
        new_x, new_y = self.player_x, self.player_y
        moved = False
        
        if pyxel.btn(pyxel.KEY_W):
            new_x += math.cos(self.player_angle) * speed
            new_y += math.sin(self.player_angle) * speed
            moved = True
        if pyxel.btn(pyxel.KEY_S):
            new_x -= math.cos(self.player_angle) * speed
            new_y -= math.sin(self.player_angle) * speed
            moved = True
        if pyxel.btn(pyxel.KEY_A):
            new_x += math.cos(self.player_angle - math.pi/2) * speed
            new_y += math.sin(self.player_angle - math.pi/2) * speed
            moved = True
        if pyxel.btn(pyxel.KEY_D):
            new_x += math.cos(self.player_angle + math.pi/2) * speed
            new_y += math.sin(self.player_angle + math.pi/2) * speed
            moved = True
        
        # 壁との衝突判定
        if 0 < new_x < self.map_width and 0 < new_y < self.map_height:
            if self.world_map[int(new_y)][int(new_x)] == 0:
                old_x, old_y = self.player_x, self.player_y
                self.player_x, self.player_y = new_x, new_y
                
                # 移動音（グリッド単位で移動した時）
                if moved and (int(old_x) != int(new_x) or int(old_y) != int(new_y)):
                    pyxel.play(2, 2)
                
                # 歩行音
                if moved:
                    self.step_timer += 1
                    if self.step_timer >= 20:
                        pyxel.play(0, 0)
                        self.step_timer = 0
        
        # 射撃
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            pyxel.play(1, 1)  # 銃声
            
            # レイキャスティングで最初に当たるゾンビを攻撃
            hit_zombie = False
            for zombie in self.zombies:
                if zombie['alive']:
                    # プレイヤーからゾンビへのベクトル
                    dx = zombie['x'] - self.player_x
                    dy = zombie['y'] - self.player_y
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    # プレイヤーの向きとゾンビの方向の内積で前方判定
                    forward_x = math.cos(self.player_angle)
                    forward_y = math.sin(self.player_angle)
                    dot_product = (dx * forward_x + dy * forward_y) / distance
                    
                    # 前方かつ照準内かつ距離10以内なら攻撃
                    if dot_product > 0.8 and distance < 10:
                        angle_to_zombie = math.atan2(dy, dx)
                        angle_diff = abs(angle_to_zombie - self.player_angle)
                        if angle_diff > math.pi:
                            angle_diff = 2 * math.pi - angle_diff
                        
                        if angle_diff < 0.3:
                            zombie['hp'] -= 1
                            pyxel.play(2, 3)  # ヒット音
                            hit_zombie = True
                            if zombie['hp'] <= 0:
                                zombie['alive'] = False
                                # 爆発エフェクト追加
                                self.explosions.append({
                                    'x': zombie['x'],
                                    'y': zombie['y'],
                                    'timer': 20
                                })
                            break
        
        # 爆発エフェクト更新
        for explosion in self.explosions[:]:
            explosion['timer'] -= 1
            if explosion['timer'] <= 0:
                self.explosions.remove(explosion)
        
        # クリア判定
        if self.player_x > 18 and all(not z['alive'] for z in self.zombies):
            if not self.game_clear:
                pyxel.play(3, 4)  # クリアジングル
            self.game_clear = True
        elif self.player_x > 18 and any(z['alive'] for z in self.zombies):
            # ゾンビが残っている場合の警告
            pass
    
    def cast_ray(self, angle):
        x, y = self.player_x, self.player_y
        dx, dy = math.cos(angle), math.sin(angle)
        
        for i in range(100):
            x += dx * 0.1
            y += dy * 0.1
            
            if x < 0 or x >= self.map_width or y < 0 or y >= self.map_height:
                return i * 0.1, x, y
            if self.world_map[int(y)][int(x)] == 1:
                return i * 0.1, x, y
        return 10, x, y
    
    def draw(self):
        pyxel.cls(1)
        
        # 一人称視点レンダリング
        fov = math.pi / 3
        for x in range(160):
            ray_angle = self.player_angle - fov/2 + (x / 160) * fov
            distance, hit_x, hit_y = self.cast_ray(ray_angle)
            
            # 壁の高さ計算
            wall_height = min(60, 300 / max(distance, 0.1))
            wall_top = 60 - wall_height // 2
            wall_bottom = 60 + wall_height // 2
            
            # 天井（格子柄）
            for y in range(0, int(wall_top)):
                # 天井の格子パターン
                grid_x = int(self.player_x * 2 + x * 0.1) % 8
                grid_y = int(self.player_y * 2 + y * 0.2) % 8
                if grid_x < 4 and grid_y < 4:
                    color = 5
                else:
                    color = 6
                pyxel.pset(x, y, color)
            
            # 壁のテクスチャ
            base_color = 5 if distance < 5 else 13
            texture_x = int((hit_x + hit_y) * 4) % 4
            
            for y in range(int(wall_top), int(wall_bottom)):
                if (x + y) % 8 < 4 and texture_x % 2 == 0:
                    color = base_color + 1 if base_color < 15 else base_color - 1
                else:
                    color = base_color
                pyxel.pset(x, y, color)
            
            # 床（細かい格子柄）
            for y in range(int(wall_bottom), 120):
                # 床の細かい格子パターン
                distance_to_floor = (120 - y) * 0.5
                grid_x = int(self.player_x * 4 + x * 0.2 + distance_to_floor) % 4
                grid_y = int(self.player_y * 4 + distance_to_floor) % 4
                if grid_x < 2 and grid_y < 2:
                    color = 2
                else:
                    color = 3
                pyxel.pset(x, y, color)
        
        # ゾンビ描画
        for zombie in self.zombies:
            if zombie['alive']:
                dx = zombie['x'] - self.player_x
                dy = zombie['y'] - self.player_y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < 10:
                    angle_to_zombie = math.atan2(dy, dx)
                    angle_diff = angle_to_zombie - self.player_angle
                    
                    # 角度を-π〜πに正規化
                    while angle_diff > math.pi:
                        angle_diff -= 2 * math.pi
                    while angle_diff < -math.pi:
                        angle_diff += 2 * math.pi
                    
                    # 視野内なら描画
                    if abs(angle_diff) < math.pi/3:
                        screen_x = 80 + angle_diff * 160 / (math.pi/3)
                        zombie_size = max(8, 40 / distance)
                        color = 8 if zombie['hp'] == 3 else 9 if zombie['hp'] == 2 else 10
                        
                        # ゾンビの体
                        body_width = max(4, zombie_size // 2)
                        body_height = max(6, zombie_size)
                        pyxel.rect(screen_x - body_width//2, 60 - body_height//2, body_width, body_height, color)
                        
                        # 頭
                        head_size = max(2, zombie_size // 4)
                        pyxel.rect(screen_x - head_size//2, 60 - body_height//2 - head_size, head_size, head_size, color)
                        
                        # 手（バンザイポーズ）
                        arm_size = max(1, zombie_size // 6)
                        # 左手
                        pyxel.rect(screen_x - body_width//2 - arm_size, 60 - body_height//4, arm_size, arm_size*2, color)
                        # 右手
                        pyxel.rect(screen_x + body_width//2, 60 - body_height//4, arm_size, arm_size*2, color)
        
        # 爆発エフェクト描画
        for explosion in self.explosions:
            dx = explosion['x'] - self.player_x
            dy = explosion['y'] - self.player_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < 10:
                angle_to_explosion = math.atan2(dy, dx)
                angle_diff = angle_to_explosion - self.player_angle
                
                while angle_diff > math.pi:
                    angle_diff -= 2 * math.pi
                while angle_diff < -math.pi:
                    angle_diff += 2 * math.pi
                
                if abs(angle_diff) < math.pi/3:
                    screen_x = 80 + angle_diff * 160 / (math.pi/3)
                    explosion_size = max(10, 50 / distance)
                    
                    # 爆発パーティクル
                    for i in range(8):
                        px = screen_x + random.randint(-explosion_size//2, explosion_size//2)
                        py = 60 + random.randint(-explosion_size//2, explosion_size//2)
                        color = random.choice([8, 9, 10, 7])
                        pyxel.rect(px, py, 2, 2, color)
        
        # クロスヘア
        pyxel.line(78, 60, 82, 60, 7)
        pyxel.line(80, 58, 80, 62, 7)
        
        # ミニマップ（右上）
        map_scale = 2
        map_offset_x = 120
        map_offset_y = 5
        
        # マップ背景
        pyxel.rect(map_offset_x - 1, map_offset_y - 1, self.map_width * map_scale + 2, self.map_height * map_scale + 2, 0)
        
        # マップ描画
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.world_map[y][x] == 1:
                    pyxel.rect(map_offset_x + x * map_scale, map_offset_y + y * map_scale, map_scale, map_scale, 5)
                else:
                    pyxel.rect(map_offset_x + x * map_scale, map_offset_y + y * map_scale, map_scale, map_scale, 1)
        
        # ゴールエリア
        for y in range(4, 11):
            pyxel.rect(map_offset_x + 19 * map_scale, map_offset_y + y * map_scale, map_scale, map_scale, 11)
        
        # ゾンビ
        for zombie in self.zombies:
            if zombie['alive']:
                zx = int(zombie['x'] * map_scale)
                zy = int(zombie['y'] * map_scale)
                color = 8 if zombie['hp'] == 3 else 9 if zombie['hp'] == 2 else 10
                pyxel.rect(map_offset_x + zx - 1, map_offset_y + zy - 1, 2, 2, color)
        
        # プレイヤー
        px = int(self.player_x * map_scale)
        py = int(self.player_y * map_scale)
        pyxel.rect(map_offset_x + px - 1, map_offset_y + py - 1, 3, 3, 12)
        
        # プレイヤーの向き
        end_x = px + int(math.cos(self.player_angle) * 4)
        end_y = py + int(math.sin(self.player_angle) * 4)
        pyxel.line(map_offset_x + px, map_offset_y + py, map_offset_x + end_x, map_offset_y + end_y, 7)
        
        # UI
        alive_zombies = sum(1 for z in self.zombies if z['alive'])
        pyxel.text(5, 5, f"Zombies: {alive_zombies}", 7)
        pyxel.text(5, 15, "WASD:Move Mouse:Look Click:Shoot", 7)
        pyxel.text(5, 25, "Goal: Kill all zombies, reach EXIT", 7)
        pyxel.text(5, 35, f"Pos: {self.player_x:.1f},{self.player_y:.1f}", 7)
        pyxel.text(110, 50, "MAP", 7)
        
        # ゴール方向の矢印
        if alive_zombies == 0:
            pyxel.text(60, 110, ">>> EXIT >>>", 11)
        
        if self.game_clear:
            # 背景を暗くして文字を見やすく
            pyxel.rect(30, 45, 100, 30, 0)
            pyxel.rect(32, 47, 96, 26, 1)
            
            # 大きな文字で表示
            pyxel.text(40, 50, "ESCAPED!", 11)
            pyxel.text(35, 60, "Press R to restart", 7)

FPSGame()