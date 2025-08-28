# N Key Rollover - Pygame Edition

A modern Pygame remake of the classic ASCII dungeon crawler "N Key Rollover". This version features enhanced graphics, smooth gameplay, and modern game mechanics while preserving the core gameplay of the original.

## Features

### Visual Improvements
- **Modern 2D Graphics**: Replaced ASCII characters with colorful rectangles and shapes
- **Smooth Animation**: 60 FPS gameplay with smooth movement and transitions
- **Visual Effects**: Attack indicators, health bars, and status effects
- **Color-coded Enemies**: Different enemy types have distinct colors and sizes

### Gameplay Features
- **Real-time Combat**: Fast-paced action with immediate feedback
- **Multiple Enemy Types**: 5 different enemy types with unique behaviors:
  - **Stickfigure** (Red): Fast and weak
  - **Cow** (Brown): Slow but strong  
  - **Rambo** (Magenta): Balanced and aggressive
  - **Dragon** (Green): Powerful with high health
  - **Big** (Orange): Massive size and damage
- **AI Behavior**: Enemies wander, chase, and attack with realistic AI
- **Scoring System**: Earn points for defeating enemies
- **Health System**: Take damage and heal using points

### Controls
- **WASD** or **Arrow Keys**: Move player
- **SPACE**: Attack nearby enemies
- **F**: Heal (costs 50 points)
- **ESC**: Quit game

## Installation

1. Install Python 3.7 or higher
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Game

```bash
python nkeyrollover_pygame.py
```

## Game Mechanics

### Player
- **Health**: 100 HP, decreases when taking damage
- **Movement**: 200 pixels/second speed
- **Attack**: 80-pixel range, 25 damage, 0.3-second duration
- **Healing**: Costs 50 points, restores 25 HP

### Enemies
- **Spawn**: New enemies spawn every 3 seconds at screen edges
- **AI States**:
  - **Wander**: Random movement when player not detected
  - **Chase**: Pursue player when within detection range
  - **Attack**: Deal damage when in attack range
  - **Dying**: Death animation before removal
- **Detection**: 150-pixel detection range for most enemies
- **Rewards**: 100 points per enemy defeated

### Difficulty Scaling
- Maximum 10 enemies on screen at once
- Enemies continuously spawn to maintain challenge
- Different enemy types provide varied combat experiences

## Technical Features

### Architecture
- **Entity-Component System**: Clean separation of game logic
- **State Management**: Proper game state handling
- **Event-driven Input**: Responsive controls with pygame events
- **Delta Time**: Frame-rate independent movement and timing

### Performance
- **Optimized Rendering**: Efficient drawing with pygame
- **Memory Management**: Proper cleanup of inactive entities
- **Collision Detection**: Fast distance-based collision system

## Differences from Original

### Improvements
- **Visual Appeal**: Modern graphics instead of ASCII
- **Smooth Movement**: Pixel-perfect movement vs. tile-based
- **Real-time Action**: No turn-based mechanics
- **Immediate Feedback**: Visual and audio cues
- **Simplified Controls**: Standard WASD movement

### Preserved Elements
- **Core Gameplay**: Beat-em-up with MOBA-style controls
- **Enemy AI**: Similar behavior patterns to original
- **Combat System**: Attack mechanics and damage dealing
- **Progression**: Score-based advancement

## Future Enhancements

Potential additions for future versions:
- **Sound Effects**: Audio feedback for actions
- **Particle Effects**: Visual effects for attacks and explosions
- **Weapon Types**: Different weapons with unique properties
- **Power-ups**: Temporary abilities and stat boosts
- **Levels**: Multiple areas with different challenges
- **Boss Battles**: Special challenging enemies
- **Multiplayer**: Local or online co-op play

## Code Structure

```
pygame_version/
├── nkeyrollover_pygame.py    # Main game file
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

### Key Classes
- **Game**: Main game loop and initialization
- **GameWorld**: World state and entity management
- **Player**: Player entity with movement and combat
- **Enemy**: AI-controlled enemy entities
- **Renderer**: Graphics and UI rendering
- **InputHandler**: Keyboard input processing

## License

This is a remake of the original "N Key Rollover" game. Please refer to the original project's license for usage terms.

## Contributing

Feel free to fork this project and submit pull requests for improvements or bug fixes!
