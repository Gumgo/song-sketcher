#include "libengine.h"
#include "wav.h"

#include <portaudio.h>

#include <algorithm>
#include <atomic>
#include <string>
#include <thread>
#include <unordered_map>
#include <vector>

struct s_device {
    int32_t m_portaudio_device_index = 0;
    std::string m_name = {};
    PaTime m_suggested_latency = 0;
};

using t_clip_id = int32_t;

struct s_clip {
    std::vector<float> m_samples = {};
};

// Amount of time in a single recording buffer
static const float k_recording_buffer_length_seconds = 5.0f;

// Amount of time remaining in the current recording buffer before we allocate the next one
static const float k_recording_buffer_padding_seconds = 1.0f;

struct s_recording_buffer {
    std::vector<float> m_samples = {};
    std::atomic<size_t> m_usage = 0;
    s_recording_buffer *m_prev = nullptr;
    std::atomic<s_recording_buffer *> m_next = nullptr;
};

class c_recording_allocator {
public:
    c_recording_allocator() = default;

    void start(size_t recording_buffer_length, size_t recording_buffer_padding);
    void stop();
    void save_recorded_samples(std::vector<float> &buffer);
    void clear();
    s_recording_buffer *get_first_buffer() { return m_first_buffer; }

private:
    void thread_main();

    std::thread *m_thread = nullptr;
    size_t m_recording_buffer_length = 0;
    size_t m_recording_buffer_padding = 0;
    s_recording_buffer *m_first_buffer = nullptr;
    s_recording_buffer *m_last_buffer = nullptr;
    std::atomic<bool> m_terminate = false;
};

struct s_playback_clip {
    t_clip_id m_clip_id = 0;
    int32_t m_start_sample_index = 0;
    int32_t m_end_sample_index = 0;
    int32_t m_playback_start_sample_index = 0;

    s_playback_clip *m_prev_active_playback_clip = nullptr;
    s_playback_clip *m_next_active_playback_clip = nullptr;
};

enum class e_playback_event {
    k_start_clip,
    k_stop_clip
};

struct s_playback_event {
    e_playback_event m_event = e_playback_event::k_start_clip;
    size_t m_playback_clip_index = 0;
    int32_t m_sample_index = 0;
};

struct s_engine_state {
    bool m_portaudio_initialized = false;
    std::vector<s_device> m_input_devices = {};
    std::vector<s_device> m_output_devices = {};
    int32_t m_default_input_device_index = -1;
    int32_t m_default_output_device_index = -1;

    int32_t m_sample_rate = 0;

    t_clip_id m_next_clip_id = 0;
    std::unordered_map<t_clip_id, s_clip> m_clips = {};

    // The current portaudio stream
    PaStream *m_stream = nullptr;

    bool m_recording = false;
    t_clip_id m_recording_clip_id = -1;
    c_recording_allocator m_recording_allocator = {};
    std::atomic<s_recording_buffer *> m_current_recording_buffer = nullptr;
    int32_t m_recording_underflows = 0;

    std::vector<s_playback_clip> m_playback_clips = {};         // List of all clips in the current playback
    std::vector<s_playback_event> m_playback_events = {};       // Ordered list of start and stop events for clips
    s_playback_clip *m_first_active_playback_clip = nullptr;    // Linked list of active playback clips

    bool m_playing = false;
    std::atomic<int32_t> m_playback_sample_index = 0;
    size_t m_next_playback_event_index = 0;
};

static s_engine_state g_engine_state;

static void activate_playback_clip(size_t playback_clip_index);
static void deactivate_playback_clip(size_t playback_clip_index);

static int recording_stream_main(
    const void *input,
    void *output,
    unsigned long frame_count,
    const PaStreamCallbackTimeInfo *time_info,
    PaStreamCallbackFlags status_flags,
    void *user_data);

static int playback_stream_main(
    const void *input,
    void *output,
    unsigned long frame_count,
    const PaStreamCallbackTimeInfo *time_info,
    PaStreamCallbackFlags status_flags,
    void *user_data);

// Common error checks
#define ERROR_IF_RECORDING                                                                          \
do {                                                                                                \
    if (g_engine_state.m_recording) {                                                               \
        PyErr_SetString(PyExc_Exception, "Cannot perform this action while recording is active");   \
        return nullptr;                                                                             \
    }                                                                                               \
} while (0)

#define ERROR_IF_PLAYING                                                                            \
do {                                                                                                \
    if (g_engine_state.m_recording) {                                                               \
        PyErr_SetString(PyExc_Exception, "Cannot perform this action while playback is active");    \
        return nullptr;                                                                             \
    }                                                                                               \
} while (0)

#define ERROR_IF_INVALID_CLIP_ID(clip_id)                                       \
do {                                                                            \
    if (g_engine_state.m_clips.find(clip_id) == g_engine_state.m_clips.end()) { \
        PyErr_SetString(PyExc_ValueError, "Invalid clip ID");                   \
        return nullptr;                                                         \
    }                                                                           \
} while (0)

PyObject *initialize(PyObject *self) {
    if (g_engine_state.m_portaudio_initialized) {
        PyErr_SetString(PyExc_Exception, "Engine already initialized");
        return nullptr;
    }

    PaError error = Pa_Initialize();
    if (error != paNoError) {
        PyErr_SetString(PyExc_Exception, Pa_GetErrorText(error));
        return nullptr;
    }

    int32_t device_count = Pa_GetDeviceCount();
    if (device_count < 0) {
        Pa_Terminate();
        PyErr_SetString(PyExc_Exception, "Error occurred querying devices");
        return nullptr;
    }

    int32_t default_input_device_index = Pa_GetDefaultInputDevice();
    int32_t default_output_device_index = Pa_GetDefaultOutputDevice();

    for (int32_t device_index = 0; device_index < device_count; ++device_index) {
        const PaDeviceInfo *device_info = Pa_GetDeviceInfo(device_index);
        s_device device;
        device.m_portaudio_device_index = device_index;
        device.m_name = device_info->name;

        if (device_info->maxInputChannels > 0) {
            if (device_index == default_input_device_index) {
                g_engine_state.m_default_input_device_index =
                    static_cast<int32_t>(g_engine_state.m_input_devices.size());
            }

            g_engine_state.m_input_devices.push_back(device);
            g_engine_state.m_input_devices.back().m_suggested_latency = device_info->defaultLowInputLatency;
        }

        if (device_info->maxOutputChannels > 0) {
            if (device_index == default_output_device_index) {
                g_engine_state.m_default_output_device_index =
                    static_cast<int32_t>(g_engine_state.m_output_devices.size());
            }

            g_engine_state.m_output_devices.push_back(device);
            g_engine_state.m_output_devices.back().m_suggested_latency = device_info->defaultLowOutputLatency;
        }
    }

    g_engine_state.m_portaudio_initialized = true;
    Py_RETURN_NONE;
}

PyObject *shutdown(PyObject *self) {
    ERROR_IF_RECORDING;
    ERROR_IF_PLAYING;

    if (g_engine_state.m_portaudio_initialized) {
        Pa_Terminate();
        g_engine_state.m_portaudio_initialized = false;
    }

    Py_RETURN_NONE;
}

PyObject *get_input_device_count(PyObject *self) {
    return PyLong_FromSize_t(g_engine_state.m_input_devices.size());
}

PyObject *get_default_input_device_index(PyObject *self) {
    return PyLong_FromLong(g_engine_state.m_default_input_device_index);
}

PyObject *get_input_device_name(PyObject *self, PyObject *args) {
    int32_t index;
    if (!PyArg_ParseTuple(args, "i", &index)) {
        return nullptr;
    }

    if (index < 0 || index >= g_engine_state.m_input_devices.size()) {
        PyErr_SetString(PyExc_ValueError, "Device index out of range");
        return nullptr;
    }

    return PyUnicode_FromString(g_engine_state.m_input_devices[index].m_name.c_str());
}

PyObject *get_output_device_count(PyObject *self) {
    return PyLong_FromSize_t(g_engine_state.m_output_devices.size());
}

PyObject *get_default_output_device_index(PyObject *self) {
    return PyLong_FromLong(g_engine_state.m_default_output_device_index);
}

PyObject *get_output_device_name(PyObject *self, PyObject *args) {
    int32_t index;
    if (!PyArg_ParseTuple(args, "i", &index)) {
        return nullptr;
    }

    if (index < 0 || index >= g_engine_state.m_output_devices.size()) {
        PyErr_SetString(PyExc_ValueError, "Device index out of range");
        return nullptr;
    }

    return PyUnicode_FromString(g_engine_state.m_output_devices[index].m_name.c_str());
}

PyObject *set_sample_rate(PyObject *self, PyObject *args) {
    ERROR_IF_RECORDING;
    ERROR_IF_PLAYING;

    int32_t sample_rate;
    if (!PyArg_ParseTuple(args, "i", &sample_rate)) {
        return nullptr;
    }

    if (sample_rate <= 0) {
        PyErr_SetString(PyExc_ValueError, "Invalid sample rate");
        return nullptr;
    }

    if (!g_engine_state.m_clips.empty()) {
        PyErr_SetString(PyExc_Exception, "Cannot set sample rate when clips exist");
        return nullptr;
    }

    g_engine_state.m_sample_rate = sample_rate;
    Py_RETURN_NONE;
}

PyObject *load_clip(PyObject *self, PyObject *args) {
    ERROR_IF_RECORDING;
    ERROR_IF_PLAYING;

    char *filename;
    if (!PyArg_ParseTuple(args, "s", &filename)) {
        return nullptr;
    }

    std::vector<float> samples;
    uint32_t sample_rate;
    if (!read_wav(filename, samples, sample_rate)) {
        PyErr_Format(PyExc_IOError, "Failed to read '%s'", filename);
        return nullptr;
    }

    if (sample_rate != g_engine_state.m_sample_rate) {
        PyErr_Format(PyExc_ValueError, "Incorrect sample rate, got %u but expected %d", sample_rate, g_engine_state.m_sample_rate);
        return nullptr;
    }

    t_clip_id clip_id = g_engine_state.m_next_clip_id++;
    s_clip &clip = g_engine_state.m_clips.emplace(std::make_pair(clip_id, s_clip())).first->second;
    std::swap(samples, clip.m_samples);

    return PyLong_FromLong(clip_id);
}

PyObject *save_clip(PyObject *self, PyObject *args) {
    t_clip_id clip_id;
    const char *filename;
    if (!PyArg_ParseTuple(args, "is", &clip_id, &filename)) {
        return nullptr;
    }

    ERROR_IF_INVALID_CLIP_ID(clip_id);

    const s_clip &clip = g_engine_state.m_clips[clip_id];
    const float *samples = clip.m_samples.size() > 0 ? &clip.m_samples.front() : nullptr;
    if (!write_wav(filename, samples, clip.m_samples.size(), static_cast<uint32_t>(g_engine_state.m_sample_rate))) {
        PyErr_Format(PyExc_IOError, "Failed to write '%s'", filename);
        return nullptr;
    }

    Py_RETURN_NONE;
}

PyObject *delete_clip(PyObject *self, PyObject *args) {
    ERROR_IF_RECORDING;
    ERROR_IF_PLAYING;

    t_clip_id clip_id;
    if (!PyArg_ParseTuple(args, "i", &clip_id)) {
        return nullptr;
    }

    ERROR_IF_INVALID_CLIP_ID(clip_id);

    g_engine_state.m_clips.erase(clip_id);
    Py_RETURN_NONE;
}

void c_recording_allocator::start(size_t recording_buffer_length, size_t recording_buffer_padding) {
    m_recording_buffer_length = recording_buffer_length;
    m_recording_buffer_padding = recording_buffer_padding;
    m_terminate = false;

    m_first_buffer = new s_recording_buffer();
    m_first_buffer->m_samples.resize(m_recording_buffer_length);
    m_last_buffer = m_first_buffer;

    m_thread = new std::thread([this]() { thread_main(); });
}

void c_recording_allocator::stop() {
    m_terminate = true;
    m_thread->join();
    delete m_thread;
    m_thread = nullptr;
}

void c_recording_allocator::save_recorded_samples(std::vector<float> &buffer) {
    size_t sample_count = 0;
    s_recording_buffer *recording_buffer = m_first_buffer;
    while (recording_buffer) {
        sample_count += recording_buffer->m_usage;
        recording_buffer = recording_buffer->m_next;
    }

    buffer.clear();
    buffer.reserve(sample_count);
    recording_buffer = m_first_buffer;
    while (recording_buffer) {
        size_t usage = recording_buffer->m_usage;
        for (size_t i = 0; i < usage; ++i) {
            buffer.push_back(recording_buffer->m_samples[i]);
        }
        sample_count += recording_buffer->m_usage;
        recording_buffer = recording_buffer->m_next;
    }
}

void c_recording_allocator::clear() {
    s_recording_buffer *recording_buffer = m_first_buffer;
    while (recording_buffer) {
        s_recording_buffer *next = recording_buffer->m_next;
        delete recording_buffer;
        recording_buffer = next;
    }

    m_first_buffer = nullptr;
    m_last_buffer = nullptr;
}

void c_recording_allocator::thread_main() {
    while (!m_terminate) {
        if (m_last_buffer->m_usage >= m_recording_buffer_length - m_recording_buffer_padding) {
            // Buffer is nearly used up, so allocate another one
            s_recording_buffer *new_buffer = new s_recording_buffer();
            new_buffer->m_samples.resize(m_recording_buffer_length);
            new_buffer->m_prev = m_last_buffer;

            // Atomically set the next pointer
            m_last_buffer->m_next = new_buffer;
            m_last_buffer = new_buffer;
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }
}

PyObject *start_recording_clip(PyObject *self, PyObject *args) {
    int32_t input_device_index;
    int32_t output_device_index;
    int32_t frames_per_buffer;
    if (!PyArg_ParseTuple(args, "iii", &input_device_index, &output_device_index, &frames_per_buffer)) {
        return nullptr;
    }

    ERROR_IF_RECORDING;
    ERROR_IF_PLAYING;

    if (g_engine_state.m_sample_rate <= 0) {
        PyErr_SetString(PyExc_ValueError, "Invalid sample rate");
        return nullptr;
    }

    if (input_device_index < 0 || static_cast<uint32_t>(input_device_index) >= g_engine_state.m_input_devices.size()) {
        PyErr_SetString(PyExc_ValueError, "Invalid input device index");
        return nullptr;
    }

    if (output_device_index < 0 || static_cast<uint32_t>(output_device_index) >= g_engine_state.m_output_devices.size()) {
        PyErr_SetString(PyExc_ValueError, "Invalid input device index");
        return nullptr;
    }

    if (frames_per_buffer <= 0) {
        PyErr_SetString(PyExc_ValueError, "Invalid frames per buffer");
        return nullptr;
    }

    const s_device &input_device = g_engine_state.m_input_devices[input_device_index];
    const s_device &output_device = g_engine_state.m_output_devices[output_device_index];

    // Setup the stream parameters
    PaStreamParameters input_params;
    input_params.device = input_device.m_portaudio_device_index;
    input_params.channelCount = 1;
    input_params.sampleFormat = paFloat32;
    input_params.suggestedLatency = input_device.m_suggested_latency;
    input_params.hostApiSpecificStreamInfo = nullptr;

    PaStreamParameters output_params;
    output_params.device = output_device.m_portaudio_device_index;
    output_params.channelCount = 1;
    output_params.sampleFormat = paFloat32;
    output_params.suggestedLatency = output_device.m_suggested_latency;
    output_params.hostApiSpecificStreamInfo = nullptr;

    PaError result = Pa_IsFormatSupported(
        &input_params,
        &output_params,
        static_cast<double>(g_engine_state.m_sample_rate));
    if (result != paFormatIsSupported) {
        PyErr_SetString(PyExc_Exception, Pa_GetErrorText(result));
        return nullptr;
    }

    // Start up the allocator first to make sure we never underrun
    size_t recording_buffer_length = static_cast<size_t>(g_engine_state.m_sample_rate * k_recording_buffer_length_seconds);
    size_t recording_buffer_padding = static_cast<size_t>(g_engine_state.m_sample_rate * k_recording_buffer_padding_seconds);
    g_engine_state.m_recording_allocator.start(recording_buffer_length, recording_buffer_padding);
    g_engine_state.m_current_recording_buffer = g_engine_state.m_recording_allocator.get_first_buffer();

    result = Pa_OpenStream(
        &g_engine_state.m_stream,
        &input_params,
        &output_params,
        static_cast<double>(g_engine_state.m_sample_rate),
        static_cast<uint32_t>(frames_per_buffer),
        paNoFlag,
        recording_stream_main,
        nullptr);
    if (result != paNoError) {
        PyErr_SetString(PyExc_Exception, Pa_GetErrorText(result));
        g_engine_state.m_recording_allocator.stop();
        g_engine_state.m_recording_allocator.clear();
        return nullptr;
    }

    result = Pa_StartStream(g_engine_state.m_stream);
    if (result != paNoError) {
        Pa_CloseStream(g_engine_state.m_stream);
        g_engine_state.m_stream = nullptr;

        PyErr_SetString(PyExc_Exception, Pa_GetErrorText(result));
        g_engine_state.m_recording_allocator.stop();
        g_engine_state.m_recording_allocator.clear();
        return nullptr;
    }

    g_engine_state.m_recording = true;

    t_clip_id clip_id = g_engine_state.m_next_clip_id++;
    g_engine_state.m_clips.emplace(std::make_pair(clip_id, s_clip()));
    g_engine_state.m_recording_clip_id = clip_id;

    return PyLong_FromLong(clip_id);
}

PyObject *stop_recording_clip(PyObject *self) {
    if (!g_engine_state.m_recording) {
        PyErr_SetString(PyExc_Exception, "Not recording");
        return nullptr;
    }

    // It would be bad if this failed...
    if (Pa_StopStream(g_engine_state.m_stream) != paNoError) {
        PyErr_SetString(PyExc_Exception, "Failed to stop the stream");
        return nullptr;
    }

    // This too...
    if (Pa_CloseStream(g_engine_state.m_stream) != paNoError) {
        PyErr_SetString(PyExc_Exception, "Failed to close the stream");
        return nullptr;
    }

    g_engine_state.m_recording_allocator.stop();

    s_clip &clip = g_engine_state.m_clips[g_engine_state.m_recording_clip_id];
    g_engine_state.m_recording_allocator.save_recorded_samples(clip.m_samples);
    g_engine_state.m_recording_allocator.clear();
    g_engine_state.m_current_recording_buffer = nullptr;

    g_engine_state.m_recording = false;
    g_engine_state.m_recording_clip_id = -1;
    Py_RETURN_NONE;
}

PyObject *get_latest_recorded_samples(PyObject *self, PyObject *args) {
    int32_t sample_count;
    if (!PyArg_ParseTuple(args, "i", &sample_count)) {
        return nullptr;
    }

    if (!g_engine_state.m_recording) {
        PyErr_SetString(PyExc_Exception, "Not recording");
        return nullptr;
    }

    if (sample_count < 0) {
        PyErr_SetString(PyExc_ValueError, "Invalid sample count");
        return nullptr;
    }

    std::vector<double> latest_samples(sample_count, 0.0);
    int32_t samples_remaining = sample_count;
    const s_recording_buffer *recording_buffer = g_engine_state.m_current_recording_buffer;
    while (samples_remaining > 0 && recording_buffer) {
        size_t recording_buffer_samples_remaining = recording_buffer->m_usage;
        size_t amount_to_copy = std::min(static_cast<size_t>(samples_remaining), recording_buffer_samples_remaining);
        for (size_t i = 0; i < amount_to_copy; ++i) {
            // Note pre-increment because we are iterating down to 0
            latest_samples[--samples_remaining] = recording_buffer->m_samples[--recording_buffer_samples_remaining];
        }

        recording_buffer = recording_buffer->m_prev;
    }

    PyObject *list = PyList_New(sample_count);
    if (!list) {
        return nullptr;
    }

    for (int32_t i = 0; i < sample_count; ++i) {
        PyObject *value = PyFloat_FromDouble(latest_samples[i]);
        if (!value) {
            Py_DECREF(list);
            return nullptr;
        }
        PyList_SET_ITEM(list, i, value);
    }

    return list;
}

PyObject *get_clip_sample_count(PyObject *self, PyObject *args) {
    t_clip_id clip_id;
    if (!PyArg_ParseTuple(args, "i", &clip_id)) {
        return nullptr;
    }

    ERROR_IF_INVALID_CLIP_ID(clip_id);

    const s_clip &clip = g_engine_state.m_clips[clip_id];
    return PyLong_FromSize_t(clip.m_samples.size());
}

PyObject *get_clip_samples(PyObject *self, PyObject *args) {
    t_clip_id clip_id;
    int32_t max_sample_count;
    if (!PyArg_ParseTuple(args, "ii", &clip_id, &max_sample_count)) {
        return nullptr;
    }

    ERROR_IF_INVALID_CLIP_ID(clip_id);

    const s_clip &clip = g_engine_state.m_clips[clip_id];

    if (max_sample_count <= 0) {
        max_sample_count = static_cast<int32_t>(clip.m_samples.size());
    }

    int32_t sample_count = std::min(static_cast<int32_t>(clip.m_samples.size()), max_sample_count);
    PyObject *list = PyList_New(sample_count);
    if (!list) {
        return nullptr;
    }

    for (int32_t i = 0; i < max_sample_count; ++i) {
        // Spread out samples evenly if the count exceeds max_sample_count
        int64_t source_index = static_cast<int64_t>(i) * static_cast<int64_t>(clip.m_samples.size()) / max_sample_count;
        PyObject *value = PyFloat_FromDouble(clip.m_samples[source_index]);
        if (!value) {
            Py_DECREF(list);
            return nullptr;
        }
        PyList_SET_ITEM(list, i, value);
    }

    return list;
}

PyObject *playback_builder_begin(PyObject *self) {
    ERROR_IF_RECORDING;
    ERROR_IF_PLAYING;

    g_engine_state.m_playback_clips.clear();
    Py_RETURN_NONE;
}

PyObject *playback_builder_add_clip(PyObject *self, PyObject *args) {
    ERROR_IF_RECORDING;
    ERROR_IF_PLAYING;

    t_clip_id clip_id;
    int32_t start_sample_index;
    int32_t end_sample_index;
    int32_t playback_start_sample_index;
    if (!PyArg_ParseTuple(args, "iiii", &clip_id, &start_sample_index, &end_sample_index, &playback_start_sample_index)) {
        return nullptr;
    }

    ERROR_IF_INVALID_CLIP_ID(clip_id);

    const s_clip &clip = g_engine_state.m_clips[clip_id];
    if (start_sample_index < 0
        || static_cast<uint32_t>(start_sample_index) > clip.m_samples.size()
        || end_sample_index < 0
        || static_cast<uint32_t>(end_sample_index) > clip.m_samples.size()
        || start_sample_index > end_sample_index) {
        PyErr_SetString(PyExc_ValueError, "Invalid start/end sample indices");
        return nullptr;
    }

    s_playback_clip playback_clip;
    playback_clip.m_clip_id = clip_id;
    playback_clip.m_start_sample_index = start_sample_index;
    playback_clip.m_end_sample_index = end_sample_index;
    playback_clip.m_playback_start_sample_index = playback_start_sample_index;
    g_engine_state.m_playback_clips.push_back(playback_clip);

    Py_RETURN_NONE;
}

PyObject *playback_builder_finalize(PyObject *self) {
    ERROR_IF_RECORDING;
    ERROR_IF_PLAYING;

    g_engine_state.m_playback_events.clear();

    g_engine_state.m_playback_events.reserve(g_engine_state.m_playback_clips.size() * 2);
    for (size_t i = 0; i < g_engine_state.m_playback_clips.size(); ++i) {
        const s_playback_clip &playback_clip = g_engine_state.m_playback_clips[i];
        int32_t clip_length = playback_clip.m_end_sample_index - playback_clip.m_start_sample_index;
        s_playback_event start_event = { e_playback_event::k_start_clip, i, playback_clip.m_playback_start_sample_index };
        s_playback_event stop_event = { e_playback_event::k_stop_clip, i, playback_clip.m_playback_start_sample_index + clip_length };

        g_engine_state.m_playback_events.push_back(start_event);
        g_engine_state.m_playback_events.push_back(stop_event);
    }

    // Sort events using a stable sort - end events should always come after start events, even if the sample count is 0
    std::stable_sort(
        g_engine_state.m_playback_events.begin(),
        g_engine_state.m_playback_events.end(),
        [](const s_playback_event &a, const s_playback_event &b) { return a.m_sample_index < b.m_sample_index; });

    Py_RETURN_NONE;
}

PyObject *start_playback(PyObject *self, PyObject *args) {
    int32_t output_device_index;
    int32_t frames_per_buffer;
    int32_t sample_index;
    if (!PyArg_ParseTuple(args, "iii", &output_device_index, &frames_per_buffer, &sample_index)) {
        return nullptr;
    }

    ERROR_IF_RECORDING;
    ERROR_IF_PLAYING;

    if (g_engine_state.m_sample_rate <= 0) {
        PyErr_SetString(PyExc_ValueError, "Invalid sample rate");
        return nullptr;
    }

    if (output_device_index < 0 || static_cast<uint32_t>(output_device_index) >= g_engine_state.m_output_devices.size()) {
        PyErr_SetString(PyExc_ValueError, "Invalid input device index");
        return nullptr;
    }

    if (frames_per_buffer <= 0) {
        PyErr_SetString(PyExc_ValueError, "Invalid frames per buffer");
        return nullptr;
    }

    const s_device &output_device = g_engine_state.m_output_devices[output_device_index];

    // Setup the stream parameters
    PaStreamParameters output_params;
    output_params.device = output_device.m_portaudio_device_index;
    output_params.channelCount = 1;
    output_params.sampleFormat = paFloat32;
    output_params.suggestedLatency = output_device.m_suggested_latency;
    output_params.hostApiSpecificStreamInfo = nullptr;

    PaError result = Pa_IsFormatSupported(
        nullptr,
        &output_params,
        static_cast<double>(g_engine_state.m_sample_rate));
    if (result != paFormatIsSupported) {
        PyErr_SetString(PyExc_Exception, Pa_GetErrorText(result));
        return nullptr;
    }

    // Go through all the clip events and clear them from the active list
    g_engine_state.m_first_active_playback_clip = nullptr;
    for (size_t i = 0; i < g_engine_state.m_playback_clips.size(); ++i) {
        s_playback_clip &playback_clip = g_engine_state.m_playback_clips[i];
        playback_clip.m_prev_active_playback_clip = nullptr;
        playback_clip.m_next_active_playback_clip = nullptr;
    }

    // Activate and deactivate the appropriate playback clips for our starting point
    g_engine_state.m_next_playback_event_index = 0;
    for (size_t i = 0; i < g_engine_state.m_playback_events.size(); ++i) {
        const s_playback_event &playback_event = g_engine_state.m_playback_events[i];
        if (playback_event.m_sample_index > sample_index) {
            // This event occurs after our start sample, so don't process it or anything that comes after it
            break;
        }

        if (playback_event.m_event == e_playback_event::k_start_clip) {
            activate_playback_clip(playback_event.m_playback_clip_index);
        } else {
            assert(playback_event.m_event == e_playback_event::k_stop_clip);
            deactivate_playback_clip(playback_event.m_playback_clip_index);
        }
    }

    g_engine_state.m_playback_sample_index = sample_index;

    result = Pa_OpenStream(
        &g_engine_state.m_stream,
        nullptr,
        &output_params,
        static_cast<double>(g_engine_state.m_sample_rate),
        static_cast<uint32_t>(frames_per_buffer),
        paNoFlag,
        playback_stream_main,
        nullptr);
    if (result != paNoError) {
        PyErr_SetString(PyExc_Exception, Pa_GetErrorText(result));
        return nullptr;
    }

    result = Pa_StartStream(g_engine_state.m_stream);
    if (result != paNoError) {
        Pa_CloseStream(g_engine_state.m_stream);
        g_engine_state.m_stream = nullptr;

        PyErr_SetString(PyExc_Exception, Pa_GetErrorText(result));
        return nullptr;
    }

    g_engine_state.m_playing = true;
    Py_RETURN_NONE;
}

PyObject *stop_playback(PyObject *self) {
    if (!g_engine_state.m_playing) {
        PyErr_SetString(PyExc_Exception, "Not playing");
        return nullptr;
    }

    // It would be bad if this failed...
    if (Pa_StopStream(g_engine_state.m_stream) != paNoError) {
        PyErr_SetString(PyExc_Exception, "Failed to stop the stream");
        return nullptr;
    }

    // This too...
    if (Pa_CloseStream(g_engine_state.m_stream) != paNoError) {
        PyErr_SetString(PyExc_Exception, "Failed to close the stream");
        return nullptr;
    }

    g_engine_state.m_playing = false;
    Py_RETURN_NONE;
}

PyObject *get_playback_sample_index(PyObject *self) {
    return PyLong_FromLong(g_engine_state.m_playback_sample_index);
}

static void activate_playback_clip(size_t playback_clip_index) {
    s_playback_clip &playback_clip = g_engine_state.m_playback_clips[playback_clip_index];
    assert(playback_clip.m_prev_active_playback_clip == nullptr);
    assert(playback_clip.m_next_active_playback_clip == nullptr);

    if (g_engine_state.m_first_active_playback_clip != nullptr) {
        g_engine_state.m_first_active_playback_clip->m_next_active_playback_clip = &playback_clip;
        playback_clip.m_prev_active_playback_clip = g_engine_state.m_first_active_playback_clip;
    }

    g_engine_state.m_first_active_playback_clip = &playback_clip;
}

static void deactivate_playback_clip(size_t playback_clip_index) {
    s_playback_clip &playback_clip = g_engine_state.m_playback_clips[playback_clip_index];

    if (playback_clip.m_prev_active_playback_clip == nullptr) {
        g_engine_state.m_first_active_playback_clip = playback_clip.m_next_active_playback_clip;
    } else {
        playback_clip.m_prev_active_playback_clip->m_next_active_playback_clip = playback_clip.m_next_active_playback_clip;
    }

    if (playback_clip.m_next_active_playback_clip != nullptr) {
        playback_clip.m_next_active_playback_clip->m_prev_active_playback_clip = playback_clip.m_prev_active_playback_clip;
    }

    playback_clip.m_prev_active_playback_clip = nullptr;
    playback_clip.m_next_active_playback_clip = nullptr;
}

int recording_stream_main(
    const void *input,
    void *output,
    unsigned long frame_count,
    const PaStreamCallbackTimeInfo *time_info,
    PaStreamCallbackFlags status_flags,
    void *user_data) {
    s_recording_buffer *recording_buffer = g_engine_state.m_current_recording_buffer;

    size_t frame_index = 0;
    while (frame_index < frame_count) {
        size_t capacity = recording_buffer->m_samples.size();
        size_t usage = recording_buffer->m_usage;
        if (usage == capacity) {
            recording_buffer = recording_buffer->m_next;
            if (!recording_buffer) {
                ++g_engine_state.m_recording_underflows;
                break;
            }

            capacity = recording_buffer->m_samples.size();
            usage = recording_buffer->m_usage;
            assert(usage == 0); // A new recording buffer should have no usage
        }

        size_t copy_amount = std::min(static_cast<size_t>(frame_count), capacity - usage);
        recording_buffer->m_usage += copy_amount;
        for (size_t i = 0; i < copy_amount; ++i) {
            recording_buffer->m_samples[usage++] = static_cast<const float *>(input)[frame_index++];
        }
    }

    // Update the current recording buffer for the next callback
    g_engine_state.m_current_recording_buffer = recording_buffer;

    return paContinue;
}

int playback_stream_main(
    const void *input,
    void *output,
    unsigned long frame_count,
    const PaStreamCallbackTimeInfo *time_info,
    PaStreamCallbackFlags status_flags,
    void *user_data) {
    // Zero the output buffer because we're going to accumulate clip samples
    float *output_buffer = reinterpret_cast<float *>(output);
    memset(output_buffer, 0, frame_count * sizeof(float));

    int32_t current_sample_index = g_engine_state.m_playback_sample_index;
    int32_t end_sample_index = current_sample_index + static_cast<int32_t>(frame_count);
    int32_t output_buffer_offset = 0;
    while (current_sample_index < end_sample_index) {
        // Phase 1: determine how many samples we can process before an event occurs
        int32_t iteration_end_sample_index = end_sample_index;
        const s_playback_event *next_playback_event = nullptr;
        if (g_engine_state.m_next_playback_event_index < g_engine_state.m_playback_events.size()) {
            next_playback_event = &g_engine_state.m_playback_events[g_engine_state.m_next_playback_event_index];
            if (next_playback_event->m_sample_index < end_sample_index) {
                iteration_end_sample_index = next_playback_event->m_sample_index;
            } else {
                next_playback_event = nullptr; // Ignore it for now, we won't process any samples for this event
            }
        }

        // Phase 2: accumulate data from clips into the output buffer
        if (current_sample_index != iteration_end_sample_index) {
            int32_t iteration_sample_count = iteration_end_sample_index - current_sample_index;

            const s_playback_clip *playback_clip = g_engine_state.m_first_active_playback_clip;
            while (playback_clip) {
                const s_clip &clip = g_engine_state.m_clips[playback_clip->m_clip_id];
                int32_t clip_start_sample =
                    current_sample_index - playback_clip->m_playback_start_sample_index + playback_clip->m_start_sample_index;
                for (int32_t i = 0; i < iteration_sample_count; ++i) {
                    output_buffer[output_buffer_offset + i] += clip.m_samples[clip_start_sample + i];
                }

                playback_clip = playback_clip->m_next_active_playback_clip;
            }

            current_sample_index = iteration_end_sample_index;
            output_buffer_offset += iteration_sample_count;
        }

        // Phase 3: process the next event to activate or deactivate clips
        if (next_playback_event != nullptr) {
            // Activate or deactivate the clip associated with this event
            if (next_playback_event->m_event == e_playback_event::k_start_clip) {
                activate_playback_clip(next_playback_event->m_playback_clip_index);
            } else {
                assert(next_playback_event->m_event == e_playback_event::k_stop_clip);
                deactivate_playback_clip(next_playback_event->m_playback_clip_index);
            }

            // Advance to the next event
            ++g_engine_state.m_next_playback_event_index;
        }
    }

    g_engine_state.m_playback_sample_index = end_sample_index;
    return paContinue;
}
