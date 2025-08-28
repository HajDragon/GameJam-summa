#!/usr/bin/env python3

import pygame
import sys
import yaml
import logging
import time
import random
import math
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60
TILE_SIZE = 32

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)

# Game colors
WALL_COLOR = GRAY
FLOOR_COLOR = DARK_GRAY
PLAYER_COLOR = BLUE
ENEMY_COLOR = RED
HEALTH_COLOR = GREEN
DAMAGE_COLOR = RED

class Direction(Enum):
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"

class EnemyType(Enum):
    STICKFIGURE = "stickfigure"
    COW = "cow"
    RAMBO = "rambo"
    DRAGON = "dragon"
    BIG = "big"

class WeaponType(Enum):
    HIT_SQUARE = "hitSquare"
    HIT_LINE = "hitLine"
    HIT_WHIP = "hitWhip"
    BUCKLER = "buckler"
    CHARGE = "charge"
    SPITFIRE = "spitfire"

@dataclass
class Vector2:
    x: float
    y: float
    
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)
    
    def distance_to(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

@dataclass 
class Coordinates:
    x: int
    y: int

class Entity:
    def __init__(self):
        self.id = None
        self.active = True
        
class Player(Entity):
    def __init__(self, x: int, y: int):
        super().__init__()
        self.position = Vector2(x, y)
        self.health = 100
        self.max_health = 100
        self.speed = 200  # pixels per second
        self.direction = Direction.RIGHT
        self.is_attacking = False
        self.attack_timer = 0
        self.attack_duration = 0.3
        self.weapon_type = WeaponType.HIT_SQUARE
        self.damage = 25
        
    def update(self, dt: float):
        if self.is_attacking:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.is_attacking = False
    
    def move(self, dx: float, dy: float, dt: float):
        self.position.x += dx * self.speed * dt
        self.position.y += dy * self.speed * dt
        
        # Keep player on screen
        self.position.x = max(TILE_SIZE, min(SCREEN_WIDTH - TILE_SIZE, self.position.x))
        self.position.y = max(TILE_SIZE, min(SCREEN_HEIGHT - TILE_SIZE, self.position.y))
        
        # Update direction
        if dx > 0:
            self.direction = Direction.RIGHT
        elif dx < 0:
            self.direction = Direction.LEFT
    
    def attack(self):
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = self.attack_duration
    
    def take_damage(self, damage: int):
        self.health = max(0, self.health - damage)
    
    def heal(self, amount: int):
        self.health = min(self.max_health, self.health + amount)

class Enemy(Entity):
    def __init__(self, x: int, y: int, enemy_type: EnemyType):
        super().__init__()
        self.position = Vector2(x, y)
        self.enemy_type = enemy_type
        self.health = 50
        self.max_health = 50
        self.speed = 100
        self.direction = Direction.LEFT
        self.damage = 15
        self.attack_range = 50
        self.detection_range = 150
        self.state = "wander"  # wander, chase, attack, dying
        self.target_position = Vector2(x, y)
        self.wander_timer = 0
        self.attack_timer = 0
        self.dying_timer = 0
        
        # Configure based on enemy type
        self._configure_enemy_type()
    
    def _configure_enemy_type(self):
        if self.enemy_type == EnemyType.STICKFIGURE:
            self.health = self.max_health = 30
            self.speed = 120
            self.damage = 10
        elif self.enemy_type == EnemyType.COW:
            self.health = self.max_health = 80
            self.speed = 60
            self.damage = 20
        elif self.enemy_type == EnemyType.RAMBO:
            self.health = self.max_health = 60
            self.speed = 140
            self.damage = 25
        elif self.enemy_type == EnemyType.DRAGON:
            self.health = self.max_health = 120
            self.speed = 80
            self.damage = 35
        elif self.enemy_type == EnemyType.BIG:
            self.health = self.max_health = 150
            self.speed = 50
            self.damage = 40
    
    def update(self, dt: float, player: Player):
        if self.health <= 0:
            self.state = "dying"
            self.dying_timer += dt
            if self.dying_timer > 1.0:  # Death animation duration
                self.active = False
            return
        
        distance_to_player = self.position.distance_to(player.position)
        
        if self.state == "wander":
            self._update_wander(dt, player, distance_to_player)
        elif self.state == "chase":
            self._update_chase(dt, player, distance_to_player)
        elif self.state == "attack":
            self._update_attack(dt, player, distance_to_player)
    
    def _update_wander(self, dt: float, player: Player, distance_to_player: float):
        # Check if player is in detection range
        if distance_to_player < self.detection_range:
            self.state = "chase"
            return
        
        # Wander behavior
        self.wander_timer += dt
        if self.wander_timer > 2.0:  # Change direction every 2 seconds
            self.wander_timer = 0
            angle = random.uniform(0, 2 * math.pi)
            self.target_position = Vector2(
                self.position.x + math.cos(angle) * 100,
                self.position.y + math.sin(angle) * 100
            )
        
        # Move towards target
        self._move_towards_target(dt)
    
    def _update_chase(self, dt: float, player: Player, distance_to_player: float):
        # Check if player is too far
        if distance_to_player > self.detection_range * 1.5:
            self.state = "wander"
            return
        
        # Check if in attack range
        if distance_to_player < self.attack_range:
            self.state = "attack"
            self.attack_timer = 0
            return
        
        # Chase player
        self.target_position = Vector2(player.position.x, player.position.y)
        self._move_towards_target(dt)
    
    def _update_attack(self, dt: float, player: Player, distance_to_player: float):
        self.attack_timer += dt
        
        # Attack duration
        if self.attack_timer > 1.0:
            # Deal damage to player if still in range
            if distance_to_player < self.attack_range:
                player.take_damage(self.damage)
            
            # Go back to chase
            self.state = "chase"
        
        # If player moves away, go back to chase
        if distance_to_player > self.attack_range * 1.5:
            self.state = "chase"
    
    def _move_towards_target(self, dt: float):
        dx = self.target_position.x - self.position.x
        dy = self.target_position.y - self.position.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 5:  # Don't jitter when very close
            dx /= distance
            dy /= distance
            
            self.position.x += dx * self.speed * dt
            self.position.y += dy * self.speed * dt
            
            # Update direction
            if dx > 0:
                self.direction = Direction.RIGHT
            elif dx < 0:
                self.direction = Direction.LEFT
            
            # Keep enemy on screen
            self.position.x = max(TILE_SIZE, min(SCREEN_WIDTH - TILE_SIZE, self.position.x))
            self.position.y = max(TILE_SIZE, min(SCREEN_HEIGHT - TILE_SIZE, self.position.y))
    
    def take_damage(self, damage: int):
        self.health = max(0, self.health - damage)

class GameWorld:
    def __init__(self):
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.enemies: List[Enemy] = []
        self.enemy_spawn_timer = 0
        self.enemy_spawn_interval = 3.0  # Spawn enemy every 3 seconds
        self.max_enemies = 10
        self.score = 0
        
    def update(self, dt: float):
        # Update player
        self.player.update(dt)
        
        # Update enemies
        for enemy in self.enemies[:]:  # Use slice to avoid modification during iteration
            enemy.update(dt, self.player)
            if not enemy.active:
                self.enemies.remove(enemy)
                self.score += 100  # Points for killing enemy
        
        # Spawn new enemies
        self.enemy_spawn_timer += dt
        if (self.enemy_spawn_timer > self.enemy_spawn_interval and 
            len(self.enemies) < self.max_enemies):
            self._spawn_enemy()
            self.enemy_spawn_timer = 0
        
        # Check player attacks
        if self.player.is_attacking:
            self._check_player_attacks()
    
    def _spawn_enemy(self):
        # Spawn enemy at random edge of screen
        edge = random.choice(['left', 'right', 'top', 'bottom'])
        
        if edge == 'left':
            x, y = 0, random.randint(TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE)
        elif edge == 'right':
            x, y = SCREEN_WIDTH, random.randint(TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE)
        elif edge == 'top':
            x, y = random.randint(TILE_SIZE, SCREEN_WIDTH - TILE_SIZE), 0
        else:  # bottom
            x, y = random.randint(TILE_SIZE, SCREEN_WIDTH - TILE_SIZE), SCREEN_HEIGHT
        
        enemy_type = random.choice(list(EnemyType))
        enemy = Enemy(x, y, enemy_type)
        self.enemies.append(enemy)
    
    def _check_player_attacks(self):
        attack_range = 80  # Player attack range
        
        for enemy in self.enemies:
            distance = self.player.position.distance_to(enemy.position)
            if distance < attack_range and enemy.health > 0:
                enemy.take_damage(self.player.damage)

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
    
    def render(self, world: GameWorld):
        # Clear screen
        self.screen.fill(FLOOR_COLOR)
        
        # Draw walls (simple border)
        pygame.draw.rect(self.screen, WALL_COLOR, (0, 0, SCREEN_WIDTH, TILE_SIZE))
        pygame.draw.rect(self.screen, WALL_COLOR, (0, 0, TILE_SIZE, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, WALL_COLOR, (SCREEN_WIDTH - TILE_SIZE, 0, TILE_SIZE, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, WALL_COLOR, (0, SCREEN_HEIGHT - TILE_SIZE, SCREEN_WIDTH, TILE_SIZE))
        
        # Draw player
        self._draw_player(world.player)
        
        # Draw enemies
        for enemy in world.enemies:
            if enemy.active:
                self._draw_enemy(enemy)
        
        # Draw UI
        self._draw_ui(world)
    
    def _draw_player(self, player: Player):
        # Draw player as a blue rectangle with direction indicator
        size = TILE_SIZE
        rect = pygame.Rect(player.position.x - size//2, player.position.y - size//2, size, size)
        
        color = PLAYER_COLOR
        if player.is_attacking:
            color = YELLOW  # Change color when attacking
        
        pygame.draw.rect(self.screen, color, rect)
        
        # Draw direction indicator
        if player.direction == Direction.RIGHT:
            pygame.draw.polygon(self.screen, WHITE, [
                (player.position.x + size//4, player.position.y - size//4),
                (player.position.x + size//2, player.position.y),
                (player.position.x + size//4, player.position.y + size//4)
            ])
        else:
            pygame.draw.polygon(self.screen, WHITE, [
                (player.position.x - size//4, player.position.y - size//4),
                (player.position.x - size//2, player.position.y),
                (player.position.x - size//4, player.position.y + size//4)
            ])
        
        # Draw attack range when attacking
        if player.is_attacking:
            pygame.draw.circle(self.screen, (255, 255, 0, 50), 
                             (int(player.position.x), int(player.position.y)), 80, 2)
    
    def _draw_enemy(self, enemy: Enemy):
        # Different colors/shapes for different enemy types
        size = TILE_SIZE
        rect = pygame.Rect(enemy.position.x - size//2, enemy.position.y - size//2, size, size)
        
        if enemy.state == "dying":
            color = DARK_GRAY
        elif enemy.enemy_type == EnemyType.STICKFIGURE:
            color = RED
        elif enemy.enemy_type == EnemyType.COW:
            color = (139, 69, 19)  # Brown
        elif enemy.enemy_type == EnemyType.RAMBO:
            color = (255, 0, 255)  # Magenta
        elif enemy.enemy_type == EnemyType.DRAGON:
            color = (0, 255, 0)  # Green
        elif enemy.enemy_type == EnemyType.BIG:
            color = (255, 165, 0)  # Orange
            size = int(TILE_SIZE * 1.5)  # Bigger size
            rect = pygame.Rect(enemy.position.x - size//2, enemy.position.y - size//2, size, size)
        else:
            color = RED
        
        pygame.draw.rect(self.screen, color, rect)
        
        # Draw health bar
        if enemy.health < enemy.max_health and enemy.state != "dying":
            bar_width = size
            bar_height = 4
            bar_x = enemy.position.x - bar_width // 2
            bar_y = enemy.position.y - size // 2 - 8
            
            # Background
            pygame.draw.rect(self.screen, RED, (bar_x, bar_y, bar_width, bar_height))
            # Health
            health_width = int(bar_width * (enemy.health / enemy.max_health))
            pygame.draw.rect(self.screen, GREEN, (bar_x, bar_y, health_width, bar_height))
        
        # Draw state indicator
        if enemy.state == "attack":
            pygame.draw.circle(self.screen, RED, 
                             (int(enemy.position.x), int(enemy.position.y)), 
                             enemy.attack_range, 2)
    
    def _draw_ui(self, world: GameWorld):
        # Health bar
        health_text = self.font.render(f"Health: {world.player.health}/{world.player.max_health}", 
                                     True, WHITE)
        self.screen.blit(health_text, (10, 10))
        
        # Health bar visual
        bar_width = 200
        bar_height = 20
        bar_x = 10
        bar_y = 50
        
        # Background
        pygame.draw.rect(self.screen, RED, (bar_x, bar_y, bar_width, bar_height))
        # Health
        health_width = int(bar_width * (world.player.health / world.player.max_health))
        pygame.draw.rect(self.screen, GREEN, (bar_x, bar_y, health_width, bar_height))
        
        # Score
        score_text = self.font.render(f"Score: {world.score}", True, WHITE)
        self.screen.blit(score_text, (10, 80))
        
        # Enemy count
        enemy_text = self.font.render(f"Enemies: {len(world.enemies)}", True, WHITE)
        self.screen.blit(enemy_text, (10, 110))
        
        # Controls
        controls = [
            "WASD: Move",
            "SPACE: Attack",
            "F: Heal (costs 50 points)",
            "ESC: Quit"
        ]
        
        for i, control in enumerate(controls):
            text = self.small_font.render(control, True, WHITE)
            self.screen.blit(text, (SCREEN_WIDTH - 250, 10 + i * 25))

class InputHandler:
    def __init__(self):
        self.keys_pressed = set()
    
    def handle_events(self, world: GameWorld) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE:
                    world.player.attack()
                elif event.key == pygame.K_f:
                    # Heal (costs points)
                    if world.score >= 50:
                        world.score -= 50
                        world.player.heal(25)
        
        # Handle continuous key presses
        keys = pygame.key.get_pressed()
        dx = dy = 0
        
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1
        
        return True, dx, dy

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("N Key Rollover - Pygame Edition")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.world = GameWorld()
        self.renderer = Renderer(self.screen)
        self.input_handler = InputHandler()
    
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            
            # Handle input
            result = self.input_handler.handle_events(self.world)
            if isinstance(result, tuple):
                self.running, dx, dy = result
                if self.running:
                    self.world.player.move(dx, dy, dt)
            else:
                self.running = result
            
            # Check game over
            if self.world.player.health <= 0:
                self._show_game_over()
                break
            
            # Update world
            self.world.update(dt)
            
            # Render
            self.renderer.render(self.world)
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()
    
    def _show_game_over(self):
        # Simple game over screen
        font = pygame.font.Font(None, 72)
        game_over_text = font.render("GAME OVER", True, RED)
        score_text = font.render(f"Final Score: {self.world.score}", True, WHITE)
        
        self.screen.fill(BLACK)
        
        # Center the text
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
        
        self.screen.blit(game_over_text, game_over_rect)
        self.screen.blit(score_text, score_rect)
        pygame.display.flip()
        
        # Wait for key press
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    waiting = False

def main():
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"Error running game: {e}")
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()
