from distutils.core import Extension, setup

# $TODO linux support
portaudio_library_directory = "../portaudio/build/msvc/x64/Release"
portaudio_library_name = "portaudio_x64"

extension = Extension(
    "engine",
    include_dirs = ["../portaudio/include"],
    libraries = [portaudio_library_name],
    library_dirs = [portaudio_library_directory],
    sources = ["bind.cpp", "libengine.cpp", "wav.cpp"]
)

setup(
    name = "engine",
    version = "1.0",
    description = "Audio engine for Song Sketcher",
    ext_modules = [extension]
)
