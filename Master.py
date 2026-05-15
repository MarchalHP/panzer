import time
from machine import Pin, PWM, I2C, UART
import random
from bmp280 import BMP280
from micropython_servo_pdm import ServoPDM
import _thread
from smbus2 import SMBus
#____________settings-user____________
# TPA critere
Max_temp = 22
Min_temp = 18
Max_pressure = 105000
Min_pressure = 95000
Max_Altitude = 500
Min_Altitude = 0
temp = pressure = altitude = 0
# securiter
distance_ral = 20
distance_stop = 5
vitesse = 100
# direction & sens
right = 1
left = 0
straight = 1
behind = 0
# song
Nader_Bell = [[1255, 500], [0, 500]]
Alert = [[440, 150], [349, 150]]
cheat_song = [[330, 100], [494, 400]]
song_mode = {'active': False, 'loop': False}
freq_active = []
tempo_active = []
volume = 100
# BT settings
BT_sens = straight
BT_direction = right
BT_klaxon_freq = 1000
BT_klaxon_volume = 100
BT_Secu = True
cheat_code = ['F','f','F','f','B','b','B','b','L','l','R','r','L','l','R','r','V','v','U','u','W','w']
#____________settings-machine____________
time.sleep(0.1) # Wait for USB to become ready
#led
ledOK = Pin(13, Pin.OUT)
ledKO = Pin(12, Pin.OUT)
ledOK.value(1)
ledKO.value(1)
#switch
switch1 = Pin(14, Pin.IN)
switch2 = Pin(15, Pin.IN)
#motor
motorDA = PWM(Pin(6))
motorDB = PWM(Pin(7))
motorGA = PWM(Pin(8))
motorGB = PWM(Pin(9))
FREQ_PWM = 1000
motorDA.freq(FREQ_PWM)
motorDB.freq(FREQ_PWM)
motorGA.freq(FREQ_PWM)
motorGB.freq(FREQ_PWM)
motorDA.duty_u16(0)
motorDB.duty_u16(0)
motorGA.duty_u16(0)
motorGB.duty_u16(0)
#capteur ultra song
trig = Pin(2, Pin.OUT)
echo = Pin(3, Pin.IN)
# capeur TPA
bus = SMBus(1)
capteur_temp = BMP280(ic2_dev=bus)
i2c = I2C(0, sda=Pin(0), scl=Pin(1))
#//capteur_temp.oversample_sett = 2
#//capteur_temp.baseline = 101325
# servo
servo = PWM(Pin(4)) 
freq = 50
min_us = 500
max_us = 2500
max_angle = 180
min_angle = 0
servo = ServoPDM(pwm=servo, min_us=min_us, max_us=max_us, freq=freq, max_angle=max_angle, min_angle=min_angle)
# Buzzer
buzzer = PWM(Pin(11))
buzzer.freq(1000)
buzzer.duty_u16(0)
# BT
uart_bt = UART(1, baudrate=9600, tx=Pin(16), rx=Pin(17))
uart_bt.init(9600, bits=8, parity=None, stop=1)
BT_log = []
# Mode
BT = False
auto = False
OFF = True
movement_mode = ['run', 'turn', 'rotate']
direction_mode = [right, left]
sens_mode = [straight, behind]
mov = direc = sen = None
#____________Rule3-Speed-vol____________
def speedvol(pourcentage):
    most = int(pourcentage * 655)
    return most
#____________stop-motor____________
def stopMotor():
    motorDA.duty_u16(0)
    motorDB.duty_u16(0)
    motorGA.duty_u16(0)
    motorGB.duty_u16(0)
#____________radar____________
def radar():
    trig.low()
    time.sleep_us(2)
    trig.high()
    time.sleep_us(10)
    trig.low()
    timeout = 30000
    start = time.ticks_us()
    while echo.value() == 0:
        if time.ticks_diff(time.ticks_us(), start) > timeout:
            return -1
        pulse_start = time.ticks_us()
    while echo.value() == 1:
        if time.ticks_diff(time.ticks_us(), start) > timeout:
            return -1
        pulse_end = time.ticks_us()
    pulse_duration = time.ticks_diff(pulse_end, pulse_start)
    distance = (pulse_duration * 0.0343) / 2
    return distance
#____________song-play____________
def play(song=None, loop=False):
    global song_mode, freq_active, tempo_active
    song_mode['active'] = True
    freq_active.clear()
    tempo_active.clear()
    if loop: song_mode['loop'] = True
    elif loop == False: song_mode['loop'] = False
    for i in song:
        freq_active.append(i[0])
        tempo_active.append(i[1])
#____________song-stop____________
def stop_song():
    global song_mode, freq_active, tempo_active
    song_mode['active'] = False
    freq_active.clear()
    tempo_active.clear()
    buzzer.duty_u16(0)
#____________klaxon____________
def klaxon(status=False):
    if status:
        buzzer.freq(BT_klaxon_freq)
        buzzer.duty_u16(speedvol(BT_klaxon_volume))
    else:
        buzzer.duty_u16(0)
#____________mode-difine____________
def switch_statut():
    global BT, auto, OFF
    if switch1.value() == 1 and switch2.value() == 0:
        BT, auto, OFF = False, True, False
    elif switch1.value() == 0 and switch2.value() == 1:
        BT, auto, OFF = True, False, False
    elif switch1.value() == 0 and switch2.value() == 0:
        BT, auto, OFF = False, False, True
    else:
        while switch1.value() == 1 and switch2.value() == 1:
            play(Alert, loop=True)
            for i in range(5):
                colorled('on')
                time.sleep(0.2)
                colorled('off')
                time.sleep(0.2)
            stop_song()
#____________movement____________
def movement(movement='run', direction=None, sens=straight):
    if not safe(sens): return
    if sens == behind:
        play(Nader_Bell, True)
    if sens == straight:
        stop_song()
    if movement == 'run':
        if sens == 1: #straight
            motorDA.duty_u16(speedvol(vitesse))
            motorDB.duty_u16(0)
            motorGA.duty_u16(speedvol(vitesse))
            motorGB.duty_u16(0)
        elif sens == 0: #behind
            motorDA.duty_u16(0)
            motorDB.duty_u16(speedvol(vitesse))
            motorGA.duty_u16(0)
            motorGB.duty_u16(speedvol(vitesse))
        else:
            stopMotor()  
    elif movement == 'turn':
        if direction == 1: #right
            if sens == 1: #straight
                motorDA.duty_u16(0)
                motorDB.duty_u16(0)
                motorGA.duty_u16(speedvol(vitesse))
                motorGB.duty_u16(0)
            elif sens == 0: #behind
                motorDA.duty_u16(0)
                motorDB.duty_u16(speedvol(vitesse))
                motorGA.duty_u16(0)
                motorGB.duty_u16(0)
            else:
                stopMotor()
        elif direction == 0: #left
            if sens == 1: #straight
                motorDA.duty_u16(speedvol(vitesse))
                motorDB.duty_u16(0)
                motorGA.duty_u16(0)
                motorGB.duty_u16(0)
            elif sens == 0: #behind
                motorDA.duty_u16(0)
                motorDB.duty_u16(0)
                motorGA.duty_u16(0)
                motorGB.duty_u16(speedvol(vitesse))
            else:
                stopMotor()
        else:
            stopMotor()
    elif movement == 'rotate':
        if direction == 1: #right
            motorDA.duty_u16(0)
            motorDB.duty_u16(speedvol(vitesse))
            motorGA.duty_u16(speedvol(vitesse))
            motorGB.duty_u16(0)
        elif direction == 0: #left
            motorDA.duty_u16(speedvol(vitesse))
            motorDB.duty_u16(0)
            motorGA.duty_u16(0)
            motorGB.duty_u16(speedvol(vitesse))
        else:
            stopMotor()  
#____________movement-analyse____________
def movement_analyse():
    global mov, direc, sen
    dis = radar()
    mov = 'run'
    direc = None
    sen = straight
    if dis != -1 and dis <= distance_stop:
        mov = random.choice(movement_mode)
        if mov == 'run':
            direc = None
            sen = behind
        elif mov == 'turn':
            direc = random.choice(direction_mode)
            sen = behind
        elif mov == 'rotate':
            direc = random.choice(direction_mode)
            sen = None 
#____________TPA____________
def TPA_info():
    global temp, pressure, altitude
    temp = capteur_temp.get_temperature
    pressure = capteur_temp.get_pressure
    altitude = capteur_temp.get_altitude
#____________TPA-info____________
def TPAnalise(temp, pressure, altitude):
    if temp <= Max_temp and temp >= Min_temp:T = True
    else:T = False
    if pressure <= Max_pressure and pressure >= Min_pressure:P = True
    else:P = False
    if altitude <= Max_Altitude and altitude >= Min_Altitude:A = True
    else:A = False
    if False == T or False == P or False == A:
        colorled('no')
        return False
    elif True == T and True == P and True == A:
        colorled('yes')
        return True
#____________led-resultanalise____________
def colorled(reponce):
    if reponce == 'yes':
        ledOK.value(1)
        ledKO.value(0)
    elif reponce == 'no': 
        ledOK.value(0)
        ledKO.value(1)
    elif reponce == 'off': 
        ledOK.value(0)
        ledKO.value(0)
    elif reponce == 'on': 
        ledOK.value(1)
        ledKO.value(1)
#____________BT-reception____________
def BT_reception():
    if uart_bt.any():
        data = uart_bt.read(1)
        if data:
            commande = data.decode('utf-8').strip()
            return commande
    return None
#___________BT-execution____________
def BT_ex(command):
    global BT_sens, BT_direction
    if command == 'F':movement('run', None, straight)
    elif command == 'f': stopMotor()
    elif command == 'B': movement('run', None, behind)
    elif command == 'b': stopMotor()
    elif command == 'L': movement('turn', left, BT_sens)
    elif command == 'l': stopMotor()
    elif command == 'R': movement('turn', right, BT_sens)
    elif command == 'r': stopMotor()
    elif command == 'U': 
        if BT_sens == straight: BT_sens = behind
        elif BT_sens == behind: BT_sens = straight
        if BT_direction == right: BT_direction = left
        elif BT_direction == left: BT_direction = right
    elif command == 'u': pass
    elif command == 'V': movement('rotate', BT_direction, None)
    elif command == 'v': pass
    elif command == 'W': klaxon(True)
    elif command == 'w': klaxon(False)
#____________security____________
def safe(sens=straight):
    global BT_Secu, vitesse
    dis = radar()
    if BT:
        sens = BT_sens
        if not BT_Secu:
            vitesse = 100
            return True 
    if dis == -1:
        vitesse = 100
        return True
    elif dis <= distance_stop and sens == straight:
        stopMotor()
        play(Alert)
        return False
    elif dis <= distance_stop and sens == behind:
        vitesse = 10
        return True
    elif dis <= distance_ral:
        vitesse = int(dis*(100/(distance_ral-distance_stop)))  
        return True
    else:
        vitesse = 100
        return True
#____________BT-cheat-check____________
def cheat_check():
    global BT_Secu
    if len(BT_log) > 1000:
        BT_log.clear()
    elif len(BT_log) > 10:
        if ("".join(cheat_code)) in ("".join([c for c in BT_log if c is not None])):
            BT_log.clear()
            BT_Secu = not BT_Secu
            play(cheat_song)
#____________setup____________
def song_setup():
    global song_mode
    while True:
        if song_mode['active'] == True:
            for i in range(len(freq_active)):
                if not song_mode['active']: break
                if freq_active[i] > 0:
                    buzzer.freq(freq_active[i])
                    buzzer.duty_u16(speedvol(volume))
                else: buzzer.duty_u16(0)
                time.sleep_ms(tempo_active[i])
            if not song_mode['loop']:
                song_mode['active'] = False
                buzzer.duty_u16(0)
        else: time.sleep(0.1)
    return
_thread.start_new_thread(song_setup, ())
#___________void-loop____________
while True:
    time.sleep(0.1)
    switch_statut()
    #____________Mode-Auto____________
    if not OFF and auto and not BT:
        TPA_info()
        if not TPAnalise(temp, pressure, altitude):
            stopMotor()
        else:
            movement('run', None, straight)
            if not safe():
                movement_analyse()
                movement(mov, direc, sen)
    #____________Mode-BT____________
    elif not OFF and not auto and BT:
        Recep = BT_reception()
        if Recep:
            BT_log.append(Recep)
            BT_ex(Recep)
            cheat_check()
        safe()
    #____________Standby____________
    elif OFF:
        stopMotor()
        servo.release()
        colorled('off')
"""
Credit
TAP : https://github.com/pimoroni/bmp280-python.git
servo : https://github.com/TTitanUA/micropython_servo_pdm
BT : https://github.com/SanitArya/Source_Code-for-RC-Bluetooth-Controller-HC-05-
a finir :
tourelle
"""