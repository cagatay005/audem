import pickle
import os

class FileStorage:
    def __init__(self, dbPath="data/echoDatabase.db"):
        self.dbPath = dbPath

    def saveDatabase(self, hashTableInstance):
        """
        Bellekteki Hash Table veritabanını diske ikili (binary) formatta kaydeder.
        """
        try:
            # Dosyayı 'wb' (Write Binary) modunda açar
            with open(self.dbPath, 'wb') as file:
                # HIGHEST_PROTOCOL en iyi sıkıştırma ve okuma hızını sağlar
                pickle.dump(hashTableInstance.database, file, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"Veritabani basariyla diske kaydedildi: {self.dbPath}")
            return True
        except Exception as e:
            print(f"Hata! Veritabani kaydedilemedi: {e}")
            return False

    def loadDatabase(self, hashTableInstance):
        """
        Diskteki ikili veritabanı dosyasını okuyup RAM'deki Hash Table'a yükler.
        """
        # Dosya yoksa hiç okumaya çalışmaz (muhtemelen sistem ilk defa çalışıyordur)
        if not os.path.exists(self.dbPath):
            print("Kayitli veritabani bulunamadi. Temiz bir baslangic yapiliyor.")
            return False
            
        try:
            # Dosyayı 'rb' (Read Binary) modunda açar
            with open(self.dbPath, 'rb') as file:
                hashTableInstance.database = pickle.load(file)
            print(f"Veritabani diskten basariyla yuklendi! Toplam Hash: {hashTableInstance.getTotalHashCount()}")
            return True
        except Exception as e:
            print(f"Hata! Veritabani yuklenirken dosya okunamadi: {e}")
            return False