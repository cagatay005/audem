#pragma once

#include <vector>
#include <cstdint>

class Spectrogram {
private:
    int windowSize; // FFT işlemine girecek her bir ses parçasının boyutu (Örn: 4096)
    int overlap;    // Pencerelerin birbirinin üstüne ne kadar bineceği (Örn: 2048)

    // Hann Pencereleme Fonksiyonu: 
    // Ses parçalara bölünürken baş ve son kısımlarda oluşan ani kesilmeleri (spectral leakage) engeller.
    std::vector<double> generateHannWindow(int size);

public:
    // Yapıcı metot (Constructor). Varsayılan olarak 4096 boyut ve %50 örtüşme kullanıldı.
    Spectrogram(int windowSize = 4096, int overlap = 2048);

    // Ana işlem fonksiyonu. Ham ses verisini alır ve 2 boyutlu bir matris döndürür.
    // Matrisin yapısı: Dış vektör zaman dilimlerini (pencereleri), iç vektör ise o dilimdeki frekans genliklerini tutar.
    std::vector<std::vector<double>> compute(const std::vector<int16_t>& audioData);
};