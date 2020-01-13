from OpenGL.GL import *

class Shader:
    def __init__(self, filename):
        with open(filename, "r") as file:
            MODE_VS = 0
            MODE_FS = 1
            vs_source_lines = []
            fs_source_lines = []

            mode = -1
            for line in file:
                trimmed_line = line.strip()
                if trimmed_line == "#vs":
                    mode = MODE_VS
                elif trimmed_line == "#fs":
                    mode = MODE_FS
                else:
                    if mode == MODE_VS:
                        vs_source_lines.append(line)
                    elif mode == MODE_FS:
                        fs_source_lines.append(line)

        vs_source = "".join(vs_source_lines)
        fs_source = "".join(fs_source_lines)

        self.vs = self._create_shader(GL_VERTEX_SHADER, vs_source)
        self.fs = self._create_shader(GL_FRAGMENT_SHADER, fs_source)

        self.program = glCreateProgram()
        glAttachShader(self.program, self.vs)
        glAttachShader(self.program, self.fs)

        glLinkProgram(self.program)
        if glGetProgramiv(self.program, GL_LINK_STATUS) != GL_TRUE:
            raise RuntimeError(glGetProgramInfoLog(self.program))

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
        glDetachShader(self.program, self.fs)

    def destroy(self):
        glDeleteProgram(self.program)
        glDeleteShader(self.vs)
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

    def loc(self, uniform_name):
        return self._uniform_locations[uniform_name]

    def _create_shader(self, type, source):
        shader = glCreateShader(type)
        glShaderSource(shader, source)
        glCompileShader(shader)
        if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
            raise RuntimeError(glGetShaderInfoLog(shader))
        return shader
