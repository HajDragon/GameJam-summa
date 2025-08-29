import logging
import esper

from system.graphics.particleprocessor import ParticleProcessor
from .mapmanager import MapManager
from .viewport import Viewport
from .textureemiter import TextureEmiter
from system.graphics.renderable import Renderable
from system.graphics.renderableprocessor import RenderableProcessor
from system.gamelogic.attackableprocessor import AttackableProcessor
from system.gamelogic.enemyprocessor import EnemyProcessor
from system.gamelogic.playerprocessor import PlayerProcessor
from system.gamelogic.offensiveskillprocessor import OffensiveSkillProcessor
from system.graphics.sceneprocessor import SceneProcessor
from system.graphics.renderableminimal import RenderableMinimal
from system.gamelogic.offensiveattackprocessor import OffensiveAttackProcessor
from system.gamelogic.movementprocessor import MovementProcessor
from system.gamelogic.aiprocessor import AiProcessor
from system.gamelogic.gametimeprocessor import GametimeProcessor
from system.gamelogic.damageprocessor import DamageProcessor
from system.gamelogic.passiveattackprocessor import PassiveAttackProcessor
from system.gamelogic.defenseprocessor import DefenseProcessor
from system.io.inputprocessor import InputProcessor
from system.graphics.characteranimationprocessor import CharacterAnimationProcessor
from system.graphics.renderableminimalprocessor import RenderableMinimalProcessor
from system.graphics.environmentprocessor import EnvironmentProcessor
from system.singletons.particleemiter import ParticleEmiter
from system.gamelogic.onhitprocessor import OnhitProcessor
from system.graphics.particleemiterprocessor import ParticleEmiterProcessor
from system.graphics.particlemirageemiterprocessor import ParticleMirageEmiterProcessor
from game.scenemanager import SceneManager
from game.statusbar import StatusBar
from utilities.entityfinder import EntityFinder
from messaging import messaging
from directmessaging import directMessaging
from system.singletons.renderablecache import renderableCache
from texture.filetextureloader import fileTextureLoader
from game.offenseloader.fileoffenseloader import fileOffenseLoader
from utilities.colorpalette import ColorPalette
from utilities.color import Color
from utilities.colortype import ColorType
from config import Config

logger = logging.getLogger(__name__)


class Game(object):
    def __init__(self, win, menuwin):
        self.pause :bool = False
        self.gameRunning :bool = True
        self.showStats = False
        self.showLog = False
        self.fullscreen :bool = False

        self.win = win
        self.world :esper.World = esper.World()

        self.viewport :Viewport = Viewport(win=win, world=self)
        self.statusBar :StatusBar = StatusBar(world=self, viewport=self.viewport)

        fileTextureLoader.loadFromFiles()
        fileOffenseLoader.loadFromFiles()

        textureEmiter :TextureEmiter = TextureEmiter(
            viewport=self.viewport,
            world=self.world)
        mapManager :MapManager = MapManager(viewport=self.viewport)
        sceneManager :SceneManager = SceneManager(
            viewport=self.viewport,
            world=self.world,
            mapManager=mapManager)
        renderableCache.init(viewport=self.viewport)
        particleEmiter = ParticleEmiter(viewport=self.viewport)

        particleProcessor = ParticleProcessor(
            viewport=self.viewport, particleEmiter=particleEmiter)
        gametimeProcessor = GametimeProcessor()
        aiProcessor = AiProcessor()
        characterAnimationProcessor = CharacterAnimationProcessor()
        playerProcessor = PlayerProcessor(
            viewport=self.viewport)
        enemyProcessor = EnemyProcessor(
            viewport=self.viewport)
        attackableProcessor = AttackableProcessor()
        offensiveAttackProcessor = OffensiveAttackProcessor()
        offensiveSkillProcessor = OffensiveSkillProcessor()
        movementProcessor = MovementProcessor(mapManager)
        inputProcessor = InputProcessor()
        renderableProcessor = RenderableProcessor(
            textureEmiter=textureEmiter,
            particleEmiter=particleEmiter)
        renderableMinimalProcessor = RenderableMinimalProcessor(
            viewport=self.viewport,
            textureEmiter=textureEmiter)
        sceneProcessor = SceneProcessor(
            viewport=self.viewport,
            sceneManager=sceneManager,
        )
        particleEmiterProcessor = ParticleEmiterProcessor(
            particleEmiter=particleEmiter
        )
        damageProcessor = DamageProcessor()
        environmentProcessor = EnvironmentProcessor(
            viewport=self.viewport, mapManager=mapManager)
        passiveAttackProcessor = PassiveAttackProcessor()
        defenseProcessor = DefenseProcessor()
        onhitProcessor = OnhitProcessor()
        emitMirageParticleEffect = ParticleMirageEmiterProcessor(
            particleEmiter=particleEmiter
        )

        self.sceneProcessor :SceneProcessor = sceneProcessor  # show F1 stats
        # self.viewport is already assigned above
        self.mapManager :MapManager = mapManager  # map is handled here in game
        self.sceneManager :SceneManager = sceneManager  # to check for showmap here in game

        self.bg = self.createBg(Config.columns, Config.rows)

        # Lots of comments to check if the order of the processors really work,
        # as Messaging looses all messages on every iteration (use DirectMessaging
        # instead)
        self.world.add_processor(gametimeProcessor)

        # KeyboardInput:getInput()
        # p generate: Message            PlayerKeypress

        # p handle:   Message            PlayerKeyPress (movement)
        # p generate: DirectMessage      movePlayer
        self.world.add_processor(inputProcessor)

        # p handle:   DirectMessage      movePlayer
        # e handle:   DirectMessage      moveEnemy
        # p generate: Message            PlayerLocation
        # p generate: Message            EmitMirageParticleEffect (appear)
        # x generate: Message            EntityMoved
        self.world.add_processor(movementProcessor)

        # p handle:   Message            PlayerLocation
        # e generate: DirectMessage      moveEnemy
        # x generate: Message            EmitTextureMinimal
        self.world.add_processor(aiProcessor)

        # e handle:   DirectMessage      moveEnemy
        # p handle:   Message            PlayerKeyPress (space/attack, weaponselect)
        # p generate: Message            PlayerAttack (via OffensiveAttack)
        # x generate: Message            AttackAt (via OffensiveAttack)
        # x generate: Message            EmitActionTexture (via OffensiveAttack)
        # x generate: Message            EmitTextureMinimal (via OffensiveAttack)
        self.world.add_processor(offensiveAttackProcessor)

        # p handle:   Message            PlayerKeyPress (skill activate)
        # x generate: Message            EmitParticleEffect (skill)
        # x generate: DirectMessage      activateSpeechBubble
        self.world.add_processor(offensiveSkillProcessor)

        # x handle:   Message            EmitParticleEffect
        # x generate: Message            AttackAt (for skills)
        self.world.add_processor(particleEmiterProcessor)

        # x generate: Message            AttackAt (passive DoT)
        self.world.add_processor(passiveAttackProcessor)

        # x generate: Message            AttackAt (via particle, dmg on move)
        self.world.add_processor(particleProcessor)

        # x handle:   Message            AttackAt
        # x generate: Message            EmitMirageParticleEffect (impact)
        self.world.add_processor(onhitProcessor)
        
        # x handle:   Message            AttackAt
        # x generate: DirectMessage      receiveDamage
        self.world.add_processor(damageProcessor)

        # x change:   Message            receiveDamage
        # x generate: Message            EmitMirageParticleEffect (floating 'Blocked')
        self.world.add_processor(defenseProcessor)

        # x handle:   DirectMessage      receiveDamage
        # x generate: Message            EntityStun
        # x generate: Message            EntityEndStun
        # x generate: Message            EntityDying
        # x generate: Message            EmitTexture
        # x generate: Message            Gameover
        # x generate: Message            EmitMirageParticleEffect (floating Damage)
        self.world.add_processor(attackableProcessor)

        # x handle:   Message            EmitMirageParticleEffect
        self.world.add_processor(emitMirageParticleEffect)

        # p handle:   Message            PlayerLocation
        # x handle:   Message            EntityDying
        # p handle:   Message            PlayerKeypress
        # x handle:   Message            Gameover
        # e generate: Message            SpawnEnemy
        # p generate: Message            SpawnPlayer
        # x generate: DirectMessage      activateSpeechBubble
        # x generate: Message            ScreenMove
        # x generate: Message            GameStart
        self.world.add_processor(sceneProcessor)

        # x handle:   Message            ScreenMove
        # x handle:   Message            GameStart
        self.world.add_processor(environmentProcessor)

        # e handle:   Message            SpawnEnemy
        # e generate: Message            EntityAttack
        # x generate: Message            EntityDead
        self.world.add_processor(enemyProcessor)

        # p handle:   Message            SpawnPlayer
        # p handle:   Message            PlayerAttack
        self.world.add_processor(playerProcessor)

        # e handle:   Message            EntityDying
        # p handle:   Message            PlayerAttack
        # x handle:   Message            AttackWindup
        # x handle:   Message            EntityAttack
        # x handle:   Message            EntityMoved
        # x handle:   Message            EntityStun
        # x handle:   Message            EntityEndStun
        self.world.add_processor(characterAnimationProcessor)

        # x handle:   Message            EmitTextureMinimal
        # x handle:   Message            EmitTexture
        self.world.add_processor(renderableMinimalProcessor)

        # x handle:   DirectMessage      activateSpeechBubble (emit)
        # x generate: DirectMessage      activateSpeechBubble (because of damage)
        self.world.add_processor(renderableProcessor)


    def draw1(self, frame :int):
        """Draws backmost layer (e.g. map)"""
        # clear buffer
        self.viewport.win._buffer._double_buffer = self.copyBg()

        if self.sceneManager.currentScene.showMap():
            self.mapManager.draw()


    def copyBg(self):
        box = [line[:] for line in self.bg]
        return box


    def createBg(self, width, height, uni=False):
        box = []
        width = self.viewport.win._buffer._width
        height = self.viewport.win._buffer._height

        fg, attr = ColorPalette.getColorByColor(Color.black)
        bg, _ = ColorPalette.getColorByColor(Color.black)
        w = 1

        tl = (ord(u"┌"), fg, attr, bg, w)
        tr = (ord(u"┐"), fg, attr, bg, w)
        bl = (ord(u"└"), fg, attr, bg, w)
        br = (ord(u"┘"), fg, attr, bg, w)
        h = (ord(u"─"), fg, attr, bg, w)
        v = (ord(u"│"), fg, attr, bg, w)
        s = (ord(u" "), fg, attr, bg, w)

        meWidth = Config.columns
        meHeight = Config.rows

        # top line
        line = []
        line.append(tl)
        n = 0
        while n < meWidth - 2:
            line.append(h)
            n += 1
        line.append(tr)
        while n < width:
            line.append(s)
            n += 1
        box.append(line)

        # middle
        line = []
        line.append(v)
        n = 0
        while n < meWidth - 2:
            line.append(s)
            n += 1
        line.append(v)

        # rest
        while n < width:
            line.append(s)
            n += 1
        for _ in range(meHeight - 2):
            box.append(line)

        # bottom line
        line = []
        line.append(bl)
        n = 0
        while n < meWidth - 2:
            line.append(h)
            n += 1
        line.append(br)
        while n < width:
            line.append(s)
            n += 1
        box.append(line)

        # rest
        y = meHeight
        while y < height:
            line = []
            n = 0
            while n < width:
                line.append(s)
                n += 1
            y += 1
            box.append(line)

        return box


    def advance(self, deltaTime :float, frame :int):
        """Advance game, and draw game entities (e.g. player, effects)"""
        if self.pause:
            return

        messaging.setFrame(frame)
        directMessaging.setFrame(frame)

        self.world.process(deltaTime)  # this also draws
        self.mapManager.advance(deltaTime)

        messaging.reset()


    def draw2(self, frame :int):
        """Draws foremost layer (e.g. "pause" sign)"""
        if self.sceneManager.currentScene.showMap():
            self.statusBar.drawStatusbar()

        if self.showStats:
            self.drawStats()

        # not drawing related, but who cares
        if frame % 1000 == 0:
            self.logEntityStats()

        if self.pause:
            color, attr = ColorPalette.getColorByColor(Color.white)
            self.viewport.addstr(
                12,
                40,
                "Paused",
                color,
                attr)


    def logEntityStats(self):
        renderableMinimal = 0
        for ent, rend in self.world.get_component(RenderableMinimal):
            renderableMinimal += 1

        renderable = 0
        for ent, rend in self.world.get_component(Renderable):
            renderable += 1

        logger.info("Stats: Renderable: {}  RenderableMinimal: {}".format(
            renderable, renderableMinimal
        ))


    def drawStats(self):
        x = 2
        y = 1
        color, attr = ColorPalette.getColorByColorType(ColorType.menu)

        o = []

        enemiesAlive = EntityFinder.numEnemies(
            world=self.world)
        enemiesAttacking = EntityFinder.numEnemiesInState(
            world=self.world, state='attack')
        enemiesChasing = EntityFinder.numEnemiesInState(
            world=self.world, state='chase')
        enemiesWandering = EntityFinder.numEnemiesInState(
            world=self.world, state='wander')

        o.append("Enemies:")
        o.append("  Alive     : {}".format(enemiesAlive))
        o.append("  Attacking : {}".format(enemiesAttacking))
        o.append("  Chasing   : {}".format(enemiesChasing))
        o.append("  Wandering: {}".format(enemiesWandering))

        playerEntity = EntityFinder.findPlayer(self.world)
        playerRenderable = self.world.component_for_entity(
            playerEntity, Renderable)

        o.append('Player:')
        o.append('  Location:' + str(playerRenderable.getLocation()))

        o.append('Scene:')
        o.append('  Name:' + self.sceneManager.currentScene.name)
        o.append('  Scne State:' + str(self.sceneProcessor.state))
        o.append('  Enemies Alive:' + str(self.sceneProcessor.numEnemiesAlive()))
        o.append('  Enemies Visible:' + str(self.sceneProcessor.numEnemiesVisible()))

        n = 0
        while n < len(o):
            self.viewport.addstr(y + n, x, o[n], color=color, attr=attr)
            n += 1


    def quitGame(self):
        self.gameRunning = False


    def togglePause(self):
        self.pause = not self.pause


    def toggleStats(self):
        self.showStats = not self.showStats


    def toggleLog(self):
        self.showLog = not self.showLog

    def toggleFullscreen(self):
        self.fullscreen = not self.fullscreen
        logger.info(f"Fullscreen toggled to: {self.fullscreen}")
        
        # On Windows, we can try to maximize/restore the console window
        try:
            import sys
            if sys.platform == "win32":
                import win32gui
                import win32console
                
                # Get the console window handle
                console_window = win32console.GetConsoleWindow()
                
                if self.fullscreen:
                    # Set large buffer size for fullscreen (approximately 1920x1080 in characters)
                    fullscreen_width = 240  # ~1920 pixels / 8 pixels per char
                    fullscreen_height = 67  # ~1080 pixels / 16 pixels per char
                    
                    try:
                        console_buffer = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
                        
                        # Set console buffer size first
                        coord = win32console.PyCOORDType(fullscreen_width, fullscreen_height)
                        console_buffer.SetConsoleScreenBufferSize(coord)
                        
                        # Set window size to match buffer (make it as large as possible)
                        rect = win32console.PySMALL_RECTType(0, 0, fullscreen_width - 1, fullscreen_height - 1)
                        console_buffer.SetConsoleWindowInfo(True, rect)
                        
                        # Maximize the window after setting buffer size
                        win32gui.ShowWindow(console_window, 3)  # SW_MAXIMIZE = 3
                        
                        # Update config with new dimensions
                        Config.columns = fullscreen_width
                        Config.rows = fullscreen_height
                        
                        # Update drawable areas proportionally
                        Config.areaDrawable['maxx'] = fullscreen_width - 1
                        Config.areaDrawable['maxy'] = fullscreen_height - 1
                        Config.areaMoveable['maxx'] = fullscreen_width - 1
                        Config.areaMoveable['maxy'] = fullscreen_height - 1
                        
                        # Adjust borders proportionally
                        Config.moveBorderRight = int(fullscreen_width * 0.75)
                        Config.moveBorderLeft = int(fullscreen_width * 0.1)
                        
                        logger.info(f"Fullscreen mode: {fullscreen_width}x{fullscreen_height}")
                        
                        # Refresh viewport
                        self.viewport.refreshScreenSize()
                        
                        # Force a complete screen refresh by updating the screen object
                        try:
                            # Debug: Check current screen dimensions
                            logger.info(f"Current screen object: width={getattr(self.win, '_width', 'unknown')}, height={getattr(self.win, '_height', 'unknown')}")
                            
                            # Update ALL possible dimension attributes in the screen object
                            dimension_attrs = ['_width', '_height', 'width', 'height', '_max_width', '_max_height']
                            for attr in dimension_attrs:
                                if hasattr(self.win, attr):
                                    if 'width' in attr:
                                        setattr(self.win, attr, fullscreen_width)
                                    elif 'height' in attr:
                                        setattr(self.win, attr, fullscreen_height)
                            
                            # Force clear the entire screen buffer and reset
                            self.win.clear()
                            self.win.move(0, 0)
                            
                            # Also force a refresh of the entire drawing area
                            for y in range(fullscreen_height):
                                for x in range(fullscreen_width):
                                    try:
                                        self.win.print_at(' ', x, y, 7)  # Fill with spaces
                                    except:
                                        break  # Stop if we hit a boundary
                                        
                            logger.info(f"Screen object updated and filled to use full {fullscreen_width}x{fullscreen_height} area")
                        except Exception as e:
                            logger.error(f"Error updating screen object dimensions: {e}")
                        
                    except Exception as e:
                        logger.error(f"Error setting fullscreen dimensions: {e}")
                        # Fallback to just maximizing the window
                        win32gui.ShowWindow(console_window, 3)  # SW_MAXIMIZE = 3
                        
                else:
                    # Restore to normal size
                    normal_width = 80
                    normal_height = 25
                    
                    try:
                        console_buffer = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
                        
                        # Restore window first
                        win32gui.ShowWindow(console_window, 1)  # SW_NORMAL = 1
                        
                        # Set console buffer size back to normal
                        coord = win32console.PyCOORDType(normal_width, normal_height)
                        console_buffer.SetConsoleScreenBufferSize(coord)
                        
                        # Set window size to match buffer
                        rect = win32console.PySMALL_RECTType(0, 0, normal_width - 1, normal_height - 1)
                        console_buffer.SetConsoleWindowInfo(True, rect)
                        
                        logger.info(f"Console buffer restored to {normal_width}x{normal_height}")
                        
                    except Exception as e:
                        logger.error(f"Error restoring console buffer: {e}")
                        # Fallback to just restoring window
                        win32gui.ShowWindow(console_window, 1)  # SW_NORMAL = 1
                    
                    # Restore original dimensions
                    Config.columns = normal_width
                    Config.rows = normal_height
                    Config.areaDrawable['maxx'] = 79
                    Config.areaDrawable['maxy'] = 24
                    Config.areaMoveable['maxx'] = 79
                    Config.areaMoveable['maxy'] = 24
                    Config.moveBorderRight = 60
                    Config.moveBorderLeft = 8
                    
                    logger.info("Screen restored to original size: 80x25")
                    
                    # Refresh viewport
                    self.viewport.refreshScreenSize()
                    
                    # Force a complete screen refresh by updating the screen object
                    try:
                        # Update the screen object's internal understanding of dimensions
                        self.win._width = normal_width
                        self.win._height = normal_height
                        
                        # Clear the buffer
                        self.win.clear()
                        
                        logger.info(f"Screen object restored to {normal_width}x{normal_height}")
                    except Exception as e:
                        logger.error(f"Error restoring screen object dimensions: {e}")
                
                # Force screen refresh
                self.win.clear()
                self.win.refresh()
                    
                logger.info(f"Console window {'maximized' if self.fullscreen else 'restored'}")
        except ImportError:
            logger.warning("Win32 modules not available - fullscreen toggle not supported")
        except Exception as e:
            logger.error(f"Error toggling fullscreen: {e}")
