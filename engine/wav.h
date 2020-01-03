#pragma once

#include <vector>

// Reads/writes single channel float wavs
bool read_wav(const char *filename, std::vector<float> &samples, uint32_t &sample_rate);
bool write_wav(const char *filename, const float *samples, size_t sample_count, uint32_t sample_rate);
