from enum import Enum

from OpenGL.GL import *
from OpenGL.GLU import *

import font
import icon
import shader

_resource_registry = None

def initialize():
    global _resource_registry
    _resource_registry = _ResourceRegistry()

def shutdown():
    global _resource_registry
    if _resource_registry is not None:
        _resource_registry.shutdown()
        _resource_registry = None

class _ResourceRegistry:
    def __init__(self):
        self._shaders = []
        def add_shader(shader):
            self._shaders.append(shader)
            return shader

        self.fonts = {}
        def add_font(name, font):
            self.fonts[name] = font
            return font

        self.icons = {}
        def add_icon(name, icon):
            self.icons[name] = icon
            return icon

        self.rounded_rectangle_shader = add_shader(shader.Shader("shaders/rounded_rectangle.glsl"))
        self.font_shader = add_shader(shader.Shader("shaders/font.glsl"))
        self.icon_shader = add_shader(shader.Shader("shaders/icon.glsl"))
        self.spinner_shader = add_shader(shader.Shader("shaders/spinner.glsl"))
        self.waveform_shader = add_shader(shader.Shader("shaders/waveform.glsl"))

        add_font("arial", font.Font("fonts/arial.json"))

        add_icon("arrow_up", icon.Icon("icons/arrow_up.json"))
        add_icon("arrow_down", icon.Icon("icons/arrow_down.json"))
        add_icon("plus", icon.Icon("icons/plus.json"))
        add_icon("undo", icon.Icon("icons/undo.json"))
        add_icon("redo", icon.Icon("icons/redo.json"))
        add_icon("metronome", icon.Icon("icons/metronome.json"))

    def shutdown(self):
        for shader in self._shaders:
            shader.destroy()
        for font in self.fonts.values():
            font.destroy()
        for icon in self.icons.values():
            icon.destroy()

class HorizontalAlignment(Enum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2

class VerticalAlignment(Enum):
    TOP = 0
    MIDDLE = 1
    BASELINE = 2
    BOTTOM = 3

_top_scissor_state = None

class _ScissorState:
    def __init__(self, scissor_enabled, x1, y1, x2, y2, merge):
        self.scissor_enabled = scissor_enabled
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.merge = merge

        self.resolved_x1 = None
        self.resolved_y1 = None
        self.resolved_x2 = None
        self.resolved_y2 = None

    def __enter__(self):
        global _top_scissor_state

        if self.scissor_enabled:
            x_min = min(self.x1, self.x2)
            x_max = max(self.x1, self.x2)
            y_min = min(self.y1, self.y2)
            y_max = max(self.y1, self.y2)
            self.resolved_x1 = int(round(x_min))
            self.resolved_y1 = int(round(y_min))
            self.resolved_x2 = int(round(x_max))
            self.resolved_y2 = int(round(y_max))

            if self.merge and _top_scissor_state is not None and _top_scissor_state.scissor_enabled:
                # Merge by taking the max of mins and the min of maxes
                self.resolved_x1 = max(self.resolved_x1, _top_scissor_state.resolved_x1)
                self.resolved_x2 = min(self.resolved_x2, _top_scissor_state.resolved_x2)
                self.resolved_y1 = max(self.resolved_y1, _top_scissor_state.resolved_y1)
                self.resolved_y2 = min(self.resolved_y2, _top_scissor_state.resolved_y2)

        self.prev_scissor_state = _top_scissor_state
        _top_scissor_state = self
        self._apply()

    def __exit__(self, type, value, traceback):
        global _top_scissor_state
        assert _top_scissor_state is self
        _top_scissor_state = self.prev_scissor_state

        if self.prev_scissor_state is None:
            glDisable(GL_SCISSOR_TEST)
        else:
            self.prev_scissor_state._apply()

    def _apply(self):
        if self.scissor_enabled:
            glEnable(GL_SCISSOR_TEST)
            width = max(0, self.resolved_x2 - self.resolved_x1)
            height = max(0, self.resolved_y2 - self.resolved_y1)
            glScissor(self.resolved_x1, self.resolved_y1, width, height)
        else:
            glDisable(GL_SCISSOR_TEST)

def rgba(r, g, b, a = 1.0):
    return (r, g, b, a)

def rgba255(r, g, b, a = 255.0):
    return rgba(r / 255.0, g / 255.0, b / 255.0, a / 255.0)

def drawing_begin(viewport_width_pixels, viewport_height_pixels):
    glPushMatrix()
    glViewport(0, 0, viewport_width_pixels, viewport_height_pixels)
    gluOrtho2D(0.0, viewport_width_pixels, 0.0, viewport_height_pixels)

    glClear(GL_COLOR_BUFFER_BIT)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

def drawing_end():
    glPopMatrix()

def scissor(x1, y1, x2, y2, transform = None, merge = True):
    if transform is not None:
        x1, y1 = transform.transform_point((x1, y1))
        x2, y2 = transform.transform_point((x2, y2))
    return _ScissorState(True, x1, y1, x2, y2, merge)

def scissor_clear():
    return _ScissorState(False, 0.0, 0.0, 0.0, 0.0, False)

def draw_rectangle(
    x1, y1, x2, y2, color,
    border_thickness = 0.0, border_color = None, radius = 0.0,
    left_open = False, right_open = False, top_open = False, bottom_open = False):
    shader = _resource_registry.rounded_rectangle_shader
    if border_color is None or border_thickness == 0.0:
        border_color = color
    with shader.use():
        x_min = min(x1, x2) if not left_open else (x1 + x2) * 0.5
        x_max = max(x1, x2) if not right_open else (x1 + x2) * 0.5
        y_min = min(y1, y2) if not bottom_open else (y1 + y2) * 0.5
        y_max = max(y1, y2) if not top_open else (y1 + y2) * 0.5
        glUniform4f(shader.loc("rgba"), *_get_rgba(color))
        glUniform1f(shader.loc("border_thickness"), border_thickness)
        glUniform4f(shader.loc("border_rgba"), *_get_rgba(border_color))
        glUniform1f(shader.loc("radius"), radius)
        glUniform2f(shader.loc("xy1"), x1, y1)
        glUniform2f(shader.loc("xy2"), x2, y2)
        glUniform4f(shader.loc("xy_min_max"), x_min, y_min, x_max, y_max)
        _draw_quad(x1, y1, x2, y2)

# Returns (width, ascent, descent) where descent is negative
def measure_text(text, font_name, size):
    font_object = _resource_registry.fonts[font_name]
    width = 0.0
    x = 0.0
    prev_character_code = None
    for c in text:
        character_code = ord(c)
        if not font_object.has_glyph(character_code) and c != ' ':
            character_code = font.MISSING_CHARACTER_CODE

        x += font_object.get_advance_ems(character_code)
        width = max(width, x)
        if prev_character_code is not None:
            x += font_object.get_kerning_ems(prev_character_code, character_code)

        prev_character_code = character_code

    return (width * size, font_object.ascender_size_ems * size, font_object.descender_size_ems * size)

def draw_text(text, font_name, size, x, y, horizontal_alignment, vertical_alignment, color):
    # Currently doesn't support multi-line text
    shader = _resource_registry.font_shader
    font_object = _resource_registry.fonts[font_name]
    with shader.use():
        # Adjust our position so that (x,y) represents the left baseline of the first character
        width, ascent, descent = measure_text(text, font_name, size)
        x += {
            HorizontalAlignment.LEFT: 0.0,
            HorizontalAlignment.CENTER: width * -0.5,
            HorizontalAlignment.RIGHT: -width
        }[horizontal_alignment]

        y += {
            VerticalAlignment.TOP: -ascent,
            VerticalAlignment.MIDDLE: -0.5 * (descent + ascent), # Unfortunately we don't know cap height
            VerticalAlignment.BASELINE: 0.0,
            VerticalAlignment.BOTTOM: -descent
        }[vertical_alignment]

        glEnable(GL_TEXTURE_2D)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, font_object.glyph_texture)
        glUniform4f(shader.loc("rgba"), *_get_rgba(color))
        glUniform1i(shader.loc("font_texture"), 0)
        glUniform1f(shader.loc("pxrange"), font_object.pxrange)

        prev_character_code = None
        for c in text:
            character_code = ord(c)
            if not font_object.has_glyph(character_code) and c != ' ':
                character_code = font.MISSING_CHARACTER_CODE

            x1 = x - font_object.glyph_left_offset_ems * size
            y1 = y - font_object.glyph_baseline_offset_ems * size
            x2 = x1 + font_object.glyph_width_ems * size
            y2 = y1 + font_object.glyph_height_ems * size
            glyph = font_object.glyphs[character_code]

            if c != ' ':
                _draw_textured_quad(x1, y1, glyph.u1, glyph.v1, x2, y2, glyph.u2, glyph.v2)

            x += font_object.get_advance_ems(character_code) * size
            width = max(width, x)
            if prev_character_code is not None:
                x += font_object.get_kerning_ems(prev_character_code, character_code) * size

            prev_character_code = character_code

def draw_icon(icon_name, x1, y1, x2, y2, color):
    shader = _resource_registry.icon_shader
    icon = _resource_registry.icons[icon_name]
    with shader.use():
        glEnable(GL_TEXTURE_2D)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, icon.icon_texture)
        glUniform4f(shader.loc("rgba"), *_get_rgba(color))
        glUniform1i(shader.loc("icon_texture"), 0)
        glUniform1f(shader.loc("pxrange"), icon.pxrange)
        _draw_textured_quad(x1, y1, 0.0, 0.0, x2, y2, 1.0, 1.0)

def draw_spinner(x, y, color_inner, color_outer, color_outer_background, radius_inner, radius_outer, ratio):
    shader = _resource_registry.spinner_shader
    with shader.use():
        meter_a = 0.125
        meter_c = 0.875
        meter_b = meter_a + ratio * (meter_c - meter_a)

        glUniform4f(shader.loc("inner_rgba"), *_get_rgba(color_inner))
        glUniform4f(shader.loc("outer_rgba"), *_get_rgba(color_outer))
        glUniform4f(shader.loc("outer_background_rgba"), *_get_rgba(color_outer_background))
        glUniform1f(shader.loc("inner_radius"), radius_inner)
        glUniform1f(shader.loc("outer_radius"), radius_outer)
        glUniform1f(shader.loc("meter_a"), meter_a)
        glUniform1f(shader.loc("meter_b"), meter_b)
        glUniform1f(shader.loc("meter_c"), meter_c)
        glUniform2f(shader.loc("xy_center"), x, y)
        s = radius_outer
        _draw_quad(x - s, y - s, x + s, y + s)

def draw_waveform(
    x1, y1, x2, y2, waveform_texture, background_color, waveform_color,
    border_thickness = 0.0, border_color = None):
    shader = _resource_registry.waveform_shader
    if border_color is None or border_thickness == 0.0:
        border_color = color
    with shader.use():
        glEnable(GL_TEXTURE_1D)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_1D, waveform_texture)
        glUniform1i(shader.loc("waveform_texture"), 0)
        glUniform4f(shader.loc("background_rgba"), *_get_rgba(background_color))
        glUniform4f(shader.loc("waveform_rgba"), *_get_rgba(waveform_color))
        glUniform1f(shader.loc("border_thickness"), border_thickness)
        glUniform4f(shader.loc("border_rgba"), *_get_rgba(border_color))
        glUniform2f(shader.loc("xy1"), x1, y1)
        glUniform2f(shader.loc("xy2"), x2, y2)
        _draw_textured_quad(x1, y1, 0.0, 0.0, x2, y2, 1.0, 1.0)

def _draw_quad(x1, y1, x2, y2):
	glBegin(GL_TRIANGLE_STRIP)
	glVertex3f(x1, y1, 0.0)
	glVertex3f(x2, y1, 0.0)
	glVertex3f(x1, y2, 0.0)
	glVertex3f(x2, y2, 0.0)
	glEnd()

def _draw_textured_quad(x1, y1, u1, v1, x2, y2, u2, v2):
    glBegin(GL_TRIANGLE_STRIP)
    glTexCoord2f(u1, v1)
    glVertex3f(x1, y1, 0.0)
    glTexCoord2f(u2, v1)
    glVertex3f(x2, y1, 0.0)
    glTexCoord2f(u1, v2)
    glVertex3f(x1, y2, 0.0)
    glTexCoord2f(u2, v2)
    glVertex3f(x2, y2, 0.0)
    glEnd()

def _get_rgba(color):
    if len(color) == 3:
        return (color[0], color[1], color[2], 1.0)
    else:
        assert len(color) == 4
        return color
