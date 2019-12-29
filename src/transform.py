from OpenGL.GL import *

# $TODO expand to support more general affine transforms
class Transform:
    def __init__(self, x = 0.0, y = 0.0):
        self.x = x
        self.y = y

    def __enter__(self):
        glPushMatrix()
        glMultMatrixf(self.get_opengl_matrix())

    def __exit__(self, type, value, traceback):
        glPopMatrix()

    def copy(self):
        return Transform(self.x, self.y)

    def __mul__(self, other):
        return Transform(self.x + other.x, self.y + other.y)

    def transform_point(self, point):
        return (self.x + point[0], self.y + point[1])

    # $TODO: transform_vector

    def inverse(self):
        return Transform(-self.x, -self.y)

    def get_opengl_matrix(self):
        return [
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            self.x, self.y, 0.0, 1.0
        ]
