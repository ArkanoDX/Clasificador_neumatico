import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QFrame,
                             QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class MonitorIndustrial(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sistema de Clasificación")
        self.setGeometry(100, 100, 1150, 700)

        # Estilo Global
        self.setStyleSheet("background-color: #B0B0B0;")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # === LAYOUT PRINCIPAL ===
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        # Estilo de paneles
        self.panel_style = """
            QFrame {
                background-color: #F0F0F0;
                border-radius: 15px;
                border: 2px solid #5c8a8a;
            }
        """

        # ==========================================================
        # 1. COLUMNA IZQUIERDA (CÁMARA + CONTROLES)
        # ==========================================================
        self.left_column = QVBoxLayout()

        # --- A. Cámara ---
        self.frame_camera = QFrame()
        self.frame_camera.setStyleSheet(self.panel_style)
        self.camera_layout = QVBoxLayout(self.frame_camera)

        lbl_cam_title = QLabel("VISIÓN DE LA CÁMARA")
        lbl_cam_title.setAlignment(Qt.AlignCenter)
        lbl_cam_title.setFont(QFont("Arial", 14, QFont.Bold))
        lbl_cam_title.setStyleSheet("border: none; color: #333;")
        lbl_cam_title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)  # Título fijo

        self.lbl_video = QLabel()
        self.lbl_video.setStyleSheet("background-color: black; border-radius: 10px; border: 2px solid #333;")
        self.lbl_video.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.camera_layout.addWidget(lbl_cam_title)
        self.camera_layout.addWidget(self.lbl_video)

        # --- B. Controles ---
        self.controls_container = QFrame()
        self.controls_container.setStyleSheet("background-color: transparent; border: none;")
        self.controls_layout = QHBoxLayout(self.controls_container)

        # Botón STOP
        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setFixedSize(130, 130)
        self.btn_stop.setFont(QFont("Arial", 18, QFont.Bold))
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #ff0000; color: white; border-radius: 65px; border: 4px solid #cc0000;
            }
            QPushButton:pressed { background-color: #b30000; }
        """)

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

        self.btn_off = QPushButton("APAGADO")
        self.btn_off.setStyleSheet(btn_style_small)
        self.btn_off.setFixedSize(140, 50)

        self.btns_io_layout.addWidget(self.btn_on)
        self.btns_io_layout.addSpacing(10)
        self.btns_io_layout.addWidget(self.btn_off)

        self.controls_layout.addWidget(self.btn_stop)
        self.controls_layout.addSpacing(30)
        self.controls_layout.addLayout(self.btns_io_layout)
        self.controls_layout.addStretch()

        self.left_column.addWidget(self.frame_camera, stretch=4)
        self.left_column.addSpacing(15)
        self.left_column.addWidget(self.controls_container, stretch=1)

        # ==========================================================
        # 2. COLUMNA DERECHA (GRÁFICA + HISTORIAL + EXIT)
        # ==========================================================
        self.right_column = QVBoxLayout()
        self.right_column.setSpacing(15)

        # --- C. Panel Gráfica (MODIFICADO) ---
        self.frame_graph = QFrame()
        self.frame_graph.setStyleSheet(self.panel_style)
        self.graph_layout = QVBoxLayout(self.frame_graph)
        # Reducimos márgenes internos para aprovechar espacio
        self.graph_layout.setContentsMargins(10, 10, 10, 10)

        lbl_graph_title = QLabel("GRÁFICA DE PIEZAS CLASIFICADAS")
        lbl_graph_title.setAlignment(Qt.AlignCenter)
        lbl_graph_title.setFont(QFont("Arial", 12, QFont.Bold))
        lbl_graph_title.setStyleSheet("border: none; color: #333;")
        # Importante: El título no debe crecer, solo ocupar lo necesario
        lbl_graph_title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.graph_placeholder = QLabel("(Aquí se mostrará la Gráfica en vivo)")
        self.graph_placeholder.setAlignment(Qt.AlignCenter)
        self.graph_placeholder.setStyleSheet(
            "border: 1px dashed #999; color: #666; background-color: white; border-radius: 5px;")

        # CAMBIO CLAVE: Política de expansión para llenar todo el hueco
        self.graph_placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.graph_layout.addWidget(lbl_graph_title)
        self.graph_layout.addWidget(self.graph_placeholder)

        # --- D. Panel Historial ---
        self.frame_history = QFrame()
        self.frame_history.setStyleSheet(self.panel_style)
        self.history_layout = QVBoxLayout(self.frame_history)
        self.history_layout.setContentsMargins(10, 10, 10, 10)

        lbl_hist_title = QLabel("HISTORIAL DE PIEZAS")
        lbl_hist_title.setAlignment(Qt.AlignCenter)
        lbl_hist_title.setFont(QFont("Arial", 12, QFont.Bold))
        lbl_hist_title.setStyleSheet("border: none; color: #333;")
        lbl_hist_title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Tiempo", "Clasificación", "Zona"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("background-color: white; border: 1px solid #ccc;")

        # Datos de ejemplo
        self.table.setRowCount(1)
        self.table.setItem(0, 0, QTableWidgetItem("10:05:23"))
        self.table.setItem(0, 1, QTableWidgetItem("Caja Grande"))
        self.table.setItem(0, 2, QTableWidgetItem("Zona 3"))

        self.history_layout.addWidget(lbl_hist_title)
        self.history_layout.addWidget(self.table)

        # --- E. Botón Exit ---
        self.exit_layout = QHBoxLayout()
        self.btn_exit = QPushButton("EXIT")
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

        # Agregar paneles derecha
        self.right_column.addWidget(self.frame_graph, stretch=1)
        self.right_column.addWidget(self.frame_history, stretch=1)
        self.right_column.addLayout(self.exit_layout)

        # Unir Todo
        self.main_layout.addLayout(self.left_column, stretch=5)
        self.main_layout.addLayout(self.right_column, stretch=4)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MonitorIndustrial()
    window.show()
    sys.exit(app.exec_())