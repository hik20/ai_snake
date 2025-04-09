import pygame, sys, random, math

# --- Sabitler ---
CELL_SIZE = 20
GRID_WIDTH = 20
GRID_HEIGHT = 20
SCREEN_WIDTH = CELL_SIZE * GRID_WIDTH
SCREEN_HEIGHT = CELL_SIZE * GRID_HEIGHT

# Renkler
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (40, 40, 40)

# Yön tanımları
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Pygame başlatma
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Yılan Oyunu: Akıllı Strateji")
clock = pygame.time.Clock()

# --- Yılan Sınıfı ---
class Snake:
    def __init__(self):
        self.positions = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
    
    def head_position(self):
        return self.positions[0]
    
    def move(self, direction):
        cur = self.head_position()
        new_head = (cur[0] + direction[0], cur[1] + direction[1])
        self.positions.insert(0, new_head)
        self.positions.pop()  # Kuyruk çıkarılır
    
    def grow(self):
        # Kuyruğu tekrar ekleyerek yılanı uzatır
        tail = self.positions[-1]
        self.positions.append(tail)
    
    def draw(self, surface):
        for pos in self.positions:
            rect = pygame.Rect(pos[0]*CELL_SIZE, pos[1]*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, GREEN, rect)
    
    def collides(self, pos):
        return pos in self.positions
    
    def check_self_collision(self):
        return self.head_position() in self.positions[1:]

# --- Yem Sınıfı ---
class Food:
    def __init__(self, snake_positions):
        self.position = self.random_position(snake_positions)
    
    def random_position(self, snake_positions):
        attempts = 0
        max_attempts = 50
        best_pos = None
        max_distance = 0
        
        while attempts < max_attempts:
            pos = (random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1))
            if pos not in snake_positions:
                # Yılanın başına olan mesafeyi hesapla
                head = snake_positions[0]
                distance = abs(pos[0] - head[0]) + abs(pos[1] - head[1])
                
                # En uzak konumu tut
                if distance > max_distance:
                    max_distance = distance
                    best_pos = pos
                    
            attempts += 1
        
        # En iyi konumu veya son geçerli konumu döndür
        if best_pos:
            return best_pos
        
        # Son çare - herhangi bir boş konum
        while True:
            pos = (random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1))
            if pos not in snake_positions:
                return pos
    
    def draw(self, surface):
        rect = pygame.Rect(self.position[0]*CELL_SIZE, self.position[1]*CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(surface, RED, rect)

# --- AI Kontrol Sınıfı ---
class AIController:
    def __init__(self):
        self.position_history = []  # Pozisyon geçmişi
        self.stuck_count = 0        # Sıkışma sayacı
        self.last_food_distance = 0 # Son yemek mesafesi
        self.same_distance_count = 0 # Aynı mesafede kalma sayacı
    
    def heuristic(self, a, b):
        # Manhattan mesafesi
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def get_neighbors(self, node, snake):
        neighbors = []
        for d in [UP, DOWN, LEFT, RIGHT]:
            next_node = (node[0] + d[0], node[1] + d[1])
            if 0 <= next_node[0] < GRID_WIDTH and 0 <= next_node[1] < GRID_HEIGHT:
                if next_node not in snake.positions:
                    neighbors.append(next_node)
        return neighbors
    
    def a_star(self, start, goal, snake):
        open_set = [start]
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}
        
        while open_set:
            current = min(open_set, key=lambda pos: f_score.get(pos, float('inf')))
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path
            
            open_set.remove(current)
            for neighbor in self.get_neighbors(current, snake):
                tentative_g = g_score[current] + 1
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, goal)
                    if neighbor not in open_set:
                        open_set.append(neighbor)
        return None  # Yol bulunamadı
    
    def bfs(self, start, snake):
        # BFS kullanarak güvenli yön belirleme (ilk güvenli adım)
        queue = [start]
        came_from = {start: None}
        while queue:
            current = queue.pop(0)
            for d in [UP, DOWN, LEFT, RIGHT]:
                next_node = (current[0] + d[0], current[1] + d[1])
                if 0 <= next_node[0] < GRID_WIDTH and 0 <= next_node[1] < GRID_HEIGHT:
                    if next_node not in snake.positions and next_node not in came_from:
                        came_from[next_node] = current
                        queue.append(next_node)
                        if current == start:
                            return d
        return None
    
    def choose_direction(self, snake, food):
        head = snake.head_position()
        
        # Yem ile mesafeyi hesapla (Manhattan)
        current_distance = abs(head[0] - food.position[0]) + abs(head[1] - food.position[1])
        
        # Mesafe değişmediyse ve yılan ilerlemiyorsa sayacı artır
        if hasattr(self, 'last_food_distance'):
            if current_distance >= self.last_food_distance:
                self.same_distance_count += 1
            else:
                self.same_distance_count = 0
        self.last_food_distance = current_distance
        
        # Pozisyon geçmişi takibi
        self.position_history.append(head)
        if len(self.position_history) > 100:  # Son 100 hareketi sakla
            self.position_history.pop(0)
            
        # Döngü algılama - önceki pozisyonlarda tekrar etme durumu
        head_repeat_count = self.position_history.count(head)
        
        # Eğer aynı pozisyon 3'ten fazla tekrar ediyorsa veya aynı mesafede 15+ hamle kaldıysa
        if head_repeat_count > 3 or self.same_distance_count > 15:
            print(f"Döngü algılandı! Tekrar: {head_repeat_count}, Aynı mesafe: {self.same_distance_count}")
            self.stuck_count += 1
            self.same_distance_count = 0
            
            # Tamamen rastgele bir hareket stratejisi uygula
            available_directions = []
            for d in [UP, DOWN, LEFT, RIGHT]:
                next_pos = (head[0] + d[0], head[1] + d[1])
                # Duvarları ve yılanın kendisini kontrol et
                if (0 <= next_pos[0] < GRID_WIDTH and 
                    0 <= next_pos[1] < GRID_HEIGHT and 
                    next_pos not in snake.positions):
                    available_directions.append(d)
            
            if available_directions:
                # Döngü uzun sürerse geçmiş pozisyonları sıfırla
                if self.stuck_count > 3:
                    self.position_history = []
                    self.stuck_count = 0
                    print("Tüm geçmiş temizlendi, tamamen yeni strateji!")
                
                # Bir önceki yönden farklı bir yön seç
                opposite = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}
                prev_dir = snake.direction
                
                # Mümkünse zıt yöne gitmeyi tercih et
                if opposite[prev_dir] in available_directions:
                    print("Zıt yöne dönüyorum!")
                    return opposite[prev_dir]
                else:
                    print("Rastgele yön seçiyorum!")
                    return random.choice(available_directions)
        
        # A* algoritması ile yem yolunu bul
        path = self.a_star(head, food.position, snake)
        if path and len(path) > 0:
            next_step = path[0]
            direction = (next_step[0] - head[0], next_step[1] - head[1])
            return direction
        
        # Eğer yem yolu bulunamazsa, "kaçış stratejisi" uygula
        # En uzun yolu tercih et
        max_space = 0
        best_direction = None
        
        for d in [UP, DOWN, LEFT, RIGHT]:
            next_pos = (head[0] + d[0], head[1] + d[1])
            if (0 <= next_pos[0] < GRID_WIDTH and 
                0 <= next_pos[1] < GRID_HEIGHT and 
                next_pos not in snake.positions):
                
                # Bu yönde ne kadar boş alan var?
                space = self.flood_fill(next_pos, snake)
                if space > max_space:
                    max_space = space
                    best_direction = d
        
        if best_direction:
            return best_direction
            
        # En son çare - BFS ile güvenli yön bul
        move = self.bfs(head, snake)
        if move:
            return move
            
        # Bu noktada hala yön bulunamadıysa, rastgele dene
        return random.choice([UP, DOWN, LEFT, RIGHT])
    
    def flood_fill(self, start, snake):
        visited = set([start])
        queue = [start]
        count = 0
        
        while queue:
            current = queue.pop(0)
            count += 1
            
            for d in [UP, DOWN, LEFT, RIGHT]:
                next_pos = (current[0] + d[0], current[1] + d[1])
                if (0 <= next_pos[0] < GRID_WIDTH and 
                    0 <= next_pos[1] < GRID_HEIGHT and 
                    next_pos not in snake.positions and
                    next_pos not in visited):
                    visited.add(next_pos)
                    queue.append(next_pos)
        
        return count

# --- Oyun Sınıfı ---
class SnakeGame:
    def __init__(self):
        self.snake = Snake()
        self.food = Food(self.snake.positions)
        self.ai = AIController()
        self.score = 0
        self.speed_multiplier = 1  
        self.base_speed = 10       
    
    def update(self):
        direction = self.ai.choose_direction(self.snake, self.food)
        self.snake.direction = direction
        head = self.snake.head_position()
        new_head = (head[0] + direction[0], head[1] + direction[1])
        
        # Duvar veya kendine çarpma kontrolü
        if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or 
            new_head[1] < 0 or new_head[1] >= GRID_HEIGHT or 
            new_head in self.snake.positions):
            print("Çarpışma! Oyun Bitti. Skor:", self.score)
            self.__init__()  # Oyunu sıfırla
            return
        
        self.snake.move(direction)
        
        # Yem yeme durumu
        if self.snake.head_position() == self.food.position:
            self.snake.grow()
            self.score += 10
            self.food = Food(self.snake.positions)
    
    def draw_grid(self, surface):
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(surface, GRAY, rect, 1)
    
    def draw(self, surface):
        surface.fill(BLACK)
        self.draw_grid(surface)
        self.snake.draw(surface)
        self.food.draw(surface)
        font = pygame.font.SysFont("Arial", 20)
        score_text = font.render(f"Skor: {self.score}", True, WHITE)
        surface.blit(score_text, (5, 5))
        
        # Hız göstergesi ekranı
        speed_text = font.render(f"Hız: {self.speed_multiplier}x (SPACE)", True, BLUE)
        surface.blit(speed_text, (SCREEN_WIDTH - 300, 5))
    
    def run(self):
        running = True
        while running:
            # Dinamik hız ayarı
            clock.tick(self.base_speed * self.speed_multiplier)  
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                # Hız değiştirme kontrolü - boşluk tuşu
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # Hız çarpanını değiştir (1x, 2x, 5x, 10x)
                        if self.speed_multiplier == 1:
                            self.speed_multiplier = 2
                        elif self.speed_multiplier == 2:
                            self.speed_multiplier = 5
                        elif self.speed_multiplier == 5:
                            self.speed_multiplier = 10
                        else:
                            self.speed_multiplier = 1
                        print(f"Oyun hızı: {self.speed_multiplier}x")
                        
            self.update()
            self.draw(screen)
            pygame.display.update()
        pygame.quit()
        sys.exit()

# --- Ana Fonksiyon ---
if __name__ == "__main__":
    game = SnakeGame()
    game.run()