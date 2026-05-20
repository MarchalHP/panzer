# ============================================================
# 🤖 MINI CHAR - Programme Principal
# Raspberry Pi Pico
# 
# Fonctionnalités:
#   ✅ Évitement d'obstacles (HC-SR04)
#   ✅ Indicateur qualité environnement (BMP280 + LEDs)
#   ✅ Navigation autonome
# ============================================================

import machine
import time
import random

# Importer nos modules personnalisés
from bmp280 import BMP280
from moteurs import Moteurs
from capteurs import HCSR04

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⚙️  CONFIGURATION DES PINS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# I2C pour le BMP280
I2C_SDA = 4
I2C_SCL = 5

# HW-354 (Moteurs)
PIN_IN1 = 10   # Moteur gauche - direction A
PIN_IN2 = 11   # Moteur gauche - direction B
PIN_IN3 = 12   # Moteur droit  - direction A
PIN_IN4 = 13   # Moteur droit  - direction B
PIN_ENA = 14   # Vitesse moteur gauche (PWM)
PIN_ENB = 15   # Vitesse moteur droit  (PWM)

# HC-SR04 (Ultrason)
PIN_TRIG = 2
PIN_ECHO = 3

# LEDs
PIN_LED_VERTE = 20   # Environnement OK
PIN_LED_ROUGE = 21   # Environnement dangereux

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎛️  PARAMÈTRES DE COMPORTEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Distance minimale avant obstacle (en cm)
DISTANCE_DANGER    = 15   # STOP immédiat
DISTANCE_ATTENTION = 30   # Ralentir

# Vitesse de déplacement
VITESSE_NORMALE  = 70  # % de vitesse max
VITESSE_LENTE    = 40  # % en mode attention
VITESSE_ROTATION = 55  # % pour les virages

# Plages de qualité environnementale
# Température normale: 18°C à 28°C
TEMP_MIN_OK = 18.0
TEMP_MAX_OK = 28.0

# Pression normale au niveau de la mer: ~1013 hPa
# En intérieur, généralement entre 980 et 1030 hPa
PRESSION_MIN_OK = 980.0
PRESSION_MAX_OK = 1030.0

# Intervalle de lecture des capteurs environnementaux (secondes)
INTERVALLE_BMP = 3.0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 INITIALISATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("=" * 40)
print("  🤖 Démarrage du Mini Char!")
print("=" * 40)

# Initialiser I2C pour le BMP280
i2c = machine.I2C(0, sda=machine.Pin(I2C_SDA), scl=machine.Pin(I2C_SCL), freq=400000)

# Créer les objets de chaque composant
bmp = BMP280(i2c)
moteurs = Moteurs(PIN_IN1, PIN_IN2, PIN_IN3, PIN_IN4, PIN_ENA, PIN_ENB)
sonar = HCSR04(PIN_TRIG, PIN_ECHO)

# Initialiser les LEDs
led_verte = machine.Pin(PIN_LED_VERTE, machine.Pin.OUT)
led_rouge = machine.Pin(PIN_LED_ROUGE, machine.Pin.OUT)

# Éteindre les LEDs au départ
led_verte.value(0)
led_rouge.value(0)

print("\n✅ Tous les composants sont prêts!")
print("🚦 Démarrage dans 3 secondes...\n")

# Animation de démarrage (clignoter les 2 LEDs)
for _ in range(3):
    led_verte.value(1)
    led_rouge.value(1)
    time.sleep_ms(300)
    led_verte.value(0)
    led_rouge.value(0)
    time.sleep_ms(300)

time.sleep(1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🛠️  FONCTIONS UTILITAIRES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
        # Capteur n'a rien détecté = voie libre
        return "libre"
    
    elif distance <= DISTANCE_DANGER:
        # ⛔ DANGER - Obstacle très proche!
        
        # 1. Arrêt d'urgence
        moteurs.arreter()
        time.sleep_ms(200)
        
        # 2. Reculer un peu
        moteurs.reculer(VITESSE_LENTE)
        time.sleep_ms(500)
        moteurs.arreter()
        time.sleep_ms(100)
        
        # 3. Tourner aléatoirement gauche ou droite
        #    (pour ne pas toujours aller du même côté)
        if random.randint(0, 1) == 0:
            moteurs.tourner_gauche(VITESSE_ROTATION)
            direction = "gauche"
        else:
            moteurs.tourner_droite(VITESSE_ROTATION)
            direction = "droite"
        
        time.sleep_ms(600)  # Durée de la rotation
        moteurs.arreter()
        
        return f"danger! recul + rotation {direction}"
    
    elif distance <= DISTANCE_ATTENTION:
        # ⚠️  ATTENTION - Obstacle proche, ralentir
        moteurs.avancer(VITESSE_LENTE)
        return f"attention ({distance}cm) - ralenti"
    
    else:
        # ✅ Voie libre - avancer normalement
        return "libre"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔄 BOUCLE PRINCIPALE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Horodatage pour ne pas lire le BMP280 à chaque cycle
# (inutile de le lire 100x par seconde, ça change peu)
dernier_bmp = time.time()
environnement_ok = True  # Par défaut = OK

print("🏁 Le char commence à avancer!")
print("-" * 40)

# Démarrer le mouvement
moteurs.avancer(VITESSE_NORMALE)

try:
    while True:
        
        # ── 1. LIRE LE CAPTEUR ULTRASONIQUE ──────────────
        distance = sonar.mesurer_distance()
        
        # ── 2. ÉVITEMENT D'OBSTACLE ───────────────────────
        action = eviter_obstacle(distance)
        
        # Si on n'est pas en danger, continuer d'avancer
        if action == "libre":
            moteurs.avancer(VITESSE_NORMALE)
        
        # ── 3. LIRE LE BMP280 (moins fréquemment) ─────────
        maintenant = time.time()
        if maintenant - dernier_bmp >= INTERVALLE_BMP:
            
            try:
                temperature, pression = bmp.lire_tout()
                environnement_ok = evaluer_environnement(temperature, pression)
                mettre_a_jour_leds(environnement_ok)
                
                # Affichage dans la console pour le débogage
                statut = "✅ OK" if environnement_ok else "⚠️  ANORMAL"
                print(f"🌡️  Temp: {temperature}°C | "
                      f"📊 Pression: {pression}hPa | "
                      f"Environnement: {statut}")
                
            except Exception as e:
                print(f"❌ Erreur BMP280: {e}")
            
            dernier_bmp = maintenant
        
        # ── 4. AFFICHAGE DISTANCE (débogage) ──────────────
        if distance != -1:
            print(f"📡 Distance: {distance}cm | Action: {action}")
        
        # Petite pause pour ne pas surcharger le processeur
        time.sleep_ms(50)  # 20 lectures par seconde


except KeyboardInterrupt:
    # L'utilisateur a appuyé sur Ctrl+C → arrêt propre
    print("\n\n🛑 Arrêt du char!")
    moteurs.arreter()
    led_verte.value(0)
    led_rouge.value(0)
    print("👋 Au revoir!")
