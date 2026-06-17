#pragma once

#include "iAudioCapture.h"
#include <windows.h>
#include <mmsystem.h> // Windows WaveIn API'si için gerekli kütüphane
#include <vector>
#include <mutex>

#pragma comment(lib, "winmm.lib")

class WindowsAudio : public IAudioCapture {
private:
    HWAVEIN hWaveIn;             // Windows ses giriş cihazı tutucusu (Handle)
    WAVEFORMATEX waveFormat;     // Ses formatı ayarları (Örnekleme hızı, kanal, bit derinliği)
    
    // Ses kesintisi olmaması için çift tampon (Double buffering) tekniği kullanıldı
    WAVEHDR waveHeader[2];       
    
    std::vector<int16_t> audioBuffer; // Arayüze döndürülecek asıl ses verisi
    bool isRecording;                 // Kayıt durumunu takip eden bayrak
    std::mutex bufferMutex;           // İşletim sistemi sesi arka planda doldururken çakışmayı önleyecek kilit (Thread safety)

    // İşletim sistemi tamponu sesle doldurduğunda otomatik olarak tetiklenecek geri çağırım (Callback) fonksiyonu
    static void CALLBACK waveInCallback(HWAVEIN hwi, UINT uMsg, DWORD_PTR dwInstance, DWORD_PTR dwParam1, DWORD_PTR dwParam2);

public:
    WindowsAudio();
    ~WindowsAudio() override;

    // IAudioCapture arayüzünden gelen zorunlu fonksiyonlar
    bool startCapture() override;
    void stopCapture() override;
    std::vector<int16_t> getAudioBuffer() override;
    int getSampleRate() const override;
};