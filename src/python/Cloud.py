import requests
import os
import base64
import wave
import audioop

class ShazamCloud:
    def __init__(self, apiKey="BURAYA_KENDI_RAPIDAPI_ANAHTARINIZI_YAZIN"):
        self.apiKey = apiKey
        self.url = "https://shazam.p.rapidapi.com/songs/v2/detect"
        
        self.headers = {
            "content-type": "text/plain",
            "X-RapidAPI-Key": self.apiKey,
            "X-RapidAPI-Host": "shazam.p.rapidapi.com"
        }

    def identifySong(self, audioFilePath):
        if not os.path.exists(audioFilePath):
            return {"error": "Ses dosyası bulunamadı."}

        try:
            # 1. Standart wave kütüphanesi ile dosyayı ve özelliklerini okur
            with wave.open(audioFilePath, "rb") as wf:
                framerate = wf.getframerate()
                nchannels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                
                # Sadece ham sesi okur (44 Baytlık Kimlik kartı otomatik olarak ayrılır)
                rawData = wf.readframes(wf.getnframes())

            # 2. FREKANS DÖNÜŞÜMÜ (Resampling)
            # Eğer ses 44100 Hz değilse (ki C++ motorumuz 8000 Hz üretiyor), Shazam için dönüştürüldü.
            if framerate != 44100:
                print(f"🎵 Frekans Uyuşmazlığı Çözülüyor: {framerate} Hz -> 44100 Hz")
                # audioop modülü ile kaliteyi bozmadan sesi sündürerek 44100'e yayar
                rawData, _ = audioop.ratecv(rawData, sampwidth, nchannels, framerate, 44100, None)

            # 3. Sesi Base64 formatına çevirir
            base64Audio = base64.b64encode(rawData).decode('utf-8')

            print(f"☁️ Buluta bağlanılıyor... (Gönderilen Veri: {len(base64Audio) // 1024} KB)")
            
            response = requests.post(self.url, data=base64Audio, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'track' in result and result['track']:
                    songName = result['track']['title']
                    artist = result['track']['subtitle']
                    return {"success": True, "title": songName, "artist": artist}
                else:
                    return {"success": False, "message": "Şarkı bulunamadı. (Farklı bir kısmını dinletmeyi deneyin)"}
            else:
                return {"error": f"API Hatası: {response.status_code} - Lütfen API anahtarınızı kontrol edin."}

        except Exception as e:
            return {"error": str(e)}
