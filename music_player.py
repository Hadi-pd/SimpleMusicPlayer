# music_player.py - Simple Music Player (نسخه نهایی با ذخیره تنظیمات)
import os
import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pygame
import mutagen
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.wave import WAVE
from mutagen.id3 import ID3
from mutagen.easyid3 import EasyID3

class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # مسیر فایل تنظیمات
        self.settings_file = self.get_settings_path("player_settings.json")
        self.settings = self.load_settings()
        
        # مسیر امن برای آیکون
        icon_path = self.get_resource_path("icon.ico")
        self.icon = QIcon(icon_path)
        self.setWindowIcon(self.icon)
        
        # اول custom_music_folder را تعریف کنیم
        self.custom_music_folder = self.settings.get("last_folder", "")
        
        self.init_ui()
        self.init_pygame()
        self.music_files = []
        self.current_index = -1
        self.is_playing = False
        self.is_paused = False
        self.volume = 0.7
        self.song_durations = {}
        self.current_position = 0
        self.total_duration = 0
        self.seeking = False
        
        # بارگذاری موسیقی
        self.load_music_files()
        
        # بازیابی آخرین ترانه
        last_song = self.settings.get("last_song", "")
        if last_song and os.path.exists(last_song) and last_song in self.music_files:
            self.current_index = self.music_files.index(last_song)
            last_position = self.settings.get("last_position", 0)
            self.current_position = last_position
    
    def get_settings_path(self, filename):
        """مسیر فایل تنظیمات در پوشه کاربر"""
        app_data = Path.home() / ".simplemusicplayer"
        app_data.mkdir(exist_ok=True)
        return str(app_data / filename)
    
    def load_settings(self):
        """بارگذاری تنظیمات از فایل"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save_settings(self):
        """ذخیره تنظیمات در فایل"""
        try:
            settings = {
                "last_folder": self.custom_music_folder,
                "last_song": self.music_files[self.current_index] if 0 <= self.current_index < len(self.music_files) else "",
                "last_position": self.current_position if self.is_playing else 0,
                "volume": int(self.volume * 100)  # ذخیره به صورت عدد صحیح
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"خطا در ذخیره تنظیمات: {e}")
        
    def get_resource_path(self, relative_path):
        """برای پشتیبانی از PyInstaller (exe) و اجرای عادی"""
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        else:
            return os.path.join(os.path.abspath("."), relative_path)
        
    def init_ui(self):
        self.setWindowTitle("Simple Music Player")
        self.setGeometry(300, 100, 900, 700)
        self.setMinimumSize(800, 600)
        
        # تم تیره مدرن
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f0f0f, stop:1 #1a1a1a);
                color: #ffffff;
            }
            QLabel {
                color: #e0e0e0;
                font-family: 'Segoe UI', sans-serif;
            }
            QListWidget {
                background-color: rgba(30, 30, 30, 180);
                border: none;
                border-radius: 12px;
                padding: 8px;
                font-size: 14px;
                color: #d0d0d0;
            }
            QListWidget::item {
                padding: 12px 10px;
                border-bottom: 1px solid rgba(80, 80, 80, 0.3);
                border-radius: 8px;
                margin: 2px 4px;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                font-weight: bold;
            }
            QListWidget::item:hover {
                background-color: rgba(100, 100, 150, 0.3);
                border-radius: 8px;
            }
            QPushButton {
                background-color: transparent;
                border: 2px solid transparent;
                border-radius: 25px;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 12px;
                min-width: 50px;
                min-height: 50px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
            #playButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                font-size: 20px;
                min-width: 70px;
                min-height: 70px;
                border-radius: 35px;
            }
            #playButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #764ba2, stop:1 #667eea);
            }
            #folderButton {
                background: rgba(100, 150, 255, 0.2);
                font-size: 14px;
                padding: 8px 16px;
            }
            #folderButton:hover {
                background: rgba(100, 150, 255, 0.4);
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: rgba(80, 80, 80, 0.6);
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: white;
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
                border: 3px solid #667eea;
            }
            QSlider::handle:horizontal:hover {
                width: 22px;
                height: 22px;
                margin: -7px 0;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # هدر با دکمه انتخاب پوشه
        header_layout = QHBoxLayout()
        self.folder_label = QLabel("پوشه موسیقی:")
        self.folder_label.setStyleSheet("font-size: 14px; color: #a0a0a0;")
        header_layout.addWidget(self.folder_label)
        
        self.folder_path_label = QLabel("")
        self.folder_path_label.setStyleSheet("""
            font-size: 13px;
            color: #66ccff;
            padding: 6px 12px;
            background: rgba(50, 50, 70, 0.3);
            border-radius: 8px;
            border: 1px solid rgba(100, 150, 255, 0.2);
        """)
        self.folder_path_label.setWordWrap(True)
        header_layout.addWidget(self.folder_path_label, 1)
        
        self.folder_btn = QPushButton("📁 انتخاب پوشه")
        self.folder_btn.setObjectName("folderButton")
        self.folder_btn.setToolTip("انتخاب پوشه حاوی فایل‌های موسیقی")
        self.folder_btn.clicked.connect(self.select_music_folder)
        header_layout.addWidget(self.folder_btn)
        
        layout.addLayout(header_layout)
        
        # بخش بالایی: کاور + اطلاعات آهنگ
        top_frame = QFrame()
        top_frame.setStyleSheet("background-color: rgba(30, 30, 30, 0.6); border-radius: 16px; padding: 20px;")
        top_layout = QHBoxLayout(top_frame)
        
        self.album_art = QLabel()
        self.album_art.setFixedSize(200, 200)
        self.album_art.setStyleSheet("border-radius: 16px; background-color: #2a2a2a; border: 3px solid #444;")
        self.album_art.setAlignment(Qt.AlignCenter)
        self.album_art.setText("🎵")
        self.album_art.setFont(QFont("Segoe UI", 60))
        top_layout.addWidget(self.album_art)
        
        info_layout = QVBoxLayout()
        info_layout.addStretch()
        
        self.song_title = QLabel("Simple Music Player")
        self.song_title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.song_title.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.song_title)
        
        self.artist_label = QLabel("برای شروع، یک پوشه انتخاب کنید")
        self.artist_label.setFont(QFont("Segoe UI", 16))
        self.artist_label.setStyleSheet("color: #b0b0b0;")
        self.artist_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.artist_label)
        
        info_layout.addStretch()
        top_layout.addLayout(info_layout)
        layout.addWidget(top_frame, 1)
        
        # کنترل‌های پخش
        controls_layout = QHBoxLayout()
        controls_layout.addStretch()
        
        self.prev_btn = QPushButton("⏮")
        self.prev_btn.clicked.connect(self.prev_song)
        controls_layout.addWidget(self.prev_btn)
        
        self.play_btn = QPushButton("▶")
        self.play_btn.setObjectName("playButton")
        self.play_btn.clicked.connect(self.play_pause)
        controls_layout.addWidget(self.play_btn)
        
        self.next_btn = QPushButton("⏭")
        self.next_btn.clicked.connect(self.next_song)
        controls_layout.addWidget(self.next_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # نوار پیشرفت
        progress_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setFont(QFont("Segoe UI", 12))
        progress_layout.addWidget(self.current_time_label)
        
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.sliderPressed.connect(self.start_seeking)
        self.progress_slider.sliderReleased.connect(self.end_seeking)
        self.progress_slider.sliderMoved.connect(self.update_seek_position)
        progress_layout.addWidget(self.progress_slider, 1)
        
        self.total_time_label = QLabel("00:00")
        self.total_time_label.setFont(QFont("Segoe UI", 12))
        progress_layout.addWidget(self.total_time_label)
        layout.addLayout(progress_layout)
        
        # کنترل صدا و وضعیت
        bottom_layout = QHBoxLayout()
        volume_group = QHBoxLayout()
        volume_group.addWidget(QLabel("🔊"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(150)
        self.volume_slider.valueChanged.connect(self.change_volume)
        volume_group.addWidget(self.volume_slider)
        self.volume_label = QLabel("70%")
        volume_group.addWidget(self.volume_label)
        bottom_layout.addLayout(volume_group)
        
        bottom_layout.addStretch()
        self.status_label = QLabel("آماده")
        self.status_label.setStyleSheet("color: #66ff99; font-style: italic;")
        bottom_layout.addWidget(self.status_label)
        layout.addLayout(bottom_layout)
        
        # لیست پخش
        self.song_list = QListWidget()
        self.song_list.itemDoubleClicked.connect(self.play_selected_song)
        layout.addWidget(self.song_list, 2)
        
        # بازیابی حجم از تنظیمات - تبدیل به int
        saved_volume = self.settings.get("volume", 70)
        if isinstance(saved_volume, float):
            saved_volume = int(saved_volume)
        self.volume_slider.setValue(saved_volume)
        self.change_volume(saved_volume)
        
        # تایمرها
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(100)
        
        self.end_check_timer = QTimer()
        self.end_check_timer.timeout.connect(self.check_song_end)
        self.end_check_timer.start(500)
        
        # تایمر برای ذخیره خودکار تنظیمات
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_settings)
        self.save_timer.start(30000)  # هر 30 ثانیه ذخیره شود
        
        # به‌روزرسانی نمایش مسیر پوشه (بعد از تنظیم همه چیز)
        QTimer.singleShot(100, self.update_folder_display)

    def init_pygame(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)

    def get_music_folder(self):
        """دریافت پوشه موسیقی (پیش‌فرض یا انتخاب شده)"""
        if self.custom_music_folder and os.path.exists(self.custom_music_folder):
            return self.custom_music_folder
        else:
            # پوشه پیش‌فرض ویندوز 11/10
            music_folder = Path.home() / "Music"
            if not music_folder.exists():
                music_folder = Path(os.getenv('USERPROFILE') or Path.home()) / "Music"
                music_folder.mkdir(parents=True, exist_ok=True)
            return str(music_folder)

    def update_folder_display(self):
        """به‌روزرسانی نمایش مسیر پوشه"""
        folder = self.get_music_folder()
        # نمایش مسیر کوتاه شده اگر خیلی طولانی باشد
        if len(folder) > 50:
            display_path = "..." + folder[-47:]
        else:
            display_path = folder
        self.folder_path_label.setText(display_path)
        self.folder_path_label.setToolTip(folder)

    def select_music_folder(self):
        """انتخاب پوشه موسیقی جدید"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "انتخاب پوشه موسیقی",
            self.get_music_folder(),
            QFileDialog.ShowDirsOnly
        )
        
        if folder:
            self.custom_music_folder = folder
            self.update_folder_display()
            if self.load_music_files():
                self.save_settings()
                
                # نمایش پیام موفقیت
                self.status_label.setText(f"پوشه جدید بارگذاری شد: {os.path.basename(folder)}")
                QTimer.singleShot(3000, lambda: self.status_label.setText("آماده"))

    def extract_album_art(self, file_path):
        try:
            if file_path.lower().endswith('.mp3'):
                audio = ID3(file_path)
                for tag in audio.tags.values():
                    if tag.FrameID.startswith('APIC'):
                        return QPixmap.fromImage(QImage.fromData(tag.data))
            elif file_path.lower().endswith('.flac'):
                audio = mutagen.File(file_path)
                if audio and audio.pictures:
                    return QPixmap.fromImage(QImage.fromData(audio.pictures[0].data))
        except:
            pass
        return None

    def extract_metadata(self, file_path):
        try:
            if file_path.lower().endswith('.mp3'):
                audio = EasyID3(file_path)
            else:
                audio = mutagen.File(file_path)
                if not audio or not audio.tags:
                    return None, None
                audio = audio.tags
            
            title = audio.get('title', [os.path.basename(file_path)])[0]
            artist = audio.get('artist', ['ناشناس'])[0]
            return title, artist
        except:
            return None, None

    def get_audio_duration(self, file_path):
        try:
            if file_path.lower().endswith('.mp3'):
                return MP3(file_path).info.length
            elif file_path.lower().endswith('.flac'):
                return FLAC(file_path).info.length
            elif file_path.lower().endswith('.wav'):
                return WAVE(file_path).info.length
            else:
                audio = mutagen.File(file_path)
                return audio.info.length if audio else 180
        except:
            return 180

    def load_music_files(self):
        """بارگذاری فایل‌های موسیقی از پوشه"""
        music_folder = self.get_music_folder()
        
        if not os.path.exists(music_folder):
            QMessageBox.warning(self, "هشدار", 
                f"پوشه موسیقی یافت نشد!\n\n{music_folder}\n\nلطفاً یک پوشه انتخاب کنید.")
            return False
            
        extensions = ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac']
        self.music_files = []
        
        for root, _, files in os.walk(music_folder):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    self.music_files.append(os.path.join(root, file))
                    
        if not self.music_files:
            QMessageBox.information(self, "اطلاع", 
                f"هیچ فایل موسیقی در پوشه زیر یافت نشد:\n{music_folder}\n\nفرمت‌های پشتیبانی شده: {', '.join(extensions)}")
            return False
            
        self.song_list.clear()
        self.song_durations.clear()
        
        for file_path in self.music_files:
            title, artist = self.extract_metadata(file_path)
            if not title:
                title = os.path.basename(file_path)
            if not artist:
                artist = "ناشناس"
                
            duration = self.get_audio_duration(file_path)
            self.song_durations[file_path] = duration
            duration_str = self.format_time(duration)
            
            item_text = f"{title} - {artist}  [{duration_str}]"
            self.song_list.addItem(item_text)
            
        self.status_label.setText(f"{len(self.music_files)} آهنگ بارگذاری شد")
        return True

    def update_album_art(self, file_path):
        pixmap = self.extract_album_art(file_path)
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(200, 200, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.album_art.setPixmap(scaled)
        else:
            self.album_art.setText("🎵")
            self.album_art.setPixmap(QPixmap())

    def play_current_song(self):
        if not (0 <= self.current_index < len(self.music_files)):
            return
            
        try:
            current_file = self.music_files[self.current_index]
            pygame.mixer.music.load(current_file)
            pygame.mixer.music.set_volume(self.volume)
            
            # اگر موقعیت ذخیره شده وجود دارد، از آنجا شروع کن
            if hasattr(self, 'resume_position') and self.resume_position > 0:
                pygame.mixer.music.play(start=self.resume_position)
                delattr(self, 'resume_position')
            else:
                pygame.mixer.music.play()
            
            self.is_playing = True
            self.is_paused = False
            self.play_btn.setText("⏸")
            
            title, artist = self.extract_metadata(current_file)
            if not title:
                title = os.path.basename(current_file)
            if not artist:
                artist = "ناشناس"
                
            self.song_title.setText(title)
            self.artist_label.setText(artist)
            self.update_album_art(current_file)
            
            self.total_duration = self.song_durations.get(current_file, 180)
            self.total_time_label.setText(self.format_time(self.total_duration))
            
            # اگر موقعیت ذخیره شده داشتیم، آن را تنظیم کن
            if hasattr(self, 'initial_position'):
                current_time = self.initial_position
                delattr(self, 'initial_position')
            else:
                current_time = 0
                
            self.current_time_label.setText(self.format_time(current_time))
            progress = int((current_time / self.total_duration) * 1000) if self.total_duration > 0 else 0
            self.progress_slider.setValue(min(progress, 1000))
            self.current_position = current_time
            self.song_list.setCurrentRow(self.current_index)
            self.status_label.setText(f"در حال پخش: {title}")
            
            # ذخیره تنظیمات
            self.save_settings()
            
        except Exception as e:
            print(f"خطا در پخش: {e}")
            QMessageBox.critical(self, "خطا", "خطا در پخش فایل!")

    def play_pause(self):
        if not self.music_files:
            QMessageBox.warning(self, "خطا", "هیچ آهنگی برای پخش وجود ندارد.")
            return
            
        if self.current_index == -1:
            self.current_index = 0
            self.play_current_song()
        elif self.is_playing:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.is_playing = False
            self.play_btn.setText("▶")
            self.status_label.setText("مکث شده")
        else:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
            else:
                self.play_current_song()
            self.is_playing = True
            self.play_btn.setText("⏸")
            self.status_label.setText("در حال پخش")

    def stop_music(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.play_btn.setText("▶")
        self.progress_slider.setValue(0)
        self.current_time_label.setText("00:00")
        self.status_label.setText("متوقف شد")

    def prev_song(self):
        if not self.music_files: return
        self.stop_music()
        self.current_index = (self.current_index - 1) % len(self.music_files)
        self.play_current_song()

    def next_song(self):
        if not self.music_files: return
        self.stop_music()
        self.current_index = (self.current_index + 1) % len(self.music_files)
        self.play_current_song()

    def play_selected_song(self, item):
        index = self.song_list.row(item)
        if 0 <= index < len(self.music_files):
            self.stop_music()
            self.current_index = index
            self.play_current_song()

    def change_volume(self, value):
        self.volume = value / 100.0
        self.volume_label.setText(f"{value}%")
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self.volume)

    def update_progress(self):
        if self.is_playing and pygame.mixer.music.get_busy() and not self.seeking:
            try:
                current_time = pygame.mixer.music.get_pos() / 1000.0
                if current_time >= 0 and self.total_duration > 0:
                    self.current_position = current_time
                    progress = int((current_time / self.total_duration) * 1000)
                    self.progress_slider.setValue(min(progress, 1000))
                    self.current_time_label.setText(self.format_time(current_time))
            except:
                pass

    def check_song_end(self):
        if self.is_playing and not pygame.mixer.music.get_busy() and not self.is_paused:
            if self.current_position >= self.total_duration - 1:
                self.next_song()

    def start_seeking(self):
        self.seeking = True

    def end_seeking(self):
        if self.is_playing and self.total_duration > 0:
            new_position = (self.progress_slider.value() / 1000.0) * self.total_duration
            try:
                current_file = self.music_files[self.current_index]
                pygame.mixer.music.load(current_file)
                pygame.mixer.music.play(start=new_position)
                pygame.mixer.music.set_volume(self.volume)
                self.current_position = new_position
                self.current_time_label.setText(self.format_time(new_position))
            except:
                pass
        self.seeking = False

    def update_seek_position(self, value):
        if self.total_duration > 0:
            position = (value / 1000.0) * self.total_duration
            self.current_time_label.setText(self.format_time(position))

    def format_time(self, seconds):
        if seconds < 0:
            return "00:00"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def closeEvent(self, event):
        """ذخیره وضعیت نهایی هنگام بستن برنامه"""
        if self.is_playing and 0 <= self.current_index < len(self.music_files):
            self.current_position = pygame.mixer.music.get_pos() / 1000.0
        
        self.stop_music()
        self.save_settings()
        pygame.mixer.quit()
        event.accept()


def main():
    app = QApplication(sys.argv)
    
    # مسیر مطلق آیکون
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    
    # برای حالت exe
    if getattr(sys, 'frozen', False):
        # اگر exe شده باشد
        base_path = sys._MEIPASS
        icon_path = os.path.join(base_path, "icon.ico")
    else:
        # حالت عادی
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    
    # ایجاد QIcon
    app_icon = QIcon(icon_path)
    
    # تنظیم آیکون برای کل برنامه
    app.setWindowIcon(app_icon)
    app.setStyle('Fusion')
    
    player = MusicPlayer()
    player.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()