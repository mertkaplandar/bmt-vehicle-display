import math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QPainterPath

class SpeedCircularGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.max_value = 120  # Maksimum hız

    def set_value(self, val):
        self.value = max(0, min(val, self.max_value))
        self.update()  # Kadranı yeniden çiz

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        side = min(width, height)

        # Kadranı kare alan içinde ortala
        painter.setViewport((width - side) // 2, (height - side) // 2, side, side)
        painter.setWindow(0, 0, 200, 200)

        cx, cy = 100, 105
        radius = 90

        # 1. Arka plan gösterge halkası (İnce, modern pasif ark)
        bg_pen = QPen(QColor("#e2e8f0"), 8, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(cx - radius, cy - radius, radius * 2, radius * 2, 210 * 16, -270 * 16)

        # 2. Aktif hız yayı (Dolu kısım - Şık modern mavi)
        if self.value > 0:
            span_angle = -int((self.value / self.max_value) * 270 * 16)
            active_pen = QPen(QColor("#2563eb"), 10, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(active_pen)
            painter.drawArc(cx - radius, cy - radius, radius * 2, radius * 2, 210 * 16, span_angle)

        # 3. İç dekoratif ince çember (Otomotiv kokpit hissi için derinlik katmanı)
        inner_ring_pen = QPen(QColor("#cbd5e1"), 1, Qt.DashLine)
        painter.setPen(inner_ring_pen)
        painter.drawEllipse(QPointF(cx, cy), radius - 16, radius - 16)

        # 4. Kadran çizgileri (Tick marks) ve Sayılar (0 - 120 arası)
        # Her 5 birimde bir minör, her 20'de majör çizgi
        for v in range(0, self.max_value + 1, 5):
            fraction = v / self.max_value
            angle_deg = 210 - (fraction * 270)
            rad = math.radians(angle_deg)

            is_major = (v % 20 == 0)
            is_medium = (v % 10 == 0 and not is_major)
            
            if is_major:
                tick_len = 8
                tick_width = 2
                color = "#1e293b"
            elif is_medium:
                tick_len = 5
                tick_width = 1.5
                color = "#64748b"
            else:
                tick_len = 3
                tick_width = 1
                color = "#cbd5e1"

            r_outer = radius - 4
            r_inner = r_outer - tick_len

            x1 = cx + r_outer * math.cos(rad)
            y1 = cy - r_outer * math.sin(rad)
            x2 = cx + r_inner * math.cos(rad)
            y2 = cy - r_inner * math.sin(rad)

            tick_pen = QPen(QColor(color), tick_width)
            painter.setPen(tick_pen)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

            # Büyük çizgilerin yanına sayıları yazdır (0, 20, 40, 60, 80, 100, 120)
            if is_major:
                r_text = r_inner - 16
                tx = cx + r_text * math.cos(rad)
                ty = cy - r_text * math.sin(rad)

                painter.setPen(QColor("#1e293b"))
                painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
                text_rect = QRectF(tx - 18, ty - 10, 36, 20)
                painter.drawText(text_rect, Qt.AlignCenter, str(v))

        # 5. Merkezdeki dijital hız göstergesi (Modern ve net tipografi)
        painter.setPen(QColor("#0f172a"))
        painter.setFont(QFont("Segoe UI", 28, QFont.Bold))
        painter.drawText(QRectF(50, 62, 100, 45), Qt.AlignCenter, str(int(self.value)))
        
        # "KM/H" birimi
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.setPen(QColor("#64748b"))
        painter.drawText(QRectF(50, 110, 100, 18), Qt.AlignCenter, "KM/H")


class RpmCircularGauge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.max_value = 6000  # Maksimum devir (RPM)

    def set_value(self, val):
        self.value = max(0, min(val, self.max_value))
        self.update()  # Kadranı yeniden çiz

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        side = min(width, height)

        # Kadranı kare alan içinde ortala
        painter.setViewport((width - side) // 2, (height - side) // 2, side, side)
        painter.setWindow(0, 0, 200, 200)

        cx, cy = 100, 100
        radius = 90

        # 1. Arka plan gösterge halkası (İnce, modern pasif ark)
        bg_pen = QPen(QColor("#e2e8f0"), 8, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(cx - radius, cy - radius, radius * 2, radius * 2, 210 * 16, -270 * 16)

        # 2. Aktif devir yayı (Dolu kısım - Şık modern mavi)
        if self.value > 0:
            span_angle = -int((self.value / self.max_value) * 270 * 16)
            active_pen = QPen(QColor("#2563eb"), 10, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(active_pen)
            painter.drawArc(cx - radius, cy - radius, radius * 2, radius * 2, 210 * 16, span_angle)

        # 3. İç dekoratif ince çember (Otomotiv kokpit hissi için derinlik katmanı)
        inner_ring_pen = QPen(QColor("#cbd5e1"), 1, Qt.DashLine)
        painter.setPen(inner_ring_pen)
        painter.drawEllipse(QPointF(cx, cy), radius - 16, radius - 16)

        # 4. Kadran çizgileri (Tick marks) ve Sayılar (0 - 6000 RPM arası, x1000 ölçekli)
        # Her 250 RPM'de minör, her 500'de orta, her 1000'de majör çizgi
        for v in range(0, self.max_value + 1, 250):
            fraction = v / self.max_value
            angle_deg = 210 - (fraction * 270)
            rad = math.radians(angle_deg)

            is_major = (v % 1000 == 0)
            is_medium = (v % 500 == 0 and not is_major)
            
            if is_major:
                tick_len = 8
                tick_width = 2
                color = "#1e293b"
            elif is_medium:
                tick_len = 5
                tick_width = 1.5
                color = "#64748b"
            else:
                tick_len = 3
                tick_width = 1
                color = "#cbd5e1"

            r_outer = radius - 4
            r_inner = r_outer - tick_len

            x1 = cx + r_outer * math.cos(rad)
            y1 = cy - r_outer * math.sin(rad)
            x2 = cx + r_inner * math.cos(rad)
            y2 = cy - r_inner * math.sin(rad)

            tick_pen = QPen(QColor(color), tick_width)
            painter.setPen(tick_pen)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

            # Büyük çizgilerin yanına sayıları yazdır (0, 1, 2, 3, 4, 5, 6)
            if is_major:
                r_text = r_inner - 16
                tx = cx + r_text * math.cos(rad)
                ty = cy - r_text * math.sin(rad)

                painter.setPen(QColor("#1e293b"))
                painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
                text_rect = QRectF(tx - 18, ty - 10, 36, 20)
                painter.drawText(text_rect, Qt.AlignCenter, str(v // 1000))

        # 5. Merkezdeki dijital devir göstergesi (4 haneli sayı sığacak şekilde 22pt)
        painter.setPen(QColor("#0f172a"))
        painter.setFont(QFont("Segoe UI", 22, QFont.Bold))
        painter.drawText(QRectF(45, 62, 110, 45), Qt.AlignCenter, str(int(self.value)))
        
        # "x1000 RPM" birimi
        painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
        painter.setPen(QColor("#64748b"))
        painter.drawText(QRectF(45, 110, 110, 18), Qt.AlignCenter, "x1000 RPM")



class VerticalFuelBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0          # Şarj yüzdesi (0 - 100)
        self.voltage = 0.0      # Voltaj değeri (V)
        self.energy_wh = 0      # Kalan enerji (Wh)
        self.max_value = 100

    def set_value(self, val):
        """Şarj yüzdesini günceller (0-100)"""
        self.value = max(0, min(val, self.max_value))
        self.update()

    def set_voltage(self, volt):
        """Voltaj değerini günceller (V)"""
        self.voltage = max(0.0, float(volt))
        self.update()

    def set_energy(self, wh):
        """Kalan enerji miktarını günceller (Wh)"""
        self.energy_wh = max(0.0, float(wh))
        self.update()

    def set_battery_data(self, val, volt, wh):
        """İsteğe bağlı olarak üçünü tek seferde günceller"""
        self.value = max(0, min(val, self.max_value))
        self.voltage = max(0.0, float(volt))
        self.energy_wh = max(0.0, float(wh))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Üst başlık ve alt kısımdaki üç veri (Yüzde + Wh + Voltaj) için boşluklar
        top_margin = 24
        bottom_margin = 74
        bar_h = h - top_margin - bottom_margin
        if bar_h <= 10:
            return

        # Bar genişliği ve konumu
        bar_w = min(28, int(w * 0.38))
        bar_x = (w // 2) - bar_w + 4
        bar_y = top_margin
        radius = 6

        # 1. Üst etiket
        painter.setPen(QColor("#64748b"))
        painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
        painter.drawText(QRectF(0, 2, w, 20), Qt.AlignCenter, "BATTERY")

        # 2. Arka plan gövdesi
        bg_rect = QRectF(bar_x, bar_y, bar_w, bar_h)
        painter.setPen(QPen(QColor("#cbd5e1"), 1))
        painter.setBrush(QColor("#e2e8f0"))
        painter.drawRoundedRect(bg_rect, radius, radius)

        # 3. Doluluk seviyesi
        if self.value > 0:
            fill_ratio = self.value / self.max_value
            fill_h = bar_h * fill_ratio
            fill_y = bar_y + (bar_h - fill_h)

            if self.value <= 15:
                fill_color = QColor("#dc2626")  # Kritik seviye (Kırmızı)
            elif self.value <= 30:
                fill_color = QColor("#f59e0b")  # Uyarı seviyesi (Turuncu)
            else:
                fill_color = QColor("#2563eb")  # Normal seviye (Tema mavisi)

            clip_path = QPainterPath()
            clip_path.addRoundedRect(bg_rect, radius, radius)
            painter.setClipPath(clip_path)

            painter.setPen(Qt.NoPen)
            painter.setBrush(fill_color)
            painter.drawRect(QRectF(bar_x, fill_y, bar_w, fill_h))
            painter.setClipping(False)

        # 4. Sağ taraftaki ölçek çizgileri ve sayılar (0 - 100)
        tick_start_x = bar_x + bar_w + 5
        for v in range(0, 101, 10):
            ratio = v / 100.0
            y = bar_y + bar_h - (ratio * bar_h)

            is_major = (v % 25 == 0)
            is_medium = (v % 50 == 0)

            tick_len = 7 if is_major else 4
            pen_color = "#1e293b" if is_major else "#94a3b8"
            pen_w = 1.5 if is_major else 1

            painter.setPen(QPen(QColor(pen_color), pen_w))
            painter.drawLine(QPointF(tick_start_x, y), QPointF(tick_start_x + tick_len, y))

            if is_medium:
                painter.setPen(QColor("#1e293b"))
                painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
                painter.drawText(
                    QRectF(tick_start_x + tick_len + 3, y - 7, 26, 14),
                    Qt.AlignLeft | Qt.AlignVCenter,
                    str(v)
                )

        # 5. Alt kısımda Şarj Yüzdesi, Kalan Enerji (Wh) ve Voltaj Etiketleri
        # Şarj Yüzdesi (%)
        painter.setPen(QColor("#0f172a"))
        painter.setFont(QFont("Segoe UI", 16, QFont.Bold))
        painter.drawText(QRectF(0, h - 70, w, 22), Qt.AlignCenter, f"%{int(self.value)}")

        # Kalan Enerji (Wh)
        painter.setPen(QColor("#0f766e"))
        painter.setFont(QFont("Segoe UI", 14, QFont.Bold))
        painter.drawText(QRectF(0, h - 47, w, 21), Qt.AlignCenter, f"{int(self.energy_wh)} Wh")

        # Voltaj Değeri (V)
        painter.setPen(QColor("#2563eb"))
        painter.setFont(QFont("Segoe UI", 15, QFont.Bold))
        painter.drawText(QRectF(0, h - 25, w, 22), Qt.AlignCenter, f"{self.voltage:.1f} V")


class DotMatrixShifter(QWidget):
    # Yüksek yoğunluklu 7x9 dot-matrix karakter haritaları
    FONT_7X9 = {
        "P": [
            "1111110",
            "1100011",
            "1100011",
            "1100011",
            "1111110",
            "1100000",
            "1100000",
            "1100000",
            "1100000",
        ],
        "R": [
            "1111110",
            "1100011",
            "1100011",
            "1100011",
            "1111110",
            "1101100",
            "1100110",
            "1100011",
            "1100011",
        ],
        "N": [
            "1100011",
            "1110011",
            "1111011",
            "1101111",
            "1100111",
            "1100011",
            "1100011",
            "1100011",
            "1100011",
        ],
        "D": [
            "1111100",
            "1100110",
            "1100011",
            "1100011",
            "1100011",
            "1100011",
            "1100011",
            "1100110",
            "1111100",
        ],
        "1": [
            "0001100",
            "0011100",
            "0111100",
            "0001100",
            "0001100",
            "0001100",
            "0001100",
            "0001100",
            "0111111",
        ],
        "2": [
            "0111110",
            "1100011",
            "0000011",
            "0000110",
            "0001100",
            "0011000",
            "0110000",
            "1100000",
            "1111111",
        ],
        "3": [
            "0111110",
            "1100011",
            "0000011",
            "0000011",
            "0011110",
            "0000011",
            "0000011",
            "1100011",
            "0111110",
        ],
        "4": [
            "0000110",
            "0001110",
            "0011110",
            "0110110",
            "1100110",
            "1111111",
            "0000110",
            "0000110",
            "0000110",
        ],
        "5": [
            "1111111",
            "1100000",
            "1100000",
            "1111110",
            "0000011",
            "0000011",
            "0000011",
            "1100011",
            "0111110",
        ],
        "6": [
            "0111110",
            "1100011",
            "1100000",
            "1111110",
            "1100011",
            "1100011",
            "1100011",
            "1100011",
            "0111110",
        ],
        "-": [
            "0000000",
            "0000000",
            "0000000",
            "0000000",
            "1111111",
            "0000000",
            "0000000",
            "0000000",
            "0000000",
        ],
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.gear = "P"

    def set_gear(self, gear_val):
        """Vites değerini günceller ('P', 'R', 'N', 'D' veya 1-6)"""
        text = str(gear_val).strip().upper()
        self.gear = text if text in self.FONT_7X9 else "-"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Dış çerçeve
        bg_rect = QRectF(2, 2, w - 4, h - 4)
        painter.setPen(QPen(QColor("#cbd5e1"), 1.5))
        painter.setBrush(QColor("#f1f5f9"))
        painter.drawRoundedRect(bg_rect, 8, 8)

        # 7x9 yoğun matris yerleşimi
        cols, rows = 7, 9
        padding = 8
        avail_w = w - (padding * 2)
        avail_h = h - (padding * 2)
        if avail_w <= 0 or avail_h <= 0:
            return

        cell_w = avail_w / cols
        cell_h = avail_h / rows
        # Noktaların birbirine yakın ve yoğun görünmesi için çap oranı artırıldı
        dot_radius = min(cell_w, cell_h) * 0.40

        start_x = (w - (cols * cell_w)) / 2
        start_y = (h - (rows * cell_h)) / 2

        matrix = self.FONT_7X9.get(self.gear, self.FONT_7X9["-"])
        active_color = QColor("#dc2626")    # Parlak Kırmızı LED
        inactive_color = QColor("#cbd5e1")  # Pasif LED

        painter.setPen(Qt.NoPen)

        for r in range(rows):
            for c in range(cols):
                is_on = (matrix[r][c] == "1")
                cx = start_x + (c + 0.5) * cell_w
                cy = start_y + (r + 0.5) * cell_h

                if is_on:
                    # Kırmızı LED parlama (glow) efekti
                    glow = QColor("#ef4444")
                    glow.setAlpha(60)
                    painter.setBrush(glow)
                    painter.drawEllipse(QPointF(cx, cy), dot_radius * 1.4, dot_radius * 1.4)

                    painter.setBrush(active_color)
                else:
                    painter.setBrush(inactive_color)

                painter.drawEllipse(QPointF(cx, cy), dot_radius, dot_radius)