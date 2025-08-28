#!/usr/bin/env python3
"""
N Key Rollover - Full Pygame Port
Complete port of the original game preserving all mechanics, AI, and systems
"""

import pygame
import sys
import os
import logging

# Add the original game path to import original modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from game_engine import GameEngine

def main():
    """Main game entry point"""
    logging.basicConfig(level=logging.INFO)
    
    # Change working directory to parent (original game directory)
    original_game_dir = os.path.join(os.path.dirname(__file__), '..')
    os.chdir(original_game_dir)
    
    # Initialize Pygame
    pygame.init()
    
    # Create and run the game engine
    engine = GameEngine()
    engine.run()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
