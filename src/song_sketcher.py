from OpenGL.GL import *
from OpenGL.GLU import *
import pygame
from pygame.locals import *

import drawing
import editor
import parameter
import timer
import units
import widget_manager

class SongSketcher:
    def __init__(self):
        pygame.init()

        # Do this early so OpenGL commands don't fail
        self._display_size = (800, 600)
        self._dpi = 96 # $TODO Query this somehow
        self._quit = False
        self._surface = pygame.display.set_mode(self._display_size, DOUBLEBUF | OPENGL)

        units.initialize(self._dpi)
        drawing.initialize()
        parameter.initialize()
        timer.initialize()
        widget_manager.initialize(self._display_size)

        self._editor = editor.Editor(self._display_size)

    def shutdown(self):
        self._editor.shutdown()

        widget_manager.shutdown()
        timer.shutdown()
        parameter.shutdown()
        drawing.shutdown()

    def run(self):
        fps = 60
        dt = 1.0 / float(fps)
        clock = pygame.time.Clock()

        while not self._quit:
            clock.tick(fps)

            parameter.update(dt)
            timer.update(dt)

            # Process events
            widget_manager.get().begin_process_events()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit = True # $TODO We should route this to the editor instead
                widget_manager.get().process_event(event)

            self._editor.update(dt)

            drawing.drawing_begin(self._display_size[0], self._display_size[1])
            widget_manager.get().draw()
            drawing.drawing_end()

            pygame.display.flip()

song_sketcher = SongSketcher()
song_sketcher.run()
song_sketcher.shutdown()