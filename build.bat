@echo off
echo EchoTrace C++ Motoru Derleniyor...

set PYTHON_INCLUDE="C:\Users\musta\AppData\Local\Programs\Python\Python310\include"
set PYTHON_LIBS="C:\Users\musta\AppData\Local\Programs\Python\Python310\libs"

:: Derlenecek tum C++ dosyalari
set SRC_FILES=src\cpp\audio\windowsAudio.cpp src\cpp\math\fourierTransform.cpp src\cpp\core\spectrogram.cpp src\cpp\core\fingerprint.cpp src\cpp\bridge\pythonWrapper.cpp src\cpp\audio\wavWriter.cpp

:: MSVC Derleyici (cl.exe) komutu
:: /O2 -> Maksimum hiz optimizasyonu
:: /LD -> DLL (Windows kutuphanesi) olustur
:: /MD -> Dinamik calisma zamani kutuphanelerini bagla
:: /I -> Python baslik (header) dosyalarinin yolu
echo Derleme basladi, lutfen bekleyin...
cl.exe /EHsc /O2 /LD /MD /I %PYTHON_INCLUDE% %SRC_FILES% /link /LIBPATH:%PYTHON_LIBS% /OUT:build\audio_engine.pyd
if %errorlevel% neq 0 (
    echo.
    echo DERLEME HATASI OLUSTU!
) else (
    echo.
    echo DERLEME BASARILI! Dosya 'build\audio_engine.pyd' konumuna cikarildi.
    
    :: Ortaligi temizle (Gereksiz ara dosyalari sil)
    del *.obj
    del build\audio_engine.lib
    del build\audio_engine.exp
)
pause