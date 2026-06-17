#pragma once

#include <vector>
#include <cstdint>

// Spektrogram üzerindeki tepe noktalarını temsil eden yapı (Yıldızlar)
struct Peak {
    int timeIdx;      // Zaman eksenindeki indeksi
    int freqIdx;      // Frekans eksenindeki indeksi
    double amplitude; // Sesin o noktadaki şiddeti (Enerjisi)
};

// Veritabanına kaydedilecek ve aranacak olan parmak izi (Hash) yapısı
struct Fingerprint {
    uint64_t hashValue; // Frekanslar ve aralarındaki zaman farkından üretilen 64-bit şifre
    int anchorTime;     // Çapa (anchor) noktasının mutlak zamanı (Eşleştirme sırasında zaman kaymasını bulmak için)
};

class FingerprintManager {
private:
    int peakNeighborhood; // Tepe noktası ararken bakılacak komşuluk yarıçapı (Kare boyutu)
    double minAmplitude;  // Arka plan gürültüsünü elemek için minimum genlik sınırı

    // Hedef bölge (Target Zone) ayarları - Çapa noktası ile eşleştirilecek hedeflerin sınırları
    int targetZoneDelay;  // Çapa noktasından kaç zaman birimi sonra hedef bölge başlıyor
    int targetZoneWidth;  // Hedef bölgenin zaman eksenindeki genişliği

public:
    // Yapıcı metot (Constructor) varsayılan ayarlarıyla
    FingerprintManager(int neighborhood = 5, double minAmp = 10.0, 
                       int tzDelay = 3, int tzWidth = 10);

    // 1. Aşama: Spektrogram matrisinden en yüksek enerjili tepe noktalarını çıkarır (Takımyıldızı)  :))
    std::vector<Peak> extractConstellation(const std::vector<std::vector<double>>& spectrogram);

    // 2. Aşama: Tepe noktalarını ikili gruplar (anchor ve target) halinde eşleştirerek hash üretir
    std::vector<Fingerprint> generateHashes(const std::vector<Peak>& peaks);
};