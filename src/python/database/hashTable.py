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
                for songId, anchorTime in self.database[hashValue]:
                    
                    # Zaman hizalaması (Time Alignment) algoritması için aradaki farkı bulur
                    timeDifference = targetTime - anchorTime
                    
                    if songId not in matches:
                        matches[songId] = []
                    
                    matches[songId].append(timeDifference)
                    
        return matches
    
    def getAllSongsWithStats(self):
        """
        Veritabanındaki tüm şarkıları ve kaçar adet parmak izine sahip olduklarını döndürür.
        Döndürülen yapı: {'Şarkı Adı': parmakİziSayısı, ...}
        """
        songStats = {}
        
        # Veritabanındaki tüm hash kayıtlarını tarar
        for hashValue, occurrences in self.database.items():
            # Her bir hash kaydında hangi şarkıların geçtiğine bakar
            for songId, anchorTime in occurrences:
                if songId not in songStats:
                    songStats[songId] = 0
                songStats[songId] += 1
                
        return songStats
    
    def deleteSong(self, songIdToDelete):
        """
        Belirtilen şarkıyı ve ona ait tüm hash kayıtlarını veritabanından siler.
        """
        keysToRemove = []
        
        # Veritabanını tarayıp, silinecek şarkıya ait kayıtları tespit eder
        for hashValue, occurrences in self.database.items():
            # Silinecek şarkı haricindeki kayıtları tutan yeni bir liste oluşturur
            newOccurrences = [occ for occ in occurrences if occ[0] != songIdToDelete]
            
            if not newOccurrences:
                # Eğer bu hash sadece o şarkıya ait idiyse, o hash'i tamamen siler
                keysToRemove.append(hashValue)
            else:
                # Eğer bu hash başka şarkılarda da geçiyorsa, listeyi günceller
                self.database[hashValue] = newOccurrences
        
        # Tespit edilen hash'leri ana veritabanından temizler
        for key in keysToRemove:
            del self.database[key]
            
        return len(keysToRemove) 

    def getTotalHashCount(self):
        # Sistemdeki toplam kayıtlı parmak izi sayısını döndürür
        return len(self.database)