import imageio
from OpenGL.GL import *
from OpenGL.GLU import *

class WaveformTexture:
    def __init__(self, samples = None, sample_count = None):
        if samples is not None:
            assert sample_count is None
            sample_count = len(samples)
        self._sample_count = sample_count

        self._waveform_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_1D, self._waveform_texture)
        glTexImage1D(GL_TEXTURE_1D, 0, GL_R32F, sample_count, 0, GL_RED, GL_FLOAT, samples)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)

    def update_samples(self, samples):
        assert len(samples) == self._sample_count
        glBindTexture(GL_TEXTURE_1D, self._waveform_texture)
        glTexSubImage1D(GL_TEXTURE_1D, 0, 0, len(samples), GL_RED, GL_FLOAT, samples)

    def destroy(self):
        glDeleteTextures(self._waveform_texture)

    @property
    def waveform_texture(self):
        return self._waveform_texture
