import sys
import os
import json
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QStackedWidget, QLabel, QGraphicsOpacityEffect, QSlider
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import (
    QFile, QTimer, Qt, QPropertyAnimation,
    QSequentialAnimationGroup, QEasingCurve
)
from PySide6.QtGui import QShortcut, QKeySequence, QPixmap, QColor, QPainter, QIcon

from GaugeBars import SpeedCircularGauge, RpmCircularGauge, VerticalFuelBar, DotMatrixShifter
from SerialTelemetryManger import SerialTelemetryManager


DEFAULT_CONFIG = {
    "ui": {
        "full_screen": False,
        "hide_cursor": False,
        "window_width": 1024,
        "window_height": 600,
    },
    "serial": {
        "port": "/dev/serial0",
        "baudrate": 115200,
        "header": "<",
        "footer": ">",
    },
    "battery": {
        "min_voltage": 55.0,
        "max_voltage": 84.0,
        "total_capacity_wh": 2500.0,
    },
    "power_ratio": {
        "default_battery_pct": 0,
        "default_hydrogen_pct": 100,
        "step_delta": 5,
    },
    "thresholds": {
        "battery_temp_warning_c": 60.0,
        "insulation_res_warning_ohm": 20.0,
    },
}

SPLASH_CONFIG = {
    "title_text": "BMT MACH - Hidromobil",
    "logo_max_width": 600,
    "logo_max_height": 480,
    "background_color": "#f8f9fa",
    "hold_duration_ms": 1000,
    "fade_duration_ms": 800,
}

class VehicleDashboard:
    """BMT MACH Araç Gösterge Paneli Ana Kontrol Sınıfı"""

    # =========================================================================
    # 1. BAŞLATMA, KONFİGÜRASYON, UI VE STİL YÜKLEME METOTLARI
    # =========================================================================
    def __init__(self, config_path="config.json", ui_path="mainwindow.ui", qss_path="style.qss", debugmode=False):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config = self.load_config(config_path)

        ui_cfg = self.config["ui"]
        ratio_cfg = self.config["power_ratio"]
        thresh_cfg = self.config["thresholds"]
        serial_cfg = self.config["serial"]

        self.debugmode = bool(debugmode)
        self.battery_pct = int(ratio_cfg["default_battery_pct"])
        self.hydrogen_pct = int(ratio_cfg["default_hydrogen_pct"])
        self.step_delta = int(ratio_cfg["step_delta"])

        self.batteryTempThreshold = float(thresh_cfg["battery_temp_warning_c"])
        self.insulationResThreshold = float(thresh_cfg["insulation_res_warning_ohm"])

        # Arayüz ve stil yüklemeleri
        self.load_stylesheet(self.resolve_path(qss_path))
        self.window = self.load_ui(self.resolve_path(ui_path))

        # Bileşen ve sinyal bağlantıları
        self.init_connections()
        self.setup_settings_controls()
        self.init_event_loop_timer()
        self.init_shortcuts()

        # Pencere ikonu, boyut, tam ekran ve imleç ayarları
        icon_path = self.resolve_path("assets/logo.png")
        if os.path.exists(icon_path):
            self.window.setWindowIcon(QIcon(icon_path))

        win_w = int(ui_cfg["window_width"])
        win_h = int(ui_cfg["window_height"])
        full_screen = bool(ui_cfg["full_screen"])
        hide_cursor = bool(ui_cfg["hide_cursor"])

        if full_screen:
            self.window.showFullScreen()
        else:
            self.window.setFixedSize(win_w, win_h)
            self.window.show()

        if hide_cursor:
            self.window.setCursor(Qt.BlankCursor)
        else:
            self.window.unsetCursor()

        # Açılış ekranı (Splash)
        if not self.debugmode:
            self.splash = SplashOverlay(
                self.window,
                splash_cfg=SPLASH_CONFIG,
                logo_path=self.resolve_path("assets/logo-no-background.png"),
            )
            self.splash.show()
            self.splash.raise_()

        # UART seri haberleşme başlatma
        self.connectionStatus = self.window.findChild(QLabel, "connectionStatus")
        if self.connectionStatus:
            self.connectionStatus.setText(f"● Port ({serial_cfg['port']}): Bağlanıyor...")

        self.uart = SerialTelemetryManager(
            port=serial_cfg["port"],
            baudrate=int(serial_cfg["baudrate"]),
            header=serial_cfg["header"],
            footer=serial_cfg["footer"],
        )
        self.uart.telemetry_received.connect(self.update_dashboard_telemetry)
        self.uart.connection_status.connect(self.on_serial_status_changed)
        self.uart.connection_status.connect(lambda ok, msg: self.window.statusbar.showMessage(msg))
        self.uart.start()

        self.window.stackedWidget.setCurrentIndex(0)
        self.update_dashboard_telemetry(self.uart.data)

    def resolve_path(self, path: str) -> str:
        """Göreli dosya yolunu main.py dizinine göre çözümler"""
        if os.path.isabs(path):
            return path
        return os.path.join(self.base_dir, path)

    def load_config(self, config_path: str) -> dict:
        """JSON yapılandırma dosyasını okur ve varsayılan değerlerle birleştirir"""
        resolved_path = self.resolve_path(config_path)
        merged = {
            section: values.copy() if isinstance(values, dict) else values
            for section, values in DEFAULT_CONFIG.items()
        }

        if not os.path.exists(resolved_path):
            print(f"Uyarı: '{resolved_path}' bulunamadı, varsayılan ayarlar kullanılıyor.")
            return merged

        try:
            with open(resolved_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                for section, values in loaded.items():
                    if section in merged and isinstance(merged[section], dict) and isinstance(values, dict):
                        merged[section].update(values)
                    else:
                        merged[section] = values
        except (OSError, json.JSONDecodeError) as e:
            print(f"Uyarı: '{resolved_path}' okunamadı ({e}), varsayılan ayarlar kullanılıyor.")

        return merged

    def load_stylesheet(self, qss_path):
        """QSS stil dosyasını okur ve tüm uygulamaya uygular"""
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
        """Qt Designer (.ui) dosyasını yükleyip ana pencere nesnesini döndürür"""
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

    # =========================================================================
    # 2. SAYFA GEÇİŞLERİ, ÖZEL GÖSTERGE YERLEŞİMİ VE KISAYOL METOTLARI
    # =========================================================================
    def init_connections(self):
        """Sayfa geçiş butonlarını bağlar ve özel QPainter göstergelerini yerleştirir"""
        sw = self.window.findChild(QStackedWidget, "stackedWidget")
        if sw:
            sw.setCurrentIndex(0)
            if main_btn := self.window.findChild(QPushButton, "backButton"):
                main_btn.clicked.connect(lambda: sw.setCurrentIndex(0))
            if settings_btn := self.window.findChild(QPushButton, "settingsButton"):
                settings_btn.clicked.connect(lambda: sw.setCurrentIndex(1))
            if exit_btn := self.window.findChild(QPushButton, "exitButton"):
                exit_btn.clicked.connect(self.close_application)

        # Hız Kadranı
        container = self.window.findChild(QWidget, "speedGaugeContainer")
        if container:
            if container.layout() is None:
                layout = QVBoxLayout(container)
                layout.setContentsMargins(0, 0, 0, 0)
            self.speed_gauge = SpeedCircularGauge(container)
            container.layout().addWidget(self.speed_gauge)

        # RPM Kadranı (UI'da mevcutsa)
        rpm_container = self.window.findChild(QWidget, "rpmGaugeContainer")
        if rpm_container:
            if rpm_container.layout() is None:
                layout = QVBoxLayout(rpm_container)
                layout.setContentsMargins(0, 0, 0, 0)
            self.rpm_gauge = RpmCircularGauge(rpm_container)
            rpm_container.layout().addWidget(self.rpm_gauge)

        # Dikey Batarya Barı
        fuel_container = self.window.findChild(QWidget, "fuelContainer")
        if fuel_container:
            if fuel_container.layout() is None:
                layout = QVBoxLayout(fuel_container)
                layout.setContentsMargins(0, 0, 0, 0)
            self.fuel_bar = VerticalFuelBar(fuel_container)
            fuel_container.layout().addWidget(self.fuel_bar)

        # Dot-Matrix Vites Göstergesi
        shifter_container = self.window.findChild(QWidget, "shifterContainer")
        if shifter_container:
            if shifter_container.layout() is None:
                layout = QVBoxLayout(shifter_container)
                layout.setContentsMargins(0, 0, 0, 0)
            self.shifter = DotMatrixShifter(shifter_container)
            shifter_container.layout().addWidget(self.shifter)

    def init_shortcuts(self):
        """Test aşamasında Esc tuşu ile güvenli çıkış kısayolunu tanımlar"""
        self.escape_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self.window)
        self.escape_shortcut.activated.connect(self.close_application)

    def close_application(self):
        """Seri portu güvenli şekilde kapatır ve uygulamadan çıkar"""
        if hasattr(self, "uart") and self.uart:
            self.uart.stop()
        self.window.close()

    # =========================================================================
    # 3. PERİYODİK DÖNGÜ VE DEBUG SİMÜLASYON METOTLARI
    # =========================================================================
    def init_event_loop_timer(self):
        """Qt Main Loop üzerinde çalışan 100 ms periyotlu zamanlayıcıyı başlatır"""
        self.update_timer = QTimer(self.window)
        self.update_timer.timeout.connect(self.main_loop_update)
        self.update_timer.start(100)  # 100 ms (10 FPS)

    def main_loop_update(self):
        """Debug modu aktifken göstergelere sabit test değerleri basar"""
        pass

    # =========================================================================
    # 4. AYARLAR SAYFASI (BATARYA / HİDROJEN ORANI) KONTROL METOTLARI
    # =========================================================================
    def setup_settings_controls(self):
        """Settings sayfasındaki slider, artırma/azaltma ve onay butonlarını bağlar"""
        self.ratio_slider = self.window.findChild(QSlider, "currentUsingRatioSlider")
        self.btn_decrease = self.window.findChild(QPushButton, "sliderDecreaseButton")
        self.btn_increase = self.window.findChild(QPushButton, "sliderIncreaseButton")
        self.btn_zero = self.window.findChild(QPushButton, "sliderZeroValueButton")
        self.btn_hundred = self.window.findChild(QPushButton, "sliderHunderedValueButton")
        self.btn_ok = self.window.findChild(QPushButton, "okButton")

        self.lbl_battery_use = self.window.findChild(QLabel, "batteryUseValue")
        self.lbl_hydrogen_use = self.window.findChild(QLabel, "hydrogenUseValue")

        if self.ratio_slider:
            self.ratio_slider.setRange(0, 100)
            self.ratio_slider.setValue(self.battery_pct)
            self.ratio_slider.valueChanged.connect(self.on_ratio_slider_changed)
            self.on_ratio_slider_changed(self.ratio_slider.value())

        if self.btn_decrease:
            self.btn_decrease.clicked.connect(lambda: self.adjust_ratio_slider(-self.step_delta))
        if self.btn_increase:
            self.btn_increase.clicked.connect(lambda: self.adjust_ratio_slider(self.step_delta))
        if self.btn_zero:
            self.btn_zero.clicked.connect(lambda: self.ratio_slider.setValue(0))
        if self.btn_hundred:
            self.btn_hundred.clicked.connect(lambda: self.ratio_slider.setValue(100))
        if self.btn_ok:
            self.btn_ok.clicked.connect(self.send_ratio_settings)

    def adjust_ratio_slider(self, delta):
        """Slider değerini verilen miktar kadar değiştirir"""
        if self.ratio_slider:
            new_val = max(0, min(100, self.ratio_slider.value() + delta))
            self.ratio_slider.setValue(new_val)

    def on_ratio_slider_changed(self, value):
        """Slider değiştikçe Batarya ve Hidrojen etiketlerini günceller (Henüz göndermez)"""
        self.battery_pct = int(value)
        self.hydrogen_pct = 100 - self.battery_pct

        if self.lbl_battery_use:
            self.lbl_battery_use.setText(f"%{self.battery_pct}")
        if self.lbl_hydrogen_use:
            self.lbl_hydrogen_use.setText(f"%{self.hydrogen_pct}")

    def send_ratio_settings(self):
        """Gönder (okButton) butonuna basıldığında oranları UART üzerinden iletir"""
        if hasattr(self, "uart") and self.uart:
            sent = self.uart.send_power_ratio(self.battery_pct, self.hydrogen_pct)
            if sent:
                self.window.statusbar.showMessage(
                    f"Oranlar gönderildi -> Batarya: %{self.battery_pct}, Hidrojen: %{self.hydrogen_pct}", 3000
                )
            else:
                self.window.statusbar.showMessage("Hata: Seri port bağlı değil!", 3000)

    # =========================================================================
    # 5. UART TELEMETRİ VERİ İŞLEME VE BAĞLANTI DURUMU METOTLARI
    # =========================================================================
    def update_dashboard_telemetry(self, data: dict):
        """UART'tan gelen telemetri verilerini hesaplar ve tüm göstergelere yazar"""
        bat_cfg = self.config["battery"]
        min_voltage = float(bat_cfg["min_voltage"])
        max_voltage = float(bat_cfg["max_voltage"])
        total_capacity_wh = float(bat_cfg["total_capacity_wh"])

        temp_svg = self.resolve_path("assets/icons/warning_temp.svg")
        res_svg = self.resolve_path("assets/icons/warning_res.svg")

        # 1. Hız Kadranı
        if hasattr(self, "speed_gauge"):
            self.speed_gauge.set_value(data["speed"])

        # 2. Batarya Voltajı, SoC Yüzdesi ve Kalan Enerji (Wh)
        voltage = data["battery_voltage"]
        voltage_span = max_voltage - min_voltage
        soc_percent = ((voltage - min_voltage) / voltage_span) * 100.0 if voltage_span != 0 else 0.0
        soc_percent = max(0.0, min(100.0, soc_percent))
        remaining_wh = (soc_percent / 100.0) * total_capacity_wh

        if hasattr(self, "fuel_bar"):
            self.fuel_bar.set_battery_data(soc_percent, voltage, remaining_wh)

        # 3. Vites Göstergesi
        if hasattr(self, "shifter"):
            gear_map = {-1: "R", 0: "N", 1: "D"}
            gear_str = gear_map.get(data["gear"], str(data["gear"]))
            self.shifter.set_gear(gear_str)

        # 4. Sağ Telemetri Kartı Değerleri
        self.window.batteryCurrentValue.setText(f"{data['battery_current']:.1f} A")
        self.window.batteryTemperatureValue.setText(f"{data['battery_temp']:.1f} °C")
        self.window.chargePowerValue.setText(f"{data['charge_power']:.1f} W")
        self.window.insulationResValue.setText(f"{data['insulation_res']:.0f} Ω")

        temp_warn_lbl = self.window.findChild(QLabel, "batteryTemperatureWarning")
        if temp_warn_lbl:
            temp_color = "#EF4444" if data["battery_temp"] >= self.batteryTempThreshold else "#6B7280"
            self.set_svg_label_color(temp_warn_lbl, temp_svg, temp_color, (40, 40))

        res_warn_lbl = self.window.findChild(QLabel, "insulationResWarning")
        if res_warn_lbl:
            res_color = "#EF4444" if data["insulation_res"] >= self.insulationResThreshold else "#6B7280"
            self.set_svg_label_color(res_warn_lbl, res_svg, res_color, (40, 40))

    def on_serial_status_changed(self, is_connected: bool, message: str):
        """UART bağlantı durumuna göre durum etiketini ve alt çubuğu günceller"""
        lbl_status = getattr(self, "connectionStatus", None)

        if lbl_status:
            if is_connected:
                lbl_status.setText(f"● BAĞLI ({message})")
                lbl_status.setStyleSheet(
                    "background-color: #dcfce7; color: #15803d; font-size: 11pt; "
                    "font-weight: 700; border-radius: 10px; padding: 6px 12px;"
                )
            else:
                lbl_status.setText(f"● BAĞLI DEĞİL ({message})")
                lbl_status.setStyleSheet(
                    "background-color: #fee2e2; color: #b91c1c; font-size: 11pt; "
                    "font-weight: 700; border-radius: 10px; padding: 6px 12px;"
                )

        self.window.statusbar.showMessage(message, 4000)

    def set_svg_label_color(self, label, svg_path: str, color_hex: str, size: tuple[int, int] = (24, 24)):
        """SVG dosyasını belirtilen boyutta ve renkte QLabel'a pixmap olarak yükler."""
        renderer = QSvgRenderer(svg_path)
        pixmap = QPixmap(size[0], size[1])
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor(color_hex))
        painter.end()

        label.setPixmap(pixmap)


class SplashOverlay(QWidget):
    """Açılışta tüm ekranı kaplayan, logo ve yazıyı birlikte gösteren animasyon katmanı"""

    def __init__(self, parent, splash_cfg=None, logo_path="assets/logo-no-background.png"):
        super().__init__(parent)
        cfg = {**SPLASH_CONFIG, **(splash_cfg or {})}
        self._bg_color = cfg["background_color"]

        self.setGeometry(0, 0, parent.width(), parent.height())
        self.setAttribute(Qt.WA_DeleteOnClose)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(30)

        if os.path.exists(logo_path):
            self.logo_label = QLabel(self)
            self.logo_label.setAlignment(Qt.AlignCenter)
            self.logo_label.setStyleSheet("background: transparent;")
            pixmap = QPixmap(logo_path)
            scaled = pixmap.scaled(
                int(cfg["logo_max_width"]),
                int(cfg["logo_max_height"]),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.logo_label.setPixmap(scaled)
            layout.addWidget(self.logo_label)

        self.title_label = QLabel(cfg["title_text"], self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size: 32px; font-weight: bold; color: #212529; background: transparent;"
        )
        layout.addWidget(self.title_label)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)

        self.start_animation(
            hold_ms=int(cfg["hold_duration_ms"]),
            fade_ms=int(cfg["fade_duration_ms"]),
        )

    def paintEvent(self, event):
        """Arka planı tamamen opak boyar, arkadaki ekranı gizler"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(self._bg_color))

    def start_animation(self, hold_ms=1000, fade_ms=800):
        """Logoyu sabit tutup ardından yumuşak geçişle (fade-out) kapatır"""
        self.hold = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.hold.setDuration(hold_ms)
        self.hold.setStartValue(1.0)
        self.hold.setEndValue(1.0)

        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(fade_ms)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.InOutCubic)

        self.anim_group = QSequentialAnimationGroup(self)
        self.anim_group.addAnimation(self.hold)
        self.anim_group.addAnimation(self.fade_out)

        self.anim_group.finished.connect(self.close)
        self.anim_group.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = VehicleDashboard(config_path="config.json", debugmode=False)

    app.aboutToQuit.connect(dashboard.uart.stop)

    sys.exit(app.exec())