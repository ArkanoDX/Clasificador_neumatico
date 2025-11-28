from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QTableWidget,
                             QTableWidgetItem, QHeaderView, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QImage, QPixmap
import matplotlib

matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# --- CLASE LIENZO (GRÁFICA) ---
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.fig.patch.set_facecolor('#F0F0F0')
        self.axes.set_facecolor('white')
        self.fig.subplots_adjust(left=0.10, right=0.95, top=0.90, bottom=0.15)
        super(MplCanvas, self).__init__(self.fig)


# --- VENTANA PRINCIPAL ---
class MonitorIndustrial(QMainWindow):
    # Señales para comunicar eventos a main.py
    command_signal = pyqtSignal(str)  # Enviar orden 'S', 'P', etc.

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Clasificación (Webcam USB)")
        self.setGeometry(100, 100, 1150, 700)
        self.setStyleSheet("background-color: #3b4252;")

        # Datos para gráfica
        self.x_data = [0]
        self.y_zone1, self.y_zone2, self.y_zone3 = [0], [0], [0]
        self.counters = [0, 0, 0]
        self.event_index = 0

        self.setup_ui()
        self.init_graph()

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # Estilos
        panel_style = "QFrame { background-color: #F0F0F0; border-radius: 15px; border: 2px solid #5c8a8a; }"

        # --- IZQUIERDA: CÁMARA Y CONTROLES ---
        left_layout = QVBoxLayout()

        # Panel Cámara
        self.frame_cam = QFrame()
        self.frame_cam.setStyleSheet(panel_style)
        cam_layout = QVBoxLayout(self.frame_cam)

        lbl_title = QLabel("VISIÓN EN TIEMPO REAL")
        lbl_title.setFont(QFont("Arial", 14, QFont.Bold))
        lbl_title.setAlignment(Qt.AlignCenter)

        self.lbl_video = QLabel("INICIANDO CÁMARA...")
        self.lbl_video.setStyleSheet("background-color: black; border-radius: 10px; color: white;")
        self.lbl_video.setAlignment(Qt.AlignCenter)
        self.lbl_video.setScaledContents(True)

        cam_layout.addWidget(lbl_title)
        cam_layout.addWidget(self.lbl_video)

        # Controles
        controls_layout = QHBoxLayout()

        btn_stop = QPushButton("STOP")
        btn_stop.setFixedSize(100, 100)
        btn_stop.setStyleSheet("background-color: red; color: white; border-radius: 50px; font-weight: bold;")
        btn_stop.clicked.connect(lambda: self.command_signal.emit('P'))

        btn_start = QPushButton("START")
        btn_start.setFixedSize(120, 50)
        btn_start.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 10px;")
        btn_start.clicked.connect(lambda: self.command_signal.emit('S'))

        controls_layout.addWidget(btn_stop)
        controls_layout.addWidget(btn_start)

        left_layout.addWidget(self.frame_cam, stretch=3)
        left_layout.addLayout(controls_layout)

        # --- DERECHA: GRÁFICA Y TABLA ---
        right_layout = QVBoxLayout()

        # Gráfica
        self.frame_graph = QFrame()
        self.frame_graph.setStyleSheet(panel_style)
        graph_layout = QVBoxLayout(self.frame_graph)
        self.canvas = MplCanvas(self)
        graph_layout.addWidget(QLabel("ESTADÍSTICAS"))
        graph_layout.addWidget(self.canvas)

        # Tabla
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Hora", "Color", "Px", "Zona"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("background-color: white;")

        right_layout.addWidget(self.frame_graph, stretch=1)
        right_layout.addWidget(self.table, stretch=1)

        self.main_layout.addLayout(left_layout, stretch=6)
        self.main_layout.addLayout(right_layout, stretch=4)

    def init_graph(self):
        self.canvas.axes.clear()
        self.canvas.axes.grid(True, linestyle='--')
        self.canvas.draw()

    # SLOT: Actualizar imagen de video
    def update_image(self, qt_image):
        self.lbl_video.setPixmap(QPixmap.fromImage(qt_image))

    # SLOT: Actualizar datos (Llamado desde main)
    def update_data(self, hora, color, altura, zona):
        # Tabla
        self.table.insertRow(0)
        self.table.setItem(0, 0, QTableWidgetItem(hora))
        self.table.setItem(0, 1, QTableWidgetItem(color))
        self.table.setItem(0, 2, QTableWidgetItem(str(altura)))
        self.table.setItem(0, 3, QTableWidgetItem(str(zona)))

        # Gráfica
        try:
            z = int(zona)
            self.event_index += 1
            self.x_data.append(self.event_index)
            if z == 1:
                self.counters[0] += 1
            elif z == 2:
                self.counters[1] += 1
            elif z == 3:
                self.counters[2] += 1

            self.y_zone1.append(self.counters[0])
            self.y_zone2.append(self.counters[1])
            self.y_zone3.append(self.counters[2])

            # Limitar a últimos 20
            if len(self.x_data) > 20:
                self.x_data = self.x_data[-20:]
                self.y_zone1 = self.y_zone1[-20:]
                self.y_zone2 = self.y_zone2[-20:]
                self.y_zone3 = self.y_zone3[-20:]

            self.canvas.axes.clear()
            self.canvas.axes.grid(True, linestyle='--')
            self.canvas.axes.set_title("Conteo por Zonas")
            self.canvas.axes.plot(self.x_data, self.y_zone1, 'o-', label='Z1', color='blue')
            self.canvas.axes.plot(self.x_data, self.y_zone2, '^-', label='Z2', color='green')
            self.canvas.axes.plot(self.x_data, self.y_zone3, 's-', label='Z3', color='red')
            self.canvas.axes.legend()
            self.canvas.draw()
        except Exception:
            pass