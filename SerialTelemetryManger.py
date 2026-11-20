import serial
from PySide6.QtCore import QThread, Signal

class SerialTelemetryManager(QThread):
    # Arayüze (main.py) veri ve durum aktarmak için Qt Sinyalleri
    telemetry_received = Signal(dict)
    connection_status = Signal(bool, str)

    def __init__(self, port="COM3", baudrate=115200, header="<", footer=">", parent=None):
        super().__init__(parent)
        self.port = port
        self.baudrate = baudrate
        self.header = header
        self.footer = footer

        self.serial_conn = None
        self._running = False
        self._rx_buffer = ""

        # Son alınan telemetri değerleri
        self.data = {
            "speed": 0.0,               # Hız (km/h)
            "battery_voltage": 0.0,     # Batarya Voltajı (V)
            "battery_current": 0.0,     # Çekilen Akım (A)
            "battery_temp": 0.0,        # Batarya Sıcaklığı (°C)
            "charge_power": 0.0,        # Şarj Gücü (W veya kW)
            "insulation_res": 0.0,      # İzolasyon Direnci (kΩ)
            "gear": 0                   # Vites Durumu (0: N, 1: D, -1: R vb. veya float)
        }

    def run(self):
        """Arka planda çalışan UART okuma döngüsü"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.05
            )
            self._running = True
            self.connection_status.emit(True, f"{self.port} ({self.baudrate})")
        except serial.SerialException as e:
            self.connection_status.emit(False, f"Port hatası")
            return

        while self._running:
            try:
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    raw_bytes = self.serial_conn.read(self.serial_conn.in_waiting)
                    self._rx_buffer += raw_bytes.decode("utf-8", errors="ignore")
                    self._process_buffer()
                else:
                    self.msleep(10)  # CPU kullanımını düşük tutmak için 10ms bekle
            except serial.SerialException as e:
                self.connection_status.emit(False, f"Bağlantı koptu: {e}")
                break

        self._close_port()

    def _process_buffer(self):
        """Tampon bellekten header ve footer arasındaki tam paketleri ayrıştırır"""
        while self.header in self._rx_buffer and self.footer in self._rx_buffer:
            start_idx = self._rx_buffer.find(self.header)
            end_idx = self._rx_buffer.find(self.footer, start_idx)

            # Footer henüz gelmediyse bir sonraki okumayı bekle
            if end_idx == -1:
                break

            # Header ile footer arasındaki ham metni çıkar
            payload = self._rx_buffer[start_idx + len(self.header):end_idx].strip()
            # İşlenen paketi tampon bellekten temizle
            self._rx_buffer = self._rx_buffer[end_idx + len(self.footer):]

            self._parse_packet(payload)

    def _parse_packet(self, payload: str):
        """Virgülle ayrılmış 7 veriyi float olarak ayrıştırıp sözlüğe atar"""
        parts = [p.strip() for p in payload.split(",")]
        if len(parts) != 7:
            return  # Eksik veya bozuk paketi yoksay

        try:
            values = [float(x) for x in parts]
            self.data = {
                "speed": values[0],
                "battery_voltage": values[1],
                "battery_current": values[2],
                "battery_temp": values[3],
                "charge_power": values[4],
                "insulation_res": values[5],
                "gear": int(values[6]) if values[6].is_integer() else values[6]
            }
            # Güncel veriyi sinyal ile arayüze gönder
            self.telemetry_received.emit(self.data.copy())
        except ValueError:
            # Sayıya çevrilemeyen bozuk karakter varsa paketi atla
            pass

    def send_packet(
        self,
        speed: float,
        battery_voltage: float,
        battery_current: float,
        battery_temp: float,
        charge_power: float,
        insulation_res: float,
        gear: float
    ) -> bool:
        """Verilen 7 değeri header + virgüllü float + footer formatında UART'tan gönderir"""
        if not (self.serial_conn and self.serial_conn.is_open):
            return False

        payload = (
            f"{float(speed):.2f},"
            f"{float(battery_voltage):.2f},"
            f"{float(battery_current):.2f},"
            f"{float(battery_temp):.2f},"
            f"{float(charge_power):.2f},"
            f"{float(insulation_res):.2f},"
            f"{float(gear):.1f}"
        )
        packet = f"{self.header}{payload}{self.footer}\n"

        try:
            self.serial_conn.write(packet.encode("utf-8"))
            return True
        except serial.SerialException:
            return False

    def send_power_ratio(self, battery_pct: int, hydrogen_pct: int) -> bool:
        """Batarya ve Hidrojen kullanım oranlarını UART üzerinden gönderir (Örn: $60,40>)"""
        if not (self.serial_conn and self.serial_conn.is_open):
            return False

        # Telemetri paketinden ('<') ayırt etmek için başlangıç karakteri olarak '$' kullanıyoruz
        packet = f"${int(battery_pct)},{int(hydrogen_pct)}{self.footer}\n"

        try:
            self.serial_conn.write(packet.encode("utf-8"))
            return True
        except serial.SerialException:
            return False

    def stop(self):
        """Thread'i ve seri portu güvenli şekilde kapatır"""
        self._running = False
        self.wait(500)
        self._close_port()

    def _close_port(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()