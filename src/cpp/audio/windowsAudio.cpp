#include "windowsAudio.h"
#include <iostream>

// İşletim sisteminin her seferinde vereceği ses paketinin boyutu
const int BUFFER_SIZE = 4096;

WindowsAudio::WindowsAudio() : hWaveIn(nullptr), isRecording(false) {
    // Ses formatı belirlenir
    waveFormat.wFormatTag = WAVE_FORMAT_PCM;
    waveFormat.nChannels = 1;                    
    waveFormat.nSamplesPerSec = 8000;             // Saniyede 8000 örnek
    waveFormat.wBitsPerSample = 16;               // Her bir örnek 16-bit yer kaplar
    waveFormat.nBlockAlign = (waveFormat.nChannels * waveFormat.wBitsPerSample) / 8;
    waveFormat.nAvgBytesPerSec = waveFormat.nSamplesPerSec * waveFormat.nBlockAlign;
    waveFormat.cbSize = 0;
}

WindowsAudio::~WindowsAudio() {
    // Sınıf yok edildiğinde (program kapandığında) mikrofonu açık bırakmamak için durdurur
    stopCapture();
}

bool WindowsAudio::startCapture() {
    if (isRecording) return true;

    // Ses giriş cihazını açar. WAVE_MAPPER, Windows'taki varsayılan mikrofonu/girişi otomatik seçer.
    MMRESULT result = waveInOpen(&hWaveIn, WAVE_MAPPER, &waveFormat,
                                 (DWORD_PTR)waveInCallback, (DWORD_PTR)this, CALLBACK_FUNCTION);

    if (result != MMSYSERR_NOERROR) {
        std::cerr << "Hata: Ses cihazi acilamadi!" << std::endl;
        return false;
    }

    // Ses kesintisi olmaması için "Double Buffering" (Çift Tampon) kullanıldı.
    // İşletim sistemi bir tamponu doldururken, diğerinden veri çekildi böylece akıcılık saglandi.
    for (int i = 0; i < 2; ++i) {
        waveHeader[i].lpData = new char[BUFFER_SIZE * 2]; // 16-bit = 2 byte
        waveHeader[i].dwBufferLength = BUFFER_SIZE * 2;
        waveHeader[i].dwBytesRecorded = 0;
        waveHeader[i].dwUser = 0;
        waveHeader[i].dwFlags = 0;
        waveHeader[i].dwLoops = 0;

        waveInPrepareHeader(hWaveIn, &waveHeader[i], sizeof(WAVEHDR));
        waveInAddBuffer(hWaveIn, &waveHeader[i], sizeof(WAVEHDR));
    }

    isRecording = true;
    waveInStart(hWaveIn); // Kaydı fiilen başlatır
    return true;
}

void WindowsAudio::stopCapture() {
    if (!isRecording) return;
    isRecording = false;

    waveInStop(hWaveIn);
    waveInReset(hWaveIn);

    // Ayrılan bellekleri (RAM) sisteme geri iade eder (Memory leak önleme)
    for (int i = 0; i < 2; ++i) {
        waveInUnprepareHeader(hWaveIn, &waveHeader[i], sizeof(WAVEHDR));
        delete[] waveHeader[i].lpData;
    }

    waveInClose(hWaveIn);
    hWaveIn = nullptr;
}

std::vector<int16_t> WindowsAudio::getAudioBuffer() {
    // İşletim sistemi arka planda bu diziye veri yazarken okunmasını engellemek için kilit (mutex) konuldu.
    std::lock_guard<std::mutex> lock(bufferMutex);
    
    // Mevcut birikmiş sesi kopyalar
    std::vector<int16_t> copyBuffer = audioBuffer;
    
    // Okunan veri silinir ki bir sonraki çağırmada aynı sesi tekrar işlenmesin
    audioBuffer.clear(); 
    
    return copyBuffer;
}

int WindowsAudio::getSampleRate() const {
    return waveFormat.nSamplesPerSec;
}

// İşletim sistemi bir tamponu (buffer) tamamen doldurduğunda bu fonksiyon otomatik olarak tetiklenir (Callback)
void CALLBACK WindowsAudio::waveInCallback(HWAVEIN hwi, UINT uMsg, DWORD_PTR dwInstance, DWORD_PTR dwParam1, DWORD_PTR dwParam2) {
    if (uMsg == WIM_DATA) { // Yeni ses verisi geldiyse
        WindowsAudio* audioObj = (WindowsAudio*)dwInstance;
        WAVEHDR* pWaveHeader = (WAVEHDR*)dwParam1;

        if (pWaveHeader->dwBytesRecorded > 0) {
            std::lock_guard<std::mutex> lock(audioObj->bufferMutex);
            
            // Baytları 16-bit tamsayılara (PCM genlik değerlerine) çevirir
            int16_t* pData = (int16_t*)pWaveHeader->lpData;
            int sampleCount = pWaveHeader->dwBytesRecorded / 2; 
            
            // Gelen sayı dizisini asıl tampona ekler
            audioObj->audioBuffer.insert(audioObj->audioBuffer.end(), pData, pData + sampleCount);
        }

        // Kayıt devam ediyorsa, dolan ve işlem biten tamponu işletim sistemine boş olarak geri verir böylece bellek birikmesi önlendi.
        if (audioObj->isRecording) {
            waveInAddBuffer(hwi, pWaveHeader, sizeof(WAVEHDR));
        }
    }
}