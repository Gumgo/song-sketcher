import os
import pathlib

_PROJECTS_DIRECTORY = "./projects"

_project_manager = None

def initialize():
    global _project_manager
    _project_manager = ProjectManager()

def shutdown():
    global _project_manager
    if _project_manager is not None:
        _project_manager.shutdown()
        _project_manager = None

def get():
    return _project_manager

# $TODO handle errors at call sites
class ProjectManager:
    def __init__(self):
        try:
            os.mkdir(_PROJECTS_DIRECTORY)
        except FileExistsError:
            pass

    def shutdown(self):
        pass

    def fixup_project_name(self, name):
        return name.lstrip(" ").rstrip(" ")

    def is_valid_project_name(self, name):
        if len(name) == 0 or name.startswith(" ") or name.endswith(" "):
            return False

        for c in name:
            valid = c.isalnum() or c == "_" or c == " "
            if not valid:
                return False

        return True

    def get_project_directory(self, name):
        return pathlib.Path(_PROJECTS_DIRECTORY) / name

    def project_exists(self, name):
        return self.get_project_directory(name).exists()

    def create_project(self, name):
        os.mkdir(str(self.get_project_directory(name)))
