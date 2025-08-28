#!/usr/bin/env python3

import pygame
import sys
import yaml
import logging
import time
import random
import math
import os
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

# Initialize Pygame
pygame.init()
pygame.mixer.init()

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
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
BROWN = (139, 69, 19)
MAGENTA = (255, 0, 255)

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

class ParticleType(Enum):
    DAMAGE = "damage"
    HEAL = "heal"
    DEATH = "death"
    ATTACK = "attack"

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
    
    def normalize(self):
        magnitude = math.sqrt(self.x**2 + self.y**2)
        if magnitude > 0:
            return Vector2(self.x / magnitude, self.y / magnitude)
        return Vector2(0, 0)

class Particle:
    def __init__(self, x: float, y: float, particle_type: ParticleType):
        self.position = Vector2(x, y)
        self.velocity = Vector2(
            random.uniform(-100, 100),
            random.uniform(-100, 100)
        )
        self.particle_type = particle_type
        self.lifetime = 1.0
        self.max_lifetime = 1.0
        self.size = random.uniform(2, 6)
        
        if particle_type == ParticleType.DAMAGE:
            self.color = RED
        elif particle_type == ParticleType.HEAL:
            self.color = GREEN
        elif particle_type == ParticleType.DEATH:
            self.color = DARK_GRAY
        elif particle_type == ParticleType.ATTACK:
            self.color = YELLOW
        else:
            self.color = WHITE
    
    def update(self, dt: float) -> bool:
        self.position = self.position + self.velocity * dt
        self.velocity = self.velocity * 0.95  # Drag
        self.lifetime -= dt
        return self.lifetime > 0
    
    def render(self, screen):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        color = (*self.color, alpha)
        size = int(self.size * (self.lifetime / self.max_lifetime))
        if size > 0:
            # Create a surface with per-pixel alpha
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (size, size), size)
            screen.blit(surf, (self.position.x - size, self.position.y - size))

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.music_volume = 0.7
        self.sfx_volume = 0.5
        
        # Generate simple sounds programmatically
        self._generate_sounds()
    
    def _generate_sounds(self):
        """Generate simple sounds since we don't have sound files"""
        # Create attack sound
        self.sounds['attack'] = self._generate_beep(440, 0.1)
        self.sounds['damage'] = self._generate_beep(220, 0.2)
        self.sounds['heal'] = self._generate_beep(660, 0.3)
        self.sounds['enemy_death'] = self._generate_beep(150, 0.4)
    
    def _generate_beep(self, frequency: int, duration: float):
        """Generate a simple beep sound"""
        import numpy as np
        sample_rate = 22050
        frames = int(duration * sample_rate)
        arr = np.zeros((frames, 2))
        for i in range(frames):
            wave = 4096 * np.sin(2 * np.pi * frequency * i / sample_rate)
            arr[i] = [wave, wave]
        sound = pygame.sndarray.make_sound(arr.astype(np.int16))
        sound.set_volume(self.sfx_volume)
        return sound
    
    def play_sound(self, sound_name: str):
        if sound_name in self.sounds:
            self.sounds[sound_name].play()

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
        self.last_position = Vector2(x, y)
        self.invulnerable_timer = 0
        self.invulnerable_duration = 1.0  # 1 second of invulnerability after taking damage
        
    def update(self, dt: float):
        if self.is_attacking:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.is_attacking = False
        
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= dt
        
        self.last_position = Vector2(self.position.x, self.position.y)
    
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
    
    def attack(self) -> bool:
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = self.attack_duration
            return True
        return False
    
    def take_damage(self, damage: int) -> bool:
        if self.invulnerable_timer <= 0:
            self.health = max(0, self.health - damage)
            self.invulnerable_timer = self.invulnerable_duration
            return True
        return False
    
    def heal(self, amount: int):
        self.health = min(self.max_health, self.health + amount)
    
    def is_invulnerable(self) -> bool:
        return self.invulnerable_timer > 0

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
        self.last_attack_time = 0
        self.attack_cooldown = 1.5
        self.hit_timer = 0  # For hit effect
        
        # Configure based on enemy type
        self._configure_enemy_type()
    
    def _configure_enemy_type(self):
        if self.enemy_type == EnemyType.STICKFIGURE:
            self.health = self.max_health = 30
            self.speed = 120
            self.damage = 10
            self.attack_cooldown = 1.0
        elif self.enemy_type == EnemyType.COW:
            self.health = self.max_health = 80
            self.speed = 60
            self.damage = 20
            self.attack_cooldown = 2.0
        elif self.enemy_type == EnemyType.RAMBO:
            self.health = self.max_health = 60
            self.speed = 140
            self.damage = 25
            self.attack_cooldown = 1.2
        elif self.enemy_type == EnemyType.DRAGON:
            self.health = self.max_health = 120
            self.speed = 80
            self.damage = 35
            self.attack_cooldown = 1.8
        elif self.enemy_type == EnemyType.BIG:
            self.health = self.max_health = 150
            self.speed = 50
            self.damage = 40
            self.attack_cooldown = 2.5
    
    def update(self, dt: float, player: 'Player', current_time: float):
        if self.hit_timer > 0:
            self.hit_timer -= dt
            
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
            self._update_attack(dt, player, distance_to_player, current_time)
    
    def _update_wander(self, dt: float, player: 'Player', distance_to_player: float):
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
    
    def _update_chase(self, dt: float, player: 'Player', distance_to_player: float):
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
    
    def _update_attack(self, dt: float, player: 'Player', distance_to_player: float, current_time: float):
        self.attack_timer += dt
        
        # Attack duration
        if self.attack_timer > 0.5:  # Wind-up time
            # Deal damage to player if still in range and cooldown is ready
            if (distance_to_player < self.attack_range and 
                current_time - self.last_attack_time > self.attack_cooldown):
                if player.take_damage(self.damage):
                    self.last_attack_time = current_time
            
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
        self.hit_timer = 0.2  # Hit effect duration

class GameWorld:
    def __init__(self):
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.enemies: List[Enemy] = []
        self.particles: List[Particle] = []
        self.enemy_spawn_timer = 0
        self.enemy_spawn_interval = 3.0  # Spawn enemy every 3 seconds
        self.max_enemies = 10
        self.score = 0
        self.game_time = 0
        self.sound_manager = SoundManager()
        
    def update(self, dt: float):
        self.game_time += dt
        
        # Update player
        self.player.update(dt)
        
        # Update particles
        self.particles = [p for p in self.particles if p.update(dt)]
        
        # Update enemies
        for enemy in self.enemies[:]:  # Use slice to avoid modification during iteration
            enemy.update(dt, self.player, self.game_time)
            if not enemy.active:
                self.enemies.remove(enemy)
                self.score += 100  # Points for killing enemy
                self.sound_manager.play_sound('enemy_death')
                # Add death particles
                self._add_particles(enemy.position.x, enemy.position.y, ParticleType.DEATH)
        
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
                old_health = enemy.health
                enemy.take_damage(self.player.damage)
                if enemy.health < old_health:  # Damage was dealt
                    self.sound_manager.play_sound('damage')
                    self._add_particles(enemy.position.x, enemy.position.y, ParticleType.DAMAGE)
    
    def _add_particles(self, x: float, y: float, particle_type: ParticleType):
        for _ in range(5):
            particle = Particle(x, y, particle_type)
            self.particles.append(particle)
    
    def heal_player(self, cost: int = 50, heal_amount: int = 25):
        if self.score >= cost and self.player.health < self.player.max_health:
            self.score -= cost
            self.player.heal(heal_amount)
            self.sound_manager.play_sound('heal')
            self._add_particles(self.player.position.x, self.player.position.y, ParticleType.HEAL)
            return True
        return False

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 48)
    
    def render(self, world: GameWorld):
        # Clear screen with gradient effect
        self._draw_background()
        
        # Draw walls
        self._draw_walls()
        
        # Draw particles (behind entities)
        for particle in world.particles:
            particle.render(self.screen)
        
        # Draw player
        self._draw_player(world.player)
        
        # Draw enemies
        for enemy in world.enemies:
            if enemy.active:
                self._draw_enemy(enemy)
        
        # Draw UI
        self._draw_ui(world)
    
    def _draw_background(self):
        # Create a simple gradient background
        for y in range(SCREEN_HEIGHT):
            color_value = int(32 + (y / SCREEN_HEIGHT) * 32)  # Gradient from dark to slightly lighter
            color = (color_value, color_value, color_value + 10)
            pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))
    
    def _draw_walls(self):
        # Draw walls with some texture
        wall_thickness = TILE_SIZE
        
        # Top wall
        for x in range(0, SCREEN_WIDTH, wall_thickness):
            color_offset = (x // wall_thickness) % 2 * 20
            color = (WALL_COLOR[0] + color_offset, WALL_COLOR[1] + color_offset, WALL_COLOR[2] + color_offset)
            pygame.draw.rect(self.screen, color, (x, 0, wall_thickness, wall_thickness))
        
        # Bottom wall
        for x in range(0, SCREEN_WIDTH, wall_thickness):
            color_offset = (x // wall_thickness) % 2 * 20
            color = (WALL_COLOR[0] + color_offset, WALL_COLOR[1] + color_offset, WALL_COLOR[2] + color_offset)
            pygame.draw.rect(self.screen, color, (x, SCREEN_HEIGHT - wall_thickness, wall_thickness, wall_thickness))
        
        # Left wall
        for y in range(0, SCREEN_HEIGHT, wall_thickness):
            color_offset = (y // wall_thickness) % 2 * 20
            color = (WALL_COLOR[0] + color_offset, WALL_COLOR[1] + color_offset, WALL_COLOR[2] + color_offset)
            pygame.draw.rect(self.screen, color, (0, y, wall_thickness, wall_thickness))
        
        # Right wall
        for y in range(0, SCREEN_HEIGHT, wall_thickness):
            color_offset = (y // wall_thickness) % 2 * 20
            color = (WALL_COLOR[0] + color_offset, WALL_COLOR[1] + color_offset, WALL_COLOR[2] + color_offset)
            pygame.draw.rect(self.screen, color, (SCREEN_WIDTH - wall_thickness, y, wall_thickness, wall_thickness))
    
    def _draw_player(self, player: Player):
        # Draw player as a blue rectangle with direction indicator
        size = TILE_SIZE
        rect = pygame.Rect(player.position.x - size//2, player.position.y - size//2, size, size)
        
        color = PLAYER_COLOR
        if player.is_attacking:
            color = YELLOW  # Change color when attacking
        elif player.is_invulnerable():
            # Flicker effect when invulnerable
            if int(pygame.time.get_ticks() / 100) % 2:
                color = (PLAYER_COLOR[0], PLAYER_COLOR[1], PLAYER_COLOR[2], 128)
        
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, WHITE, rect, 2)  # Border
        
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
            pygame.draw.circle(self.screen, YELLOW, 
                             (int(player.position.x), int(player.position.y)), 80, 3)
    
    def _draw_enemy(self, enemy: Enemy):
        # Different colors/shapes for different enemy types
        size = TILE_SIZE
        
        if enemy.enemy_type == EnemyType.BIG:
            size = int(TILE_SIZE * 1.5)  # Bigger size
        
        rect = pygame.Rect(enemy.position.x - size//2, enemy.position.y - size//2, size, size)
        
        # Base color
        if enemy.state == "dying":
            color = DARK_GRAY
        elif enemy.enemy_type == EnemyType.STICKFIGURE:
            color = RED
        elif enemy.enemy_type == EnemyType.COW:
            color = BROWN
        elif enemy.enemy_type == EnemyType.RAMBO:
            color = MAGENTA
        elif enemy.enemy_type == EnemyType.DRAGON:
            color = GREEN
        elif enemy.enemy_type == EnemyType.BIG:
            color = ORANGE
        else:
            color = RED
        
        # Hit effect - flash white when hit
        if enemy.hit_timer > 0:
            color = WHITE
        
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, BLACK, rect, 2)  # Border
        
        # Draw enemy type indicator
        if enemy.enemy_type == EnemyType.DRAGON:
            # Draw wings for dragon
            wing_points = [
                (enemy.position.x - size//2, enemy.position.y - size//4),
                (enemy.position.x - size, enemy.position.y),
                (enemy.position.x - size//2, enemy.position.y + size//4)
            ]
            pygame.draw.polygon(self.screen, color, wing_points)
        
        # Draw health bar
        if enemy.health < enemy.max_health and enemy.state != "dying":
            bar_width = size
            bar_height = 6
            bar_x = enemy.position.x - bar_width // 2
            bar_y = enemy.position.y - size // 2 - 10
            
            # Background
            pygame.draw.rect(self.screen, RED, (bar_x, bar_y, bar_width, bar_height))
            # Health
            health_width = int(bar_width * (enemy.health / enemy.max_health))
            pygame.draw.rect(self.screen, GREEN, (bar_x, bar_y, health_width, bar_height))
            pygame.draw.rect(self.screen, BLACK, (bar_x, bar_y, bar_width, bar_height), 1)
        
        # Draw state indicator
        if enemy.state == "attack":
            pygame.draw.circle(self.screen, RED, 
                             (int(enemy.position.x), int(enemy.position.y)), 
                             enemy.attack_range, 2)
        elif enemy.state == "chase":
            pygame.draw.circle(self.screen, YELLOW, 
                             (int(enemy.position.x), int(enemy.position.y)), 
                             5, 2)
    
    def _draw_ui(self, world: GameWorld):
        # Create UI background
        ui_surface = pygame.Surface((SCREEN_WIDTH, 150), pygame.SRCALPHA)
        ui_surface.fill((0, 0, 0, 128))
        self.screen.blit(ui_surface, (0, 0))
        
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
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Score
        score_text = self.font.render(f"Score: {world.score}", True, WHITE)
        self.screen.blit(score_text, (10, 80))
        
        # Game time
        time_text = self.small_font.render(f"Time: {int(world.game_time)}s", True, WHITE)
        self.screen.blit(time_text, (10, 110))
        
        # Enemy count and info
        enemy_text = self.font.render(f"Enemies: {len(world.enemies)}", True, WHITE)
        self.screen.blit(enemy_text, (250, 10))
        
        # Controls
        controls = [
            "WASD: Move",
            "SPACE: Attack",
            "F: Heal (50 pts)",
            "ESC: Quit"
        ]
        
        for i, control in enumerate(controls):
            text = self.small_font.render(control, True, WHITE)
            self.screen.blit(text, (SCREEN_WIDTH - 200, 10 + i * 25))
        
        # Invulnerability indicator
        if world.player.is_invulnerable():
            inv_text = self.small_font.render("INVULNERABLE", True, YELLOW)
            self.screen.blit(inv_text, (250, 50))

class InputHandler:
    def __init__(self):
        self.keys_pressed = set()
    
    def handle_events(self, world: GameWorld) -> Tuple[bool, float, float]:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, 0, 0
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False, 0, 0
                elif event.key == pygame.K_SPACE:
                    if world.player.attack():
                        world.sound_manager.play_sound('attack')
                        world._add_particles(world.player.position.x, world.player.position.y, ParticleType.ATTACK)
                elif event.key == pygame.K_f:
                    world.heal_player()
        
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
        pygame.display.set_caption("N Key Rollover - Enhanced Pygame Edition")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.world = GameWorld()
        self.renderer = Renderer(self.screen)
        self.input_handler = InputHandler()
    
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            
            # Handle input
            self.running, dx, dy = self.input_handler.handle_events(self.world)
            if self.running:
                self.world.player.move(dx, dy, dt)
            
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
        # Enhanced game over screen
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Game over text
        font = pygame.font.Font(None, 72)
        game_over_text = font.render("GAME OVER", True, RED)
        
        # Stats
        stats_font = pygame.font.Font(None, 36)
        score_text = stats_font.render(f"Final Score: {self.world.score}", True, WHITE)
        time_text = stats_font.render(f"Time Survived: {int(self.world.game_time)}s", True, WHITE)
        enemies_text = stats_font.render(f"Enemies Defeated: {self.world.score // 100}", True, WHITE)
        
        restart_text = stats_font.render("Press any key to exit", True, YELLOW)
        
        # Center the text
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20))
        time_rect = time_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
        enemies_rect = enemies_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 120))
        
        self.screen.blit(game_over_text, game_over_rect)
        self.screen.blit(score_text, score_rect)
        self.screen.blit(time_text, time_rect)
        self.screen.blit(enemies_text, enemies_rect)
        self.screen.blit(restart_text, restart_rect)
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
