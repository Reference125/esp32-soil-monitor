"""
ESP32 Soil Moisture Monitor
----------------------------
Estação IoT para monitoramento da umidade do solo usando:
- ESP32
- Sensor YL-69
- Display OLED SSD1306 via I2C
- ThingSpeak

O projeto realiza uma leitura a cada intervalo configurado,
exibe o resultado no OLED e envia os dados para o ThingSpeak.

IMPORTANTE:
As credenciais ficam em config.py, que não deve ser versionado.
"""

from machine import Pin, ADC, I2C
import network
import time
import urequests

from ssd1306 import SSD1306_I2C
from config import WIFI_SSID, WIFI_PASSWORD, THINGSPEAK_WRITE_API_KEY


# ==============================================================
# CONFIGURAÇÕES DE HARDWARE E APLICAÇÃO
# ==============================================================

# GPIO conectado ao AOUT do YL-69.
# GPIO4 pertence ao ADC2 no ESP32 clássico e conflita com o Wi-Fi.
SENSOR_ADC_PIN = 4

# GPIO usado para alimentar o sensor somente durante a medição.
SENSOR_POWER_PIN = 23

# Pinos do barramento I2C.
I2C_SDA_PIN = 21
I2C_SCL_PIN = 22

# Endereço I2C mais comum dos displays SSD1306.
OLED_I2C_ADDR = 0x3C

# Resolução do OLED.
OLED_WIDTH = 128
OLED_HEIGHT = 64

# Intervalo entre leituras, em minutos.
READ_INTERVAL_MIN = 20

# Valores obtidos durante a calibração.
# ADC_DRY = leitura com sensor seco.
# ADC_WET = leitura com sensor molhado.
ADC_DRY = 45000
ADC_WET = 15000


# ==============================================================
# INICIALIZAÇÃO DOS COMPONENTES
# ==============================================================

# Controla a alimentação do sensor.
sensor_power = Pin(SENSOR_POWER_PIN, Pin.OUT)
sensor_power.off()

# Inicializa o ADC.
adc = ADC(Pin(SENSOR_ADC_PIN))

# Atenuação para permitir uma faixa de entrada maior.
adc.atten(ADC.ATTN_11DB)

# Inicializa o barramento I2C.
i2c = I2C(
    0,
    sda=Pin(I2C_SDA_PIN),
    scl=Pin(I2C_SCL_PIN),
    freq=100000
)

# Inicializa o display OLED.
oled = SSD1306_I2C(
    OLED_WIDTH,
    OLED_HEIGHT,
    i2c,
    addr=OLED_I2C_ADDR
)

# Inicializa a interface Wi-Fi no modo Station.
wlan = network.WLAN(network.STA_IF)


# ==============================================================
# WI-FI
# ==============================================================

def wifi_connect(timeout_s=15):
    """Ativa o Wi-Fi e tenta conectar ao roteador."""

    wlan.active(True)

    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        while not wlan.isconnected() and timeout_s > 0:
            time.sleep(1)
            timeout_s -= 1

    return wlan.isconnected()


def wifi_off():
    """Desconecta e desativa o Wi-Fi."""

    if wlan.active():
        wlan.disconnect()

    wlan.active(False)


# ==============================================================
# LEITURA DO SENSOR
# ==============================================================

def read_moisture():
    """
    Realiza a leitura do YL-69 e converte o valor bruto para %.

    Retorna:
        raw: valor bruto do ADC.
        pct: umidade estimada entre 0 e 100%.
    """

    # O ADC2 não deve ser utilizado com o Wi-Fi ativo.
    sensor_power.on()

    # Aguarda a alimentação do sensor estabilizar.
    time.sleep_ms(150)

    # read_u16() retorna um valor de 0 a 65535.
    raw = adc.read_u16()

    # Desliga o sensor após a medição.
    sensor_power.off()

    # Evita divisão por zero caso a calibração esteja inválida.
    span = ADC_DRY - ADC_WET

    if span != 0:
        pct = (ADC_DRY - raw) * 100 // span
    else:
        pct = 0

    # Mantém o resultado entre 0 e 100%.
    pct = max(0, min(100, pct))

    return raw, pct


# ==============================================================
# DISPLAY
# ==============================================================

def update_oled(pct, wifi_ok):
    """Atualiza o display OLED com a umidade e o estado do Wi-Fi."""

    oled.fill(0)

    oled.text("Umidade do solo", 0, 0)
    oled.text("{}%".format(pct), 0, 24)
    oled.text("Wifi OK" if wifi_ok else "Sem Wifi", 0, 48)

    oled.show()


# ==============================================================
# THINGSPEAK
# ==============================================================

def send_thingspeak(pct, raw):
    """
    Envia os dados para o ThingSpeak.

    Field 1 = umidade (%)
    Field 2 = leitura bruta do ADC
    """

    url = (
        "http://api.thingspeak.com/update?"
        "api_key={}&field1={}&field2={}"
    ).format(
        THINGSPEAK_WRITE_API_KEY,
        pct,
        raw
    )

    try:
        response = urequests.get(url)
        response.close()

        print("Dados enviados ao ThingSpeak.")
        return True

    except Exception as error:
        print("Erro ao enviar para o ThingSpeak:", error)
        return False


# ==============================================================
# PROGRAMA PRINCIPAL
# ==============================================================

def main():
    """Executa continuamente o ciclo de monitoramento."""

    while True:

        # 1. Desliga o Wi-Fi para liberar o ADC2.
        wifi_off()

        # 2. Faz a leitura do sensor.
        raw, pct = read_moisture()

        print(
            "Leitura -> raw: {} | umidade: {}%".format(
                raw,
                pct
            )
        )

        # 3. Liga o Wi-Fi.
        wifi_ok = wifi_connect()

        # 4. Envia os dados para a nuvem.
        if wifi_ok:
            send_thingspeak(pct, raw)
        else:
            print("Falha ao conectar no Wi-Fi.")

        # 5. Atualiza o display.
        update_oled(pct, wifi_ok)

        # 6. Desliga o Wi-Fi enquanto aguarda o próximo ciclo.
        wifi_off()

        # 7. Aguarda o próximo ciclo.
        time.sleep(READ_INTERVAL_MIN * 60)


# ==============================================================
# PONTO DE ENTRADA
# ==============================================================

if __name__ == "__main__":
    main()
