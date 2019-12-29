import imageio
from OpenGL.GL import *
from OpenGL.GLU import *

import json
import numpy as np
import os
import pathlib

class Icon:
    def __init__(self, filename):
        with open(filename, "r") as file:
            icon_data = json.load(file)

            folder = pathlib.Path(os.path.dirname(filename))
            image_filename = str(folder / icon_data["icon_image_file"])
            self._pxrange = icon_data["pxrange"]

            icon_image = imageio.imread(image_filename)
            assert icon_image.dtype == np.uint8
            assert len(icon_image.shape) == 3
            assert icon_image.shape[2] == 3

            icon_width = icon_image.shape[1]
            icon_height = icon_image.shape[0]

            # Flip y coord
            icon_texture_data = np.reshape(np.flipud(icon_image), -1)

            self._icon_texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self._icon_texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, icon_width, icon_height, 0, GL_RGB, GL_UNSIGNED_BYTE, icon_texture_data)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

    def destroy(self):
        glDeleteTextures(self._icon_texture)

    @property
    def icon_texture(self):
        return self._icon_texture

    @property
    def pxrange(self):
        return self._pxrange
