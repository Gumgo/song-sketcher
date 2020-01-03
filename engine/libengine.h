#pragma once

#include <Python.h>

// Initialize the engine
PyObject *initialize(PyObject *self);

// Shutdown the engine
PyObject *shutdown(PyObject *self);

// Query the number of input devices
PyObject *get_input_device_count(PyObject *self);

// Returns the default input device index, or None if a default doesn't exist
// Returns: default_device_index
PyObject *get_default_input_device_index(PyObject *self);

// Get the name of the ith input device
// Arguments: device_index
PyObject *get_input_device_name(PyObject *self, PyObject *args);

// Query the number of output devices
PyObject *get_output_device_count(PyObject *self);

// Returns the default output device index, or None if a default doesn't exist
// Returns: default_device_index
PyObject *get_default_output_device_index(PyObject *self);

// Get the name of the ith output device
// Arguments: device_index
PyObject *get_output_device_name(PyObject *self, PyObject *args);

// Sets the sample rate
// Arguments: sample_rate
PyObject *set_sample_rate(PyObject *self, PyObject *args);

// Load a clip from a file
// Arguments: filename
// Returns: clip_id
PyObject *load_clip(PyObject *self, PyObject *args);

// Save a clip to a file
// Arguments: clip_id, filename
PyObject *save_clip(PyObject *self, PyObject *args);

// Deletes a clip
// Arguments: clip_id
PyObject *delete_clip(PyObject *self, PyObject *args);

// Starts recording a clip
// Arguments: input_device_index, output_device_index, frames_per_buffer
// Returns: clip_id
PyObject *start_recording_clip(PyObject *self, PyObject *args);

// Stops the current recording
PyObject *stop_recording_clip(PyObject *self);

// Returns the n latest recorded samples
// Arguments: sample_count
// Returns: samples
PyObject *get_latest_recorded_samples(PyObject *self, PyObject *args);

// Returns the number of samples in the clip
// Arguments: clip_id
// Returns: sample_count
PyObject *get_clip_sample_count(PyObject *self, PyObject *args);

// Returns the samples in a clip, sampling evenly if the number of samples exceeds max_sample_count
// Arguments: clip_id, max_sample_count
// Returns: samples
PyObject *get_clip_samples(PyObject *self, PyObject *args);

// Starts building playback
PyObject *playback_builder_begin(PyObject *self);

// Adds a clip to the current playback track
// Arguments: clip_id, start_sample_index, end_sample_index, playback_start_sample_index
PyObject *playback_builder_add_clip(PyObject *self, PyObject *args);

// Finalizes the playback builder, allowing for playback to start
PyObject *playback_builder_finalize(PyObject *self);

// Starts playback at the given sample index
// Arguments: output_device_index, frames_per_buffer, sample_index
PyObject *start_playback(PyObject *self, PyObject *args);

// Stops playback
PyObject *stop_playback(PyObject *self);

// Returns the current playback sample index
// Returns: sample_index
PyObject *get_playback_sample_index(PyObject *self);