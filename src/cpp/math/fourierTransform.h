#pragma once

#include <vector>
#include <complex>
#include <cstdint>

// Karmaşık sayılarla çalışılacağı için kodun okunuşunu kolaylaştıran bir takma ad (alias) tanımlandı
using Complex = std::complex<double>;

class FourierTransform {
public:
    // Sesi zaman düzleminden (genlik) frekans düzlemine çeviren ana algoritma.
    // Cooley-Tukey FFT algoritmasını kullanır. Performans için veriyi referans (&) olarak alıp üzerinde değişiklik yapar (In-place).
    static void computeFFT(std::vector<Complex>& data);

    // İşletim sisteminden aldığımız ham ses verisini (int16_t) karmaşık sayılara çevirip FFT'ye hazırlayan fonksiyon.
    // Sesin gerçek kısmı genliktir, sanal kısmı (i) ise 0 olarak başlatılır.
    static std::vector<Complex> convertToComplex(const std::vector<int16_t>& audioData);

    // Veri boyutunu 2'nin en yakın üst kuvvetine tamamlar (Zero-padding).
    // Cooley-Tukey algoritması matematiksel olarak sadece 2^N boyutundaki dizilerle çalışabilir.
    static void padToPowerOfTwo(std::vector<Complex>& data);
};