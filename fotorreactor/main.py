import sys
from PyQt5.QtWidgets import QApplication
from gui_fotorreactor import VentanaSimulacion

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ventana = VentanaSimulacion()
    ventana.show()
    sys.exit(app.exec_())
    