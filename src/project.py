import json

PROJECT_FILENAME = "project.json"

class Clip:
    def __init__(self):
        self.id = None                  # Unique identifier for the clip
        self.name = ""                  # Display name for the clip
        self.sample_count = 0           # Total number of samples in the clip
        self.start_sample_index = 0     # The first sample we should start playing
        self.end_sample_index = 0       # The sample after the last sample played
        self.measure_count = 0          # The number of measures the clip spans NOT including the intro and outro

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

    def load(self, path):
        with open(str(path), "r") as file:
            project = json.load(file)

        self.sample_rate = int(project["sample_rate"])
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
            self.clips.append(clip)

        self.clip_categories = []
        for loaded_clip_category in project["clip_categories"]:
            clip_category = ClipCategory()
            clip_category.name = loaded_clip_category["name"]
            clip_category.color = tuple(int(x) for x in loaded_clip_category["color"])
            clip_category.clip_ids = [int(x) for x in loaded_clip_category["clip_ids"]]
            self.clip_categories.append(clip_category)

        self.tracks = []
        for loaded_track in project["tracks"]:
            track = Track()
            track.name = loaded_track["name"]
            track.measure_clip_ids = [int(x) for x in loaded_track["measure_clip_ids"]]
            self.tracks.append(track)

    def get_clip_by_id(self, clip_id):
        # Could optimize
        return next((x for x in self.clips if x.id == clip_id))
