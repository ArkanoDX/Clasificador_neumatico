#include "esp_camera.h"
#include <Arduino.h>

// ======================= PINES ==========================
#define VALVE_SMALL 12
#define VALVE_MEDIUM 13
#define VALVE_LARGE 2

#define MOTOR_IN1 14
#define MOTOR_IN2 15

#define BTN_START 1   // BOTÓN FÍSICO START
#define BTN_STOP  3   // BOTÓN FÍSICO STOP

// ======================= VARIABLES ==========================
bool systemEnabled = false;
bool processingBox = false;

unsigned long lastDetectTime = 0;
const int DOUBLE_BOX_TIMEOUT = 400;

// ======================= RANGOS EN PIXELES ==========================
const int SMALL_MIN_PX = 27;
const int SMALL_MAX_PX = 68;

const int MEDIUM_MIN_PX = 81;
const int MEDIUM_MAX_PX = 108;

const int LARGE_MIN_PX = 121;
const int LARGE_MAX_PX = 175;

// ===========================================================
//   MOTOR CONTROL
// ===========================================================
void motorStop() {
  digitalWrite(MOTOR_IN1, LOW);
  digitalWrite(MOTOR_IN2, LOW);
}

void motorForward() {
  digitalWrite(MOTOR_IN1, HIGH);
  digitalWrite(MOTOR_IN2, LOW);
}

// ===========================================================
//   VÁLVULAS
// ===========================================================
void closeAllValves() {
  digitalWrite(VALVE_SMALL, LOW);
  digitalWrite(VALVE_MEDIUM, LOW);
  digitalWrite(VALVE_LARGE, LOW);
}

void activateValve(int zone) {
  closeAllValves();
  if (zone == 1) digitalWrite(VALVE_SMALL, HIGH);
  if (zone == 2) digitalWrite(VALVE_MEDIUM, HIGH);
  if (zone == 3) digitalWrite(VALVE_LARGE, HIGH);
}

// ===========================================================
//   DETECCIÓN COLOR
// ===========================================================
String detectColor(uint8_t r, uint8_t g, uint8_t b) {
  if (b > r && b > g) return "AZUL";
  if (r > g && r > b) return "ROJO";
  if (r > 150 && g > 60 && b < 80) return "NARANJA";
  return "DESCONOCIDO";
}

// ===========================================================
//   CLASIFICACIÓN
// ===========================================================
int classifyBox(String color, int pxHeight) {
  if (pxHeight >= SMALL_MIN_PX && pxHeight <= SMALL_MAX_PX) return 1; // pequeña
  if (pxHeight >= MEDIUM_MIN_PX && pxHeight <= MEDIUM_MAX_PX) return 2; // mediana
  if (pxHeight >= LARGE_MIN_PX && pxHeight <= LARGE_MAX_PX) return 3; // grande
  return 0; // nada válido
}

// ===========================================================
//   CÁMARA INIT
// ===========================================================
void initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0 = 5;
  config.pin_d1 = 18;
  config.pin_d2 = 19;
  config.pin_d3 = 21;
  config.pin_d4 = 36;
  config.pin_d5 = 39;
  config.pin_d6 = 34;
  config.pin_d7 = 35;
  config.pin_xclk = 0;
  config.pin_pclk = 22;
  config.pin_vsync = 25;
  config.pin_href = 23;
  config.pin_sccb_sda = 26;
  config.pin_sccb_scl = 27;
  config.pin_pwdn = 32;
  config.pin_reset = -1;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_RGB565;
  config.frame_size = FRAMESIZE_QVGA;
  config.fb_count = 1;

  esp_camera_init(&config);
}

// ===========================================================
//   SETUP
// ===========================================================
void setup() {
  Serial.begin(115200); // Velocidad para Python

  pinMode(VALVE_SMALL, OUTPUT);
  pinMode(VALVE_MEDIUM, OUTPUT);
  pinMode(VALVE_LARGE, OUTPUT);
  closeAllValves();

  pinMode(MOTOR_IN1, OUTPUT);
  pinMode(MOTOR_IN2, OUTPUT);
  motorStop();

  pinMode(BTN_START, INPUT_PULLUP);
  pinMode(BTN_STOP, INPUT_PULLUP);

  initCamera();
  
  // Mensaje inicial (opcional, Python lo ignorará si no empieza con DATA)
  Serial.println("Sistema listo - Esperando comandos...");
}

// ===========================================================
//   LOOP PRINCIPAL
// ===========================================================
void loop() {

  // -----------------------------------------------------------
  // 1. LEER COMANDOS DESDE PYTHON (NUEVO)
  // -----------------------------------------------------------
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    
    // Comando 'S' (Start/Encendido) desde la GUI
    if (cmd == 'S') {
       if (!systemEnabled) {
          systemEnabled = true;
          processingBox = false;
          closeAllValves();
          motorForward();
          // Serial.println("DEBUG: START Remoto"); 
       }
    }
    
    // Comando 'P' (Parar/Stop) desde la GUI
    else if (cmd == 'P') {
       systemEnabled = false;
       motorStop();
       closeAllValves();
       // Serial.println("DEBUG: STOP Remoto");
    }
  }

  // -----------------------------------------------------------
  // 2. LEER BOTONES FÍSICOS (Mantenemos funcionalidad original)
  // -----------------------------------------------------------
  if (!digitalRead(BTN_STOP)) {
    systemEnabled = false;
    motorStop();
    closeAllValves();
    delay(500);
  }

  if (!digitalRead(BTN_START)) {
    if (!systemEnabled) {
      systemEnabled = true;
      processingBox = false;
      closeAllValves();
      motorForward();
      delay(500);
    }
  }

  if (!systemEnabled) return;

  // -----------------------------------------------------------
  // 3. PROCESAMIENTO DE IMAGEN
  // -----------------------------------------------------------
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) return;

  int width = fb->width;
  int height = fb->height;
  uint8_t *buffer = fb->buf;

  int top = 9999;
  int bottom = 0;
  long sumR = 0, sumG = 0, sumB = 0;
  int count = 0;

  // Escaneo vertical (Zona central)
  for (int y = 0; y < height; y++) {
    for (int x = width / 3; x < 2 * width / 3; x++) {

      int i = (y * width + x) * 2;
      uint8_t byte1 = buffer[i];
      uint8_t byte2 = buffer[i + 1];

      uint8_t r = (byte1 & 0xF8);
      uint8_t g = ((byte1 & 0x07) << 5) | ((byte2 & 0xE0) >> 3);
      uint8_t b = (byte2 & 0x1F) << 3;

      // Umbral de detección (Caja vs Fondo)
      if (r > 40 || g > 40 || b > 40) {
        if (y < top) top = y;
        if (y > bottom) bottom = y;

        sumR += r;
        sumG += g;
        sumB += b;
        count++;
      }
    }
  }

  esp_camera_fb_return(fb);

  int pxHeight = bottom - top;
  String color = "DESCONOCIDO";
  if (count > 50) color = detectColor(sumR / count, sumG / count, sumB / count);

  // Doble caja (Seguridad)
  if (millis() - lastDetectTime < DOUBLE_BOX_TIMEOUT && pxHeight > 30) {
    motorStop();
    systemEnabled = false;
    closeAllValves();
    return;
  }

  if (pxHeight > 30) lastDetectTime = millis();

  // Sin caja detectada
  if (pxHeight < 30) {
    if (!processingBox) motorForward();
    return;
  }

  // -----------------------------------------------------------
  // 4. CAJA DETECTADA -> CLASIFICAR
  // -----------------------------------------------------------
  motorStop(); // Detener cinta para clasificar

  if (!processingBox) {
    processingBox = true;
    int zone = classifyBox(color, pxHeight);

    // --- COMUNICACIÓN CON PYTHON ---
    // Enviamos una cadena formateada CSV: DATA,Color,Altura,Zona
    Serial.print("DATA,");
    Serial.print(color);
    Serial.print(",");
    Serial.print(pxHeight);
    Serial.print(",");
    Serial.println(zone);
    // -------------------------------

    activateValve(zone);

    delay(1500); // Tiempo de actuación del pistón
    closeAllValves();

    systemEnabled = false; // Esperar siguiente START (Manual o Remoto)
  }
}