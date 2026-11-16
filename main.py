import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, 
    QStackedWidget, QLabel, QGraphicsOpacityEffect
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import (
    QFile, QTimer, Qt, QPropertyAnimation, 
    QSequentialAnimationGroup, QEasingCurve
)
from PySide6.QtGui import QShortcut, QKeySequence, QPixmap, QColor, QPainter

from GaugeBars import CircularGauge, VerticalFuelBar


class SplashOverlay(QWidget):
    """Açılışta tüm ekranı kaplayan, logo ve yazıyı birlikte gösteren animasyon katmanı"""
    def __init__(self, parent, logo_path="assets/logo.png"):
        super().__init__(parent)
        self.setGeometry(0, 0, parent.width(), parent.height())
        self.setAttribute(Qt.WA_DeleteOnClose)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(30)  # Logo ile yazı arasındaki dikey boşluk

        # 1. Logo Görseli (Varsa gösterilir)
        if os.path.exists(logo_path):
            self.logo_label = QLabel(self)
            self.logo_label.setAlignment(Qt.AlignCenter)
            self.logo_label.setStyleSheet("background: transparent;")
            pixmap = QPixmap(logo_path)
            scaled = pixmap.scaled(420, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled)
            layout.addWidget(self.logo_label)

        # 2. Başlık Yazısı (Her durumda logonun altında görünür)
        self.title_label = QLabel("BMT MACH - Hidromobil", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: #212529; background: transparent;"
        )
        layout.addWidget(self.title_label)

        # Opaklık efektini tüm katmana uygula
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)

        self.start_animation()

    def paintEvent(self, event):
        """Arka planı tamamen opak boyar, arkadaki ekranı gizler"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#f8f9fa"))

    def start_animation(self):
        # 1. Logo ve yazı sabit durur (1000ms)
        self.hold = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.hold.setDuration(1000)
        self.hold.setStartValue(1.0)
        self.hold.setEndValue(1.0)

        # 2. Tüm beyaz perde, logo ve yazı birlikte eriyerek ana ekranı açar (800ms)
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(800)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.InOutCubic)

        self.anim_group = QSequentialAnimationGroup(self)
        self.anim_group.addAnimation(self.hold)
        self.anim_group.addAnimation(self.fade_out)

        self.anim_group.finished.connect(self.close)
        self.anim_group.start()


class VehicleDashboard:
    def __init__(self, ui_path="mainwindow.ui", qss_path="style.qss", debugmode=False):
        self.debugmode = debugmode

        self.load_stylesheet(qss_path)       # 1. Stil dosyasını (QSS) global olarak uygula
        self.window = self.load_ui(ui_path)  # 2. UI dosyasını doğrudan ana pencere olarak yükle

        self.init_connections()              # 3. Sinyal ve slot bağlantıları
        self.init_event_loop_timer()         # 4. Qt Event Loop üzerinde çalışacak timer
        self.init_shortcuts()                # 5. Esc tuşu ile güvenli çıkış kısayolu

        # --- GÖMÜLÜ SİSTEM / QT TEMEL AYARLARI ---
        self.window.setFixedSize(1024, 600)
        self.window.show()
        # self.window.setCursor(Qt.BlankCursor)

        # debugmode False ise açılış logosu animasyonunu başlat
        if not self.debugmode:
            self.splash = SplashOverlay(self.window, logo_path="assets/logo.png")
            self.splash.show()
            self.splash.raise_()

    def load_stylesheet(self, qss_path):
        file = QFile(qss_path)
        if file.open(QFile.ReadOnly | QFile.Text):
            stylesheet = str(file.readAll(), encoding="utf-8")
            app_instance = QApplication.instance()
            if app_instance:
                app_instance.setStyleSheet(stylesheet)
            file.close()
        else:
            print(f"Uyarı: '{qss_path}' bulunamadı!")

    def load_ui(self, ui_path):
        file = QFile(ui_path)
        if not file.open(QFile.ReadOnly):
            print(f"Hata: '{ui_path}' dosyası açılamadı!")
            sys.exit(-1)

        loader = QUiLoader()
        window = loader.load(file, None)
        file.close()

        if not window:
            print("Hata: Arayüz yüklenemedi!")
            sys.exit(-1)

        window.setWindowTitle("BMT MACH - Hidromobil")
        return window

    def init_connections(self):
        """Butonlar, QStackedWidget vb. elemanların bağlantıları"""
        sw = self.window.findChild(QStackedWidget, "stackedWidget")
        if sw:
            sw.setCurrentIndex(0)
            if main_btn := self.window.findChild(QPushButton, "backButton"):
                main_btn.clicked.connect(lambda: sw.setCurrentIndex(0))
            if settings_btn := self.window.findChild(QPushButton, "settingsButton"):
                settings_btn.clicked.connect(lambda: sw.setCurrentIndex(1))

        container = self.window.findChild(QWidget, "gaugeContainer")
        if container:
            if container.layout() is None:
                layout = QVBoxLayout(container)
                layout.setContentsMargins(0, 0, 0, 0)
            self.speed_gauge = CircularGauge(container)
            container.layout().addWidget(self.speed_gauge)

        fuel_container = self.window.findChild(QWidget, "fuelContainer")
        if fuel_container:
            if fuel_container.layout() is None:
                layout = QVBoxLayout(fuel_container)
                layout.setContentsMargins(0, 0, 0, 0)
            self.fuel_bar = VerticalFuelBar(fuel_container)
            fuel_container.layout().addWidget(self.fuel_bar)

    def init_event_loop_timer(self):
        """Qt Main Loop üzerinde çalışan periyodik timer"""
        self.update_timer = QTimer(self.window)
        self.update_timer.timeout.connect(self.main_loop_update)
        self.update_timer.start(100)  # 100 ms (10 FPS)

    def main_loop_update(self):
        """Araç verilerinin güncelleneceği ana döngü fonksiyonu"""

        if hasattr(self, 'speed_gauge'):
            self.speed_gauge.set_value(53)

        if hasattr(self, 'fuel_bar'):
            self.fuel_bar.set_value(53)
            self.fuel_bar.set_voltage(48)

    def init_shortcuts(self):
        """Test aşamasında Esc tuşuna basıldığında programın kapanmasını sağlar"""
        self.escape_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self.window)
        self.escape_shortcut.activated.connect(self.window.close)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # debugmode=True yaparsanız logo animasyonu atlanır ve doğrudan ekran açılır
    dashboard = VehicleDashboard(debugmode=True)

    sys.exit(app.exec())