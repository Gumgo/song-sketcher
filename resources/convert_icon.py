import json
import os
import pathlib
import sys

MSDFGEN_EXECUTABLE = pathlib.Path("../msdfgen/x64/Release/msdfgen.exe")

icon_filename = sys.argv[1]
width = int(sys.argv[2])
height = int(sys.argv[3])
output_directory = pathlib.Path(sys.argv[4])
icon_name = os.path.splitext(os.path.basename(icon_filename))[0]
icon_json_filename = icon_name + ".json"
icon_image_filename = icon_name + ".png"
icon_json_output_filename = str(output_directory / icon_json_filename)
icon_image_output_filename = str(output_directory / icon_image_filename)

pxrange = 12

output = {
    "icon_image_file": icon_image_filename,
    "pxrange": pxrange
}

result = os.system("\"{}\" msdf -svg {} -size {} {} -o {} -pxrange {}".format(
    MSDFGEN_EXECUTABLE,
    icon_filename,
    width,
    height,
    icon_image_output_filename,
    pxrange))
assert result == 0

with open(icon_json_output_filename, "w") as json_file:
    json.dump(output, json_file, indent = 2)
