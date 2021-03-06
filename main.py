import OpenGL
OpenGL.ERROR_CHECKING = False # Enable this when modifying OpenGL code

from OpenGL.GL import *
import pygame
from pygame.locals import *

from song_sketcher import drawing
from song_sketcher import editor
from song_sketcher import engine
from song_sketcher import parameter
from song_sketcher import project_manager
from song_sketcher import settings
from song_sketcher import timer
from song_sketcher import units
from song_sketcher import widget_manager

class SongSketcher:
    def __init__(self):
        pygame.init()

        fullscreen = False

        # Do this early so OpenGL commands don't fail
        self._display_size = (1024, 768)
        self._dpi = 96 # $TODO Query this somehow
        self._quit = False
        if fullscreen:
            self._surface = pygame.display.set_mode((0, 0), FULLSCREEN | DOUBLEBUF | OPENGL)
            self._display_size = self._surface.get_size()
        else:
            self._surface = pygame.display.set_mode(self._display_size, DOUBLEBUF | OPENGL)

        units.initialize(self._dpi)
        drawing.initialize()
        parameter.initialize()
        timer.initialize()
        widget_manager.initialize(self._display_size)
        project_manager.initialize()
        engine.initialize()
        settings.initialize()

        self._editor = editor.Editor()

    def shutdown(self):
        self._editor.shutdown()

        settings.shutdown()
        engine.shutdown()
        project_manager.shutdown()
        widget_manager.shutdown()
        timer.shutdown()
        parameter.shutdown()
        drawing.shutdown()

    def run(self):
        fps = 60
        dt = 1.0 / float(fps)
        clock = pygame.time.Clock()

        while not self._editor.should_quit():
            clock.tick(fps)

            parameter.update(dt)
            timer.update(dt)

            # Process events
            widget_manager.get().begin_process_events()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._editor.request_quit()
                else:
                    widget_manager.get().process_event(event)

            self._editor.update(dt)

            drawing.drawing_begin(self._display_size[0], self._display_size[1])
            widget_manager.get().draw()
            drawing.drawing_end()

            pygame.display.flip()

song_sketcher = SongSketcher()
song_sketcher.run()
song_sketcher.shutdown()