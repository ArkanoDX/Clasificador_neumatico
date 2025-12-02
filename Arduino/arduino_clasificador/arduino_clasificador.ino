#include <Wire.h>

// ===== PINES =====
#define MOTOR_IN1 5
#define MOTOR_IN2 6   

// Asignación según tu hardware
#define ACTUADOR_1 4    // Relay Naranja (Para piezas Naranjas)
#define ACTUADOR_2 12   // Relay Verde (Para piezas Verdes)

#define BTN_START 7
#define BTN_STOP  8

bool systemEnabled = false;

// =====================================================
//           CONFIGURACIÓN DE TIEMPOS (AJUSTAR AQUÍ)
// =====================================================
// Tiempo que tarda la banda en llevar la pieza desde la cámara hasta el actuador
// AJUSTA ESTOS VALORES EN MILISEGUNDOS SEGÚN LA VELOCIDAD DE TU BANDA
const int TIEMPO_VIAJE_ACTUADOR_1 = 500;  // Ejemplo: 0.5 seg para llegar al primer pistón
const int TIEMPO_VIAJE_ACTUADOR_2 = 1500; // Ejemplo: 1.5 seg para llegar al segundo pistón

// Tiempo que el pistón se queda afuera empujando
const int TIEMPO_EMPUJE = 500; 

void apagarReles() {
  // Lógica Inversa: HIGH = APAGADO
  digitalWrite(ACTUADOR_1, HIGH); 
  digitalWrite(ACTUADOR_2, HIGH);
}

void activarPiston(int pinRelay, int tiempoEspera) {
  if (!systemEnabled) return; // Seguridad

  Serial.print("Pieza detectada. Esperando llegada al actuador...");
  
  // 1. Esperar a que la pieza llegue enfrente del actuador
  // (El Arduino hace una pausa aquí, bloqueando, ideal para proyectos sencillos)
  delay(tiempoEspera);

  // 2. Activar Pistón (LOW = ON)
  digitalWrite(pinRelay, LOW);
  Serial.println("¡DISPARO!");
  
  // 3. Mantener extendido
  delay(TIEMPO_EMPUJE);
  
  // 4. Retraer
  digitalWrite(pinRelay, HIGH);
}

void iniciarSistema() {
  systemEnabled = true;
  digitalWrite(MOTOR_IN1, HIGH);
  digitalWrite(MOTOR_IN2, LOW);
}

void detenerSistema() {
  systemEnabled = false;
  digitalWrite(MOTOR_IN1, LOW);
  digitalWrite(MOTOR_IN2, LOW);
  apagarReles();
}

void setup() {
  Serial.begin(115200); 
  
  pinMode(MOTOR_IN1, OUTPUT);
  pinMode(MOTOR_IN2, OUTPUT);
  pinMode(ACTUADOR_1, OUTPUT);
  pinMode(ACTUADOR_2, OUTPUT);
  pinMode(BTN_START, INPUT_PULLUP);
  pinMode(BTN_STOP, INPUT_PULLUP);

  apagarReles();
  digitalWrite(MOTOR_IN1, LOW); 
  digitalWrite(MOTOR_IN2, LOW);
  
  Serial.println("SISTEMA LISTO. Esperando comandos 1 o 2.");
}

void loop() {
  // Botones Manuales
  if (digitalRead(BTN_STOP) == LOW) { detenerSistema(); delay(300); }
  if (digitalRead(BTN_START) == LOW) { iniciarSistema(); delay(300); }

  // Lectura Serial desde Python
  if (Serial.available() > 0) {
    char cmd = Serial.read();

    if (cmd == 'S') iniciarSistema();
    if (cmd == 'P') detenerSistema();

    // --- LÓGICA DE CLASIFICACIÓN ---
    if (cmd == '1') {
      // PIEZA NARANJA -> Actuador 1
      activarPiston(ACTUADOR_1, TIEMPO_VIAJE_ACTUADOR_1);
    }
    else if (cmd == '2') {
      // PIEZA VERDE -> Actuador 2
      activarPiston(ACTUADOR_2, TIEMPO_VIAJE_ACTUADOR_2);
    }
    else if (cmd == '3') {
      // PIEZA AZUL -> No hacemos nada
      Serial.println("Pieza AZUL: Dejando pasar...");
    }
  }
}