#include <Wire.h>

// ===== PINES =====
#define MOTOR_IN1 5
#define MOTOR_IN2 6   
#define RELAY_VERDE   12  // Vamos a usar este para la prueba
#define RELAY_NARANJA 4   

#define BTN_START 7
#define BTN_STOP  8

// ===== VARIABLES =====
bool systemEnabled = false;

// =====================================================
//           FUNCIONES
// =====================================================

void motorStop() {
  digitalWrite(MOTOR_IN1, LOW);
  digitalWrite(MOTOR_IN2, LOW);
}

void motorForward() {
  digitalWrite(MOTOR_IN1, HIGH);
  digitalWrite(MOTOR_IN2, LOW);
}

void apagarReles() {
  // LÓGICA INVERSA: HIGH = APAGADO
  digitalWrite(RELAY_VERDE, HIGH); 
  digitalWrite(RELAY_NARANJA, HIGH); 
}

void disparoPrueba() {
  // Solo disparamos si el sistema está activo (O quita esta línea si quieres probar sin motor)
  // if (!systemEnabled) return; 

  Serial.println("¡SEÑAL RECIBIDA! Disparando actuador...");

  // 1. Asegurar apagado
  apagarReles();
  
  // 2. ACTIVAR EL RELÉ 1 (Pin 12)
  // LOW = ENCENDIDO
  digitalWrite(RELAY_VERDE, LOW); 
  
  // 3. Esperar 1 segundo
  delay(1000); 
  
  // 4. Apagar
  apagarReles(); 
  Serial.println("Disparo terminado.");
}

void iniciarSistema() {
  systemEnabled = true;
  motorForward();
}

void detenerSistema() {
  systemEnabled = false;
  motorStop();
  apagarReles();
}

// =====================================================
//           SETUP
// =====================================================
void setup() {
  Serial.begin(115200); 
  
  pinMode(MOTOR_IN1, OUTPUT);
  pinMode(MOTOR_IN2, OUTPUT);
  pinMode(RELAY_VERDE, OUTPUT);
  pinMode(RELAY_NARANJA, OUTPUT);
  pinMode(BTN_START, INPUT_PULLUP);
  pinMode(BTN_STOP, INPUT_PULLUP);

  // Estado inicial: Todo apagado (HIGH)
  apagarReles();
  motorStop();
  
  Serial.println("MODO PRUEBA LISTO: Cualquier detección activa el pistón.");
}

// =====================================================
//           LOOP
// =====================================================
void loop() {
  // 1. BOTONES
  if (digitalRead(BTN_STOP) == LOW) {
    detenerSistema();
    delay(300); 
  }

  if (digitalRead(BTN_START) == LOW) {
    iniciarSistema();
    delay(300); 
  }

  // 2. ESCUCHAR A PYTHON
  if (Serial.available() > 0) {
    char cmd = Serial.read();

    // Comandos de Control
    if (cmd == 'S') iniciarSistema();
    if (cmd == 'P') detenerSistema();

    // COMANDOS DE DETECCIÓN (SIMPLIFICADO)
    // Si llega CUALQUIERA de estos, disparamos el mismo pistón
    if (cmd == '1' || cmd == '2' || cmd == '3') {
      disparoPrueba();
    }
  }
}