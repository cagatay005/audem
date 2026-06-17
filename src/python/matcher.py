class Matcher:
    def __init__(self, minScoreThreshold=5):
        # Bir şarkının "kesin eşleşti" sayılabilmesi için histogramda oluşması gereken minimum tepe noktası (skor).
        # Ortam gürültüsüne göre bu değeri ileride artırıp azaltabilir.
        self.minScoreThreshold = minScoreThreshold

    def findBestMatch(self, matches):
        """
        Veritabanından dönen eşleşmeleri analiz eder ve en olası şarkıyı bulur.
        matches formatı: {songId: [fark1, fark2, fark1, fark3, fark1 ...]}
        """
        bestSongId = None
        highestScore = 0

        # Her bir şarkı için zaman farkı histogramı oluşturur
        for songId, timeDifferences in matches.items():
            histogram = {}
            
            # Zaman farklarını sayarak bir oy sandığı (histogram) oluşturur
            for diff in timeDifferences:
                if diff not in histogram:
                    histogram[diff] = 0
                histogram[diff] += 1
            
            # Bu şarkı için en çok tekrar eden zaman farkını (en yüksek tepe noktasını) bulur
            if histogram:
                # Oyların en yüksek olanını alır
                currentMaxScore = max(histogram.values())
                
                # Eğer bu şarkının skoru, şu ana kadarki en iyi skordan yüksekse tahta o geçer
                if currentMaxScore > highestScore:
                    highestScore = currentMaxScore
                    bestSongId = songId

        # Eğer bulunan en yüksek skor, güvenilirlik sınırını (threshold) geçiyorsa şarkıyı döndür
        if highestScore >= self.minScoreThreshold:
            return bestSongId, highestScore
        else:
            # Sınırı geçemediyse, muhtemelen rastgele gürültüler eşleşmiştir
            return None, highestScore