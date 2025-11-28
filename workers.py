import cv2
import numpy as np
import serial
import time
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage


# ==========================================
# 1. WORKER DE VISIÓN (LÓGICA DE BANDA TRANSPORTADORA)
# ==========================================
class VisionWorker(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    detected_signal = pyqtSignal(str, int, int)

    def __init__(self, camera_index):
        super().__init__()
        self.camera_index = camera_index
        self.is_running = True

        # --- CALIBRACIÓN DE COLOR (HSV) ---
        # Ajusta esto para que solo vea tus piezas y no el fondo
        self.lower_blue = np.array([100, 150, 50])
        self.upper_blue = np.array([140, 255, 255])

        # --- CONFIGURACIÓN DE LA BANDA ---
        # Posición de la línea de disparo (Eje X, pixeles)
        # Ajusta esto para que coincida con el momento en que la pieza pasa frente a los sensores/pistones
        self.trigger_line_x = 320
        self.trigger_offset = 20  # Margen de error (+/- 20 px)

    def run(self):
        print(f"--> Iniciando Webcam (Índice {self.camera_index})...")
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)

        if not cap.isOpened():
            print(f"❌ ERROR: No se detectó cámara en el índice {self.camera_index}.")
            return

        print("✅ CÁMARA LISTA. Alinea la línea roja con tus actuadores.")

        last_trigger_time = 0

        while self.is_running:
            ret, frame = cap.read()
            if ret:
                frame = cv2.resize(frame, (640, 480))

                # 1. DIBUJAR LÍNEA DE DISPARO (Referencia visual)
                # Cuando la pieza toque esta línea roja, se activará el pistón
                cv2.line(frame, (self.trigger_line_x, 0), (self.trigger_line_x, 480), (0, 0, 255), 2)

                # 2. PROCESAMIENTO DE IMAGEN
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv, self.lower_blue, self.upper_blue)
                # Limpiar ruido
                mask = cv2.erode(mask, None, iterations=2)
                mask = cv2.dilate(mask, None, iterations=2)

                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for cnt in contours:
                    area = cv2.contourArea(cnt)

                    if area > 1500:  # Ignorar ruido pequeño
                        x, y, w, h = cv2.boundingRect(cnt)

                        # Calcular el CENTRO del objeto (Centroide)
                        cx = x + w // 2
                        cy = y + h // 2

                        # Dibujar caja y centro
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)

                        # --- LÓGICA DE DISPARO ---
                        # Si el centro del objeto cruza la línea de disparo (con un margen pequeño)
                        # Y ha pasado al menos 1 segundo desde la última activación (para no repetir)
                        if (
                                self.trigger_line_x - self.trigger_offset < cx < self.trigger_line_x + self.trigger_offset) and \
                                (time.time() - last_trigger_time > 1.0):

                            # CLASIFICACIÓN POR TAMAÑO (Altura en px)
                            zone = 0
                            if h < 80:
                                zone = 1  # Pequeña
                            elif h < 150:
                                zone = 2  # Mediana
                            else:
                                zone = 3  # Grande

                            print(f"⚡ DISPARO! Objeto en zona {zone} (Altura: {h}px)")

                            # Enviar señal
                            self.detected_signal.emit("AZUL", h, zone)
                            last_trigger_time = time.time()

                            # Efecto visual: Cambiar línea a Verde momentáneamente
                            cv2.line(frame, (self.trigger_line_x, 0), (self.trigger_line_x, 480), (0, 255, 0), 5)

                # Enviar a GUI
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                qt_img = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
                self.change_pixmap_signal.emit(qt_img)
            else:
                pass

        cap.release()

    def stop(self):
        self.is_running = False
        self.wait()


# ==========================================
# 2. WORKER SERIAL (Sin cambios, solo confirmando)
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
            print(f"✅ Conectado al ESP32 en {self.port}")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Error conectando al ESP32: {e}")

    def send_command(self, cmd):
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(cmd.encode())
            except:
                pass

    def stop(self):
        if self.serial_conn:
            self.serial_conn.close()