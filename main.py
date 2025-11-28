import sys
import time
from PyQt5.QtWidgets import QApplication
from gui_interface import MonitorIndustrial
from workers import VisionWorker, SerialController

# ==========================================
# CONFIGURACIÓN DEL SISTEMA
# ==========================================
CAMERA_INDEX = 0  # Prueba con 0 o 1 si no sale tu cámara USB
PUERTO_ESP_CONTROL = 'COM5'  # <--- ¡Revisa en el Administrador de Dispositivos!


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = MonitorIndustrial()

        print("Iniciando sistema...")

        # 1. Iniciar VISIÓN (Cámara USB)
        self.vision = VisionWorker(CAMERA_INDEX)

        # 2. Iniciar CONTROL (ESP32 por Serial)
        self.controller = SerialController(PUERTO_ESP_CONTROL)
        self.controller.start()

        # --- CONEXIONES ENTRE MÓDULOS ---

        # A) Ver el video en la pantalla
        self.vision.change_pixmap_signal.connect(self.window.update_image)

        # B) Si Vision detecta algo -> Avisar a Main para que decida qué hacer
        self.vision.detected_signal.connect(self.handle_detection)

        # C) Si aprietas botones en la GUI -> Mandar orden al ESP32
        self.window.command_signal.connect(self.controller.send_command)

        # ¡Arrancar la cámara!
        self.vision.start()

        self.window.show()
        sys.exit(self.app.exec_())

    def handle_detection(self, color, altura, zona):
        print(f"¡DETECTADO! Zona: {zona} | Altura: {altura}")

        # 1. Mandar la orden física al ESP32
        # Convertimos el número de zona (int) a texto ('1', '2', '3')
        comando = str(zona)
        self.controller.send_command(comando)

        # 2. Actualizar la tabla y gráfica en la pantalla
        hora = time.strftime("%H:%M:%S")
        self.window.update_data(hora, color, altura, zona)


if __name__ == "__main__":
    MainApp()