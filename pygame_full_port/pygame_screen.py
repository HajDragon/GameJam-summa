"""
Pygame Screen - Adapter that makes Pygame compatible with original game's screen interface
"""

import pygame
import logging
from typing import List, Tuple, Dict, Any

from utilities.color import Color
from utilities.colorpalette import ColorPalette
from common.coordinates import Coordinates
from asciimatics.event import KeyboardEvent

logger = logging.getLogger(__name__)

class PygameScreen:
    """Pygame adapter for original game's screen interface"""
    
    # Screen constants (from asciimatics.Screen)
    KEY_ESCAPE = 27
    KEY_F1 = -1  # F1 key
    KEY_F2 = -2  # F2 key
    KEY_F3 = -3  # F3 key
    KEY_F4 = -4  # F4 key
    KEY_F5 = -5  # F5 key
    KEY_F6 = -6  # F6 key
    KEY_F7 = -7  # F7 key
    KEY_F8 = -8  # F8 key
    KEY_F9 = -9  # F9 key
    KEY_F10 = -10 # F10 key
    KEY_F11 = -11 # F11 key
    KEY_F12 = -12 # F12 key
    KEY_UP = -13
    KEY_DOWN = -14
    KEY_LEFT = -15
    KEY_RIGHT = -16
    KEY_HOME = -17
    KEY_END = -18
    KEY_PAGE_UP = -19
    KEY_PAGE_DOWN = -20
    KEY_DELETE = -21
    KEY_INSERT = -22
    KEY_TAB = 9
    KEY_BACK = 8
    
    # Color constants
    COLOUR_BLACK = 0
    COLOUR_RED = 1
    COLOUR_GREEN = 2
    COLOUR_YELLOW = 3
    COLOUR_BLUE = 4
    COLOUR_MAGENTA = 5
    COLOUR_CYAN = 6
    COLOUR_WHITE = 7
    
    # Attribute constants
    A_BOLD = 1
    A_NORMAL = 0
    A_REVERSE = 2
    A_UNDERLINE = 4
    
    def __init__(self, pygame_screen: pygame.Surface, font: pygame.font.Font):
        """Initialize pygame screen adapter"""
        self.pygame_screen = pygame_screen
        self.font = font
        self.width = pygame_screen.get_width()
        self.height = pygame_screen.get_height()
        
        # Character dimensions for ASCII rendering
        self.char_width = self.font.size('W')[0]
        self.char_height = self.font.get_height()
        
        # Text grid dimensions
        self.text_width = self.width // self.char_width
        self.text_height = self.height // self.char_height
        
        # Buffer for text rendering
        self.text_buffer: List[List[Tuple[str, Color]]] = []
        self.clear_buffer()
        
        # Event queue for input handling
        self.event_queue = []
        
        # Key mapping from pygame to asciimatics
        self.key_map = {
            pygame.K_ESCAPE: self.KEY_ESCAPE,
            pygame.K_F1: self.KEY_F1,
            pygame.K_F2: self.KEY_F2,
            pygame.K_F3: self.KEY_F3,
            pygame.K_F4: self.KEY_F4,
            pygame.K_F5: self.KEY_F5,
            pygame.K_F6: self.KEY_F6,
            pygame.K_F7: self.KEY_F7,
            pygame.K_F8: self.KEY_F8,
            pygame.K_F9: self.KEY_F9,
            pygame.K_F10: self.KEY_F10,
            pygame.K_F11: self.KEY_F11,
            pygame.K_F12: self.KEY_F12,
            pygame.K_UP: self.KEY_UP,
            pygame.K_DOWN: self.KEY_DOWN,
            pygame.K_LEFT: self.KEY_LEFT,
            pygame.K_RIGHT: self.KEY_RIGHT,
            pygame.K_HOME: self.KEY_HOME,
            pygame.K_END: self.KEY_END,
            pygame.K_PAGEUP: self.KEY_PAGE_UP,
            pygame.K_PAGEDOWN: self.KEY_PAGE_DOWN,
            pygame.K_DELETE: self.KEY_DELETE,
            pygame.K_INSERT: self.KEY_INSERT,
            pygame.K_TAB: self.KEY_TAB,
            pygame.K_BACKSPACE: self.KEY_BACK,
        }
        
        # Create a mock _buffer object for compatibility
        class MockBuffer:
            def __init__(self, width, height):
                self._width = width
                self._height = height
                self.width = width
                self.height = height
                # Add double buffer for compatibility with game.py
                self._double_buffer = [
                    [(' ', 7, 0, 0, 1) for _ in range(width)]
                    for _ in range(height)
                ]
        
        self._buffer = MockBuffer(self.text_width, self.text_height)
        
        logger.info(f"Screen initialized: {self.width}x{self.height} pixels, {self.text_width}x{self.text_height} chars")
    
    def clear_buffer(self):
        """Clear the text buffer"""
        self.text_buffer = [
            [(' ', Color.white) for _ in range(self.text_width)]
            for _ in range(self.text_height)
        ]
    
    def putch(self, x: int, y: int, char: str, color: Color = Color.white):
        """Put a character at given position (original game interface)"""
        if 0 <= x < self.text_width and 0 <= y < self.text_height:
            self.text_buffer[y][x] = (char, color)
    
    def addstr(self, x: int, y: int, text: str, color: Color = Color.white):
        """Add string at given position (original game interface)"""
        for i, char in enumerate(text):
            if x + i < self.text_width:
                self.putch(x + i, y, char, color)
    
    def move(self, x: int, y: int):
        """Move cursor (original game interface - not used much)"""
        pass
    
    def refresh(self):
        """Refresh screen (original game interface)"""
        self.render()
    
    def clear(self):
        """Clear screen (original game interface)"""
        self.clear_buffer()
    
    def getch(self):
        """Get character input (original game interface - handled by input system)"""
        return -1
    
    def nodelay(self, flag: bool):
        """Set nodelay mode (original game interface - not needed)"""
        pass
    
    def render(self):
        """Render the text buffer to pygame screen"""
        # Clear pygame screen
        self.pygame_screen.fill((0, 0, 0))
        
        # Render each character
        for y in range(self.text_height):
            for x in range(self.text_width):
                char, color = self.text_buffer[y][x]
                if char != ' ':  # Only render non-space characters
                    # Convert Color enum to RGB
                    rgb_color = self.color_to_rgb(color)
                    
                    # Render character
                    text_surface = self.font.render(char, True, rgb_color)
                    pixel_x = x * self.char_width
                    pixel_y = y * self.char_height
                    self.pygame_screen.blit(text_surface, (pixel_x, pixel_y))
    
    def color_to_rgb(self, color: Color) -> Tuple[int, int, int]:
        """Convert game Color enum to RGB tuple"""
        color_map = {
            Color.black: (0, 0, 0),
            Color.white: (229, 229, 229),
            Color.red: (205, 0, 0),
            Color.green: (0, 205, 0),
            Color.blue: (0, 0, 205),
            Color.yellow: (205, 205, 0),
            Color.magenta: (205, 0, 205),
            Color.cyan: (0, 205, 205),
            Color.grey: (77, 77, 77),
            Color.brightred: (255, 0, 0),
            Color.brightgreen: (0, 255, 0),
            Color.brightblue: (0, 0, 255),
            Color.brightyellow: (255, 255, 0),
            Color.brightmagenta: (255, 0, 255),
            Color.brightcyan: (0, 255, 255),
            Color.brightwhite: (255, 255, 255),
        }
        return color_map.get(color, (255, 255, 255))
    
    def get_text_dimensions(self) -> Tuple[int, int]:
        """Get text grid dimensions"""
        return self.text_width, self.text_height
    
    def pixel_to_text_coords(self, pixel_x: int, pixel_y: int) -> Tuple[int, int]:
        """Convert pixel coordinates to text coordinates"""
        text_x = pixel_x // self.char_width
        text_y = pixel_y // self.char_height
        return text_x, text_y
    
    def text_to_pixel_coords(self, text_x: int, text_y: int) -> Tuple[int, int]:
        """Convert text coordinates to pixel coordinates"""
        pixel_x = text_x * self.char_width
        pixel_y = text_y * self.char_height
        return pixel_x, pixel_y
    
    def get_from(self, x: int, y: int) -> Tuple[int, int, int, int]:
        """
        Get the character at the specified location.
        Returns a 4-tuple of (ascii code, foreground, attributes, background)
        """
        # Check bounds
        if x < 0 or x >= self.text_width or y < 0 or y >= self.text_height:
            return (32, 7, 0, 0)  # Return space character with default colors
        
        # Get character from buffer if available
        if y < len(self.text_buffer) and x < len(self.text_buffer[y]):
            char, color = self.text_buffer[y][x]
            ascii_code = ord(char) if char else 32
            fg_color = 7  # Default white
            bg_color = 0  # Default black
            attributes = 0  # No special attributes
            return (ascii_code, fg_color, attributes, bg_color)
        else:
            return (32, 7, 0, 0)  # Return space character with default colors
    
    def print_at(self, text: str, x: int, y: int, colour: int, attr: int = 0, bg: int = None):
        """
        Print text at specified position (original game interface)
        Args:
            text: Text to print
            x: X coordinate
            y: Y coordinate  
            colour: Foreground color
            attr: Text attributes (bold, etc.)
            bg: Background color (optional)
        """
        # Convert color index to Color enum
        color_map = {
            0: Color.black,
            1: Color.red,
            2: Color.green,
            3: Color.yellow,
            4: Color.blue,
            5: Color.magenta,
            6: Color.cyan,
            7: Color.white,
        }
        
        text_color = color_map.get(colour, Color.white)
        
        # Handle single character or string
        if len(text) == 1:
            self.putch(x, y, text, text_color)
        else:
            self.addstr(x, y, text, text_color)
    
    def handle_pygame_event(self, pygame_event):
        """Convert pygame event to asciimatics-style event and add to queue"""
        if pygame_event.type == pygame.KEYDOWN:
            # Map pygame key to asciimatics key code
            if pygame_event.key in self.key_map:
                key_code = self.key_map[pygame_event.key]
            else:
                # For regular character keys, use the unicode value
                if pygame_event.unicode:
                    key_code = ord(pygame_event.unicode)
                else:
                    key_code = pygame_event.key
            
            # Create asciimatics-style keyboard event
            event = KeyboardEvent(key_code)
            self.event_queue.append(event)
    
    def get_event(self):
        """Get next event from queue (original game interface)"""
        if self.event_queue:
            return self.event_queue.pop(0)
        return None
    
    @property
    def dimensions(self) -> Tuple[int, int]:
        """Get screen dimensions (original game interface)"""
        return self.text_height, self.text_width
    
    def has_resized(self) -> bool:
        """Check if screen has been resized (original game interface)"""
        return False
    
    def max_height(self) -> int:
        """Get maximum height (original game interface)"""
        return self.text_height
    
    def max_width(self) -> int:
        """Get maximum width (original game interface)"""
        return self.text_width
    
    @property
    def palette(self):
        """Get color palette (original game interface)"""
        # Return a simple 8-color palette compatible with asciimatics
        return [
            (0, 0, 0),       # Black
            (255, 0, 0),     # Red
            (0, 255, 0),     # Green
            (255, 255, 0),   # Yellow
            (0, 0, 255),     # Blue
            (255, 0, 255),   # Magenta
            (0, 255, 255),   # Cyan
            (255, 255, 255), # White
        ]
    
    @property
    def colours(self) -> int:
        """Get number of colors supported (original game interface)"""
        return 8
