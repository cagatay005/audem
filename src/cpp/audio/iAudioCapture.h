#pragma once

#include <vector>
#include <cstdint>

// Tüm işletim sistemleri için ortak ses yakalama şablonu
class IAudioCapture {
public:
    // Sanal yıkıcı - bellek sızıntıları için
    virtual ~IAudioCapture() = default;

    // Ses dinlemeyi başlatır. Başarılı olursa true döner.
    virtual bool startCapture() = 0;

    // Ses dinlemeyi durdurur.
    virtual void stopCapture() = 0;

    // O anki ses tamponunu (buffer) döndürür.
    // Ses verileri (PCM) genelde 16-bit tamsayı (int16_t) olarak işlenir.
    virtual std::vector<int16_t> getAudioBuffer() = 0;

    // Sistemin saniyede kaç örnek (sample) aldığını döndürür (Örn: 8000, 44100)
    virtual int getSampleRate() const = 0;
};