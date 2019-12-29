_dpi = None

def initialize(dpi):
    global _dpi
    _dpi = dpi

def inches(x):
    assert _dpi is not None
    return x * _dpi

def points(x):
    return x * _dpi / 72.0
