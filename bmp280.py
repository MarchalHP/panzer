import machine
import time
class BMP280:
    I2C_ADDRESS = 0x76
    def __init__(self, i2c, address=0x76):
        self.i2c = i2c
        self.address = address
        devices = self.i2c.scan()
        if self.address not in devices:
            print(f"BMP280 non trouvé! Appareils détectés: {devices}")
        else: print("✅ BMP280 trouvé!")
        self._lire_calibration()
        self.i2c.writeto_mem(self.address, 0xF4, bytes([0x27]))
        self.i2c.writeto_mem(self.address, 0xF5, bytes([0xA0]))
    def _lire_calibration(self):
        cal = self.i2c.readfrom_mem(self.address, 0x88, 24)
        self.dig_T1 = (cal[1] << 8) | cal[0]
        self.dig_T2 = self._signe((cal[3] << 8) | cal[2])
        self.dig_T3 = self._signe((cal[5] << 8) | cal[4])
        self.dig_P1 = (cal[7] << 8) | cal[6]
        self.dig_P2 = self._signe((cal[9] << 8) | cal[8])
        self.dig_P3 = self._signe((cal[11] << 8) | cal[10])
        self.dig_P4 = self._signe((cal[13] << 8) | cal[12])
        self.dig_P5 = self._signe((cal[15] << 8) | cal[14])
        self.dig_P6 = self._signe((cal[17] << 8) | cal[16])
        self.dig_P7 = self._signe((cal[19] << 8) | cal[18])
        self.dig_P8 = self._signe((cal[21] << 8) | cal[20])
        self.dig_P9 = self._signe((cal[23] << 8) | cal[22])
    def _signe(self, valeur):
        if valeur > 32767:
            valeur -= 65536
        return valeur
    def _lire_brut(self):
        data = self.i2c.readfrom_mem(self.address, 0xF7, 6)
        pression_brute = ((data[0] << 16) | (data[1] << 8) | data[2]) >> 4
        temp_brute     = ((data[3] << 16) | (data[4] << 8) | data[5]) >> 4
        return pression_brute, temp_brute
    def lire_temperature(self):
        _, temp_brute = self._lire_brut()
        var1 = (temp_brute / 16384.0 - self.dig_T1 / 1024.0) * self.dig_T2
        var2 = (temp_brute / 131072.0 - self.dig_T1 / 8192.0) ** 2 * self.dig_T3
        self.t_fine = var1 + var2
        temperature = self.t_fine / 5120.0
        return round(temperature, 2)
    def lire_pression(self):
        pression_brute, _ = self._lire_brut()
        self.lire_temperature()
        var1 = self.t_fine / 2.0 - 64000.0
        var2 = var1 * var1 * self.dig_P6 / 32768.0
        var2 = var2 + var1 * self.dig_P5 * 2.0
        var2 = var2 / 4.0 + self.dig_P4 * 65536.0
        var1 = (self.dig_P3 * var1 * var1 / 524288.0 + self.dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.dig_P1
        if var1 == 0:
            return 0
        pression = 1048576.0 - pression_brute
        pression = ((pression - var2 / 4096.0) * 6250.0) / var1
        var1 = self.dig_P9 * pression * pression / 2147483648.0
        var2 = pression * self.dig_P8 / 32768.0
        pression = pression + (var1 + var2 + self.dig_P7) / 16.0
        return round(pression / 100.0, 2)
    def lire_tout(self):
        temp = self.lire_temperature()
        pression = self.lire_pression()
        return temp, pression
