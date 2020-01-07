import os

build_dir = "build"
icons_dir = "build/icons"
fonts_dir = "build/fonts"

try:
    os.mkdir(build_dir)
    os.mkdir(icons_dir)
    os.mkdir(fonts_dir)
except FileExistsError:
    pass

icons = [
    ("accept", 64, 64),
    ("arrow_down", 32, 32),
    ("arrow_up", 32, 32),
    ("delete", 64, 64),
    ("load", 64, 64),
    ("metronome", 64, 64),
    ("metronome_disabled", 64, 64),
    ("new", 64, 64),
    ("pause", 64, 64),
    ("play", 64, 64),
    ("plus", 64, 64),
    ("quit", 64, 64),
    ("record", 64, 64),
    ("redo", 64, 64),
    ("reject", 64, 64),
    ("save", 64, 64),
    ("save_as", 64, 64),
    ("settings", 64, 64),
    ("stop", 64, 64),
    ("undo", 64, 64)
]

fonts = [
    "arial"
]

for name, width, height in icons:
    os.system("convert_icon.py {}.svg {} {} {}".format(name, width, height, icons_dir))

for name in fonts:
    os.system("convert_font.py {}.ttf {}".format(name, fonts_dir))
