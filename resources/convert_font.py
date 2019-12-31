import imageio
import json
import math
import numpy as np
import os
import pathlib
import sys

MSDFGEN_EXECUTABLE = pathlib.Path("../msdfgen/x64/Release/msdfgen.exe")

font_filename = sys.argv[1]
font_name = os.path.splitext(os.path.basename(font_filename))[0]
font_json_filename = font_name + ".json"
font_image_filename = font_name + ".png"

characters = []
characters += [x for x in range(32, 127)] # Add standard ASCII characters
characters += [x for x in range(128, 256)] # Add extended ASCII characters
characters.append(0x25A1) # Missing character symbol

try:
    os.mkdir("glyphs")
except FileExistsError:
    pass

width = 96
height = 96
scale = 2
pxrange = 12
translate_x = 4
translate_y = 16

output = {
    "font_file": os.path.basename(font_filename),
    "font_image_file": font_image_filename,
    "glyph_width": width,
    "glyph_height": height,
    "glyph_offset_x": translate_x * scale,
    "glyph_offset_y": translate_y * scale,
    "glyph_scale": scale,
    "glyph_pxrange": pxrange
}

atlas_row_count = int(math.ceil(math.sqrt(len(characters))))
atlas_col_count = (len(characters) + atlas_row_count + 1) // atlas_row_count

atlas_width = atlas_row_count * width
atlas_height = atlas_col_count * height
atlas = np.ndarray([atlas_height, atlas_width, 3], dtype = np.uint8)

glyphs = []
row_index = 0
col_index = 0
for character in characters:
    output_filename = "glyphs/glyph_{}.png".format(character)
    result = os.system("\"{}\" msdf -font {} {} -o {} -size {} {} -scale {} -translate {} {} -pxrange {}".format(
        MSDFGEN_EXECUTABLE,
        font_filename,
        character,
        output_filename,
        width,
        height,
        scale,
        translate_x,
        translate_y,
        pxrange))
    assert result == 0

    atlas_x = row_index * width
    atlas_y = col_index * height

    glyph_image = imageio.imread(output_filename)
    if len(glyph_image.shape) == 2:
        # Special case - single channel
        assert glyph_image.shape == (height, width)
        for y in range(height):
            for c in range(3):
                atlas[atlas_y + y, atlas_x:atlas_x + width, c] = glyph_image[y, :]
    else:
        assert glyph_image.shape in [(height, width, 3), (height, width, 4)]
        assert glyph_image.dtype == np.uint8
        for y in range(height):
            atlas[atlas_y + y, atlas_x:atlas_x + width, 0:3] = glyph_image[y, :, 0:3]

    glyphs.append({
        "character": character,
        "atlas_x": atlas_x,
        "atlas_y": atlas_y
    })

    row_index += 1
    if row_index == atlas_row_count:
        row_index = 0
        col_index += 1

output["glyphs"] = glyphs

with open(font_json_filename, "w") as json_file:
    json.dump(output, json_file, indent = 2)
imageio.imwrite(font_image_filename, atlas)
