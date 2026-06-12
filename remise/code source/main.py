import machine
import time
import random
from bmp280 import BMP280
from capteurs import HCSR04

# =========================================================================
# CLASSE MOTEURS (Intégrée et configurée en VRAI PWM)
# =========================================================================
class Moteurs:
    """
    Contrôle les 2 moteurs du char via le pont en H MX1508 / HW-354
    Respecte le schéma : un côté reçoit le PWM, l'autre reçoit 0.
    """
    VITESSE_MAX = 65535

    def __init__(self, in1, in2, in3, in4):
        # Configuration des broches en PWM à une fréquence de 1000Hz
        self.in1 = machine.PWM(machine.Pin(in1))
        self.in2 = machine.PWM(machine.Pin(in2))
        self.in3 = machine.PWM(machine.Pin(in3))
        self.in4 = machine.PWM(machine.Pin(in4))
        
        self.in1.freq(1000)
        self.in2.freq(1000)
        self.in3.freq(1000)
        self.in4.freq(1000)
        
        self.arreter()
        print("Moteurs initialisés en VRAI PWM !")

    def _vitesse_pwm(self, pourcentage):
        """Convertit un pourcentage (0-100) en valeur PWM (0-65535)"""
        pourcentage = max(0, min(100, pourcentage))
        return int(pourcentage / 100.0 * self.VITESSE_MAX)

    def avancer(self, vitesse=70):
        """Respecte le schéma : IN1=PWM, IN2=0 | IN3=PWM, IN4=0"""
        pwm = self._vitesse_pwm(vitesse)
        self.in1.duty_u16(pwm)
        self.in2.duty_u16(0)
        self.in3.duty_u16(pwm)
        self.in4.duty_u16(0)

    def reculer(self, vitesse=70):
        """Respecte le schéma : IN1=0, IN2=PWM | IN3=0, IN4=PWM"""
        pwm = self._vitesse_pwm(vitesse)
        self.in1.duty_u16(0)
        self.in2.duty_u16(pwm)
        self.in3.duty_u16(0)
        self.in4.duty_u16(pwm)

    def tourner_gauche(self, vitesse=60):
        """Moteur gauche recule, moteur droit avance"""
        pwm = self._vitesse_pwm(vitesse)
        self.in1.duty_u16(0)
        self.in2.duty_u16(pwm)
        self.in3.duty_u16(pwm)
        self.in4.duty_u16(0)

    def tourner_droite(self, vitesse=60):
        """Moteur gauche avance, moteur droit recule"""
        pwm = self._vitesse_pwm(vitesse)
        self.in1.duty_u16(pwm)
        self.in2.duty_u16(0)
        self.in3.duty_u16(0)
        self.in4.duty_u16(pwm)

    def arreter(self):
        """Arrêter tous les moteurs (Standby : tout à 0)"""
        self.in1.duty_u16(0)
        self.in2.duty_u16(0)
        self.in3.duty_u16(0)
        self.in4.duty_u16(0)


# =========================================================================
# CONFIGURATION DES BROCHES ET CONSTANTES
# =========================================================================
I2C_SDA = 0
I2C_SCL = 1

PIN_IN1 = 13
PIN_IN2 = 12
PIN_IN3 = 11
PIN_IN4 = 10

PIN_TRIG = 9
PIN_ECHO = 8
PIN_LED_VERTE = 14
PIN_LED_ROUGE = 15

DISTANCE_DANGER    = 15
DISTANCE_ATTENTION = 30
VITESSE_NORMALE  = 70
VITESSE_LENTE    = 40
VITESSE_ROTATION = 55

TEMP_MIN_OK = 18.0
TEMP_MAX_OK = 28.0
PRESSION_MIN_OK = 980.0
PRESSION_MAX_OK = 1030.0
INTERVALLE_BMP = 3.0


# =========================================================================
# INITIALISATION DU MATÉRIEL
# =========================================================================
print("=" * 40)
print("Démarrage du Mini Char!")
print("=" * 40)

# Bus I2C et Capteur BMP280 (avec l'adresse correcte 119 / 0x77)
i2c = machine.I2C(0, sda=machine.Pin(I2C_SDA), scl=machine.Pin(I2C_SCL), freq=400000)
bmp = BMP280(i2c, address=119)

# Instanciation des moteurs et du sonar
moteurs = Moteurs(PIN_IN1, PIN_IN2, PIN_IN3, PIN_IN4)
sonar = HCSR04(PIN_TRIG, PIN_ECHO)

# Configuration des LEDs
led_verte = machine.Pin(PIN_LED_VERTE, machine.Pin.OUT)
led_rouge = machine.Pin(PIN_LED_ROUGE, machine.Pin.OUT)
led_verte.value(0)
led_rouge.value(0)

print("\nTous les composants sont prêts!")
print("Démarrage dans 3 secondes...\n")

# Clignotement de départ
for _ in range(3):
    led_verte.value(1)
    led_rouge.value(1)
    time.sleep_ms(300)
    led_verte.value(0)
    led_rouge.value(0)
    time.sleep_ms(300)

time.sleep(1)


# =========================================================================
# FONCTIONS DE LOGIQUE
# =========================================================================
def evaluer_environnement(temperature, pression):
    temp_ok     = TEMP_MIN_OK <= temperature <= TEMP_MAX_OK
    pression_ok = PRESSION_MIN_OK <= pression <= PRESSION_MAX_OK
    return temp_ok and pression_ok

def mettre_a_jour_leds(environnement_ok):
    if environnement_ok:
        led_verte.value(1)
        led_rouge.value(0)
    else:
        led_verte.value(0)
        led_rouge.value(1)

def eviter_obstacle(distance):
    if distance == -1:
        return "libre"
    elif distance <= DISTANCE_DANGER:
        moteurs.arreter()
        time.sleep_ms(200)
        moteurs.reculer(VITESSE_LENTE)
        time.sleep_ms(500)
        moteurs.arreter()
        time.sleep_ms(100)
        
        if random.randint(0, 1) == 0:
            moteurs.tourner_gauche(VITESSE_ROTATION)
            direction = "gauche"
        else:
            moteurs.tourner_droite(VITESSE_ROTATION)
            direction = "droite"
            
        time.sleep_ms(600)
        moteurs.arreter()
        return f"danger! recul + rotation {direction}"
        
    elif distance <= DISTANCE_ATTENTION:
        moteurs.avancer(VITESSE_LENTE)
        return f"attention ({distance}cm) - ralenti"
    else:
        return "libre"


# =========================================================================
# BOUCLE PRINCIPALE
# =========================================================================
dernier_bmp = time.time()
environnement_ok = True

print("Le char commence à avancer!")
print("-" * 40)
moteurs.avancer(VITESSE_NORMALE)

try:
    while True:
        # 1. Gestion de la distance
        distance = sonar.mesurer_distance()
        action = eviter_obstacle(distance)
        
        if action == "libre":
            moteurs.avancer(VITESSE_NORMALE)
            
        # 2. Gestion périodique du BMP280 + Distance groupée (Toutes les 3 secondes)
        maintenant = time.time()
        if maintenant - dernier_bmp >= INTERVALLE_BMP:
            try:
                temperature, pression = bmp.lire_tout()
                environnement_ok = evaluer_environnement(temperature, pression)
                mettre_a_jour_leds(environnement_ok)
                
                statut = "OK" if environnement_ok else "ANORMAL"
                
                # Traduction texte de la distance pour la ligne groupée
                txt_distance = f"{distance}cm" if distance != -1 else "Erreur capteur"
                
                # === AFFICHAGE TOUT-EN-UN ICI ===
                print(f"Temp: {temperature}°C | "
                      f"Pression: {pression}hPa | "
                      f"Environnement: {statut} | "
                      f"Distance: {txt_distance}")
                      
            except Exception as e:
                print(f"Erreur BMP280: {e}")
            dernier_bmp = maintenant
            
        # 3. Affichage immédiat UNIQUEMENT en cas de danger ou d'attention
        if distance != -1 and action != "libre":
            print(f"[ALERTE] Distance active: {distance}cm | Action: {action}")
            
        time.sleep_ms(50)

except KeyboardInterrupt:
    # Arrêt d'urgence propre (Ctrl+C dans Thonny)
    print("\n\nArrêt du char!")
    moteurs.arreter()
    led_verte.value(0)
    led_rouge.value(0)
    print("Au revoir!")
    
