import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QFormLayout, QLineEdit, QPushButton, QLabel, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from config import DATOS_PROFE
from model import simular_bioproceso_shp


class CanvasGrafico(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(7, 5), dpi=100)
        super().__init__(self.fig)
        self.setParent(parent)

    def graficar_simulacion(self, t, X, S, t_corte):
        self.fig.clear()
        
        self.ax1 = self.fig.add_subplot(111)
        self.ax2 = self.ax1.twinx()

        # 1. EJE IZQUIERDO: BIOMASA (ax1)
        l1 = self.ax1.plot(t, X, 'r-', linewidth=2.5, label='Biomasa X (g/L)')
        self.ax1.set_xlabel('Tiempo de Proceso (Horas)', fontsize=10)
        self.ax1.set_ylabel('Biomasa (g/L)', color='red', fontsize=10)
        self.ax1.tick_params(axis='y', labelcolor='red')

        # 2. EJE DERECHO: CARGA ORGÁNICA DQO (ax2)
        l2 = self.ax2.plot(t, S, 'b--', linewidth=2.5, label='Carga Orgánica DQO (%)')
        self.ax2.set_ylabel('Carga Orgánica DQO (%)', color='blue', fontsize=10)
        self.ax2.tick_params(axis='y', labelcolor='blue')

        # Línea de transición SHP
        self.ax1.axvline(x=t_corte, color='gray', linestyle=':', linewidth=1.5)

        # Leyenda superior combinada
        lines = l1 + l2
        labels = [l.get_label() for l in lines]
        self.ax1.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, 1.14), ncol=2, fontsize=9)

        self.ax1.grid(True, alpha=0.3)

        self.fig.tight_layout()
        self.draw()


# CLASE PRINCIPAL DE LA VENTANA
class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modelo Mínimo SHP - Galdieria sulphuraria")
        self.setGeometry(100, 100, 1050, 600)

        # Widget central y Layout principal horizontal
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QHBoxLayout(widget_central)

        # --- PANEL IZQUIERDO: CONTROLES DE ENTRADA ---
        panel_izq = QVBoxLayout()
        
        # Grupo 1: Entradas (Medio de Vinaza)
        grupo_entradas = QGroupBox("Entradas: Caracterización Vinaza")
        form_entradas = QFormLayout()
        
        self.input_brix = QLineEdit(DATOS_PROFE["brix"])
        self.input_ph = QLineEdit(DATOS_PROFE["ph"])
        self.input_dqo_ini = QLineEdit(DATOS_PROFE["dqo_ini"])
        self.input_dqo_fin = QLineEdit(DATOS_PROFE["dqo_fin"])
        
        form_entradas.addRow("Concentración (°Brix):", self.input_brix)
        form_entradas.addRow("pH inicial:", self.input_ph)
        form_entradas.addRow("DQO Inicial (%):", self.input_dqo_ini)
        form_entradas.addRow("DQO Target Final (%):", self.input_dqo_fin)
        grupo_entradas.setLayout(form_entradas)
        panel_izq.addWidget(grupo_entradas)

        # Grupo 2: Proceso (Tiempos SHP)
        grupo_proceso = QGroupBox("Proceso: Tiempos de Fase (SHP)")
        form_proceso = QFormLayout()
        
        self.input_t_het = QLineEdit(DATOS_PROFE["tiempo_het"])
        self.input_t_fot = QLineEdit(DATOS_PROFE["tiempo_fot"])
        
        form_proceso.addRow("Horas Heterotrofía:", self.input_t_het)
        form_proceso.addRow("Horas Fotoinducción:", self.input_t_fot)
        grupo_proceso.setLayout(form_proceso)
        panel_izq.addWidget(grupo_proceso)

        # Botones
        self.btn_ejecutar = QPushButton("Simular Bioproceso")
        self.btn_ejecutar.setStyleSheet("background-color: #d1e7dd; font-weight: bold; padding: 8px;")
        self.btn_ejecutar.clicked.connect(self.ejecutar_simulacion)
        panel_izq.addWidget(self.btn_ejecutar)

        self.btn_reset = QPushButton("Cargar Datos por defecto (profe)")
        self.btn_reset.clicked.connect(self.restaurar_datos)
        panel_izq.addWidget(self.btn_reset)

        # Resultado numérico
        self.label_res = QLabel("Estado: Esperando simulación...")
        self.label_res.setWordWrap(True)
        panel_izq.addWidget(self.label_res)
        panel_izq.addStretch()

        # --- PANEL DERECHO: GRÁFICO EMBEBIDO ---
        panel_der = QVBoxLayout()
        self.canvas = CanvasGrafico(self)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        panel_der.addWidget(self.toolbar)
        panel_der.addWidget(self.canvas)

        # Agregar paneles al layout principal
        layout_principal.addLayout(panel_izq, 35)  # 35% ancho
        layout_principal.addLayout(panel_der, 65)  # 65% ancho

        # Ejecutar simulación inicial al abrir
        self.ejecutar_simulacion()

    def ejecutar_simulacion(self):
        try:
            dqo_ini = float(self.input_dqo_ini.text())
            dqo_fin = float(self.input_dqo_fin.text())
            t_het = float(self.input_t_het.text())
            t_fot = float(self.input_t_fot.text())
            ph = float(self.input_ph.text())
            brix = float(self.input_brix.text())

            # Pasa ph y brix al modelo
            t, X, S = simular_bioproceso_shp(dqo_ini, dqo_fin, t_het, t_fot, ph, brix)
            self.canvas.graficar_simulacion(t, X, S, t_het)

            dqo_simulada_final = S[-1]                        # Lo que calculó la EDO
            dqo_real_final = float(self.input_dqo_fin.text()) # El dato de entrada/referencia

            error_absoluto = abs(dqo_simulada_final - dqo_real_final)

            self.label_res.setText(
                f"<b>Resultados del Modelo:</b><br>"
                f"• DQO Final Simulada: <b>{dqo_simulada_final:.2f}%</b><br>"
                f"• DQO Final Meta (Lab): <b>{dqo_real_final:.2f}%</b><br>"
                f"• Desviación del Modelo: <b>{error_absoluto:.2f}%</b>"
            )

        except ValueError:
            QMessageBox.critical(self, "Error de entrada", "Por favor ingresa números válidos en todos los campos.")

    def restaurar_datos(self):
        self.input_brix.setText(DATOS_PROFE["brix"])
        self.input_ph.setText(DATOS_PROFE["ph"])
        self.input_dqo_ini.setText(DATOS_PROFE["dqo_ini"])
        self.input_dqo_fin.setText(DATOS_PROFE["dqo_fin"])
        self.input_t_het.setText(DATOS_PROFE["tiempo_het"])
        self.input_t_fot.setText(DATOS_PROFE["tiempo_fot"])
        self.ejecutar_simulacion()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec_())