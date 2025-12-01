import serial
import time

# AJUSTA TU PUERTO AQUÍ (Ej. 'COM5', 'COM3')
PUERTO = 'COM5'
BAUD_RATE = 115200

try:
    print(f"Abriendo puerto {PUERTO}...")
    ser = serial.Serial(PUERTO, BAUD_RATE, timeout=1)
    time.sleep(2)  # Espera obligatoria al reiniciar Arduino
    print("✅ Conexión establecida.\n")

    print("--- INICIANDO TEST DE DISPARO ---")
    print("Enviando orden '1' cada 3 segundos...")
    print("Presiona Ctrl + C para detener.\n")

    while True:
        print(">> Enviando: '1' (Activar Relé)")
        ser.write(b'1')  # Enviamos el byte

        # Esperamos ver si el Arduino responde algo (opcional)
        if ser.in_waiting > 0:
            respuesta = ser.readline().decode('utf-8').strip()
            print(f"   Arduino respondió: {respuesta}")

        time.sleep(3)

except serial.SerialException:
    print(f"❌ ERROR: No se pudo abrir el puerto {PUERTO}.")
    print("   1. Cierra el Arduino IDE.")
    print("   2. Desconecta y conecta el USB.")
except KeyboardInterrupt:
    print("\nTest finalizado.")
    if 'ser' in locals() and ser.is_open:
        ser.close()