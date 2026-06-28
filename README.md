# AUDEM - Hybrid Audio Recognition Engine

![C++ Core](https://img.shields.io/badge/Core-C++%20%28High%20Performance%29-blue?style=flat-square)
![Python GUI](https://img.shields.io/badge/GUI-PyQt6%20%28Glassmorphism%29-green?style=flat-square)
![Bilingual](https://img.shields.io/badge/Language-EN%20%7C%20TR-red?style=flat-square)

Audem is a modern desktop-based hybrid music recognition system powered by a high-performance C++ Digital Signal Processing (DSP) core and the Shazam Cloud API. 

It is not just a song identifier; it is an audio engineering project capable of converting sound into mathematical frequencies (hashes), storing them in its local database, learning new tracks, and operating with zero latency.

## Key Features

* **C++ DSP Core:** Audio recording and microphone listening operations are handled at the hardware level using C++. Extracted audio frequencies are converted into "fingerprints" (hashes) in seconds.
* **Cloud Network (Shazam Integration):** Ambient sounds not found locally are optimized and transmitted to Shazam servers in milliseconds. Song title, artist, and album cover are reflected on the interface in real-time.
* **Local Learning and Library:** You can teach the system new songs by letting it listen. Audem stores these songs in the `echoDatabase.db` purely as mathematical codes without consuming disk space.
* **Memory Manager:** A built-in library panel where you can list and manage the songs you have taught, along with their fingerprint counts.
* **Asynchronous Multiprocessing:** To prevent the GUI from freezing during listening, heavy C++ audio processing tasks bypass Python's Global Interpreter Lock (GIL) and are isolated to a completely different CPU core using `ProcessPoolExecutor`.
* **Bilingual Support:** Turkish (TR) and English (EN) interface that responds instantly with a single click.

## Modern "Glassmorphism" Interface (PyQt6)

Audem's interface differs from standard windows:
* **Frameless Design:** Classic Windows borders are removed to build a semi-transparent, frosted glass-effect (Glassmorphism) structure.
* **Live Animations:** Overlapping neon sine waves sensitive to sound intensity, drawn entirely with mathematical functions during the listening process.
* **Dynamic Image Processing:** Stubborn album covers (e.g., `.webp` format) fetched from the internet are parsed into pixels using `Pillow` and safely rendered on the screen via the `pyqtSignal` pipeline without freezing the interface.

## Architecture and Technologies

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Audio Recording & DSP** | `C++` | Low-level memory management and microphone capture |
| **Interface (GUI)** | `PyQt6` | GPU-accelerated desktop design with signal/slot architecture |
| **Cloud Bridge** | `Python Requests` | Bypassing anti-bot systems with custom User-Agent identity |
| **Image Processing** | `Pillow (PIL)` | Converting raw pixels to QT format (RGBA8888) |
| **Database** | `Custom HashTable` | Finding matches with lightning-fast O(1) time complexity |

## Installation and Execution

Follow these steps to compile and run the project on your local machine:

**1. Clone the Repository:**
```bash
git clone [https://github.com/YOUR_USERNAME/audem.git](https://github.com/YOUR_USERNAME/audem.git)
cd audem
```
**2. Install Required Python Libraries:**
```bash
pip install PyQt6 requests Pillow
```
**3. Launch the Application:**
```bash
python src/python/guiApp.py
```
**Note:**C++ compilation files are included in the project as .pyd. The Python bridge communicates directly with these files.

## Developer Notes 
* **API Security:** The RapidAPI key used for Shazam integration must be stored in .gitignore or as an Environment Variable for security. If you fork the code, do not forget to add your own key into Cloud.py.
* **Thread-Safety:** GUI elements (Label, Pixmap, etc.) are never manipulated directly from background threads. All data flow is routed to the main thread via Qt's pyqtSignal architecture, making it 100% thread-safe.
