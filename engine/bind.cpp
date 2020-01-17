#include "libengine.h"

#define ENGINE_FUNCTION(function, flags)    \
{                                           \
    #function,                              \
    (PyCFunction)function,                  \
    flags,                                  \
    nullptr                                 \
}

PyMethodDef functions[] = {
    ENGINE_FUNCTION(initialize, METH_NOARGS),
    ENGINE_FUNCTION(shutdown, METH_NOARGS),
    ENGINE_FUNCTION(get_input_device_count, METH_NOARGS),
    ENGINE_FUNCTION(get_default_input_device_index, METH_NOARGS),
    ENGINE_FUNCTION(get_input_device_name, METH_VARARGS),
    ENGINE_FUNCTION(get_output_device_count, METH_NOARGS),
    ENGINE_FUNCTION(get_default_output_device_index, METH_NOARGS),
    ENGINE_FUNCTION(get_output_device_name, METH_VARARGS),
    ENGINE_FUNCTION(set_sample_rate, METH_VARARGS),
    ENGINE_FUNCTION(load_clip, METH_VARARGS),
    ENGINE_FUNCTION(save_clip, METH_VARARGS),
    ENGINE_FUNCTION(delete_clip, METH_VARARGS),
    ENGINE_FUNCTION(start_recording_clip, METH_VARARGS),
    ENGINE_FUNCTION(stop_recording_clip, METH_NOARGS),
    ENGINE_FUNCTION(get_recorded_sample_count, METH_NOARGS),
    ENGINE_FUNCTION(get_latest_recorded_samples, METH_VARARGS),
    ENGINE_FUNCTION(get_clip_sample_count, METH_VARARGS),
    ENGINE_FUNCTION(get_clip_samples, METH_VARARGS),
    ENGINE_FUNCTION(playback_builder_begin, METH_NOARGS),
    ENGINE_FUNCTION(playback_builder_add_clip, METH_VARARGS),
    ENGINE_FUNCTION(playback_builder_finalize, METH_NOARGS),
    ENGINE_FUNCTION(start_playback, METH_VARARGS),
    ENGINE_FUNCTION(stop_playback, METH_NOARGS),
    ENGINE_FUNCTION(get_playback_sample_index, METH_NOARGS),
    ENGINE_FUNCTION(set_metronome_samples_per_beat, METH_VARARGS),
    nullptr
};

PyModuleDef engine_module = {
    PyModuleDef_HEAD_INIT,
    "engine",
    nullptr,
    -1,
    functions,
    nullptr,
    nullptr,
    nullptr,
    nullptr
};

PyMODINIT_FUNC PyInit_engine() {
    return PyModule_Create(&engine_module);
}
