import json
import os
import pathlib

import engine

PROJECT_FILENAME = "project.json"

# These are chosen using HSV values of (x, 240, 140) where x ranges from 0 to 360
CATEGORY_COLORS = [
    (255, 43, 43),
    (255, 175, 43),
    (255, 255, 43),
    (149, 255, 43),
    (43, 255, 43),
    (43, 255, 149),
    (43, 255, 255),
    (43, 149, 255),
    (43, 43, 255),
    (149, 43, 255),
    (255, 43, 255),
    (255, 43, 149)
]

class Clip:
    def __init__(self):
        self.id = None                  # Unique identifier for the clip
        self.name = ""                  # Display name for the clip
        self.sample_count = 0           # Total number of samples in the clip
        self.start_sample_index = 0     # The first sample we should start playing
        self.end_sample_index = 0       # The sample after the last sample played
        self.measure_count = 0          # The number of measures the clip spans NOT including the intro and outro
        self.engine_clip = None         # Audio clip data stored in the engine

        self.category = None            # Used for quick access to the category

class ClipCategory:
    def __init__(self):
        self.name = ""                  # Display name for the category
        self.color = (255, 255, 255)    # Display color for clips in this category
        self.clip_ids = []              # List of clip IDs in this category

class Track:
    def __init__(self):
        self.name = ""                  # Display name for the track
        self.measure_clip_ids = []      # For each measure in the song, a clip ID, or None if no clip has been placed

class Project:
    def __init__(self):
        self.sample_rate = 48000
        self.beats_per_minute = 60.0
        self.beats_per_measure = 4

        self.clips = []
        self.clip_categories = []
        self.tracks = []

        self._next_clip_id = None

    def save(self, path):
        project = {
            "sample_rate": self.sample_rate,
            "beats_per_minutes": self.beats_per_minute,
            "beats_per_measure": self.beats_per_measure,
        }

        clips = []
        for clip in self.clips:
            clips.append({
                "id": clip.id,
                "name": clip.name,
                "sample_count": clip.sample_count,
                "start_sample_index": clip.start_sample_index,
                "end_sample_index": clip.end_sample_index,
                "measure_count": clip.measure_count
            })
        project["clips"] = clips

        clip_categories = []
        for clip_category in self.clip_categories:
            clip_categories.append({
                "name": clip_category.name,
                "color": clip_category.color,
                "clip_ids": clip_category.clip_ids
            })
        project["clip_categories"] = clip_categories

        tracks = []
        for track in self.tracks:
            tracks.append({
                "name": track.name,
                "measure_clip_ids": track.measure_clip_ids
            })
        project["tracks"] = tracks

        with open(str(path), "w") as file:
            json.dump(project, file, indent = 4)

        folder = pathlib.Path(os.path.dirname(path))
        for clip in self.clips:
            engine.save_clip(clip.id, str(folder / "{}.wav".format(clip.id)))

    def load(self, path):
        folder = pathlib.Path(os.path.dirname(path))
        with open(str(path), "r") as file:
            project = json.load(file)

        self.sample_rate = int(project["sample_rate"])
        engine.set_sample_rate(self.sample_rate)

        self.beats_per_minute = project["beats_per_minutes"]
        self.beats_per_measure = int(project["beats_per_measure"])

        self.clips = []
        for loaded_clip in project["clips"]:
            clip = Clip()
            clip.id = int(loaded_clip["id"])
            clip.name = loaded_clip["name"]
            clip.sample_count = int(loaded_clip["sample_count"])
            clip.start_sample_index = int(loaded_clip["start_sample_index"])
            clip.end_sample_index = int(loaded_clip["end_sample_index"])
            clip.measure_count = int(loaded_clip["measure_count"])
            clip.engine_clip = engine.load_clip(str(folder / "{}.wav".format(clip.id)))
            self.clips.append(clip)

        self.clip_categories = []
        for loaded_clip_category in project["clip_categories"]:
            clip_category = ClipCategory()
            clip_category.name = loaded_clip_category["name"]
            clip_category.color = tuple(int(x) for x in loaded_clip_category["color"])
            clip_category.clip_ids = [int(x) for x in loaded_clip_category["clip_ids"]]
            for clip_id in clip_category.clip_ids:
                self.get_clip_by_id(clip_id).category = clip_category
            self.clip_categories.append(clip_category)

        self.tracks = []
        for loaded_track in project["tracks"]:
            track = Track()
            track.name = loaded_track["name"]
            track.measure_clip_ids = [int(x) for x in loaded_track["measure_clip_ids"]]
            self.tracks.append(track)

    def generate_clip_id(self):
        if self._next_clip_id is None:
            self._next_clip_id = max((x.id for x in self.clips), default = -1) + 1
        clip_id = self._next_clip_id
        self._next_clip_id += 1
        return clip_id

    def get_clip_by_id(self, clip_id):
        # Could optimize
        return next((x for x in self.clips if x.id == clip_id))
