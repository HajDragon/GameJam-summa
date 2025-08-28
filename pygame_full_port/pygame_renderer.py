"""
Pygame Renderer - Handles rendering of game elements using Pygame
"""

import pygame
import logging
from typing import Dict, List, Tuple, Any

from pygame_screen import PygameScreen
from common.coordinates import Coordinates
from utilities.color import Color

logger = logging.getLogger(__name__)

class PygameRenderer:
    """Handles rendering of game elements"""
    
    def __init__(self, screen: PygameScreen):
        """Initialize renderer"""
        self.screen = screen
        logger.info("Renderer initialized")
    
    def render_character(self, x: int, y: int, char: str, color: Color = Color.white):
        """Render a single character at given position"""
        self.screen.putch(x, y, char, color)
    
    def render_string(self, x: int, y: int, text: str, color: Color = Color.white):
        """Render a string at given position"""
        self.screen.addstr(x, y, text, color)
    
    def render_animation_frame(self, x: int, y: int, frame: List[List[str]], colors: List[List[Color]] = None):
        """Render an animation frame at given position"""
        if colors is None:
            # Default to white if no colors provided
            colors = [[Color.white for _ in row] for row in frame]
        
        for row_idx, row in enumerate(frame):
            for col_idx, char in enumerate(row):
                if char and char != ' ':  # Only render non-empty, non-space characters
                    render_x = x + col_idx
                    render_y = y + row_idx
                    color = colors[row_idx][col_idx] if row_idx < len(colors) and col_idx < len(colors[row_idx]) else Color.white
                    self.screen.putch(render_x, render_y, char, color)
    
    def clear(self):
        """Clear the screen"""
        self.screen.clear()
    
    def render_line(self, x1: int, y1: int, x2: int, y2: int, char: str = '-', color: Color = Color.white):
        """Render a line between two points using ASCII characters"""
        # Simple line rendering using ASCII characters
        if x1 == x2:  # Vertical line
            start_y, end_y = (y1, y2) if y1 < y2 else (y2, y1)
            for y in range(start_y, end_y + 1):
                self.screen.putch(x1, y, '|', color)
        elif y1 == y2:  # Horizontal line
            start_x, end_x = (x1, x2) if x1 < x2 else (x2, x1)
            for x in range(start_x, end_x + 1):
                self.screen.putch(x, y1, '-', color)
        else:
            # Diagonal line (simple approximation)
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            sx = 1 if x1 < x2 else -1
            sy = 1 if y1 < y2 else -1
            err = dx - dy
            
            x, y = x1, y1
            while True:
                self.screen.putch(x, y, char, color)
                if x == x2 and y == y2:
                    break
                e2 = 2 * err
                if e2 > -dy:
                    err -= dy
                    x += sx
                if e2 < dx:
                    err += dx
                    y += sy
    
    def render_box(self, x: int, y: int, width: int, height: int, color: Color = Color.white):
        """Render a box outline using ASCII characters"""
        # Top and bottom borders
        for i in range(width):
            self.screen.putch(x + i, y, '-', color)
            self.screen.putch(x + i, y + height - 1, '-', color)
        
        # Left and right borders
        for i in range(height):
            self.screen.putch(x, y + i, '|', color)
            self.screen.putch(x + width - 1, y + i, '|', color)
        
        # Corners
        self.screen.putch(x, y, '+', color)
        self.screen.putch(x + width - 1, y, '+', color)
        self.screen.putch(x, y + height - 1, '+', color)
        self.screen.putch(x + width - 1, y + height - 1, '+', color)
