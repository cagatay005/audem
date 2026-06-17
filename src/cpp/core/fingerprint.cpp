#include "fingerprint.h"
#include <algorithm>

FingerprintManager::FingerprintManager(int neighborhood, double minAmp, int tzDelay, int tzWidth)
    : peakNeighborhood(neighborhood), minAmplitude(minAmp), 
      targetZoneDelay(tzDelay), targetZoneWidth(tzWidth) {}

std::vector<Peak> FingerprintManager::extractConstellation(const std::vector<std::vector<double>>& spectrogram) {
    std::vector<Peak> peaks;
    if (spectrogram.empty() || spectrogram[0].empty()) return peaks;

    int timeSize = spectrogram.size();
    int freqSize = spectrogram[0].size();

    // Matrisin her bir noktasını (zaman, frekans) tarar
    for (int t = 0; t < timeSize; ++t) {
        for (int f = 0; f < freqSize; ++f) {
            double amp = spectrogram[t][f];
            
            // Genlik çok düşükse, arka plan gürültüsüdür. Atla.
            if (amp < minAmplitude) continue;

            // Bu noktanın kendi komşuluğunda (belirli bir yarıçap içinde) en yüksek değer olup olmadığını kontrol eder.
            bool isLocalMax = true;
            int tStart = std::max(0, t - peakNeighborhood);
            int tEnd = std::min(timeSize - 1, t + peakNeighborhood);
            int fStart = std::max(0, f - peakNeighborhood);
            int fEnd = std::min(freqSize - 1, f + peakNeighborhood);

            for (int i = tStart; i <= tEnd && isLocalMax; ++i) {
                for (int j = fStart; j <= fEnd && isLocalMax; ++j) {
                    // Etrafta daha yüksek enerjili bir nokta varsa, bu nokta tepe değildir
                    if (spectrogram[i][j] > amp && (i != t || j != f)) {
                        isLocalMax = false;
                    }
                }
            }

            // Etrafın en büyüğüyse, bunu bir "yıldız" (Peak) olarak kaydet
            if (isLocalMax) {
                peaks.push_back({t, f, amp});
            }
        }
    }
    return peaks;
}

std::vector<Fingerprint> FingerprintManager::generateHashes(const std::vector<Peak>& peaks) {
    std::vector<Fingerprint> fingerprints;
    if (peaks.empty()) return fingerprints;

    // Tepe noktalarını zaman çizgisinde sıraya dizer.
    std::vector<Peak> sortedPeaks = peaks;
    std::sort(sortedPeaks.begin(), sortedPeaks.end(), [](const Peak& a, const Peak& b) {
        return a.timeIdx < b.timeIdx;
    });

    for (size_t i = 0; i < sortedPeaks.size(); ++i) {
        const Peak& anchor = sortedPeaks[i];

        // Çapa noktasının ilerisindeki "Hedef Bölge"yi (Target Zone) tara
        for (size_t j = i + 1; j < sortedPeaks.size(); ++j) {
            const Peak& target = sortedPeaks[j];
            
            int timeDelta = target.timeIdx - anchor.timeIdx;

            // Hedef bölgeye henüz ulaşımadıysa bir sonrakine geç
            if (timeDelta < targetZoneDelay) continue;
            
            // Hedef bölge sınırını aştıysa aramayı kes (Çok uzak yıldızlarla eşleşme yapılmaz)
            if (timeDelta > (targetZoneDelay + targetZoneWidth)) break;

            // ŞİFRELEME (HASHING) AŞAMASI
            // Güçlü ve eşsiz bir şifre için 3 değeri tek bir 64-bit tam sayı içinde sıkıştırılır:
            // Yapı: [Çapa Frekansı (16 bit)] | [Hedef Frekansı (16 bit)] | [Zaman Farkı (16 bit)]
            uint64_t hashValue = (static_cast<uint64_t>(anchor.freqIdx) << 32) |
                                 (static_cast<uint64_t>(target.freqIdx) << 16) |
                                 (static_cast<uint64_t>(timeDelta));

            fingerprints.push_back({hashValue, anchor.timeIdx});
        }
    }

    return fingerprints;
}