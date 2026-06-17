#include "fourierTransform.h"
#include <cmath>
#include <algorithm>

// Pi sayısı yüksek hassasiyetle tanımlandı :))) çok iyi ölçümler yapmak için
const double PI = 3.141592653589793238460;

std::vector<Complex> FourierTransform::convertToComplex(const std::vector<int16_t>& audioData) {
    std::vector<Complex> complexData;
    complexData.reserve(audioData.size()); // Bellek tahsisi önden yapılarak hız kazanıldı
    
    for (int16_t sample : audioData) {
        // Gerçek kısım ses genliği, sanal kısım 0
        complexData.push_back(Complex(sample, 0.0));
    }
    
    return complexData;
}

void FourierTransform::padToPowerOfTwo(std::vector<Complex>& data) {
    size_t n = data.size();
    if (n == 0) return;
    
    size_t power = 1;
    // n'den büyük veya eşit olan ilk 2'nin kuvvetini buldu
    while (power < n) {
        power *= 2;
    }
    
    // Eğer dizi tam olarak 2'nin kuvveti değilse, sonuna (0 + 0i) eklendi (Zero-padding)
    if (power > n) {
        data.resize(power, Complex(0.0, 0.0));
    }
}

void FourierTransform::computeFFT(std::vector<Complex>& data) {
    size_t n = data.size();
    if (n <= 1) return;

    // 1. Aşama: Bit-Reversal Permutation (İndeksleri tersine çevirerek yer değiştirme)
    size_t j = 0;
    for (size_t i = 1; i < n; ++i) {
        size_t bit = n >> 1;
        while (j & bit) {
            j ^= bit;
            bit >>= 1;
        }
        j ^= bit;
        
        if (i < j) {
            std::swap(data[i], data[j]);
        }
    }

    // 2. Aşama: Cooley-Tukey Kelebek İşlemleri (Butterfly Operations)
    // len: İşlenen alt dizinin boyutu (2, 4, 8, 16 ... N)
    for (size_t len = 2; len <= n; len <<= 1) {
        // Dönüş açısı (Radyan cinsinden)
        double angle = -2.0 * PI / len; 
        Complex wlen(std::cos(angle), std::sin(angle));
        
        for (size_t i = 0; i < n; i += len) {
            Complex w(1.0, 0.0);
            
            for (size_t k = 0; k < len / 2; ++k) {
                Complex u = data[i + k];
                Complex v = data[i + k + len / 2] * w;
                
                data[i + k] = u + v;
                data[i + k + len / 2] = u - v;
                
                w *= wlen; // Bir sonraki açıya geç
            }
        }
    }
}