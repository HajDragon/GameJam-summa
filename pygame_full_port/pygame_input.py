"""
Pygame Input Handler - Converts pygame events to original game input messages
"""

import pygame
import logging
from typing import Dict, Any

from messaging import messaging, MessageType
import system.singletons.gametime

logger = logging.getLogger(__name__)

class PygameInputHandler:
    """Handles pygame input and converts to original game messages"""
    
    def __init__(self):
        """Initialize input handler"""
        self.key_mapping = self.create_key_mapping()
        logger.info("Input handler initialized")
    
    def create_key_mapping(self) -> Dict[int, int]:
        """Create mapping from pygame keys to original game key codes"""
        return {
            # Movement keys
            pygame.K_LEFT: -260,      # Arrow left
            pygame.K_RIGHT: -261,     # Arrow right  
            pygame.K_UP: -259,        # Arrow up
            pygame.K_DOWN: -258,      # Arrow down
            
            # Movement with shift (strafe)
            pygame.K_LEFT | pygame.KMOD_SHIFT: -260,
            pygame.K_RIGHT | pygame.KMOD_SHIFT: -261,
            pygame.K_UP | pygame.KMOD_SHIFT: -259,
            pygame.K_DOWN | pygame.KMOD_SHIFT: -258,
            
            # Attack keys
            pygame.K_SPACE: ord(' '),   # Attack
            
            # Weapon selection
            pygame.K_1: ord('1'),
            pygame.K_2: ord('2'),
            pygame.K_3: ord('3'),
            pygame.K_4: ord('4'),
            
            # Skills
            pygame.K_q: ord('q'),
            pygame.K_w: ord('w'),
            pygame.K_e: ord('e'),
            pygame.K_r: ord('r'),
            
            # Other abilities
            pygame.K_f: ord('f'),   # Heal
            pygame.K_g: ord('g'),   # Port
            
            # Defense
            pygame.K_TAB: -301,     # Buckler/Shield
            
            # System
            pygame.K_ESCAPE: 27,    # Escape
        }
    
    def handle_event(self, event: pygame.event.Event):
        """Handle a pygame event and convert to game messages"""
        if event.type == pygame.KEYDOWN:
            self.handle_keydown(event)
        elif event.type == pygame.KEYUP:
            self.handle_keyup(event)
    
    def handle_keydown(self, event: pygame.event.Event):
        """Handle key press events"""
        key = event.key
        mods = pygame.key.get_pressed()
        
        # Check for modified keys (like shift+arrow)
        if mods[pygame.K_LSHIFT] or mods[pygame.K_RSHIFT]:
            key |= pygame.KMOD_SHIFT
        
        # Convert to original game key code
        game_key = self.key_mapping.get(key, key)
        
        # Send key press message to original game
        messaging.add(
            type=MessageType.PlayerKeypress,
            data={
                'key': game_key,
                'time': system.singletons.gametime.getGameTime(),
            }
        )
        
        logger.debug(f"Key pressed: pygame={key}, game={game_key}")
    
    def handle_keyup(self, event: pygame.event.Event):
        """Handle key release events"""
        # Most original game logic is on key press, not release
        pass
