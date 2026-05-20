import machine
import time
import random
from bmp280 import BMP280
from moteurs import Moteurs
from capteurs import HCSR04
I2C_SDA = 4
I2C_SCL = 5
PIN_IN1 = 10
PIN_IN2 = 11
PIN_IN3 = 12
PIN_IN4 = 13
PIN_ENA = 14
PIN_ENB = 15
PIN_TRIG = 2
PIN_ECHO = 3
PIN_LED_VERTE = 20
PIN_LED_ROUGE = 21
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
print("=" * 40)
print("Démarrage du Mini Char!")
print("=" * 40)
i2c = machine.I2C(0, sda=machine.Pin(I2C_SDA), scl=machine.Pin(I2C_SCL), freq=400000)
bmp = BMP280(i2c)
moteurs = Moteurs(PIN_IN1, PIN_IN2, PIN_IN3, PIN_IN4, PIN_ENA, PIN_ENB)
sonar = HCSR04(PIN_TRIG, PIN_ECHO)
led_verte = machine.Pin(PIN_LED_VERTE, machine.Pin.OUT)
led_rouge = machine.Pin(PIN_LED_ROUGE, machine.Pin.OUT)
led_verte.value(0)
led_rouge.value(0)
print("\nTous les composants sont prêts!")
print("Démarrage dans 3 secondes...\n")
for _ in range(3):
    led_verte.value(1)
    led_rouge.value(1)
    time.sleep_ms(300)
    led_verte.value(0)
    led_rouge.value(0)
    time.sleep_ms(300)
time.sleep(1)
def evaluer_environnement(temperature, pression):
    """
    Évalue la qualité de l'environnement selon le BMP280
    
    Retourne:
        True  → Environnement OK  (LED verte)
        False → Environnement pas idéal (LED rouge)
    
    Critères:
        - Température dans la plage normale
        - Pression atmosphérique dans la plage normale
    """
    temp_ok     = TEMP_MIN_OK <= temperature <= TEMP_MAX_OK
    pression_ok = PRESSION_MIN_OK <= pression <= PRESSION_MAX_OK
    return temp_ok and pression_ok
def mettre_a_jour_leds(environnement_ok):
    """
    Met à jour les LEDs selon la qualité de l'environnement
    
    Vert  = tout est bien (temp et pression normales)
    Rouge = conditions anormales (trop chaud, pression bizarre, etc.)
    """
    if environnement_ok:
        led_verte.value(1)
        led_rouge.value(0)
    else:
        led_verte.value(0)
        led_rouge.value(1)
def eviter_obstacle(distance):
    """
    Stratégie d'évitement d'obstacle
    
    Retourne l'action effectuée comme texte pour le débogage
    """
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
dernier_bmp = time.time()
environnement_ok = True
print("Le char commence à avancer!")
print("-" * 40)
moteurs.avancer(VITESSE_NORMALE)
try:
    while True:
        distance = sonar.mesurer_distance()
        action = eviter_obstacle(distance)
        if action == "libre":
            moteurs.avancer(VITESSE_NORMALE)
        maintenant = time.time()
        if maintenant - dernier_bmp >= INTERVALLE_BMP:
            try:
                temperature, pression = bmp.lire_tout()
                environnement_ok = evaluer_environnement(temperature, pression)
                mettre_a_jour_leds(environnement_ok)
                statut = "OK" if environnement_ok else "ANORMAL"
                print(f"Temp: {temperature}°C | "
                      f"Pression: {pression}hPa | "
                      f"Environnement: {statut}")
            except Exception as e:
                print(f"Erreur BMP280: {e}")
            dernier_bmp = maintenant
        if distance != -1:
            print(f"Distance: {distance}cm | Action: {action}")
        time.sleep_ms(50)
except KeyboardInterrupt:
    print("\n\nArrêt du char!")
    moteurs.arreter()
    led_verte.value(0)
    led_rouge.value(0)
    print("Au revoir!")