import cv2
import numpy as np
import serial
import time
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage


# ==========================================
# 1. WORKER DE VISIÓN
# ==========================================
class VisionWorker(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    detected_signal = pyqtSignal(str, int, int)

    def __init__(self, camera_index):
        super().__init__()
        self.camera_index = camera_index
        self.is_running = True

        # Posición de la línea roja (ajustable según tu cámara)
        self.trigger_line_x = 320
        self.trigger_offset = 20

        # DICCIONARIO DE COLORES
        self.colors = {
            "AZUL": (
                np.array([100, 150, 50]),
                np.array([140, 255, 255])
            ),
            "VERDE": (
                np.array([40, 100, 100]),
                np.array([90, 255, 255])
            ),
            "NARANJA": (
                # Rango ajustado para tonos rojizos/amarillentos
                np.array([0, 186, 118]),
                np.array([28, 255, 255])
            )
        }

    def run(self):
        # Iniciar captura (DSHOW ayuda en Windows a que cargue más rápido)
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        last_trigger_time = 0

        while self.is_running:
            ret, frame = cap.read()
            if ret:
                frame = cv2.resize(frame, (640, 480))

                # Dibujar línea de disparo (Referencia visual) [cite: 6]
                cv2.line(frame, (self.trigger_line_x, 0), (self.trigger_line_x, 480), (0, 0, 255), 2)
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

                # Procesar cada color
                for color_name, (lower, upper) in self.colors.items():
                    mask = cv2.inRange(hsv, lower, upper)
                    # Limpieza de ruido
                    mask = cv2.erode(mask, None, iterations=2)
                    mask = cv2.dilate(mask, None, iterations=2)

                    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    for cnt in contours:
                        area = cv2.contourArea(cnt)
                        # Filtrar objetos muy pequeños
                        
                        if area > 1500:
                            x, y, w, h = cv2.boundingRect(cnt)
                            cx = x + w // 2

                            # --- DIBUJAR CAJA ---
                            box_color = (0, 255, 0)
                            if color_name == "AZUL": box_color = (255, 0, 0)
                            
                            if color_name == "NARANJA": box_color = (0, 165, 255)

                            cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)
                            cv2.putText(frame, color_name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)

                            # --- LÓGICA DE DISPARO POR COLOR ---
                            # Verificar si el centro del objeto (cx) cruza la línea de disparo
                            if (
                                    self.trigger_line_x - self.trigger_offset < cx < self.trigger_line_x + self.trigger_offset) and \
                                    (time.time() - last_trigger_time > 1.5):  # [cite: 12]
                                zone = 0

                                if color_name == "NARANJA":
                                    zone = 1  # Activa Relé 1 (Arduino PIN 4)
                                elif color_name == "VERDE":
                                    zone = 2  # Activa Relé 2 (Arduino PIN 12)
                                elif color_name == "AZUL":
                                    zone = 3  # Zona final (Arduino ignorará el comando '3')

                                print(f"⚡ DISPARO: {color_name} -> Zona {zone}")

                                # Emitir señal a Main para que envíe el comando serial
                                
                                self.detected_signal.emit(color_name, h, zone)  # [cite: 17]

                                last_trigger_time = time.time()

                                # Feedback visual: Línea verde momentánea
                                cv2.line(frame, (self.trigger_line_x, 0), (self.trigger_line_x, 480), (0, 255, 0), 5)

                # --- ENVIAR IMAGEN A LA GUI ---
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                qt_img = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
                
                self.change_pixmap_signal.emit(qt_img)

        cap.release()

    def stop(self):
        self.is_running = False
        self.wait()


# ==========================================
# 2. WORKER SERIAL (CONTROLADOR)
# ==========================================
class SerialController(QThread):
    def __init__(self, port, baudrate=115200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None

    def run(self):
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            
            print(f"✅ Arduino conectado en {self.port}")  # [cite: 19-20]
            time.sleep(2)
        except Exception as e:
            print(f"❌ Error Arduino: {e}")

    def send_command(self, cmd):
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(cmd.encode())
            except:
                pass

    def stop(self):
        if self.serial_conn:
            self.serial_conn.close()