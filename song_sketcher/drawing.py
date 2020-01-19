import ctypes
from enum import Enum
import os

from OpenGL.GL import *

from song_sketcher import font
from song_sketcher import icon
from song_sketcher import shader
from song_sketcher import transform

_render_cache = None
_resource_registry = None
_projection_matrix = None

def initialize():
    global _render_cache
    global _resource_registry
    _render_cache = _RenderCache()
    _resource_registry = _ResourceRegistry()

def shutdown():
    global _render_cache
    global _resource_registry
    if _resource_registry is not None:
        _resource_registry.shutdown()
        _resource_registry = None
    if _render_cache is not None:
        _render_cache.shutdown()
        _render_cache = None

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

        self.rounded_rectangle_shader = add_shader(shader.Shader(os.path.join("resources", "shaders", "rounded_rectangle.glsl")))
        self.font_shader = add_shader(shader.Shader(os.path.join("resources", "shaders", "font.glsl")))
        self.icon_shader = add_shader(shader.Shader(os.path.join("resources", "shaders", "icon.glsl")))
        self.spinner_shader = add_shader(shader.Shader(os.path.join("resources", "shaders", "spinner.glsl")))
        self.waveform_shader = add_shader(shader.Shader(os.path.join("resources", "shaders", "waveform.glsl")))

        add_font("arial", font.Font(os.path.join("resources", "fonts", "arial.json")))

        add_icon("accept", icon.Icon(os.path.join("resources", "icons", "accept.json")))
        add_icon("reject", icon.Icon(os.path.join("resources", "icons", "reject.json")))
        add_icon("arrow_down", icon.Icon(os.path.join("resources", "icons", "arrow_down.json")))
        add_icon("arrow_up", icon.Icon(os.path.join("resources", "icons", "arrow_up.json")))

        add_icon("new", icon.Icon(os.path.join("resources", "icons", "new.json")))
        add_icon("load", icon.Icon(os.path.join("resources", "icons", "load.json")))
        add_icon("save", icon.Icon(os.path.join("resources", "icons", "save.json")))
        add_icon("save_as", icon.Icon(os.path.join("resources", "icons", "save_as.json")))
        add_icon("settings", icon.Icon(os.path.join("resources", "icons", "settings.json")))
        add_icon("quit", icon.Icon(os.path.join("resources", "icons", "quit.json")))

        add_icon("record", icon.Icon(os.path.join("resources", "icons", "record.json")))
        add_icon("play", icon.Icon(os.path.join("resources", "icons", "play.json")))
        add_icon("pause", icon.Icon(os.path.join("resources", "icons", "pause.json")))
        add_icon("stop", icon.Icon(os.path.join("resources", "icons", "stop.json")))
        add_icon("delete", icon.Icon(os.path.join("resources", "icons", "delete.json")))
        add_icon("metronome", icon.Icon(os.path.join("resources", "icons", "metronome.json")))
        add_icon("metronome_disabled", icon.Icon(os.path.join("resources", "icons", "metronome_disabled.json")))

        add_icon("undo", icon.Icon(os.path.join("resources", "icons", "undo.json")))
        add_icon("redo", icon.Icon(os.path.join("resources", "icons", "redo.json")))

        add_icon("plus", icon.Icon(os.path.join("resources", "icons", "plus.json")))

    def shutdown(self):
        for shader in self._shaders:
            shader.destroy()
        for font in self.fonts.values():
            font.destroy()
        for icon in self.icons.values():
            icon.destroy()

class _RenderCacheType(Enum):
    TEXT = 0

class _RenderCacheData:
    def __init__(self):
        self.used_this_frame = True

    def destroy(self):
        pass

class _RenderCache:
    def __init__(self):
        # Maps (_RenderCacheType, key_data) -> (_RenderCacheData)
        self._cache = {}

    def shutdown(self):
        self.begin_frame()
        self.end_frame()
        assert len(self._cache) == 0

    # data is added using create_data_func if the type/key doesn't already exist
    def get_data(self, data_type, key, create_data_func):
        cache_key = (data_type, key)
        data = self._cache.get(cache_key, None)
        if data is None:
            data = create_data_func()
            assert isinstance(data, _RenderCacheData)
            self._cache[cache_key] = data
        data.used_this_frame = True
        return data

    def begin_frame(self):
        for data in self._cache.values():
            data.used_this_frame = False

    def end_frame(self):
        keys_to_delete = [k for k, v in self._cache.items() if not v.used_this_frame]
        for key in keys_to_delete:
            self._cache.pop(key).destroy()

class _ProjectionMatrix:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    # This returns an OpenGL-compatible matrix
    def __mul__(self, transform):
        # This represents a call to glOrtho(l, r, b, t, n, f), with
        # l = 0
        # r = width
        # b = 0
        # t = height
        # n = -1
        # f = 1
        # glOrtho() produces the matrix:
        # [ 2/(r-l)     0         0     -(r+l)/(r-l) ]
        # [    0     2/(t-b)      0     -(t+b)/(t-b) ]
        # [    0        0     -2/(f-n)  -(f+n)/(f-n) ]
        # [    0        0         0           1      ]
        # Substituting, we get:
        # [ 2/w   0    0  -1 ]
        # [  0   2/h   0  -1 ]
        # [  0    0   -1   0 ]
        # [  0    0    0   1 ]
        # Multiplying with a Transform object, we get:
        # [ 2/w   0    0  -1 ]   [ 1  0  0  x ]   [ 2/w   0    0  2x/w - 1 ]
        # [  0   2/h   0  -1 ] * [ 0  1  0  y ] = [  0   2/h   0  2y/h - 1 ]
        # [  0    0   -1   0 ]   [ 0  0  1  0 ]   [  0    0   -1     0     ]
        # [  0    0    0   1 ]   [ 0  0  0  1 ]   [  0    0    0     1     ]
        # Transpose this result for OpenGL matrix format
        w2 = 2.0 / self.width
        h2 = 2.0 / self.height
        return [
            w2, 0.0, 0.0, 0.0,
            0.0, h2, 0.0, 0.0,
            0.0, 0.0, -1.0, 0.0,
            w2 * transform.x - 1.0, h2 * transform.y - 1.0, 0.0, 1.0
        ]

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

def darken_color(color, darkness):
    rgb = tuple(c * (1.0 - darkness) for c in color[:3])
    return tuple([rgb[0], rgb[1], rgb[2], color[3]])

def lighten_color(color, lightness):
    rgb = tuple(1.0 - (1.0 - c) * (1.0 - lightness) for c in color[:3])
    return tuple([rgb[0], rgb[1], rgb[2], color[3]])

def drawing_begin(viewport_width_pixels, viewport_height_pixels):
    global _projection_matrix

    _render_cache.begin_frame()
    _projection_matrix = _ProjectionMatrix(viewport_width_pixels, viewport_height_pixels)

    glClear(GL_COLOR_BUFFER_BIT)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

def drawing_end():
    global _projection_matrix
    _projection_matrix = None
    _render_cache.end_frame()

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
    mvp_matrix = _projection_matrix * transform.get_current_transform()
    shader = _resource_registry.rounded_rectangle_shader
    if border_color is None or border_thickness == 0.0:
        border_color = color
    with shader.use():
        x_min = min(x1, x2) if not left_open else (x1 + x2) * 0.5
        x_max = max(x1, x2) if not right_open else (x1 + x2) * 0.5
        y_min = min(y1, y2) if not bottom_open else (y1 + y2) * 0.5
        y_max = max(y1, y2) if not top_open else (y1 + y2) * 0.5
        glUniformMatrix4fv(shader.uniform_loc("mvp_matrix"), 1, GL_FALSE, mvp_matrix)
        glUniform4f(shader.uniform_loc("rgba"), *_get_rgba(color))
        glUniform1f(shader.uniform_loc("border_thickness"), border_thickness)
        glUniform4f(shader.uniform_loc("border_rgba"), *_get_rgba(border_color))
        glUniform1f(shader.uniform_loc("radius"), radius)
        glUniform2f(shader.uniform_loc("xy1"), x1, y1)
        glUniform2f(shader.uniform_loc("xy2"), x2, y2)
        glUniform4f(shader.uniform_loc("xy_min_max"), x_min, y_min, x_max, y_max)

        glDrawArrays(GL_POINTS, 0, 1)

class _TextCacheData(_RenderCacheData):
    def __init__(self):
        self.width_ascent_descent = None
        self.vertex_array = None
        self.vertex_buffer = None
        self.vertex_count = None

    def destroy(self):
        if self.vertex_array is not None:
            glDeleteVertexArrays(1, self.vertex_array)
        if self.vertex_buffer is not None:
            glDeleteBuffers(1, self.vertex_buffer)

# Returns (width, ascent, descent) where descent is negative
def measure_text(text, font_name, size):
    text_data = _render_cache.get_data(_RenderCacheType.TEXT, (text, font_name, size), lambda: _TextCacheData())
    if text_data.width_ascent_descent is None:
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

        text_data.width_ascent_descent = (
            width * size,
            font_object.ascender_size_ems * size,
            font_object.descender_size_ems * size
        )
    return text_data.width_ascent_descent

def draw_text(text, font_name, size, x, y, horizontal_alignment, vertical_alignment, color):
    shader = _resource_registry.font_shader

    # Currently doesn't support multi-line text
    text_data = _render_cache.get_data(_RenderCacheType.TEXT, (text, font_name, size), lambda: _TextCacheData())
    if text_data.width_ascent_descent is None:
        # Measuring the text will cache this data
        measure_text(text, font_name, size)
        assert text_data.width_ascent_descent

    # Adjust our position so that (x,y) represents the left baseline of the first character
    width, ascent, descent = text_data.width_ascent_descent
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

    font_object = _resource_registry.fonts[font_name]
    if text_data.vertex_array is None:
        vertex_data = []
        vertex_count = 0
        prev_character_code = None
        x_offset = 0.0
        for c in text:
            character_code = ord(c)
            if not font_object.has_glyph(character_code) and c != ' ':
                character_code = font.MISSING_CHARACTER_CODE

            x1 = x_offset - font_object.glyph_left_offset_ems * size
            y1 = -font_object.glyph_baseline_offset_ems * size
            x2 = x1 + font_object.glyph_width_ems * size
            y2 = y1 + font_object.glyph_height_ems * size
            glyph = font_object.glyphs[character_code]

            if c != ' ':
                v00 = (x1, y1, glyph.u1, glyph.v1)
                v10 = (x2, y1, glyph.u2, glyph.v1)
                v01 = (x1, y2, glyph.u1, glyph.v2)
                v11 = (x2, y2, glyph.u2, glyph.v2)
                vertex_data.extend(v00 + v10 + v01 + v01 + v10 + v11)
                vertex_count += 6

            x_offset += font_object.get_advance_ems(character_code) * size
            width = max(width, x)
            if prev_character_code is not None:
                x_offset += font_object.get_kerning_ems(prev_character_code, character_code) * size

            prev_character_code = character_code

        text_data.vertex_array = glGenVertexArrays(1)
        glBindVertexArray(text_data.vertex_array)

        text_data.vertex_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, text_data.vertex_buffer)
        glBufferData(
            GL_ARRAY_BUFFER,
            len(vertex_data) * 4,
            (ctypes.c_float * len(vertex_data))(*vertex_data),
            GL_STATIC_DRAW)

        stride = 16
        glVertexAttribPointer(shader.attribute_loc("position"), 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(shader.attribute_loc("tex_coord"), 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8))
        glEnableVertexAttribArray(1)

        text_data.vertex_count = vertex_count

    with transform.Transform(x, y):
        mvp_matrix = _projection_matrix * transform.get_current_transform()
        with shader.use():
            glEnable(GL_TEXTURE_2D)
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, font_object.glyph_texture)
            glUniformMatrix4fv(shader.uniform_loc("mvp_matrix"), 1, GL_FALSE, mvp_matrix)
            glUniform4f(shader.uniform_loc("rgba"), *_get_rgba(color))
            glUniform1i(shader.uniform_loc("font_texture"), 0)
            glUniform1f(shader.uniform_loc("pxrange"), font_object.pxrange)

            glBindVertexArray(text_data.vertex_array)
            glBindBuffer(GL_ARRAY_BUFFER, text_data.vertex_buffer)
            glDrawArrays(GL_TRIANGLES, 0, text_data.vertex_count)

            glBindVertexArray(0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)

def draw_icon(icon_name, x1, y1, x2, y2, color):
    mvp_matrix = _projection_matrix * transform.get_current_transform()
    shader = _resource_registry.icon_shader
    icon = _resource_registry.icons[icon_name]
    with shader.use():
        glEnable(GL_TEXTURE_2D)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, icon.icon_texture)
        glUniformMatrix4fv(shader.uniform_loc("mvp_matrix"), 1, GL_FALSE, mvp_matrix)
        glUniform2f(shader.uniform_loc("xy1"), x1, y1)
        glUniform2f(shader.uniform_loc("xy2"), x2, y2)
        glUniform4f(shader.uniform_loc("rgba"), *_get_rgba(color))
        glUniform1i(shader.uniform_loc("icon_texture"), 0)
        glUniform1f(shader.uniform_loc("pxrange"), icon.pxrange)

        glDrawArrays(GL_POINTS, 0, 1)

def draw_spinner(x, y, color_inner, color_outer, color_outer_background, radius_inner, radius_outer, ratio):
    mvp_matrix = _projection_matrix * transform.get_current_transform()
    shader = _resource_registry.spinner_shader
    with shader.use():
        meter_a = 0.125
        meter_c = 0.875
        meter_b = meter_a + ratio * (meter_c - meter_a)
        s = radius_outer

        glUniformMatrix4fv(shader.uniform_loc("mvp_matrix"), 1, GL_FALSE, mvp_matrix)
        glUniform2f(shader.uniform_loc("xy1"), x - s, y - s)
        glUniform2f(shader.uniform_loc("xy2"), x + s, y + s)
        glUniform4f(shader.uniform_loc("inner_rgba"), *_get_rgba(color_inner))
        glUniform4f(shader.uniform_loc("outer_rgba"), *_get_rgba(color_outer))
        glUniform4f(shader.uniform_loc("outer_background_rgba"), *_get_rgba(color_outer_background))
        glUniform1f(shader.uniform_loc("inner_radius"), radius_inner)
        glUniform1f(shader.uniform_loc("outer_radius"), radius_outer)
        glUniform1f(shader.uniform_loc("meter_a"), meter_a)
        glUniform1f(shader.uniform_loc("meter_b"), meter_b)
        glUniform1f(shader.uniform_loc("meter_c"), meter_c)
        glUniform2f(shader.uniform_loc("xy_center"), x, y)

        glDrawArrays(GL_POINTS, 0, 1)

def draw_waveform(
    x1, y1, x2, y2, waveform_texture, background_color, waveform_color,
    border_thickness = 0.0, border_color = None):
    mvp_matrix = _projection_matrix * transform.get_current_transform()
    shader = _resource_registry.waveform_shader
    if border_color is None or border_thickness == 0.0:
        border_color = background_color
    with shader.use():
        glEnable(GL_TEXTURE_1D)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_1D, waveform_texture)
        glUniformMatrix4fv(shader.uniform_loc("mvp_matrix"), 1, GL_FALSE, mvp_matrix)
        glUniform2f(shader.uniform_loc("xy1"), x1, y1)
        glUniform2f(shader.uniform_loc("xy2"), x2, y2)
        glUniform1i(shader.uniform_loc("waveform_texture"), 0)
        glUniform4f(shader.uniform_loc("background_rgba"), *_get_rgba(background_color))
        glUniform4f(shader.uniform_loc("waveform_rgba"), *_get_rgba(waveform_color))
        glUniform1f(shader.uniform_loc("border_thickness"), border_thickness)
        glUniform4f(shader.uniform_loc("border_rgba"), *_get_rgba(border_color))

        glDrawArrays(GL_POINTS, 0, 1)

def _get_rgba(color):
    if len(color) == 3:
        return (color[0], color[1], color[2], 1.0)
    else:
        assert len(color) == 4
        return color
