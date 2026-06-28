import sys
import os
import threading
import requests
import math
from concurrent.futures import ProcessPoolExecutor

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QGraphicsDropShadowEffect,
                             QDialog, QListWidget, QListWidgetItem, QMessageBox, QInputDialog)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QPoint
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap, QFont

currentDir = os.path.dirname(os.path.abspath(__file__))
buildDir = os.path.abspath(os.path.join(currentDir, '..', '..', 'build'))
dataDir = os.path.abspath(os.path.join(currentDir, '..', '..', 'data'))
sys.path.append(buildDir)

from database.hashTable import HashTable
from database.fileStorage import FileStorage
from matcher import Matcher
from Cloud import Cloud

# --- C++ MOTORUNU İZOLE ETME FONKSİYONLARI ---
# Bu fonksiyonlar ana programdan bağımsız çalışarak arayüzün donmasını engeller
def engine_record_to_file(path, duration_ms):
    import audio_engine
    return audio_engine.record_to_file(path, duration_ms)

def engine_record_and_hash(duration_ms):
    import audio_engine
    return audio_engine.record_and_hash(duration_ms)

# --- THREAD İLETİŞİM SİNYALLERİ ---
class WorkerSignals(QObject):
    finished = pyqtSignal(bool, str, str, str)
    cover_ready = pyqtSignal(QPixmap)

# --- SİNÜS DALGASI ANİMASYON WIDGET'I ---
class SineWaveWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.phase = 0.0
        self.is_animating = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wave)

    def start_animation(self):
        self.is_animating = True
        self.timer.start(30) 

    def stop_animation(self):
        self.is_animating = False
        self.timer.stop()
        self.update()

    def update_wave(self):
        self.phase += 0.3
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width, height = self.width(), self.height()
        mid_y = height / 2

        if not self.is_animating:
            painter.setPen(QPen(QColor(100, 100, 100, 150), 2))
            painter.drawLine(0, int(mid_y), width, int(mid_y))
            return

        colors = [QColor(0, 168, 255, 180), QColor(156, 136, 255, 180), QColor(76, 209, 55, 180)]
        amplitudes = [25, 15, 35]
        frequencies = [0.05, 0.08, 0.03]

        for i in range(3):
            path_points = []
            painter.setPen(QPen(colors[i], 3))
            for x in range(width):
                y = mid_y + math.sin(x * frequencies[i] + self.phase + i) * amplitudes[i]
                damping = math.sin((x / width) * math.pi) 
                y = mid_y + (y - mid_y) * damping
                
                if x == 0:
                    path_points.append(QPoint(x, int(y)))
                else:
                    painter.drawLine(path_points[-1], QPoint(x, int(y)))
                    path_points.append(QPoint(x, int(y)))

# --- KÜTÜPHANE YÖNETİM PANELİ ---
class LibraryDialog(QDialog):
    def __init__(self, parent, db, storage, lang="TR"):
        super().__init__(parent)
        self.db = db
        self.storage = storage
        self.lang = lang # Ana menüden gelen aktif dili kaydeder
        
        title_text = "Audem Local Library" if self.lang == "EN" else "Audem Yerel Kütüphane"
        self.setWindowTitle(title_text)
        self.setFixedSize(400, 500)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; color: white; }
            QListWidget { background-color: #2d2d2d; border: none; border-radius: 10px; padding: 10px; font-size: 14px; }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #3d3d3d; }
            QListWidget::item:selected { background-color: #00a8ff; border-radius: 5px; }
            QPushButton { background-color: #e74c3c; color: white; border-radius: 8px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #c0392b; }
            QPushButton:pressed { background-color: #922b21; padding-top: 2px; }
        """)

        layout = QVBoxLayout(self)
        
        header_text = "Taught Songs" if self.lang == "EN" else "Öğretilen Şarkılar"
        title = QLabel(header_text)
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        self.list_widget = QListWidget()
        self.list_widget.setWordWrap(True) # Uzun şarkı isimlerinin sağdan kesilmesini önler
        layout.addWidget(self.list_widget)

        btn_del_text = "Delete Selected Song" if self.lang == "EN" else "Seçili Şarkıyı Sil"
        self.btn_delete = QPushButton(btn_del_text)
        self.btn_delete.clicked.connect(self.delete_selected)
        layout.addWidget(self.btn_delete)

        btn_close_text = "Close" if self.lang == "EN" else "Kapat"
        self.btn_close = QPushButton(btn_close_text)
        self.btn_close.setStyleSheet("QPushButton { background-color: #555; } QPushButton:hover { background-color: #777; } QPushButton:pressed { background-color: #333; padding-top: 2px; }")
        self.btn_close.clicked.connect(self.close)
        layout.addWidget(self.btn_close)

        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        stats = self.db.getAllSongsWithStats()
        if not stats:
            empty_text = "Library is currently empty." if self.lang == "EN" else "Kütüphane şu an boş."
            self.list_widget.addItem(empty_text)
            self.btn_delete.setEnabled(False)
            return
            
        self.btn_delete.setEnabled(True)
        for song, count in stats.items():
            fp_text = "fingerprints" if self.lang == "EN" else "parmak izi"
            item = QListWidgetItem(f"🎵 {song} ({count} {fp_text})")
            item.setData(Qt.ItemDataRole.UserRole, song)
            self.list_widget.addItem(item)

    def delete_selected(self):
        selected = self.list_widget.currentItem()
        if not selected or not selected.data(Qt.ItemDataRole.UserRole): return
        song_id = selected.data(Qt.ItemDataRole.UserRole)
        
        confirm_title = 'Confirm' if self.lang == "EN" else 'Onay'
        confirm_msg = f"'{song_id}' will be deleted. Are you sure?" if self.lang == "EN" else f"'{song_id}' silinecek. Emin misiniz?"
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(confirm_title)
        msg_box.setText(confirm_msg)
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        if self.lang == "EN":
            yes_btn = msg_box.addButton("Yes", QMessageBox.ButtonRole.YesRole)
            no_btn = msg_box.addButton("No", QMessageBox.ButtonRole.NoRole)
        else:
            yes_btn = msg_box.addButton("Evet", QMessageBox.ButtonRole.YesRole)
            no_btn = msg_box.addButton("Hayır", QMessageBox.ButtonRole.NoRole)
            
        msg_box.exec()
        
        if msg_box.clickedButton() == yes_btn:
            self.db.deleteSong(song_id)
            self.storage.saveDatabase(self.db)
            self.refresh_list()

# --- ANA UYGULAMA ---
class AudemGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # C++ Motorunu hapsetmek için ayrı işlemci havuzu oluşturuldu
        self.executor = ProcessPoolExecutor(max_workers=1)

        self.dbFilePath = os.path.join(dataDir, 'echoDatabase.db')
        if not os.path.exists(dataDir): os.makedirs(dataDir)
        self.db = HashTable()
        self.storage = FileStorage(dbPath=self.dbFilePath)
        self.matcher = Matcher(minScoreThreshold=10)
        self.cloudAPI = Cloud()
        self.storage.loadDatabase(self.db)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(450, 720) 

        self.oldPos = self.pos()
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("""
            QWidget#MainContainer { background-color: rgba(25, 25, 30, 230); border-radius: 25px; border: 1px solid rgba(255, 255, 255, 30); }
            QLabel { color: white; font-family: 'Segoe UI', Arial; }
        """)
        self.central_widget.setObjectName("MainContainer")
        
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # --- ÜST BAR VE BUTONLAR ---
        top_bar = QHBoxLayout()
        
        self.btn_lib = QPushButton("Kütüphane")
        self.btn_lib.setFixedSize(120, 35)
        self.btn_lib.setStyleSheet("""
            QPushButton { background-color: rgba(255, 255, 255, 20); border-radius: 17px; color: white; font-weight: bold; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 40); }
            QPushButton:pressed { background-color: rgba(255, 255, 255, 10); padding-top: 2px; }
        """)
        self.btn_lib.clicked.connect(self.open_library)

        self.current_lang = "TR" # Varsayılan dil
        self.btn_lang = QPushButton("TR")
        self.btn_lang.setFixedSize(50, 35)
        self.btn_lang.setStyleSheet("""
            QPushButton { background-color: rgba(255, 255, 255, 20); border-radius: 17px; color: white; font-weight: bold; font-size: 13px;}
            QPushButton:hover { background-color: rgba(255, 255, 255, 60); }
            QPushButton:pressed { background-color: rgba(255, 255, 255, 10); padding-top: 2px; }
        """)
        self.btn_lang.clicked.connect(self.toggle_language)

        self.btn_min = QPushButton("—")
        self.btn_min.setFixedSize(35, 35)
        self.btn_min.setStyleSheet("""
            QPushButton { background-color: rgba(255, 255, 255, 20); border-radius: 17px; color: white; font-weight: bold; font-size: 14px;}
            QPushButton:hover { background-color: rgba(255, 255, 255, 60); }
            QPushButton:pressed { background-color: rgba(255, 255, 255, 10); padding-top: 2px; }
        """)
        self.btn_min.clicked.connect(self.showMinimized) 
        
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(35, 35)
        self.btn_close.setStyleSheet("""
            QPushButton { background-color: rgba(231, 76, 60, 180); border-radius: 17px; color: white; font-weight: bold; font-size: 16px;}
            QPushButton:hover { background-color: rgba(231, 76, 60, 255); }
            QPushButton:pressed { background-color: rgba(192, 57, 43, 255); padding-top: 2px; }
        """)
        self.btn_close.clicked.connect(self.close)

        top_bar.addWidget(self.btn_lib)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_lang) 
        top_bar.addWidget(self.btn_min)
        top_bar.addWidget(self.btn_close)
        main_layout.addLayout(top_bar)

        self.title_label = QLabel("AUDEM")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 32px; font-weight: 900; letter-spacing: 5px;")
        main_layout.addWidget(self.title_label)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(250, 250)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setStyleSheet("background-color: rgba(0,0,0,100); border-radius: 20px;")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 10)
        self.cover_label.setGraphicsEffect(shadow)
        
        cover_layout = QHBoxLayout()
        cover_layout.addWidget(self.cover_label)
        main_layout.addLayout(cover_layout)

        self.song_label = QLabel("Müzik Keşfetmeye Hazır")
        self.song_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.song_label.setWordWrap(True)
        self.song_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(self.song_label)

        self.artist_label = QLabel("Ortamı dinlemek için bir mod seçin")
        self.artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.artist_label.setWordWrap(True)
        self.artist_label.setStyleSheet("font-size: 14px; color: #aaaaaa;")
        main_layout.addWidget(self.artist_label)

        self.wave_anim = SineWaveWidget()
        main_layout.addWidget(self.wave_anim)

        self.btn_cloud = QPushButton("Bulut Ağı")
        self.btn_cloud.setFixedHeight(50)
        self.btn_cloud.setStyleSheet("""
            QPushButton { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #005c97, stop:1 #363795); border-radius: 25px; color: white; font-weight: bold; font-size: 15px;}
            QPushButton:hover { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #006eb5, stop:1 #4748b8); }
            QPushButton:pressed { background-color: #002d4f; padding-top: 3px; } 
        """)
        self.btn_cloud.clicked.connect(self.run_cloud_search)
        main_layout.addWidget(self.btn_cloud)

        self.btn_local = QPushButton("Yerel Cihazda Ara")
        self.btn_local.setFixedHeight(45)
        self.btn_local.setStyleSheet("""
            QPushButton { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #11998e, stop:1 #38ef7d); border-radius: 22px; color: white; font-weight: bold; font-size: 14px;}
            QPushButton:hover { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #14b5a8, stop:1 #4efca6); }
            QPushButton:pressed { background-color: #0c6961; padding-top: 3px; }
        """)
        self.btn_local.clicked.connect(self.run_local_search)
        main_layout.addWidget(self.btn_local)

        self.btn_teach = QPushButton("Sisteme Şarkı Öğret")
        self.btn_teach.setFixedHeight(40)
        self.btn_teach.setStyleSheet("""
            QPushButton { background-color: rgba(255, 255, 255, 10); border: 1px solid rgba(255,255,255,50); border-radius: 20px; color: #cccccc; font-weight: bold;}
            QPushButton:hover { background-color: rgba(255, 255, 255, 30); color: white;}
            QPushButton:pressed { background-color: rgba(0, 0, 0, 50); padding-top: 3px; }
        """)
        self.btn_teach.clicked.connect(self.run_teach)
        main_layout.addWidget(self.btn_teach)

        self.signals = WorkerSignals()
        self.signals.finished.connect(self.on_process_finished)
        self.signals.cover_ready.connect(self.cover_label.setPixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton: self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = QPoint(event.globalPosition().toPoint() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPosition().toPoint()

    def open_library(self):
        dialog = LibraryDialog(self, self.db, self.storage, self.current_lang)
        dialog.exec()

    def toggle_language(self):
        if self.current_lang == "TR":
            # İngilizceye Geçiş
            self.current_lang = "EN"
            self.btn_lang.setText("EN")
            self.btn_lib.setText("Library")
            self.btn_cloud.setText("Cloud Network")
            self.btn_local.setText("Search Local Device")
            self.btn_teach.setText("Teach Song to System")
            if self.song_label.text() == "Müzik Keşfetmeye Hazır":
                self.song_label.setText("Ready to Discover Music")
            if self.artist_label.text() == "Ortamı dinlemek için bir mod seçin":
                self.artist_label.setText("Select a mode to listen to the environment")
        else:
            # Türkçeye Geçiş
            self.current_lang = "TR"
            self.btn_lang.setText("TR")
            self.btn_lib.setText("Kütüphane")
            self.btn_cloud.setText("Bulut Ağı")
            self.btn_local.setText("Yerel Cihazda Ara")
            self.btn_teach.setText("Sisteme Şarkı Öğret")
            if self.song_label.text() == "Ready to Discover Music":
                self.song_label.setText("Müzik Keşfetmeye Hazır")
            if self.artist_label.text() == "Select a mode to listen to the environment":
                self.artist_label.setText("Ortamı dinlemek için bir mod seçin")

    def set_ui_state(self, is_listening, main_text, sub_text):
        self.btn_cloud.setEnabled(not is_listening)
        self.btn_local.setEnabled(not is_listening)
        self.btn_teach.setEnabled(not is_listening)
        self.song_label.setText(main_text)
        self.song_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #f1c40f;")
        self.artist_label.setText(sub_text)
        self.cover_label.clear()
        
        if is_listening:
            self.wave_anim.start_animation()
        else:
            self.wave_anim.stop_animation()

    def on_process_finished(self, success, title, artist, cover_url):
        self.set_ui_state(False, title, artist)
        color = "#2ecc71" if success else "#e74c3c"
        self.song_label.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {color};")
        if cover_url: threading.Thread(target=self.download_cover, args=(cover_url,)).start()

    def download_cover(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'}
            response = requests.get(url, timeout=10, headers=headers)
            
            if response.status_code == 200:
                from PIL import Image
                from io import BytesIO
                from PyQt6.QtGui import QImage
                
                # Webp yüzünden resimler pillow ile piksellerine ayrıldı
                img = Image.open(BytesIO(response.content))
                img = img.convert("RGBA") # Tüm formatları standart RGBA'ya çevirir
                img = img.resize((250, 250), Image.Resampling.LANCZOS)
                
                # Pikselleri Qt formatına çevirir
                data = img.tobytes("raw", "RGBA")
                qim = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qim)
                
                self.signals.cover_ready.emit(pixmap)
            else:
                print(f"Resim Sunucusu Reddetti: {response.status_code}")
        except Exception as e:
            print(f"Resim İndirme Çöktü: {e}")

    def run_cloud_search(self):
        title = "Listening..." if self.current_lang == "EN" else "Ortam Dinleniyor..."
        desc = "Connecting to Audem Cloud" if self.current_lang == "EN" else "Audem Bulut ağına bağlanılıyor"
        self.set_ui_state(True, title, desc)
        threading.Thread(target=self._cloud_task).start()

    def _cloud_task(self):
        temp_wav = os.path.join(dataDir, "temp_cloud.wav")
        try:
            future = self.executor.submit(engine_record_to_file, temp_wav, 5000)
            if future.result(): 
                res = self.cloudAPI.identifySong(temp_wav)
                if res.get("success"):
                    self.signals.finished.emit(True, res['title'], res['artist'], res.get('cover', ''))
                elif res.get("error"):
                    title = "Cloud Error" if self.current_lang == "EN" else "Bulut Hatası"
                    self.signals.finished.emit(False, title, res['error'], "")
                else:
                    title = "Not Found" if self.current_lang == "EN" else "Bulunamadı"
                    desc = "Song not found in Audem global network." if self.current_lang == "EN" else "Şarkı Audem küresel ağında yok."
                    self.signals.finished.emit(False, title, desc, "")
            else:
                title = "Recording Error" if self.current_lang == "EN" else "Kayıt Hatası"
                desc = "Microphone could not be read." if self.current_lang == "EN" else "Mikrofon okunamadı."
                self.signals.finished.emit(False, title, desc, "")
        except Exception as e:
            title = "Error" if self.current_lang == "EN" else "Hata"
            self.signals.finished.emit(False, title, str(e), "")

    def run_local_search(self):
        title = "Listening..." if self.current_lang == "EN" else "Ortam Dinleniyor..."
        desc = "Scanning local archive" if self.current_lang == "EN" else "Yerel arşivde taranıyor"
        self.set_ui_state(True, title, desc)
        threading.Thread(target=self._local_task).start()

    def _local_task(self):
        try:
            future = self.executor.submit(engine_record_and_hash, 5000)
            hashes = future.result()
            if not hashes:
                title = "No Audio Detected" if self.current_lang == "EN" else "Ses Alınamadı"
                desc = "Please try again." if self.current_lang == "EN" else "Lütfen tekrar deneyin."
                self.signals.finished.emit(False, title, desc, "")
                return
            
            bestMatch, score = self.matcher.findBestMatch(self.db.queryHashes(hashes))
            if bestMatch:
                desc = f"Confidence Score: {score}" if self.current_lang == "EN" else f"Güven Skoru: {score}"
                self.signals.finished.emit(True, bestMatch, desc, "")
            else:
                title = "Not Found" if self.current_lang == "EN" else "Bulunamadı"
                desc = "This song is not in the local database." if self.current_lang == "EN" else "Bu şarkı yerel veritabanında yok."
                self.signals.finished.emit(False, title, desc, "")
        except Exception as e:
            title = "Error" if self.current_lang == "EN" else "Hata"
            self.signals.finished.emit(False, title, str(e), "")

    def run_teach(self):
        prompt_title = "New Song" if self.current_lang == "EN" else "Yeni Şarkı"
        prompt_desc = "Enter Song Name:" if self.current_lang == "EN" else "Şarkının Adını Girin:"
        song_name, ok = QInputDialog.getText(self, prompt_title, prompt_desc)
        
        if ok and song_name:
            title = "Learning..." if self.current_lang == "EN" else "Öğreniliyor..."
            desc = f"'{song_name}' is being recorded (10 sec)" if self.current_lang == "EN" else f"'{song_name}' kaydediliyor (10 sn)"
            self.set_ui_state(True, title, desc)
            threading.Thread(target=self._teach_task, args=(song_name,)).start()

    def _teach_task(self, song_name):
        try:
            future = self.executor.submit(engine_record_and_hash, 10000)
            hashes = future.result()
            if hashes:
                self.db.insertSong(song_name, hashes)
                self.storage.saveDatabase(self.db)
                
                title = "Saved to System!" if self.current_lang == "EN" else "Sisteme Kazındı!"
                desc = f"{len(hashes)} frequency points added." if self.current_lang == "EN" else f"{len(hashes)} adet frekans noktası eklendi."
                self.signals.finished.emit(True, title, desc, "")
            else:
                title = "Silence Detected" if self.current_lang == "EN" else "Sessizlik Algılandı"
                desc = "Please move closer to the source." if self.current_lang == "EN" else "Lütfen daha yakından dinletin."
                self.signals.finished.emit(False, title, desc, "")
        except Exception as e:
            title = "Error" if self.current_lang == "EN" else "Hata"
            self.signals.finished.emit(False, title, str(e), "")

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    window = AudemGUI()
    window.show()
    sys.exit(app.exec())