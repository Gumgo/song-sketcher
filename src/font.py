import freetype
import imageio
from OpenGL.GL import *
from OpenGL.GLU import *

import json
import numpy as np
import os
import pathlib

MISSING_CHARACTER_CODE = 0x25A1

class Glyph:
    def __init__(self, u1, v1, u2, v2):
        self.u1 = u1
        self.v1 = v1
        self.u2 = u2
        self.v2 = v2

# $TODO cache info about all loaded glyphs - querying advance and kerning shows up high in the profiler report
class Font:
    def __init__(self, filename):
        with open(filename, "r") as file:
            font_data = json.load(file)

            folder = pathlib.Path(os.path.dirname(filename))
            font_filename = str(folder / font_data["font_file"])
            image_filename = str(folder / font_data["font_image_file"])
            self._glyph_width = font_data["glyph_width"]
            self._glyph_height = font_data["glyph_height"]
            self._glyph_offset_x = font_data["glyph_offset_x"]
            self._glyph_offset_y = font_data["glyph_offset_y"]
            self._glyph_scale = font_data["glyph_scale"]
            self._glyph_pxrange = font_data["glyph_pxrange"]

            self._font = freetype.Face(font_filename)

            atlas_image = imageio.imread(image_filename)
            assert atlas_image.dtype == np.uint8
            assert len(atlas_image.shape) == 3
            assert atlas_image.shape[2] == 3

            atlas_width = atlas_image.shape[1]
            atlas_height = atlas_image.shape[0]

            # Flip y coord
            atlas_texture_data = np.reshape(np.flipud(atlas_image), -1)
            self.glyphs = {}
            for i, glyph in enumerate(font_data["glyphs"]):
                character = glyph["character"]
                self.glyphs[character] = i

                # Shrink by 1 pixel to pad against adjacent glyphs
                atlas_x1 = glyph["atlas_x"] + 1
                atlas_y2 = glyph["atlas_y"] + 1
                atlas_x2 = atlas_x1 + self._glyph_width - 1
                atlas_y1 = atlas_y2 + self._glyph_height - 1

                self.glyphs[character] = Glyph(
                    atlas_x1 / atlas_width,
                    1.0 - atlas_y1 / atlas_height,
                    atlas_x2 / atlas_width,
                    1.0 - atlas_y2 / atlas_height)

            self._glyph_texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self._glyph_texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, atlas_width, atlas_height, 0, GL_RGB, GL_UNSIGNED_BYTE, atlas_texture_data)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

    def destroy(self):
        glDeleteTextures(self._glyph_texture)

    # The atlas texture of all glyphs
    @property
    def glyph_texture(self):
        return self._glyph_texture

    @property
    def glyph_width_ems(self):
        return ((self._glyph_width - 2) * 64.0) / (self._glyph_scale * self._font.units_per_EM) # Subtact 2 due to padding

    @property
    def glyph_height_ems(self):
        return ((self._glyph_height - 2) * 64.0) / (self._glyph_scale * self._font.units_per_EM) # Subtact 2 due to padding

    @property
    def glyph_left_offset_ems(self):
        return ((self._glyph_offset_x - 1) * 64.0) / (self._glyph_scale * self._font.units_per_EM) # Subtact 1 due to padding

    # Offset is from the bottom of the glyph
    @property
    def glyph_baseline_offset_ems(self):
        return ((self._glyph_offset_y - 1) * 64.0) / (self._glyph_scale * self._font.units_per_EM) # Subtact 1 due to padding

    # The size of ascenders
    @property
    def ascender_size_ems(self):
        return self._font.ascender / self._font.units_per_EM

    # The size of descenders - note that this is negative
    @property
    def descender_size_ems(self):
        return self._font.descender / self._font.units_per_EM

    # Number of ems between two separate lines
    @property
    def baseline_distance_ems(self):
        return self._font.height / self._font.units_per_EM

    @property
    def pxrange(self):
        return self._glyph_pxrange

    def has_glyph(self, character_code):
        return character_code in self.glyphs

    def get_advance_ems(self, character_code):
        glyph_index = self._font.get_char_index(character_code)
        return self._font.get_advance(glyph_index, freetype.FT_LOAD_NO_SCALE) / self._font.units_per_EM

    # Kerning is negative
    def get_kerning_ems(self, left_character_code, right_character_code):
        left_glyph_index = self._font.get_char_index(left_character_code)
        right_glyph_index = self._font.get_char_index(right_character_code)
        return self._font.get_kerning(
            left_glyph_index,
            right_glyph_index,
            freetype.FT_KERNING_UNSCALED).x / self._font.units_per_EM
