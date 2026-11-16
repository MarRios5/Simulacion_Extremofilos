import sys
import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QSlider, QPushButton, QFrame, QApplication)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Importamos las matemáticas desde nuestro archivo modelo.py
from modelo import calcular_tasas

plt.style.use('dark_background')

class CanvasFotorreactor(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(250, 350)
        self.setStyleSheet("background-color: #111827; border-radius: 12px;")
        self.nivel_contaminacion = 1.0
        self.concentracion_biomasa = 0.1
        self.temperatura = 45.0

    def actualizar_estado(self, dqo, biomasa, temp):
        self.nivel_contaminacion = max(0.0, min(1.0, dqo / 18.0))
        self.concentracion_biomasa = min(1.0, biomasa / 5.0)
        self.temperatura = temp
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Luces del reactor (Rosado)
        painter.setPen(QPen(QColor('#EC4899'), 4))
        painter.setBrush(QBrush(QColor(236, 72, 153, 30)))
        painter.drawRoundedRect(15, 50, 15, h - 100, 5, 5)
        painter.drawRoundedRect(w - 30, 50, 15, h - 100, 5, 5)

        # Tanque (Azul cielo)
        rx, ry, rw, rh = 45, 40, w - 90, h - 80
        painter.setPen(QPen(QColor('#38BDF8'), 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rx, ry, rw, rh, 15, 15)

        # Líquido (Café a Azul Limpio)
        r_col = int(120 * self.nivel_contaminacion + 14 * (1 - self.nivel_contaminacion))
        g_col = int(60 * self.nivel_contaminacion + 165 * (1 - self.nivel_contaminacion))
        b_col = int(30 * self.nivel_contaminacion + 233 * (1 - self.nivel_contaminacion))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(r_col, g_col, b_col, 200)))
        painter.drawRoundedRect(rx + 4, ry + 20, rw - 8, rh - 24, 10, 10)

        # Células (Morado)
        num_celulas = int(self.concentracion_biomasa * 80) + 5
        np.random.seed(42)
        painter.setBrush(QBrush(QColor('#A855F7')))
        for _ in range(num_celulas):
            cx = np.random.randint(rx + 10, rx + rw - 10)
            cy = np.random.randint(ry + 30, ry + rh - 10)
            painter.drawEllipse(cx, cy, 6, 6)

        painter.setPen(QPen(QColor('white')))
        painter.drawText(rx + 10, ry - 10, f"FOTORREACTOR: {self.temperatura:.1f} °C")

class VentanaSimulacion(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulación de Fotorreactor - Extremófilos")
        self.setGeometry(100, 100, 1050, 650)
        self.setStyleSheet("background-color: #0F172A; color: white;")

        self.tiempo_actual, self.dt = 0.0, 0.1
        self.biomasa, self.dqo, self.temperatura = 0.15, 18.0, 45.0
        self.h_tiempo, self.h_biomasa, self.h_dqo = [], [], []

        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout()
        left_box = QVBoxLayout()

        self.reactor_widget = CanvasFotorreactor()
        left_box.addWidget(self.reactor_widget)

        self.slider_temp = QSlider(Qt.Horizontal)
        self.slider_temp.setRange(15, 60)
        self.slider_temp.setValue(45)
        self.slider_temp.valueChanged.connect(self.cambiar_temp)
        left_box.addWidget(QLabel("Temperatura (°C):"))
        left_box.addWidget(self.slider_temp)

        btn_run = QPushButton("▶ Iniciar Simulación")
        btn_run.setStyleSheet("background-color: #EC4899; font-weight: bold; padding: 8px; border-radius: 6px;")
        btn_run.clicked.connect(self.toggle_sim)
        left_box.addWidget(btn_run)

        # Gráficas
        right_box = QVBoxLayout()
        self.fig = Figure(figsize=(6, 6), facecolor='#0F172A')
        self.canvas = FigureCanvas(self.fig)
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)
        right_box.addWidget(self.canvas)

        left_container, right_container = QWidget(), QWidget()
        left_container.setLayout(left_box)
        right_container.setLayout(right_box)
        main_layout.addWidget(left_container, stretch=1)
        main_layout.addWidget(right_container, stretch=2)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.paso_sim)

    def cambiar_temp(self):
        self.temperatura = float(self.slider_temp.value())

    def toggle_sim(self):
        if self.timer.isActive(): self.timer.stop()
        else: self.timer.start()

    def paso_sim(self):
        if self.dqo <= 0.1 or self.tiempo_actual >= 12.0:
            self.timer.stop()
            return

        dB, dD = calcular_tasas(self.biomasa, self.dqo, self.temperatura)
        self.biomasa += dB * self.dt
        self.dqo = max(0.0, self.dqo + dD * self.dt)
        self.tiempo_actual += self.dt

        self.h_tiempo.append(self.tiempo_actual)
        self.h_biomasa.append(self.biomasa)
        self.h_dqo.append(self.dqo)

        self.reactor_widget.actualizar_estado(self.dqo, self.biomasa, self.temperatura)

        self.ax1.clear(); self.ax2.clear()
        self.ax1.set_facecolor('#1E293B'); self.ax2.set_facecolor('#1E293B')
        self.ax1.plot(self.h_tiempo, self.h_biomasa, color='#EC4899', linewidth=2.5) # Rosado
        self.ax2.plot(self.h_tiempo, self.h_dqo, color='#38BDF8', linewidth=2.5)     # Azul
        self.ax1.set_title("Biomasa (g/L)", color='white')
        self.ax2.set_title("Vinaza / DQO (g/L)", color='white')
        self.canvas.draw()