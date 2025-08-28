"""
Game Engine - Pygame port of the original N Key Rollover game
Preserves all original mechanics, AI, combat, and systems
"""

import pygame
import esper
import yaml
import os
import sys
import logging
from typing import Dict, List, Tuple, Any

# Import original game systems
from texture.texturehelper import TextureHelper
from game.game import Game as OriginalGame
from messaging import messaging, MessageType
from directmessaging import directMessaging, DirectMessageType
from common.direction import Direction
from common.coordinates import Coordinates
from utilities.color import Color
from utilities.colorpalette import ColorPalette
from config import Config

# Pygame-specific imports
from pygame_renderer import PygameRenderer
from pygame_input import PygameInputHandler
from pygame_screen import PygameScreen

logger = logging.getLogger(__name__)

class GameEngine:
    """Main game engine that bridges original game logic with Pygame rendering"""
    
    def __init__(self):
        """Initialize the game engine"""
        self.screen_width = 1024
        self.screen_height = 768
        self.fps = 60
        self.running = True
        
        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("N Key Rollover - Pygame Port")
        self.clock = pygame.time.Clock()
        
        # Initialize font for ASCII rendering
        self.font_size = 12
        self.font = pygame.font.Font(None, self.font_size)
        
        # Create pygame adaptations
        self.pygame_screen = PygameScreen(self.screen, self.font)
        self.renderer = PygameRenderer(self.pygame_screen)
        self.input_handler = PygameInputHandler()
        
        # Create the original game instance with pygame adaptations
        self.original_game = OriginalGame(
            win=self.pygame_screen,
            menuwin=self.pygame_screen
        )
        
        # Game state
        self.delta_time = 0.0
        self.frame_count = 0
        
        logger.info("Game engine initialized")
    
    def run(self):
        """Main game loop"""
        logger.info("Starting game loop")
        
        while self.running:
            # Calculate delta time
            self.delta_time = self.clock.tick(self.fps) / 1000.0
            
            # Handle events
            self.handle_events()
            
            # Update game logic
            self.update()
            
            # Render
            self.render()
        
        logger.info("Game loop ended")
    
    def handle_events(self):
        """Handle pygame events and convert to original game input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                # Pass event to pygame screen for input handling
                self.pygame_screen.handle_pygame_event(event)
                # Also pass to input handler
                self.input_handler.handle_event(event)
    
    def update(self):
        """Update game logic using original game systems"""
        try:
            # Calculate delta time
            dt = 1.0 / 60.0  # 60 FPS target
            
            # Advance the original game by one frame
            self.original_game.advance(dt, self.frame_count)
            self.frame_count += 1
        except Exception as e:
            logger.error(f"Error updating game: {e}")
            import traceback
            traceback.print_exc()
            # Continue running to avoid crashes
    
    def render(self):
        """Render the game using pygame"""
        # Clear screen
        self.screen.fill((0, 0, 0))  # Black background
        
        # Let the pygame screen render everything
        self.pygame_screen.render()
        
        # Update display
        pygame.display.flip()
