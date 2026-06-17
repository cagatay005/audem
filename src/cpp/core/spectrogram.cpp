#include "spectrogram.h"
#include "../math/fourierTransform.h"
#include <cmath>
#include <algorithm>

const double PI = 3.141592653589793238460;

Spectrogram::Spectrogram(int windowSize, int overlap) 
    : windowSize(windowSize), overlap(overlap) {}

std::vector<double> Spectrogram::generateHannWindow(int size) {
    std::vector<double> window(size);
    for (int i = 0; i < size; ++i) {
        // Hann penceresi formülü
        window[i] = 0.5 * (1.0 - std::cos((2.0 * PI * i) / (size - 1)));
    }
    return window;
}

std::vector<std::vector<double>> Spectrogram::compute(const std::vector<int16_t>& audioData) {
    std::vector<std::vector<double>> spectrogramMatrix;
    
    if (audioData.empty() || windowSize <= 0 || overlap >= windowSize) {
        return spectrogramMatrix;
    }

    int stepSize = windowSize - overlap;
    std::vector<double> hannWindow = generateHannWindow(windowSize);
    
    // Sesi baştan sona pencereler halinde tarar
    for (size_t startIdx = 0; startIdx < audioData.size(); startIdx += stepSize) {
        std::vector<int16_t> windowedAudio(windowSize, 0); // Varsayılan olarak 0 (Zero-padding için)
        
        // Sesin sonuna geldiğimizde taşmayı önlemek için güvenli kopyalama yapar
        int copySize = std::min(windowSize, static_cast<int>(audioData.size() - startIdx));
        
        for (int i = 0; i < copySize; ++i) {
            // Ham sesi Hann penceresi ile çarparak yumuşatıldı
            windowedAudio[i] = static_cast<int16_t>(audioData[startIdx + i] * hannWindow[i]);
        }

        // 1. Adım: Sesi karmaşık sayılara çevir
        std::vector<Complex> complexData = FourierTransform::convertToComplex(windowedAudio);
        
        // 2. Adım: Boyutu 2'nin kuvvetine tamamla (Cooley-Tukey için zorunlu)
        FourierTransform::padToPowerOfTwo(complexData);
        
        // 3. Adım: FFT algoritmasını çalıştır
        FourierTransform::computeFFT(complexData);

        // 4. Adım: Karmaşık sayıların genliğini (magnitude) hesapla
        // Nyquist teoremine göre sadece ilk yarısı anlamlıdır (frekansların simetrisi)
        size_t halfSize = complexData.size() / 2;
        std::vector<double> magnitudes(halfSize);
        
        for (size_t i = 0; i < halfSize; ++i) {
            // Büyüklük hesaplama: sqrt(reel^2 + sanal^2)
            magnitudes[i] = std::sqrt(complexData[i].real() * complexData[i].real() + 
                                      complexData[i].imag() * complexData[i].imag());
        }

        // Oluşan zaman dilimini (kolonu) spektrogram matrisine ekle
        spectrogramMatrix.push_back(magnitudes);
    }

    return spectrogramMatrix;
}