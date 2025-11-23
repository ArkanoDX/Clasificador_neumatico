import sys
import time
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QFrame,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# --- IMPORTACIONES PARA LA GRÁFICA (MATPLOTLIB) ---
import matplotlib

matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# ==========================================================
# 1. CLASE CANVAS (LIENZO DE LA GRÁFICA)
# ==========================================================
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # Creamos la figura
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        # Ajustamos el color de fondo para que coincida con el panel (#F0F0F0)
        self.fig.patch.set_facecolor('#F0F0F0')
        self.axes.set_facecolor('white')  # El área de la gráfica en blanco

        # Ajustar márgenes para aprovechar el espacio del panel
        self.fig.subplots_adjust(left=0.10, right=0.95, top=0.90, bottom=0.15)

        super(MplCanvas, self).__init__(self.fig)


# ==========================================================
# 2. CLASE WORKER (HILO SERIAL)
# ==========================================================
class SerialWorker(QThread):
    data_received = pyqtSignal(str, str, str, str)

    def __init__(self, port, baudrate=115200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.is_running = True
        self.serial_conn = None

    def run(self):
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)
            while self.is_running:
                if self.serial_conn and self.serial_conn.in_waiting:
                    try:
                        line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                        if line.startswith("DATA"):
                            parts = line.split(',')
                            if len(parts) == 4:
                                current_time = time.strftime("%H:%M:%S")
                                self.data_received.emit(current_time, parts[1], parts[2], parts[3])
                    except:
                        pass
                time.sleep(0.01)
        except:
            pass

    def send_command(self, command):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.write(command.encode())

    def stop(self):
        self.is_running = False
        if self.serial_conn: self.serial_conn.close()
        self.quit()


# ==========================================================
# 3. GUI PRINCIPAL (ESTILO ORIGINAL RESTAURADO)
# ==========================================================
class MonitorIndustrial(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sistema de Clasificación Neumático")
        self.setGeometry(100, 100, 1150, 700)

        # --- DATOS DE LA GRÁFICA ---
        self.x_data = [0]
        self.y_zone1 = [0]  # Azul
        self.y_zone2 = [0]  # Verde
        self.y_zone3 = [0]  # Rojo
        self.counters = [0, 0, 0]  # Z1, Z2, Z3
        self.event_index = 0

        # --- SERIAL ---
        self.serial_port = 'COM3'  # <--- AJUSTA TU PUERTO AQUÍ
        self.thread = SerialWorker(self.serial_port)
        self.thread.data_received.connect(self.update_system)
        self.thread.start()

        # --- ESTILOS GLOBALES (Del código original) ---
        # Fondo general oscuro/grisáceo como en tu imagen
        self.setStyleSheet("background-color: #3b4252;")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout Principal
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        # Estilo de Paneles (Bordes redondeados y fondo claro)
        self.panel_style = """
            QFrame {
                background-color: #F0F0F0;
                border-radius: 15px;
                border: 2px solid #5c8a8a;
            }
        """

        self.setup_ui()
        self.init_graph()  # Inicializar gráfica

    def setup_ui(self):
        # ==========================================================
        # COLUMNA IZQUIERDA (CÁMARA + CONTROLES) - Stretch 5
        # ==========================================================
        self.left_column = QVBoxLayout()

        # --- Panel Cámara ---
        self.frame_camera = QFrame()
        self.frame_camera.setStyleSheet(self.panel_style)
        self.camera_layout = QVBoxLayout(self.frame_camera)

        lbl_cam_title = QLabel("VISIÓN DE LA CÁMARA")
        lbl_cam_title.setAlignment(Qt.AlignCenter)
        lbl_cam_title.setFont(QFont("Arial", 14, QFont.Bold))
        lbl_cam_title.setStyleSheet("border: none; color: #333;")

        self.lbl_video = QLabel("NO VIDEO SIGNAL")
        self.lbl_video.setStyleSheet(
            "background-color: black; border-radius: 10px; border: 2px solid #333; color: white;")
        self.lbl_video.setAlignment(Qt.AlignCenter)
        self.lbl_video.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.camera_layout.addWidget(lbl_cam_title)
        self.camera_layout.addWidget(self.lbl_video)

        # --- Panel Controles ---
        self.controls_container = QFrame()
        self.controls_container.setStyleSheet("background-color: transparent; border: none;")
        self.controls_layout = QHBoxLayout(self.controls_container)

        # Botón STOP (Estilo circular original)
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setFixedSize(130, 130)
        self.btn_stop.setFont(QFont("Arial", 18, QFont.Bold))
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #ff0000; color: white; border-radius: 65px; border: 4px solid #cc0000;
            }
            QPushButton:pressed { background-color: #b30000; }
        """)
        self.btn_stop.clicked.connect(lambda: self.thread.send_command('P'))

        # Botones ON/OFF
        self.btns_io_layout = QVBoxLayout()
        btn_style_small = """
            QPushButton {
                background-color: #e6e6e6; border: 2px solid #5c8a8a; 
                border-radius: 8px; font-size: 14px; padding: 10px; color: black;
            }
            QPushButton:hover { background-color: #d9d9d9; }
            QPushButton:pressed { background-color: #bfbfbf; }
        """
        self.btn_on = QPushButton("ENCENDIDO")
        self.btn_on.setStyleSheet(btn_style_small)
        self.btn_on.setFixedSize(140, 50)
        self.btn_on.clicked.connect(lambda: self.thread.send_command('S'))

        self.btn_off = QPushButton("APAGADO")
        self.btn_off.setStyleSheet(btn_style_small)
        self.btn_off.setFixedSize(140, 50)
        self.btn_off.clicked.connect(lambda: self.thread.send_command('P'))

        self.btns_io_layout.addWidget(self.btn_on)
        self.btns_io_layout.addSpacing(10)
        self.btns_io_layout.addWidget(self.btn_off)

        self.controls_layout.addWidget(self.btn_stop)
        self.controls_layout.addSpacing(30)
        self.controls_layout.addLayout(self.btns_io_layout)
        self.controls_layout.addStretch()

        # Agregamos a la columna izquierda con las proporciones originales
        self.left_column.addWidget(self.frame_camera, stretch=4)
        self.left_column.addSpacing(15)
        self.left_column.addWidget(self.controls_container, stretch=1)

        # ==========================================================
        # COLUMNA DERECHA (GRÁFICA + HISTORIAL) - Stretch 4
        # ==========================================================
        self.right_column = QVBoxLayout()
        self.right_column.setSpacing(15)

        # --- Panel Gráfica (AQUÍ ESTÁ EL CAMBIO IMPORTANTE) ---
        self.frame_graph = QFrame()
        self.frame_graph.setStyleSheet(self.panel_style)
        self.graph_layout = QVBoxLayout(self.frame_graph)
        self.graph_layout.setContentsMargins(10, 10, 10, 10)

        lbl_graph_title = QLabel("GRÁFICA EN VIVO")
        lbl_graph_title.setAlignment(Qt.AlignCenter)
        lbl_graph_title.setFont(QFont("Arial", 12, QFont.Bold))
        lbl_graph_title.setStyleSheet("border: none; color: #333;")

        # INSERTAMOS EL CANVAS DE MATPLOTLIB
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.graph_layout.addWidget(lbl_graph_title)
        self.graph_layout.addWidget(self.canvas)

        # --- Panel Historial ---
        self.frame_history = QFrame()
        self.frame_history.setStyleSheet(self.panel_style)
        self.history_layout = QVBoxLayout(self.frame_history)
        self.history_layout.setContentsMargins(10, 10, 10, 10)

        lbl_hist_title = QLabel("HISTORIAL DE CLASIFICACIÓN")
        lbl_hist_title.setAlignment(Qt.AlignCenter)
        lbl_hist_title.setFont(QFont("Arial", 12, QFont.Bold))
        lbl_hist_title.setStyleSheet("border: none; color: #333;")

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Hora", "Color", "Altura", "Zona"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("background-color: white; border: 1px solid #ccc;")

        self.history_layout.addWidget(lbl_hist_title)
        self.history_layout.addWidget(self.table)

        # --- Botón Salir ---
        self.exit_layout = QHBoxLayout()
        self.btn_exit = QPushButton("SALIR")
        self.btn_exit.setFixedSize(100, 40)
        self.btn_exit.setStyleSheet("""
            QPushButton {
                background-color: white; border: 1px solid gray; border-radius: 5px; color: black;
            }
            QPushButton:hover { background-color: #ffcccc; border-color: red; }
        """)
        self.btn_exit.clicked.connect(self.close)
        self.exit_layout.addStretch()
        self.exit_layout.addWidget(self.btn_exit)

        # Agregamos a la columna derecha con PROPORCIONES 1 a 1 (como en la foto)
        self.right_column.addWidget(self.frame_graph, stretch=1)
        self.right_column.addWidget(self.frame_history, stretch=1)
        self.right_column.addLayout(self.exit_layout)

        # ==========================================================
        # UNIR TODO
        # ==========================================================
        # Respetamos el ratio 5:4 del código original
        self.main_layout.addLayout(self.left_column, stretch=5)
        self.main_layout.addLayout(self.right_column, stretch=4)

    # ==========================================================
    # LÓGICA GRÁFICA Y DATOS
    # ==========================================================
    def init_graph(self):
        self.canvas.axes.clear()
        self.canvas.axes.grid(True, linestyle='--', alpha=0.6)

        # Plot inicial (vacío)
        self.canvas.axes.plot(self.x_data, self.y_zone1, 'o-', label='Z1 (Azul)', color='tab:blue')
        self.canvas.axes.plot(self.x_data, self.y_zone2, '^-', label='Z2 (Verde)', color='tab:green')
        self.canvas.axes.plot(self.x_data, self.y_zone3, 's-', label='Z3 (Rojo)', color='tab:red')

        self.canvas.axes.legend(loc='upper left', fontsize='small')
        self.canvas.draw()

    def update_system(self, tiempo, color, altura, zona_str):
        # 1. Tabla
        self.table.insertRow(0)
        self.table.setItem(0, 0, QTableWidgetItem(tiempo))
        self.table.setItem(0, 1, QTableWidgetItem(color))
        self.table.setItem(0, 2, QTableWidgetItem(altura))
        self.table.setItem(0, 3, QTableWidgetItem(f"Zona {zona_str}"))

        # 2. Gráfica
        try:
            zona = int(zona_str)
            self.event_index += 1
            self.x_data.append(self.event_index)

            # Aumentar contadores
            if zona == 1:
                self.counters[0] += 1
            elif zona == 2:
                self.counters[1] += 1
            elif zona == 3:
                self.counters[2] += 1

            self.y_zone1.append(self.counters[0])
            self.y_zone2.append(self.counters[1])
            self.y_zone3.append(self.counters[2])

            # Mantener ventana de tiempo (últimos 20 eventos)
            if len(self.x_data) > 20:
                self.x_data = self.x_data[-20:]
                self.y_zone1 = self.y_zone1[-20:]
                self.y_zone2 = self.y_zone2[-20:]
                self.y_zone3 = self.y_zone3[-20:]

            # Redibujar
            self.canvas.axes.clear()
            self.canvas.axes.grid(True, linestyle='--', alpha=0.6)
            self.canvas.axes.set_title("Conteo por Zonas", fontsize=10)

            self.canvas.axes.plot(self.x_data, self.y_zone1, marker='D', linestyle='-', color='#1f77b4', label='Z1')
            self.canvas.axes.plot(self.x_data, self.y_zone2, marker='^', linestyle='-', color='#2ca02c', label='Z2')
            self.canvas.axes.plot(self.x_data, self.y_zone3, marker='o', linestyle='-', color='#d62728', label='Z3')

            self.canvas.axes.legend(loc='upper left', fontsize='small')
            self.canvas.draw()

        except ValueError:
            pass

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MonitorIndustrial()
    window.show()
    sys.exit(app.exec_())