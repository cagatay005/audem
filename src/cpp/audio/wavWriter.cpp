#include "wavWriter.h"
#include <fstream>
#include <iostream>

bool WavWriter::writeWav(const std::string& filename, const std::vector<int16_t>& audioData, int sampleRate) {
    // Dosyayı ikili (binary) yazma modunda açar
    std::ofstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "WAV dosyasi olusturulamadi: " << filename << std::endl;
        return false;
    }

    // WAV Formatı Sabitleri
    int numChannels = 1; // Mono (Tek kanal)
    int bitsPerSample = 16; // 16-bit ses kalitesi
    int byteRate = sampleRate * numChannels * bitsPerSample / 8;
    int blockAlign = numChannels * bitsPerSample / 8;
    int dataSize = audioData.size() * bitsPerSample / 8;
    int chunkSize = 36 + dataSize;

    // 1. RIFF Ana Başlığı
    file.write("RIFF", 4);
    file.write(reinterpret_cast<const char*>(&chunkSize), 4);
    file.write("WAVE", 4);

    // 2. "fmt " Alt Başlığı (Sesin teknik özellikleri)
    file.write("fmt ", 4);
    int subchunk1Size = 16; // PCM formatı
    short audioFormat = 1;  // 1 = Sıkıştırılmamış PCM verisi
    
    file.write(reinterpret_cast<const char*>(&subchunk1Size), 4);
    file.write(reinterpret_cast<const char*>(&audioFormat), 2);
    file.write(reinterpret_cast<const char*>(&numChannels), 2);
    file.write(reinterpret_cast<const char*>(&sampleRate), 4);
    file.write(reinterpret_cast<const char*>(&byteRate), 4);
    file.write(reinterpret_cast<const char*>(&blockAlign), 2);
    file.write(reinterpret_cast<const char*>(&bitsPerSample), 2);

    // 3. Ham Ses Verisi
    file.write("data", 4);
    file.write(reinterpret_cast<const char*>(&dataSize), 4);
    
    // tüm ses vektörünü tek seferde dosyaya basar
    file.write(reinterpret_cast<const char*>(audioData.data()), dataSize);

    file.close();
    return true;
}