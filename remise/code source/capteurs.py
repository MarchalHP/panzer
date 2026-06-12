import machine
import time
class HCSR04:
    """
    Classe pour le capteur de distance ultrasonique HC-SR04
    
    Fonctionnement:
    1. On envoie une impulsion sur TRIG (10 microsecondes)
    2. Le capteur envoie 8 ultrasons à 40kHz
    3. Quand l'écho revient, ECHO passe à HIGH
    4. On mesure le temps → on calcule la distance
    
    Formule: Distance (cm) = Durée (µs) / 58
    (La vitesse du son est ~340 m/s = 29µs/cm, aller-retour = 58µs/cm)
    """
    def __init__(self, trig_pin, echo_pin):
        """
        Paramètres:
            trig_pin : numéro du pin TRIG (sortie)
            echo_pin : numéro du pin ECHO (entrée)
        """
        self.trig = machine.Pin(trig_pin, machine.Pin.OUT)
        self.echo = machine.Pin(echo_pin, machine.Pin.IN)
        self.trig.value(0)
        time.sleep_ms(100)
        print("HC-SR04 initialisé!")
    def mesurer_distance(self):
        """
        Mesure et retourne la distance en centimètres
        Retourne -1 si pas de lecture valide (timeout)
        """
        self.trig.value(0)
        time.sleep_us(2)
        self.trig.value(1)
        time.sleep_us(10)
        self.trig.value(0)
        timeout = time.ticks_us()
        while self.echo.value() == 0:
            if time.ticks_diff(time.ticks_us(), timeout) > 30000:
                return -1
        debut = time.ticks_us()
        while self.echo.value() == 1:
            if time.ticks_diff(time.ticks_us(), debut) > 30000:
                return -1
        fin = time.ticks_us()
        duree = time.ticks_diff(fin, debut)
        distance = duree / 58.0
        return round(distance, 1)
    def mesurer_moyenne(self, nb_mesures=3):
        """
        Fait plusieurs mesures et retourne la moyenne
        Plus précis qu'une seule mesure
        """
        mesures = []
        for _ in range(nb_mesures):
            dist = self.mesurer_distance()
            if dist != -1 and dist <= 400:
                mesures.append(dist)
            time.sleep_ms(20)
        if mesures:
            return round(sum(mesures) / len(mesures), 1)
        else:
            return -1

