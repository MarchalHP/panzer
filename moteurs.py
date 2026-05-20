# ============================================================
# Contrôle des moteurs via le module HW-354 (L298N)
# Le HW-354 peut contrôler 2 moteurs DC indépendamment
# ============================================================

import machine
import time

class Moteurs:
    """
    Contrôle les 2 moteurs du char via le pont en H HW-354
    
    Chaque moteur a besoin de:
    - 2 pins de direction (IN1/IN2 pour gauche, IN3/IN4 pour droit)
    - 1 pin PWM pour la vitesse (ENA pour gauche, ENB pour droit)
    """
    
    # Vitesse maximum (0 à 65535 pour le PWM du Pico)
    VITESSE_MAX = 65535
    
    def __init__(self, in1, in2, in3, in4, ena, enb):
        """
        Paramètres:
            in1, in2 : pins direction moteur GAUCHE
            in3, in4 : pins direction moteur DROIT  
            ena      : pin PWM vitesse moteur GAUCHE
            enb      : pin PWM vitesse moteur DROIT
        """
        
        # Pins de direction (simples sorties numériques)
        self.in1 = machine.Pin(in1, machine.Pin.OUT)
        self.in2 = machine.Pin(in2, machine.Pin.OUT)
        self.in3 = machine.Pin(in3, machine.Pin.OUT)
        self.in4 = machine.Pin(in4, machine.Pin.OUT)
        
        # Pins de vitesse (sorties PWM - modulation de largeur d'impulsion)
        # PWM permet de varier la vitesse de 0% à 100%
        self.ena = machine.PWM(machine.Pin(ena))
        self.enb = machine.PWM(machine.Pin(enb))
        
        # Fréquence PWM à 1000 Hz (bonne pour les moteurs DC)
        self.ena.freq(1000)
        self.enb.freq(1000)
        
        # Arrêter les moteurs au démarrage
        self.arreter()
        print("✅ Moteurs initialisés!")
    
    def _vitesse_pwm(self, pourcentage):
        """Convertit un pourcentage (0-100) en valeur PWM (0-65535)"""
        # Limiter entre 0 et 100
        pourcentage = max(0, min(100, pourcentage))
        return int(pourcentage / 100.0 * self.VITESSE_MAX)
    
    def avancer(self, vitesse=70):
        """
        Avancer tout droit
        vitesse: 0 à 100 (en pourcentage)
        """
        pwm = self._vitesse_pwm(vitesse)
        
        # Moteur gauche - sens avant
        self.in1.value(1)
        self.in2.value(0)
        self.ena.duty_u16(pwm)
        
        # Moteur droit - sens avant
        self.in3.value(1)
        self.in4.value(0)
        self.enb.duty_u16(pwm)
    
    def reculer(self, vitesse=70):
        """
        Reculer tout droit
        vitesse: 0 à 100 (en pourcentage)
        """
        pwm = self._vitesse_pwm(vitesse)
        
        # Moteur gauche - sens arrière
        self.in1.value(0)
        self.in2.value(1)
        self.ena.duty_u16(pwm)
        
        # Moteur droit - sens arrière
        self.in3.value(0)
        self.in4.value(1)
        self.enb.duty_u16(pwm)
    
    def tourner_gauche(self, vitesse=60):
        """
        Tourner à gauche
        Moteur gauche recule, moteur droit avance
        """
        pwm = self._vitesse_pwm(vitesse)
        
        # Moteur gauche - ARRIÈRE
        self.in1.value(0)
        self.in2.value(1)
        self.ena.duty_u16(pwm)
        
        # Moteur droit - AVANT
        self.in3.value(1)
        self.in4.value(0)
        self.enb.duty_u16(pwm)
    
    def tourner_droite(self, vitesse=60):
        """
        Tourner à droite
        Moteur gauche avance, moteur droit recule
        """
        pwm = self._vitesse_pwm(vitesse)
        
        # Moteur gauche - AVANT
        self.in1.value(1)
        self.in2.value(0)
        self.ena.duty_u16(pwm)
        
        # Moteur droit - ARRIÈRE
        self.in3.value(0)
        self.in4.value(1)
        self.enb.duty_u16(pwm)
    
    def arreter(self):
        """Arrêter tous les moteurs"""
        self.in1.value(0)
        self.in2.value(0)
        self.in3.value(0)
        self.in4.value(0)
        self.ena.duty_u16(0)
        self.enb.duty_u16(0)
