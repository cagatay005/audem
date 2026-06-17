class HashTable:
    def __init__(self):
        # Ana veritabanı: hashValue -> [(songId, anchorTime), (songId, anchorTime)...]
        self.database = {}

    def insertSong(self, songId, hashes):
        # C++'tan gelen (hashValue, anchorTime) listesini veritabanına ekler
        for hashValue, anchorTime in hashes:
            if hashValue not in self.database:
                self.database[hashValue] = []
            
            # Aynı hash birden fazla şarkıda veya aynı şarkının farklı saniyelerinde geçebilir
            self.database[hashValue].append((songId, anchorTime))

    def queryHashes(self, targetHashes):
        # Ortamdan dinlenip üretilen hash'leri veritabanında arar
        # Döndüreceği yapı: songId -> [zamanFarkı1, zamanFarkı2, ...]
        matches = {}
        
        for hashValue, targetTime in targetHashes:
            if hashValue in self.database:
                # Eşleşme bulundu! Hangi şarkılarda geçmiş bakalım
                for songId, anchorTime in self.database[hashValue]:
                    
                    # Zaman hizalaması (Time Alignment) algoritması için aradaki farkı bulur
                    timeDifference = targetTime - anchorTime
                    
                    if songId not in matches:
                        matches[songId] = []
                    
                    matches[songId].append(timeDifference)
                    
        return matches

    def getTotalHashCount(self):
        # Sistemdeki toplam kayıtlı parmak izi sayısını döndürür
        return len(self.database)