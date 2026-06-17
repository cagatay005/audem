import sys
import os
import time

# C++ motoru 'build' klasörünün içinde olduğu için yolu ekler
currentDir = os.path.dirname(os.path.abspath(__file__))
buildDir = os.path.abspath(os.path.join(currentDir, '..', '..', 'build'))
sys.path.append(buildDir)

import audio_engine # Saf C++ şöleni :))

from database.hashTable import HashTable
from database.fileStorage import FileStorage
from matcher import Matcher
from shazamCloud import ShazamCloud # Yeni Bulut modülü içeri aktarıldı.

def main():
    print("="*40)
    print("      ECHOTRACE SES MOTORU BAŞLATILIYOR     ")
    print("="*40)

    # Veritabanı ve geçici dosya yolları
    dataDir = os.path.abspath(os.path.join(currentDir, '..', '..', 'data'))
    dbFilePath = os.path.join(dataDir, 'echoDatabase.db')
    
    # Veri klasörü yoksa oluşturuldu
    if not os.path.exists(dataDir):
        os.makedirs(dataDir)

    # Bileşenleri ayağa kaldırıldı
    db = HashTable()
    storage = FileStorage(dbPath=dbFilePath)
    matcher = Matcher(minScoreThreshold=10)
    cloudAPI = ShazamCloud() # Bulut motoru başlatıldı

    # Çevrimdışı kayıtları belleğe yükle
    storage.loadDatabase(db)

    while True:
        print("\n--- MENÜ ---")
        print("[1] Yeni Şarkı Öğret (Yerel Veritabanına Ekle)")
        print("[2] Dinle ve Şarkıyı Bul (Yerel Arama)")
        print("[3] İnternette Ara (BULUT MODU - Global Shazam)")
        print("[4] Çıkış")
        
        choice = input("Seçiminiz: ")

        if choice == '1':
            songName = input("Şarkının Adı (Örn: Sezen Aksu - Gülümse): ")
            try:
                recordTimeSec = int(input("Kaç saniye dinleyerek kaydedelim? (Örn: 10): "))
            except ValueError:
                print("Lütfen geçerli bir saniye girin!")
                continue

            print(f"\nLütfen '{songName}' şarkısını açın. Motor çalışıyor...")
            try:
                hashes = audio_engine.record_and_hash(recordTimeSec * 1000)
                if hashes:
                    db.insertSong(songName, hashes)
                    storage.saveDatabase(db)
                    print(f"Başarılı! '{songName}', {len(hashes)} adet parmak iziyle sisteme kazındı.")
                else:
                    print("Sessizlik veya sadece arka plan gürültüsü algılandı.")
            except Exception as e:
                print(f"C++ Motor Hatası: {e}")

        elif choice == '2':
            try:
                recordTimeSec = int(input("Kaç saniye dinleyelim? (Örn: 5): "))
            except ValueError:
                print("Lütfen geçerli bir saniye girin!")
                continue

            print("\nYerel veritabanı için dinleniyor... Lütfen bekleyin.")
            try:
                hashes = audio_engine.record_and_hash(recordTimeSec * 1000)
                if not hashes:
                    print("Yeterli ses frekansı alınamadı.")
                    continue
                    
                matches = db.queryHashes(hashes)
                bestMatch, score = matcher.findBestMatch(matches)
                
                print("-"*30)
                if bestMatch:
                    print(f"🎵 YEREL EŞLEŞME BULUNDU! 🎵")
                    print(f"-> Şarkı: {bestMatch}")
                    print(f"-> Güven Skoru: {score} tepe noktası hizalandı.")
                else:
                    print(f"❌ Yerel veritabanında eşleşme bulunamadı.")
                print("-"*30)
            except Exception as e:
                print(f"C++ Motor Hatası: {e}")

        elif choice == '3':
            recordTimeSec = 5 
            
            print(f"\n☁️ Bulut Modu devrede. Ortam {recordTimeSec} saniye boyunca dinleniyor...")
            temp_wav_path = os.path.join(dataDir, "temp_cloud.wav")
            
            try:
                success = audio_engine.record_to_file(temp_wav_path, recordTimeSec * 1000)
                
                if success:
                    result = cloudAPI.identifySong(temp_wav_path)
                    
                    print("-" * 30)
                    if "success" in result and result["success"]:
                        print(f"🎵 BULUT EŞLEŞMESİ BULUNDU! 🎵")
                        print(f"-> Şarkı: {result['title']}")
                        print(f"-> Sanatçı: {result['artist']}")
                    elif "error" in result:
                        print(f"❌ BULUT HATASI: {result['error']}")
                    else:
                        print(f"❌ Şarkı Shazam global veritabanında bulunamadı.")
                    print("-" * 30)
                    
                    if os.path.exists(temp_wav_path):
                        os.remove(temp_wav_path)
                else:
                    print("Ses dosyası C++ motoru tarafından oluşturulamadı.")
            except Exception as e:
                print(f"Bulut Modu Kritik Hatası: {e}")

        elif choice == '4':
            print("EchoTrace kapatılıyor. Müziğin izini sürmeye devam edin!")
            break
        else:
            print("Geçersiz bir tuşa bastınız.")

if __name__ == '__main__':
    main()