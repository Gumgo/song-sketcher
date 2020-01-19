from OpenGL.GL import *

def get_current_transform():
    return _transform_stack[-1]

class Transform:
    def __init__(self, x = 0.0, y = 0.0):
        self.x = x
        self.y = y

    def __enter__(self):
        _transform_stack.append(_transform_stack[-1] * self)

    def __exit__(self, type, value, traceback):
        _transform_stack.pop()

    def copy(self):
        return Transform(self.x, self.y)

    def __mul__(self, other):
        return Transform(self.x + other.x, self.y + other.y)

    def transform_point(self, point):
        return (self.x + point[0], self.y + point[1])

    def inverse(self):
        return Transform(-self.x, -self.y)

_transform_stack = [Transform()]
