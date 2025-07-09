import sys
import random
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QPen
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QGraphicsEffect


class MatrixRainEffect(QGraphicsEffect):
    def __init__(self, parent=None, font_size=14, update_interval=33):
        super().__init__(parent)
        self.font_size = font_size
        self.timer_interval = update_interval

        # 🎲 Mixed character set: ASCII, Katakana, glitch symbols
        ascii_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        katakana = "アァイィウヴエェオカキクケコサシスセソタチツテトナニヌネノ"
        glitch = "#$%&*@[]{}<>=+!?|\\/"
        self.characters = ascii_chars + katakana + glitch

        self.columns = 0
        self.drops = []
        self.speeds = []
        self.densities = []

        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self.timer_interval)

    def draw(self, painter):
        rect = self.boundingRect().toRect()
        width = rect.width()
        height = rect.height()

        if self.columns != width // self.font_size:
            self.columns = width // self.font_size
            self.drops = [random.randint(0, height // self.font_size)
                          for _ in range(self.columns)]
            self.speeds = [random.randint(1, 3) for _ in range(self.columns)]  # random speeds
            self.densities = [random.uniform(0.6, 1.0) for _ in range(self.columns)]  # column density

        # Fading trails
        fade_color = QColor(0, 0, 0, 50)
        painter.fillRect(rect, fade_color)

        for i in range(self.columns):
            col_density = self.densities[i]
            if random.random() > col_density:
                continue  # skip drawing for sparse columns

            char = random.choice(self.characters)
            x = i * self.font_size
            y = self.drops[i] * self.font_size

            # 🎲 Random font style: normal, bold, italic, bold+italic
            weight = QFont.Weight.Bold if random.random() < 0.5 else QFont.Weight.Normal
            italic = random.random() < 0.2
            font = QFont("Courier", self.font_size, weight, italic)
            painter.setFont(font) 

            # 🎨 Color: bright white head, neon green trails, random flicker
            if random.random() < 0.05:
                painter.setPen(QColor(255, 255, 255))  # flicker glitch (white)
            elif y == self.drops[i] * self.font_size:
                # Bright head with glow effect
                glow_color = QColor(180, 255, 180)
                pen = QPen(glow_color)
                pen.setWidth(2)
                painter.setPen(pen)
            else:
                painter.setPen(QColor(0, 255, 70))  # neon green trail

            painter.drawText(x, y, char)

            # Move drop down with variable speed
            self.drops[i] += self.speeds[i]
            if y > height and random.random() > 0.975:
                self.drops[i] = 0
                self.speeds[i] = random.randint(1, 3)
                self.densities[i] = random.uniform(0.6, 1.0)


# 🧪 Apply to any widget
if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_widget = QWidget()
    main_widget.setWindowTitle("MatrixRain QGraphicsEffect (Movie-Accurate)")
    main_widget.resize(800, 600)

    layout = QVBoxLayout(main_widget)
    label = QLabel("Movie-Accurate\nMatrix Rain Effect")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet("""
        QLabel {
            color: white;
            font-size: 24px;
            background: transparent;
        }
    """)
    layout.addWidget(label)

    # Apply the Matrix effect
    effect = MatrixRainEffect(font_size=14)
    main_widget.setGraphicsEffect(effect)

    main_widget.show()
    sys.exit(app.exec())
