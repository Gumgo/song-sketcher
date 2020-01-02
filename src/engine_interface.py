# Loads a clip with the given filename and returns its engine clip ID, or a negative value if an error occurred
def load_clip(filename, expected_sample_count):
    return -1

# Saves the clip and returns 0 for success, or a negative value if an error occurred
def save_clip(clip_id, filename):
    return -1

# Deletes the clip with the provided engine clip ID
def delete_clip(clip_id):
    pass

# Creates a new clip, starts recording, and returns the associated engine clip ID, or a negative value on failure
def start_recording_clip():
    return 0 # $TODO

# Stops the current recording
def stop_recording_clip():
    pass # $TODO

# Returns the last sample_count samples from the current recording, padding with 0 at the beginning if necessary
def get_recording_samples(sample_count):
    return [0.0] * sample_count

# Returns the number of samples in the clip with the given ID
def get_clip_sample_count(clip_id):
    return 1000

# Returns an array of samples from the clip with the given ID
def get_clip_samples(clip_id):
    return [0.0] * 1000
