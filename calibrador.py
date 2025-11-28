import cv2
import numpy as np


def nothing(x):
    pass


# Inicializar cámara (Usa 0 o 1 según tu cámara USB)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# Crear una ventana para los controles
cv2.namedWindow('Calibrador de Color')

# --- VALORES INICIALES (Para Naranja) ---
# Hue (Color): 0 - 179
# Sat (Intensidad): 0 - 255
# Val (Brillo): 0 - 255

# Creación de Trackbars
cv2.createTrackbar('H Min', 'Calibrador de Color', 0, 179, nothing)
cv2.createTrackbar('S Min', 'Calibrador de Color', 80, 255, nothing)
cv2.createTrackbar('V Min', 'Calibrador de Color', 80, 255, nothing)

cv2.createTrackbar('H Max', 'Calibrador de Color', 28, 179, nothing)
cv2.createTrackbar('S Max', 'Calibrador de Color', 255, 255, nothing)
cv2.createTrackbar('V Max', 'Calibrador de Color', 255, 255, nothing)

print("Instrucciones:")
print("1. Mueve las barras hasta que tu objeto sea BLANCO y el fondo NEGRO.")
print("2. Anota los valores de Min y Max.")
print("3. Presiona 'q' para salir.")

while True:
    ret, frame = cap.read()
    if not ret: break

    frame = cv2.resize(frame, (640, 480))

    # Convertir a HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Leer valores de las barras
    h_min = cv2.getTrackbarPos('H Min', 'Calibrador de Color')
    s_min = cv2.getTrackbarPos('S Min', 'Calibrador de Color')
    v_min = cv2.getTrackbarPos('V Min', 'Calibrador de Color')

    h_max = cv2.getTrackbarPos('H Max', 'Calibrador de Color')
    s_max = cv2.getTrackbarPos('S Max', 'Calibrador de Color')
    v_max = cv2.getTrackbarPos('V Max', 'Calibrador de Color')

    # Crear arrays para el rango
    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])

    # Crear máscara
    mask = cv2.inRange(hsv, lower, upper)

    # Mostrar resultado (Bitwise AND para ver el color real filtrado)
    result = cv2.bitwise_and(frame, frame, mask=mask)

    # Mostrar ventanas
    # cv2.imshow('Original', frame) # Descomenta si quieres ver el original también
    cv2.imshow('MASCARA (Blanco = Detectado)', mask)
    cv2.imshow('Resultado Color', result)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print(f"\n--- TUS VALORES FINALES ---")
        print(f"LOWER (Min): np.array([{h_min}, {s_min}, {v_min}])")
        print(f"UPPER (Max): np.array([{h_max}, {s_max}, {v_max}])")
        print("Copia esto en tu archivo workers.py")
        break

cap.release()
cv2.destroyAllWindows()