import machine
import time
class Moteurs:
    """
    Contrôle les 2 moteurs du char via le pont en H HW-354
    
    Chaque moteur a besoin de:
    - 2 pins de direction (IN1/IN2 pour gauche, IN3/IN4 pour droit)
    """
    VITESSE_MAX = 65535
    def __init__(self, in1, in2, in3, in4):
        """
        Paramètres:
            in1, in2 : pins direction moteur GAUCHE
            in3, in4 : pins direction moteur DROIT
        """
        self.in1 = machine.Pin(in1, machine.Pin.OUT)
        self.in2 = machine.Pin(in2, machine.Pin.OUT)
        self.in3 = machine.Pin(in3, machine.Pin.OUT)
        self.in4 = machine.Pin(in4, machine.Pin.OUT)
        self.arreter()
        print("Moteurs initialisés!")
    def _vitesse_pwm(self, pourcentage):
        """Convertit un pourcentage (0-100) en valeur PWM (0-65535)"""
        pourcentage = max(0, min(100, pourcentage))
        return int(pourcentage / 100.0 * self.VITESSE_MAX)
    def avancer(self, vitesse=70):
        """
        Avancer tout droit
        vitesse: 0 à 100 (en pourcentage)
        """
        pwm = self._vitesse_pwm(vitesse)
        self.in1.value(1)
        self.in2.value(0)
        self.in3.value(1)
        self.in4.value(0)
    def reculer(self, vitesse=70):
        """
        Reculer tout droit
        vitesse: 0 à 100 (en pourcentage)
        """
        pwm = self._vitesse_pwm(vitesse)
        self.in1.value(0)
        self.in2.value(1)
        self.in3.value(0)
        self.in4.value(1)
    def tourner_gauche(self, vitesse=60):
        """
        Tourner à gauche
        Moteur gauche recule, moteur droit avance
        """
        pwm = self._vitesse_pwm(vitesse)
        self.in1.value(0)
        self.in2.value(1)
        self.in3.value(1)
        self.in4.value(0)
    def tourner_droite(self, vitesse=60):
        """
        Tourner à droite
        Moteur gauche avance, moteur droit recule
        """
        pwm = self._vitesse_pwm(vitesse)
        self.in1.value(1)
        self.in2.value(0)
        self.in3.value(0)
        self.in4.value(1)
    def arreter(self):
        """Arrêter tous les moteurs"""
        self.in1.value(0)
        self.in2.value(0)
        self.in3.value(0)
        self.in4.value(0)
