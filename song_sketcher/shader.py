from OpenGL.GL import *

class Shader:
    def __init__(self, filename):
        with open(filename, "r") as file:
            MODE_VS = 0
            MODE_GS = 1
            MODE_FS = 2
            vs_source_lines = []
            gs_source_lines = None
            fs_source_lines = []

            mode = -1
            for line in file:
                trimmed_line = line.strip()
                if trimmed_line == "#vs":
                    mode = MODE_VS
                elif trimmed_line == "#gs":
                    mode = MODE_GS
                    if gs_source_lines is None:
                        gs_source_lines = []
                elif trimmed_line == "#fs":
                    mode = MODE_FS
                else:
                    if mode == MODE_VS:
                        vs_source_lines.append(line)
                    elif mode == MODE_GS:
                        gs_source_lines.append(line)
                    elif mode == MODE_FS:
                        fs_source_lines.append(line)

        vs_source = "".join(vs_source_lines)
        gs_source = None if gs_source_lines is None else "".join(gs_source_lines)
        fs_source = "".join(fs_source_lines)

        self.vs = self._create_shader(GL_VERTEX_SHADER, vs_source)
        self.gs = None if gs_source is None else self._create_shader(GL_GEOMETRY_SHADER, gs_source)
        self.fs = self._create_shader(GL_FRAGMENT_SHADER, fs_source)

        self.program = glCreateProgram()
        glAttachShader(self.program, self.vs)
        if self.gs is not None:
            glAttachShader(self.program, self.gs)
        glAttachShader(self.program, self.fs)

        glLinkProgram(self.program)
        if glGetProgramiv(self.program, GL_LINK_STATUS) != GL_TRUE:
            raise RuntimeError(glGetProgramInfoLog(self.program))

        # Store attribute locations in advance for better performance
        self._attribute_locations = {}
        attribute_count = glGetProgramiv(self.program, GL_ACTIVE_ATTRIBUTES)
        for i in range(attribute_count):
            buffer_size = glGetProgramiv(self.program, GL_ACTIVE_ATTRIBUTE_MAX_LENGTH)
            name_length = GLsizei()
            attribute_size = GLint()
            attribute_type = GLenum()
            name_bytes = (GLchar * buffer_size)()
            glGetActiveAttrib(self.program, i, buffer_size, name_length, attribute_size, attribute_type, name_bytes)

            name = name_bytes.value.decode("ascii")
            if len(name) > 0:
                self._attribute_locations[name] = glGetAttribLocation(self.program, name)

        # Store uniform locations in advance for better performance
        self._uniform_locations = {}
        uniform_count = glGetProgramiv(self.program, GL_ACTIVE_UNIFORMS)
        for i in range(uniform_count):
            buffer_size = glGetProgramiv(self.program, GL_ACTIVE_UNIFORM_MAX_LENGTH)
            name_length = GLsizei()
            uniform_size = GLint()
            uniform_type = GLenum()
            name_bytes = (GLchar * buffer_size)()
            glGetActiveUniform(self.program, i, buffer_size, name_length, uniform_size, uniform_type, name_bytes)

            name = name_bytes.value.decode("ascii")
            if len(name) > 0: # Sometimes we get empty uniform names? Not sure why
                self._uniform_locations[name] = glGetUniformLocation(self.program, name)

        glDetachShader(self.program, self.vs)
        if self.gs is not None:
            glDetachShader(self.program, self.gs)
        glDetachShader(self.program, self.fs)

    def destroy(self):
        glDeleteProgram(self.program)
        glDeleteShader(self.vs)
        if self.gs is not None:
            glDeleteShader(self.gs)
        glDeleteShader(self.fs)

    def use(self):
        class Use:
            def __init__(self, shader):
                self.shader = shader

            def __enter__(self):
                glUseProgram(self.shader.program)

            def __exit__(self, type, value, traceback):
                glUseProgram(0)

        return Use(self)

    def attribute_loc(self, attribute_name):
        return self._attribute_locations[attribute_name]

    def uniform_loc(self, uniform_name):
        return self._uniform_locations[uniform_name]

    def _create_shader(self, type, source):
        shader = glCreateShader(type)
        glShaderSource(shader, source)
        glCompileShader(shader)
        if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
            raise RuntimeError(glGetShaderInfoLog(shader))
        return shader
