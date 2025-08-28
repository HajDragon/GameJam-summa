#!/usr/bin/env python3

import pygame
import sys
import os
import time
import random
import yaml
from enum import Enum
from typing import Dict, List, Tuple

# ASCII Art Pygame Version - Preserving the original art style

# Colors to match the original game
class Colors:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    BROWN = (139, 69, 19)
    GRAY = (128, 128, 128)
    DARK_GREEN = (0, 128, 0)

class Direction(Enum):
    LEFT = 0
    RIGHT = 1
    UP = 2
    DOWN = 3

class ASCIIRenderer:
    """Renders ASCII art as sprites in Pygame while preserving the original look"""
    
    def __init__(self, font_size=16):
        pygame.font.init()
        # Use a monospace font to maintain ASCII art alignment
        self.font = pygame.font.Font(None, font_size)
        self.char_width = self.font.size(' ')[0]
        self.char_height = self.font.size(' ')[1]
        self.sprite_cache = {}
        
    def create_ascii_sprite(self, ascii_lines: List[str], color=Colors.WHITE, bg_color=None) -> pygame.Surface:
        """Convert ASCII art lines into a pygame surface"""
        if not ascii_lines:
            return pygame.Surface((self.char_width, self.char_height))
            
        max_width = max(len(line) for line in ascii_lines)
        width = max_width * self.char_width
        height = len(ascii_lines) * self.char_height
        
        # Create surface with per-pixel alpha for transparency
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        if bg_color:
            surface.fill(bg_color)
        
        for y, line in enumerate(ascii_lines):
            for x, char in enumerate(line):
                if char != ' ' and char != '':
                    char_surface = self.font.render(char, True, color)
                    surface.blit(char_surface, (x * self.char_width, y * self.char_height))
        
        return surface
    
    def load_ascii_file(self, filepath: str) -> List[str]:
        """Load ASCII art from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.read().split('\n')
                # Remove empty lines at the end
                while lines and not lines[-1].strip():
                    lines.pop()
                return lines
        except FileNotFoundError:
            print(f"Warning: ASCII file not found: {filepath}")
            return [" o ", "/|\\", "/ \\"]  # Default stick figure

class Animation:
    """Handles animation frames for ASCII sprites"""
    
    def __init__(self, frames: List[pygame.Surface], frame_duration=0.2):
        self.frames = frames
        self.frame_duration = frame_duration
        self.current_frame = 0
        self.frame_timer = 0
        
    def update(self, dt):
        self.frame_timer += dt
        if self.frame_timer >= self.frame_duration:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
    
    def get_current_frame(self) -> pygame.Surface:
        return self.frames[self.current_frame] if self.frames else pygame.Surface((16, 16))

class Entity:
    """Base class for all game entities"""
    
    def __init__(self, x, y, animation: Animation, color=Colors.WHITE):
        self.x = x
        self.y = y
        self.animation = animation
        self.color = color
        self.health = 100
        self.max_health = 100
        
    def update(self, dt):
        self.animation.update(dt)
        
    def render(self, screen, renderer: ASCIIRenderer):
        sprite = self.animation.get_current_frame()
        screen.blit(sprite, (self.x, self.y))

class Player(Entity):
    """Player character"""
    
    def __init__(self, x, y, renderer: ASCIIRenderer):
        # Load player animations
        standing_ascii = [" @ ", "/|\\", "/ \\"]
        walking_frames = [
            [" @ ", "/|\\", " >\\"],
            [" @ ", "/|\\", " |\\"],
            [" @ ", "/|\\", " |>"],
            [" @ ", "/|\\", "/| "]
        ]
        
        standing_sprite = renderer.create_ascii_sprite(standing_ascii, Colors.CYAN)
        walking_sprites = [renderer.create_ascii_sprite(frame, Colors.CYAN) for frame in walking_frames]
        
        self.standing_animation = Animation([standing_sprite])
        self.walking_animation = Animation(walking_sprites, 0.15)
        
        super().__init__(x, y, self.standing_animation, Colors.CYAN)
        self.speed = 100  # pixels per second
        self.is_moving = False
        
    def update(self, dt, keys):
        self.is_moving = False
        dx = dy = 0
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.speed * dt
            self.is_moving = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.speed * dt
            self.is_moving = True
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.speed * dt
            self.is_moving = True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.speed * dt
            self.is_moving = True
            
        self.x += dx
        self.y += dy
        
        # Choose animation based on movement
        if self.is_moving:
            self.animation = self.walking_animation
        else:
            self.animation = self.standing_animation
            
        super().update(dt)

class Enemy(Entity):
    """Enemy character"""
    
    def __init__(self, x, y, renderer: ASCIIRenderer, enemy_type="stickfigure"):
        # Different enemy types
        if enemy_type == "stickfigure":
            ascii_art = [" o ", "/|\\", "/ \\"]
            color = Colors.RED
        elif enemy_type == "dragon":
            ascii_art = ["/~~`  ~~\\", "/~~         ~~\\", "{       -       }"]
            color = Colors.GREEN
        elif enemy_type == "cow":
            ascii_art = [" /^^^^\\ ", "( o  o )", " )----("]
            color = Colors.BROWN
        else:
            ascii_art = [" ? ", "/|\\", "/ \\"]
            color = Colors.MAGENTA
            
        sprite = renderer.create_ascii_sprite(ascii_art, color)
        animation = Animation([sprite])
        
        super().__init__(x, y, animation, color)
        self.enemy_type = enemy_type
        self.move_timer = 0
        self.move_direction = random.choice([0, 1, 2, 3])  # Random initial direction
        
    def update(self, dt):
        # Simple AI: move randomly
        self.move_timer += dt
        if self.move_timer > 2.0:  # Change direction every 2 seconds
            self.move_timer = 0
            self.move_direction = random.choice([0, 1, 2, 3])
            
        speed = 30  # pixels per second
        if self.move_direction == 0:  # left
            self.x -= speed * dt
        elif self.move_direction == 1:  # right
            self.x += speed * dt
        elif self.move_direction == 2:  # up
            self.y -= speed * dt
        elif self.move_direction == 3:  # down
            self.y += speed * dt
            
        super().update(dt)

class MapTile:
    """Represents a map tile with ASCII art"""
    
    def __init__(self, x, y, ascii_char, color=Colors.WHITE):
        self.x = x
        self.y = y
        self.ascii_char = ascii_char
        self.color = color
        self.solid = ascii_char in ['#', '│', '─', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼']

class GameMap:
    """Handles the game map with ASCII art tiles"""
    
    def __init__(self, renderer: ASCIIRenderer):
        self.renderer = renderer
        self.tiles = []
        self.width = 80
        self.height = 24
        self.generate_map()
        
    def generate_map(self):
        """Generate a simple dungeon map"""
        # Create a simple dungeon layout
        map_layout = [
            "┌──────────────────────────────────────────────────────────────────────────────┐",
            "│                                                                              │",
            "│  ┌───┌──┐                  ┌───┐         /~~         ~~\\                     │",
            "│  │   │  │  ┌───┐    ┌────┐ │   ┌───┐    {       -       }──┐  ┌────┐       │",
            "│  │   │  │  │   │┌───│    │ │   │   │  ┌─ \\  _-     -_  /   │  │    │  ┌───┐│",
            "│  │   │  │  │   ││   │    │ │   │   │  │   '~  \\\\ //  ~'    ┌──│    │  │   ││",
            "│  │   │  │  │   ││   │    │ │   │   │  │   │  │ | | │   │   │  │    │  │   ││",
            "│  └───┴──┴──┴───┴┴───┴────┴─┴───┴───┴──┴───┴──┴─────┴───┴───┴──┴────┴──┴───┘│",
            "│                                                                              │",
            "│     o                                                                       │",
            "│    /|\\                                                                      │",
            "│    / \\                                                                      │",
            "│                                                                              │",
            "│                    o                                                        │",
            "│                   /|\\                                                       │",
            "│                   / \\                                                       │",
            "│                                                                              │",
            "│                                                                              │",
            "│                                                                              │",
            "│                                                                              │",
            "│                                                                              │",
            "│                                                                              │",
            "│                                                                              │",
            "└──────────────────────────────────────────────────────────────────────────────┘"
        ]
        
        self.tiles = []
        for y, row in enumerate(map_layout):
            tile_row = []
            for x, char in enumerate(row):
                if char in ['┌', '┐', '└', '┘', '─', '│', '├', '┤', '┬', '┴', '┼']:
                    color = Colors.WHITE
                elif char == ' ':
                    color = Colors.BLACK
                else:
                    color = Colors.GRAY
                    
                tile = MapTile(x * self.renderer.char_width, y * self.renderer.char_height, char, color)
                tile_row.append(tile)
            self.tiles.append(tile_row)
    
    def render(self, screen):
        """Render the map"""
        for row in self.tiles:
            for tile in row:
                if tile.ascii_char != ' ':
                    char_surface = self.renderer.font.render(tile.ascii_char, True, tile.color)
                    screen.blit(char_surface, (tile.x, tile.y))

class Game:
    """Main game class"""
    
    def __init__(self):
        pygame.init()
        
        # Screen setup to match ASCII terminal size
        self.char_width = 16
        self.char_height = 16
        self.screen_width = 80 * self.char_width  # 80 columns
        self.screen_height = 24 * self.char_height  # 24 rows
        
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("N Key Rollover - ASCII Style")
        
        self.clock = pygame.time.Clock()
        self.renderer = ASCIIRenderer(self.char_height)
        
        # Game state
        self.running = True
        self.player = Player(400, 300, self.renderer)
        self.enemies = []
        self.game_map = GameMap(self.renderer)
        
        # Create some enemies
        self.spawn_enemies()
        
        # HUD
        self.font = pygame.font.Font(None, 24)
        
    def spawn_enemies(self):
        """Spawn enemies around the map"""
        enemy_types = ["stickfigure", "dragon", "cow"]
        for _ in range(5):
            x = random.randint(100, self.screen_width - 100)
            y = random.randint(100, self.screen_height - 100)
            enemy_type = random.choice(enemy_types)
            self.enemies.append(Enemy(x, y, self.renderer, enemy_type))
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    # Attack (placeholder)
                    print("Attack!")
    
    def update(self, dt):
        """Update game state"""
        keys = pygame.key.get_pressed()
        
        # Update player
        self.player.update(dt, keys)
        
        # Keep player on screen
        self.player.x = max(0, min(self.screen_width - 48, self.player.x))
        self.player.y = max(0, min(self.screen_height - 48, self.player.y))
        
        # Update enemies
        for enemy in self.enemies:
            enemy.update(dt)
            # Keep enemies on screen
            enemy.x = max(0, min(self.screen_width - 48, enemy.x))
            enemy.y = max(0, min(self.screen_height - 48, enemy.y))
    
    def render(self):
        """Render the game"""
        # Clear screen with black background
        self.screen.fill(Colors.BLACK)
        
        # Draw map
        self.game_map.render(self.screen)
        
        # Draw entities
        for enemy in self.enemies:
            enemy.render(self.screen, self.renderer)
        
        self.player.render(self.screen, self.renderer)
        
        # Draw HUD
        health_text = self.font.render(f"Health: {self.player.health}", True, Colors.WHITE)
        self.screen.blit(health_text, (10, 10))
        
        points_text = self.font.render("Points: 0", True, Colors.WHITE)
        self.screen.blit(points_text, (10, 35))
        
        # Controls help
        controls = [
            "Controls: Arrow keys or WASD to move",
            "Space to attack, ESC to quit"
        ]
        for i, text in enumerate(controls):
            control_surface = self.font.render(text, True, Colors.GRAY)
            self.screen.blit(control_surface, (10, self.screen_height - 60 + i * 25))
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        print("N Key Rollover - ASCII Style Pygame Version")
        print("Controls: Arrow keys or WASD to move, Space to attack, ESC to quit")
        
        last_time = time.time()
        
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            self.handle_events()
            self.update(dt)
            self.render()
            
            self.clock.tick(60)  # 60 FPS
        
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
