#define PY_SSIZE_T_CLEAN
#include "../audio/wavWriter.h"
#include <Python.h> // Python C API
#include "../audio/windowsAudio.h"
#include "../core/spectrogram.h"
#include "../core/fingerprint.h"
#include <thread>
#include <chrono>

// Python tarafından çağrılacak olan ana fonksiyon
static PyObject* record_and_hash(PyObject* self, PyObject* args) {
    int recordTimeMs; // Python'dan gelecek olan dinleme süresi (milisaniye)

    // Python argümanını C++ integer'ına (i) dönüştürür
    if (!PyArg_ParseTuple(args, "i", &recordTimeMs)) {
        return NULL; // Dönüşüm başarısızsa hata fırlatır
    }

    // 1. AŞAMA: Sesi Kaydet
    WindowsAudio audioRecorder;
    if (!audioRecorder.startCapture()) {
        PyErr_SetString(PyExc_RuntimeError, "Mikrofon acilamadi!");
        return NULL;
    }
    
    // İşletim sistemini yormadan istenen süre kadar bekle (Bu sırada arka planda callback ile ses birikiyor)
    std::this_thread::sleep_for(std::chrono::milliseconds(recordTimeMs));
    audioRecorder.stopCapture();
    
    std::vector<int16_t> audioData = audioRecorder.getAudioBuffer();

    // 2. AŞAMA: Spektrogram Haritasını Çıkar
    Spectrogram specGen(4096, 2048);
    auto specMatrix = specGen.compute(audioData);

    // 3. AŞAMA: Parmak İzlerini (Hash) Üret
    FingerprintManager fpManager;
    auto peaks = fpManager.extractConstellation(specMatrix);
    auto hashes = fpManager.generateHashes(peaks);

    // 4. AŞAMA: C++ Verisini Python Listesine Çevir
    // Python listesi (PyList) oluşumu ↓
    PyObject* pyList = PyList_New(hashes.size());
    
    for (size_t i = 0; i < hashes.size(); ++i) {
        // Her bir hash için 2 elemanlı bir demet (Tuple) oluşturulur: (Hash, Zaman)
        PyObject* pyTuple = PyTuple_New(2);
        
        // Şifre 64-bit olduğu için Python'a PyLong_FromUnsignedLongLong ile aktarılır
        PyTuple_SetItem(pyTuple, 0, PyLong_FromUnsignedLongLong(hashes[i].hashValue));
        PyTuple_SetItem(pyTuple, 1, PyLong_FromLong(hashes[i].anchorTime));
        
        // Demeti listeye ekle
        PyList_SetItem(pyList, i, pyTuple);
    }

    // Listeyi Python'a teslim et
    return pyList;
}

static PyObject* record_to_file(PyObject* self, PyObject* args) {
    const char* filename;
    int recordTimeMs;

    // Python'dan dosya adı (s) ve süre (i) alınır
    if (!PyArg_ParseTuple(args, "si", &filename, &recordTimeMs)) {
        return NULL;
    }

    WindowsAudio audioRecorder;
    if (!audioRecorder.startCapture()) {
        PyErr_SetString(PyExc_RuntimeError, "Mikrofon acilamadi!");
        return NULL;
    }

    std::this_thread::sleep_for(std::chrono::milliseconds(recordTimeMs));
    audioRecorder.stopCapture();

    // Sesi WAV olarak diske yaz
    if (WavWriter::writeWav(filename, audioRecorder.getAudioBuffer())) {
        Py_RETURN_TRUE; // Başarılıysa Python'a True dön
    } else {
        PyErr_SetString(PyExc_IOError, "WAV dosyasi yazilamadi!");
        return NULL;
    }
}

// Modülde bulunacak fonksiyonların tablosu
static PyMethodDef AudioEngineMethods[] = {
    // {Python'daki_adi, C++_fonksiyonu, arguman_tipi, aciklama_metni}
    {"record_and_hash", record_and_hash, METH_VARARGS, "Mikrofondan ses kaydeder ve Shazam hash listesi dondurur."},
    {"record_to_file", record_to_file, METH_VARARGS, "Sesi dosyaya kaydeder."},
    {NULL, NULL, 0, NULL} // Tablo sonu belirteci
};

// Modülün genel tanımı
static struct PyModuleDef audioenginemodule = {
    PyModuleDef_HEAD_INIT,
    "audio_engine", // Python'da 'import audio_engine' diyerek çağırılan isim
    "C++ performansli Shazam cekirdek motoru",
    -1,
    AudioEngineMethods
};

// Python modülü import ettiğinde çalışacak ilk başlatıcı fonksiyon
PyMODINIT_FUNC PyInit_audio_engine(void) {
    return PyModule_Create(&audioenginemodule);
}