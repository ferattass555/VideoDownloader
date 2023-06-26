import sys
import os
import time
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QProgressBar, QVBoxLayout, QComboBox, QFileDialog, QRadioButton
from PyQt5.QtCore import QThread, pyqtSignal, Qt

from pytube import Playlist, YouTube

class DownloadThread(QThread):
    update_progress = pyqtSignal(int)
    update_speed = pyqtSignal(str)
    update_filename = pyqtSignal(str)

    def __init__(self, url, download_type, download_format, download_path):
        super().__init__()
        self.url = url
        self.download_type = download_type
        self.download_format = download_format
        self.download_path = download_path
        self.stop_flag = False

    def run(self):
        if self.download_type == "Playlist":
            playlist = Playlist(self.url)
            total_videos = len(playlist.video_urls)

            for index, video_url in enumerate(playlist.video_urls):
                if self.stop_flag:
                    break

                self.update_progress.emit((index + 1) * 100 // total_videos)

                yt = YouTube(video_url)
                if self.download_format == "MP3":
                    video = yt.streams.filter(only_audio=True).first()
                else:
                    video = yt.streams.get_highest_resolution()

                filename = f"{index+1}. {video.title}.{video.subtype}"
                self.update_filename.emit(filename)

                start_time = time.time()
                video.download(output_path=self.download_path)
                end_time = time.time()

                download_speed = self.calculateDownloadSpeed(video.filesize, start_time, end_time)
                self.update_speed.emit(download_speed)
        else:
            yt = YouTube(self.url)
            if self.download_format == "MP3":
                video = yt.streams.filter(only_audio=True).first()
            else:
                video = yt.streams.get_highest_resolution()

            filename = f"{video.title}.{video.subtype}"
            self.update_filename.emit(filename)

            start_time = time.time()
            video.download(output_path=self.download_path)
            end_time = time.time()

            download_speed = self.calculateDownloadSpeed(video.filesize, start_time, end_time)
            self.update_speed.emit(download_speed)

    def stopDownload(self):
        self.stop_flag = True

    def calculateDownloadSpeed(self, filesize, start_time, end_time):
        duration = end_time - start_time
        if duration > 0:
            speed = filesize / duration
            if speed >= 1000000:
                return f"{speed / 1000000:.2f} MB/s"
            elif speed >= 1000:
                return f"{speed / 1000:.2f} KB/s"
            else:
                return f"{speed:.2f} B/s"
        else:
            return "N/A"

class PlaylistDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Playlist Downloader")
        self.setGeometry(100, 100, 400, 400)

        self.label_type = QLabel("İndirme Türü:", self)
        self.radio_playlist = QRadioButton("Çalma Listesi", self)
        self.radio_playlist.setChecked(True)
        self.radio_single_video = QRadioButton("Tek Video", self)

        self.label_url = QLabel("URL:", self)
        self.input_url = QLineEdit(self)

        self.label_format = QLabel("İndirme Formatı:", self)
        self.format_combobox = QComboBox(self)
        self.format_combobox.addItem("MP4")
        self.format_combobox.addItem("MP3")

        self.label_path = QLabel("İndirme Yeri:", self)
        self.input_path = QLineEdit(self)

        self.button_browse = QPushButton("Gözat", self)
        self.button_browse.clicked.connect(self.browsePath)

        self.button_start = QPushButton("İndirmeye Başla", self)
        self.button_start.clicked.connect(self.startDownload)

        self.button_stop = QPushButton("İndirmeyi Durdur", self)
        self.button_stop.clicked.connect(self.stopDownload)
        self.button_stop.setEnabled(False)

        self.progress = QProgressBar(self)
        self.progress.setStyleSheet("QProgressBar { border: 1px solid grey; border-radius: 5px; background-color: #B9E2F5; text-align: center; }"
                                    "QProgressBar::chunk { background-color: #00CC7A; }")

        self.label_speed = QLabel("İndirme Hızı:", self)
        self.value_speed = QLabel("0 B/s", self)

        self.label_filename = QLabel("İndirilen Dosya:", self)
        self.value_filename = QLabel("", self)

        vbox = QVBoxLayout()
        vbox.addWidget(self.label_type)
        vbox.addWidget(self.radio_playlist)
        vbox.addWidget(self.radio_single_video)
        vbox.addWidget(self.label_url)
        vbox.addWidget(self.input_url)
        vbox.addWidget(self.label_format)
        vbox.addWidget(self.format_combobox)
        vbox.addWidget(self.label_path)
        vbox.addWidget(self.input_path)
        vbox.addWidget(self.button_browse)
        vbox.addWidget(self.button_start)
        vbox.addWidget(self.button_stop)
        vbox.addWidget(self.progress)
        vbox.addWidget(self.label_speed)
        vbox.addWidget(self.value_speed)
        vbox.addWidget(self.label_filename)
        vbox.addWidget(self.value_filename)

        vbox.setAlignment(Qt.AlignCenter)

        self.setLayout(vbox)
        self.show()

    def browsePath(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        selected_path = QFileDialog.getExistingDirectory(self, "İndirme Yeri Seç", options=options)
        if selected_path:
            self.input_path.setText(selected_path)

    def startDownload(self):
        url = self.input_url.text()
        download_type = "Playlist" if self.radio_playlist.isChecked() else "SingleVideo"
        download_format = self.format_combobox.currentText()
        download_path = self.input_path.text()

        if not url or not download_path:
            return

        self.thread = DownloadThread(url, download_type, download_format, download_path)
        self.thread.update_progress.connect(self.updateProgress)
        self.thread.update_speed.connect(self.updateSpeed)
        self.thread.update_filename.connect(self.updateFilename)
        self.thread.start()

        self.button_start.setEnabled(False)
        self.button_stop.setEnabled(True)

    def stopDownload(self):
        if self.thread.isRunning():
            self.thread.stopDownload()
            self.button_start.setEnabled(True)
            self.button_stop.setEnabled(False)

    def updateProgress(self, value):
        self.progress.setValue(value)

    def updateSpeed(self, speed):
        self.value_speed.setText(speed)

    def updateFilename(self, filename):
        self.value_filename.setText(filename)

    def timerEvent(self, event):
        self.update()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PlaylistDownloader()
    sys.exit(app.exec_())
