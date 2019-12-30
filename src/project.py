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
        self.beats_per_measue = 4

        self.clips = []
        self.clip_categories = []
        self.tracks = []
