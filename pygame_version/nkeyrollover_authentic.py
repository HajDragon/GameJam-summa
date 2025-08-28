#!/usr/bin/env python3

import pygame
import sys
import os
import time
import random
import yaml
import logging
from enum import Enum
from typing import Dict, List, Tuple

# ASCII Art Pygame Version - Loading real ASCII files from the original game

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
        try:
            # Try to use a better monospace font if available
            self.font = pygame.font.Font("C:/Windows/Fonts/consola.ttf", font_size)
        except:
            self.font = pygame.font.Font(None, font_size)
            
        self.char_width = self.font.size('W')[0]  # Use 'W' as it's typically the widest
        self.char_height = self.font.size('W')[1]
        self.sprite_cache = {}
        
    def create_ascii_sprite(self, ascii_lines: List[str], color=Colors.WHITE, bg_color=None) -> pygame.Surface:
        """Convert ASCII art lines into a pygame surface"""
        if not ascii_lines:
            return pygame.Surface((self.char_width, self.char_height), pygame.SRCALPHA)
            
        # Clean up the lines and find dimensions
        clean_lines = []
        for line in ascii_lines:
            if line.strip():  # Only add non-empty lines
                clean_lines.append(line.rstrip())  # Remove trailing whitespace
        
        if not clean_lines:
            return pygame.Surface((self.char_width, self.char_height), pygame.SRCALPHA)
            
        max_width = max(len(line) for line in clean_lines)
        width = max_width * self.char_width
        height = len(clean_lines) * self.char_height
        
        # Create surface with per-pixel alpha for transparency
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        if bg_color:
            surface.fill(bg_color)
        
        for y, line in enumerate(clean_lines):
            for x, char in enumerate(line):
                if char and char != ' ':
                    char_surface = self.font.render(char, True, color)
                    surface.blit(char_surface, (x * self.char_width, y * self.char_height))
        
        return surface
    
    def load_ascii_file(self, filepath: str) -> List[str]:
        """Load ASCII art from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Split into frames if there are multiple frames (separated by empty lines)
            frames = content.split('\n\n')
            if len(frames) > 1:
                # Return first frame for now (could be extended for animations)
                return frames[0].split('\n')
            else:
                return content.split('\n')
                
        except FileNotFoundError:
            print(f"Warning: ASCII file not found: {filepath}")
            return [" o ", "/|\\", "/ \\"]  # Default stick figure
        except Exception as e:
            print(f"Error loading ASCII file {filepath}: {e}")
            return [" ? ", "/|\\", "/ \\"]  # Error indicator

class Animation:
    """Handles animation frames for ASCII sprites"""
    
    def __init__(self, frames: List[pygame.Surface], frame_duration=0.2):
        self.frames = frames if frames else [pygame.Surface((16, 16), pygame.SRCALPHA)]
        self.frame_duration = frame_duration
        self.current_frame = 0
        self.frame_timer = 0
        
    def update(self, dt):
        if len(self.frames) > 1:
            self.frame_timer += dt
            if self.frame_timer >= self.frame_duration:
                self.frame_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.frames)
    
    def get_current_frame(self) -> pygame.Surface:
        return self.frames[self.current_frame] if self.frames else pygame.Surface((16, 16), pygame.SRCALPHA)

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
        
    def render(self, screen, camera_x=0, camera_y=0):
        sprite = self.animation.get_current_frame()
        screen.blit(sprite, (self.x - camera_x, self.y - camera_y))

class Player(Entity):
    """Player character"""
    
    def __init__(self, x, y, renderer: ASCIIRenderer):
        # Try to load real player animations from the original game
        base_path = "../data/textures/character/player/"
        
        # Load standing animation
        standing_ascii = renderer.load_ascii_file(base_path + "player_standing.ascii")
        standing_sprite = renderer.create_ascii_sprite(standing_ascii, Colors.CYAN)
        self.standing_animation = Animation([standing_sprite])
        
        # Load walking animation
        walking_ascii = renderer.load_ascii_file(base_path + "player_walking.ascii")
        # Parse multiple frames from walking animation
        if walking_ascii:
            # Split by empty lines to get individual frames
            content = '\n'.join(walking_ascii)
            frame_texts = content.split('\n\n')
            walking_sprites = []
            for frame_text in frame_texts:
                if frame_text.strip():
                    frame_lines = frame_text.split('\n')
                    sprite = renderer.create_ascii_sprite(frame_lines, Colors.CYAN)
                    walking_sprites.append(sprite)
            
            if walking_sprites:
                self.walking_animation = Animation(walking_sprites, 0.15)
            else:
                self.walking_animation = self.standing_animation
        else:
            self.walking_animation = self.standing_animation
        
        super().__init__(x, y, self.standing_animation, Colors.CYAN)
        self.speed = 120  # pixels per second
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
        # Load real enemy ASCII art from the original game
        base_path = f"../data/textures/character/{enemy_type}/"
        
        # Try to load standing animation
        standing_ascii = renderer.load_ascii_file(base_path + f"{enemy_type}_standing.ascii")
        
        # Set color based on enemy type
        if enemy_type == "stickfigure":
            color = Colors.RED
        elif enemy_type == "dragon":
            color = Colors.GREEN
        elif enemy_type == "cow":
            color = Colors.BROWN
        elif enemy_type == "rambo":
            color = Colors.YELLOW
        else:
            color = Colors.MAGENTA
            
        sprite = renderer.create_ascii_sprite(standing_ascii, color)
        animation = Animation([sprite])
        
        super().__init__(x, y, animation, color)
        self.enemy_type = enemy_type
        self.move_timer = 0
        self.move_direction = random.choice([0, 1, 2, 3])
        self.direction_duration = random.uniform(1.0, 3.0)
        
    def update(self, dt):
        # Simple AI: move randomly
        self.move_timer += dt
        if self.move_timer > self.direction_duration:
            self.move_timer = 0
            self.move_direction = random.choice([0, 1, 2, 3])
            self.direction_duration = random.uniform(1.0, 3.0)
            
        speed = 40  # pixels per second
        if self.move_direction == 0:  # left
            self.x -= speed * dt
        elif self.move_direction == 1:  # right
            self.x += speed * dt
        elif self.move_direction == 2:  # up
            self.y -= speed * dt
        elif self.move_direction == 3:  # down
            self.y += speed * dt
            
        super().update(dt)

class GameMap:
    """Handles the game map with ASCII art"""
    
    def __init__(self, renderer: ASCIIRenderer):
        self.renderer = renderer
        self.width = 100  # Larger world
        self.height = 50
        self.tile_width = renderer.char_width
        self.tile_height = renderer.char_height
        self.tiles = self.generate_dungeon()
        
    def generate_dungeon(self):
        """Generate a more complex dungeon"""
        # Create a larger, more interesting dungeon layout
        tiles = []
        
        # Fill with floor
        for y in range(self.height):
            row = []
            for x in range(self.width):
                if (x == 0 or x == self.width - 1 or 
                    y == 0 or y == self.height - 1):
                    row.append('█')  # Walls around the border
                else:
                    row.append('.')  # Floor
            tiles.append(row)
        
        # Add some rooms and corridors
        rooms = [
            (10, 5, 20, 10),   # (x, y, width, height)
            (40, 15, 15, 8),
            (70, 25, 18, 12),
            (25, 30, 12, 8),
            (55, 5, 16, 6)
        ]
        
        # Create rooms
        for rx, ry, rw, rh in rooms:
            # Room walls
            for x in range(rx, rx + rw):
                for y in range(ry, ry + rh):
                    if (x == rx or x == rx + rw - 1 or 
                        y == ry or y == ry + rh - 1):
                        if x < len(tiles[0]) and y < len(tiles):
                            tiles[y][x] = '│' if x == rx or x == rx + rw - 1 else '─'
                    else:
                        if x < len(tiles[0]) and y < len(tiles):
                            tiles[y][x] = ' '  # Room floor
        
        # Add some decorative elements
        decorations = ['┌', '┐', '└', '┘', '├', '┤', '┬', '┴']
        for _ in range(20):
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            if tiles[y][x] == '.':
                tiles[y][x] = random.choice(decorations)
        
        return tiles
    
    def get_tile(self, x, y):
        """Get tile at world coordinates"""
        tile_x = int(x // self.tile_width)
        tile_y = int(y // self.tile_height)
        
        if 0 <= tile_y < len(self.tiles) and 0 <= tile_x < len(self.tiles[0]):
            return self.tiles[tile_y][tile_x]
        return '█'  # Return wall if out of bounds
    
    def is_solid(self, x, y):
        """Check if position is solid (blocked)"""
        tile = self.get_tile(x, y)
        return tile in ['█', '│', '─', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼']
    
    def render(self, screen, camera_x, camera_y, screen_width, screen_height):
        """Render visible portion of the map"""
        # Calculate which tiles are visible
        start_x = max(0, int(camera_x // self.tile_width))
        start_y = max(0, int(camera_y // self.tile_height))
        end_x = min(self.width, int((camera_x + screen_width) // self.tile_width) + 1)
        end_y = min(self.height, int((camera_y + screen_height) // self.tile_height) + 1)
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if y < len(self.tiles) and x < len(self.tiles[0]):
                    tile = self.tiles[y][x]
                    if tile != ' ':
                        pixel_x = x * self.tile_width - camera_x
                        pixel_y = y * self.tile_height - camera_y
                        
                        # Choose color based on tile type
                        if tile in ['█', '│', '─', '┌', '┐', '└', '┘', '├', '┤', '┬', '┴', '┼']:
                            color = Colors.WHITE
                        elif tile == '.':
                            color = Colors.GRAY
                        else:
                            color = Colors.DARK_GREEN
                        
                        char_surface = self.renderer.font.render(tile, True, color)
                        screen.blit(char_surface, (pixel_x, pixel_y))

class Camera:
    """Camera system for following the player"""
    
    def __init__(self, screen_width, screen_height):
        self.x = 0
        self.y = 0
        self.screen_width = screen_width
        self.screen_height = screen_height
        
    def update(self, target_x, target_y):
        """Update camera to follow target"""
        self.x = target_x - self.screen_width // 2
        self.y = target_y - self.screen_height // 2

class Game:
    """Main game class"""
    
    def __init__(self):
        pygame.init()
        
        # Screen setup
        self.char_width = 12
        self.char_height = 18
        self.screen_width = 1024
        self.screen_height = 768
        
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("N Key Rollover - ASCII Dungeon Crawler")
        
        self.clock = pygame.time.Clock()
        self.renderer = ASCIIRenderer(self.char_height)
        
        # Camera
        self.camera = Camera(self.screen_width, self.screen_height)
        
        # Game state
        self.running = True
        self.game_map = GameMap(self.renderer)
        
        # Spawn player in a safe location
        self.player = Player(500, 300, self.renderer)
        
        # Spawn enemies
        self.enemies = []
        self.spawn_enemies()
        
        # HUD
        self.hud_font = pygame.font.Font(None, 24)
        
    def spawn_enemies(self):
        """Spawn enemies around the map"""
        enemy_types = ["stickfigure", "dragon", "cow", "rambo"]
        for _ in range(8):
            # Find a safe spawn location
            attempts = 0
            while attempts < 100:
                x = random.randint(100, self.game_map.width * self.char_width - 100)
                y = random.randint(100, self.game_map.height * self.char_height - 100)
                
                if not self.game_map.is_solid(x, y):
                    enemy_type = random.choice(enemy_types)
                    self.enemies.append(Enemy(x, y, self.renderer, enemy_type))
                    break
                attempts += 1
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    print("Attack!")
                elif event.key == pygame.K_f:
                    print("Heal!")
                elif event.key == pygame.K_g:
                    print("Port!")
    
    def update(self, dt):
        """Update game state"""
        keys = pygame.key.get_pressed()
        
        # Store old position for collision detection
        old_x, old_y = self.player.x, self.player.y
        
        # Update player
        self.player.update(dt, keys)
        
        # Check collisions with walls
        if self.game_map.is_solid(self.player.x + 24, self.player.y + 36):  # Check center-bottom of player
            self.player.x = old_x
            self.player.y = old_y
        
        # Update camera
        self.camera.update(self.player.x, self.player.y)
        
        # Update enemies
        for enemy in self.enemies:
            old_ex, old_ey = enemy.x, enemy.y
            enemy.update(dt)
            
            # Check enemy collisions with walls
            if self.game_map.is_solid(enemy.x + 12, enemy.y + 18):
                enemy.x = old_ex
                enemy.y = old_ey
                enemy.move_direction = random.choice([0, 1, 2, 3])  # Change direction
    
    def render(self):
        """Render the game"""
        # Clear screen
        self.screen.fill(Colors.BLACK)
        
        # Draw map
        self.game_map.render(self.screen, self.camera.x, self.camera.y, 
                           self.screen_width, self.screen_height)
        
        # Draw entities
        for enemy in self.enemies:
            enemy.render(self.screen, self.camera.x, self.camera.y)
        
        self.player.render(self.screen, self.camera.x, self.camera.y)
        
        # Draw HUD (fixed on screen)
        hud_bg = pygame.Surface((300, 80))
        hud_bg.fill(Colors.BLACK)
        hud_bg.set_alpha(180)
        self.screen.blit(hud_bg, (10, 10))
        
        health_text = self.hud_font.render(f"Health: {self.player.health}", True, Colors.WHITE)
        self.screen.blit(health_text, (20, 20))
        
        points_text = self.hud_font.render("Points: 0", True, Colors.WHITE)
        self.screen.blit(points_text, (20, 45))
        
        fps_text = self.hud_font.render(f"FPS: {int(self.clock.get_fps())}", True, Colors.WHITE)
        self.screen.blit(fps_text, (20, 70))
        
        # Controls (bottom of screen)
        controls = "Controls: WASD/Arrows=Move, Space=Attack, F=Heal, G=Port, ESC=Quit"
        control_surface = self.hud_font.render(controls, True, Colors.GRAY)
        self.screen.blit(control_surface, (10, self.screen_height - 30))
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        print("N Key Rollover - ASCII Dungeon Crawler")
        print("Loading real ASCII art from the original game...")
        print("Controls: WASD or Arrow keys to move, Space to attack, ESC to quit")
        
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
