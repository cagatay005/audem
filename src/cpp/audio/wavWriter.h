#pragma once

#include <string>
#include <vector>
#include <cstdint>

// Ham ses verisini (PCM) disk üzerine .wav formatında kaydeden modül
class WavWriter {
public:
    // Dosya adı, ses verisi ve örnekleme hızını alarak .wav dosyası oluşturur. Başarılı olursa true döner.
    static bool writeWav(const std::string& filename, const std::vector<int16_t>& audioData, int sampleRate = 8000);
};