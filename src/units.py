# $TODO have an option to snap to pixels, default True

SNAP_TO_PIXELS = True

_dpi = None

def initialize(dpi):
    global _dpi
    _dpi = dpi

def inches(x):
    assert _dpi is not None
    if SNAP_TO_PIXELS:
        return float(round(x * _dpi))
    else:
        return x * _dpi

def points(x):
    assert _dpi is not None
    if SNAP_TO_PIXELS:
        return float(round(x * _dpi / 72.0))
    else:
        return x * _dpi / 72.0
