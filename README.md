# nkeyrollover

* ASCII Beat Em Up 
* With MOBA controls

Follow the adventures of ASCIIMAN.

## How to Play

### Controls

**Movement:**
- **Arrow Keys** or **WASD** - Move character
- **Shift + Left/Right** - Strafe movement (move without changing direction)

**Combat:**
- **1-4** - Attack abilities (primary, secondary, tertiary, special)
- **Q, W, E, R** - Skill slots (heal, block, cleave, etc.)

**Game Controls:**
- **P** - Pause/Unpause
- **ESC** - Quit game  
- **F1** - Toggle statistics
- **F2** - Toggle debug log

### Gameplay
- Navigate through ASCII dungeons fighting enemies
- Use different attack combinations and skills
- Manage health and resources strategically
- Progress through multiple scenes and challenges

## History Lesson 

In the early days, computers were feed using paper punch cards, and produced results printed on paper. 

Then mainframes came around, where you could actually type on a keyboard, instead
of feeding it paper, and it showed the result on a primitive monitor, instead
of printing the result. Multi user support was developed, so that more than
one person can use the million dollar computer at once. Each at their own terminal. This was the short time where ASCII games were the only games available. 

Shortly after, 8-bit home computers were developed, and those with graphic
processing units quickly gained worldwide adoption (Commodore 64, Amiga). 
They could be used to play games, with graphics!

The timeframe for ASCII games was very short, and the art was lost forever. 

Or was it?


## Requirements

* Python 3.7+
* Dependencies: future, wcwidth, pywin32, pyyaml, pygame

## Running the Game

### Original ASCII Version
```bash
python nkeyrollover.py
```

### Pygame Port (Recommended)
```bash
cd pygame_full_port
python main.py
```

### Telnet Version
```
telnet dobin.ch
```


## Miscellaneous

### Mypy

```
python3.7 -m mypy nkeyrollover.py
```

VSC settings.json:
```
    "python.linting.flake8Args": ["--ignore=E231,E203,E303,E252,E251", "--max-line-length=88"],
```

### Unit tests

```
python3.7 -m unittest
```

### Performance tests 

```
python3.7 -m cProfile -s time -o perf.txt nkeyrollover.py
python3.7 readperf.py
```

## Telnet config 

Install: 
```
# apt install telnet telnetd
# cd /opt
# git clone https://github.com/dobin/nkeyrollover.git
# touch nkeyrollover/app.log
# chown game:game nkeyrollover/app.log
```

Configure:
```
# adduser game # password game
```

### With password

```
# chsh -s '/opt/nkeyrollover/nkeyrollover.py' game
```

### Without password

man telnetd:
```
     -L loginprg  This option may be used to specify a different login program.  By default, /usr/lib/telnetlogin is used.

```

inetd.conf:
```
telnet          stream  tcp     nowait  telnetd /usr/sbin/tcpd  /usr/sbin/in.telnetd -L /opt/nkeyrollover/nkeyrollover-inetd.sh
```

```
# service inetd restart
```

## Install?

Ubuntu 18.04:

```
sudo apt install python3-pip  # Install python 3.6 pip
python3.7 -m pip install pip  # install 3.7 pip
python3.7 -m pip install -r requirements.txt
```