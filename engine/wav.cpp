#include "wav.h"

#include <fstream>

struct s_wav_header {
    // riff
    uint8_t m_riff[4];
    uint32_t m_chunk_size;
    uint8_t m_wave[4];

    // fmt
    uint8_t m_subchunk_1_id[4];
    uint32_t m_subchunk_1_size;
    uint16_t m_audio_format;
    uint16_t m_channel_count;
    uint32_t m_sample_rate;
    uint32_t m_byte_rate;
    uint16_t m_block_align;
    uint16_t m_bits_per_sample;

    // data
    uint8_t m_subchunk_2_id[4];
    uint32_t m_subchunk_2_size;
};

template<typename t_value>
t_value swap_endian(t_value value) {
    // $TODO make this work on all platforms
    union {
        t_value m_value;
        uint8_t m_bytes[sizeof(t_value)];
    } u;

    u.m_value = value;
    for (size_t i = 0; i < sizeof(t_value) / 2; ++i) {
        std::swap(u.m_bytes[i], u.m_bytes[sizeof(t_value) - i - 1]);
    }
    return u.m_value;
}

template<typename t_value>
t_value little_to_native_endian(t_value value) {
    // $TODO make this work on all platforms
    return value;
}

template<typename t_value>
t_value native_to_little_endian(t_value value) {
    // $TODO make this work on all platforms
    return value;
}

bool read_wav(const char *filename, std::vector<float> &samples, uint32_t &sample_rate) {
    std::ifstream file;
    file.open(filename, std::ios::binary);
    if (!file.is_open()) {
        return false;
    }

    s_wav_header header;
    file.read(reinterpret_cast<char *>(&header), sizeof(header));
    if (file.fail()) {
        return false;
    }

    header.m_chunk_size = little_to_native_endian(header.m_chunk_size);
    header.m_subchunk_1_size = little_to_native_endian(header.m_subchunk_1_size);
    header.m_audio_format = little_to_native_endian(header.m_audio_format);
    header.m_channel_count = little_to_native_endian(header.m_channel_count);
    header.m_sample_rate = little_to_native_endian(header.m_sample_rate);
    header.m_byte_rate = little_to_native_endian(header.m_byte_rate);
    header.m_block_align = little_to_native_endian(header.m_block_align);
    header.m_bits_per_sample = little_to_native_endian(header.m_bits_per_sample);
    header.m_subchunk_2_size = little_to_native_endian(header.m_subchunk_2_size);

    static const uint8_t k_riff[] = { 'R', 'I', 'F', 'F' };
    if (memcmp(header.m_riff, k_riff, sizeof(k_riff)) != 0) {
        return false;
    }

    static const uint8_t k_wave[] = { 'W', 'A', 'V', 'E' };
    if (memcmp(header.m_wave, k_wave, sizeof(k_wave)) != 0) {
        return false;
    }

    static const uint8_t k_fmt[] = { 'f', 'm', 't', ' ' };
    if (memcmp(header.m_subchunk_1_id, k_fmt, sizeof(k_fmt)) != 0) {
        return false;
    }

    if (header.m_subchunk_1_size != 16
        || header.m_audio_format != 3 // float format
        || header.m_channel_count != 1
        || header.m_byte_rate != header.m_channel_count * header.m_sample_rate * header.m_bits_per_sample / 8
        || header.m_block_align != header.m_channel_count * header.m_bits_per_sample / 8
        || header.m_bits_per_sample != sizeof(float) * 8) { // 32 bits per float sample
        return false;
    }

    static const uint8_t k_data[] = { 'd', 'a', 't', 'a' };
    if (memcmp(header.m_subchunk_2_id, k_data, sizeof(k_data)) != 0) {
        return false;
    }

    if (header.m_subchunk_2_size % (header.m_channel_count * header.m_bits_per_sample / 8) != 0) {
        return false;
    }

    uint32_t sample_count = header.m_subchunk_2_size / sizeof(float);

    samples.resize(sample_count);
    if (sample_count > 0) {
        file.read(reinterpret_cast<char *>(&samples.front()), sample_count * sizeof(float));
    }
    sample_rate = header.m_sample_rate;

    return true;
}

bool write_wav(const char *filename, const float *samples, size_t sample_count, uint32_t sample_rate) {
    std::ofstream file;
    file.open(filename, std::ios::binary);
    if (!file.is_open()) {
        return false;
    }

    s_wav_header header = { 0 };

    uint32_t bytes_per_sample = static_cast<uint32_t>(sizeof(float));
    uint32_t data_size = static_cast<uint32_t>(sample_count * bytes_per_sample);

    static const uint8_t k_riff[] = { 'R', 'I', 'F', 'F' };
    memcpy(header.m_riff, k_riff, sizeof(k_riff));

    header.m_chunk_size = native_to_little_endian(36 + data_size);

    static const uint8_t k_wave[] = { 'W', 'A', 'V', 'E' };
    memcpy(header.m_wave, k_wave, sizeof(k_wave));

    static const uint8_t k_fmt[] = { 'f', 'm', 't', ' ' };
    memcpy(header.m_subchunk_1_id, k_fmt, sizeof(k_fmt));

    header.m_subchunk_1_size = native_to_little_endian(16);
    header.m_audio_format = native_to_little_endian(3);
    header.m_channel_count = native_to_little_endian(1);
    header.m_sample_rate = native_to_little_endian(sample_rate);
    header.m_byte_rate = native_to_little_endian(sample_rate * bytes_per_sample);
    header.m_block_align = native_to_little_endian(bytes_per_sample);
    header.m_bits_per_sample = native_to_little_endian(bytes_per_sample * 8);

    static const uint8_t k_data[] = { 'd', 'a', 't', 'a' };
    memcpy(header.m_subchunk_2_id, k_data, sizeof(k_data));

    header.m_subchunk_2_size = native_to_little_endian(data_size);

    file.write(reinterpret_cast<const char *>(&header), sizeof(header));
    if (file.fail()) {
        return false;
    }

    if (sample_count > 0) {
        file.write(reinterpret_cast<const char *>(samples), data_size);
        if (file.fail()) {
            return false;
        }
    }

    return true;
}
