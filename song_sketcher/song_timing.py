def get_samples_per_beat(sample_rate, beats_per_minute):
    seconds_per_beat = 60.0 / beats_per_minute
    return sample_rate * seconds_per_beat

def get_samples_per_measure(sample_rate, beats_per_minute, beats_per_measure):
    return get_samples_per_beat(sample_rate, beats_per_minute) * beats_per_measure

def get_measure_count(sample_rate, beats_per_minute, beats_per_measure, sample_count):
    return sample_count / get_samples_per_measure(sample_rate, beats_per_minute, beats_per_measure)