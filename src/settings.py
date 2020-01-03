import engine

_settings = None

def initialize():
    global _settings
    _settings = Settings()

def shutdown():
    global _settings
    _settings = None

def get():
    return _settings

class Settings:
    def __init__(self):
        self.input_device_index = engine.get_default_input_device_index()
        self.output_device_index = engine.get_default_output_device_index()
        self.frames_per_buffer = 1024
