# ESP32 Soil Moisture Monitor 🌱

Estação IoT baseada em ESP32 para monitoramento da umidade do solo.

O sistema utiliza um sensor YL-69 para realizar a medição, apresenta o resultado em um display OLED SSD1306 e envia os dados para o ThingSpeak para acompanhamento remoto.

## Funcionalidades

- Leitura analógica da umidade do solo;
- Conversão da leitura ADC para porcentagem;
- Display OLED 128x64 via I2C;
- Envio dos dados para o ThingSpeak;
- Registro da leitura bruta do ADC;
- Alimentação do sensor somente durante a medição;
- Ciclo automático de medição;
- Tratamento básico de falhas de conexão Wi-Fi.

## Hardware

- ESP32;
- Sensor de umidade do solo YL-69;
- Display OLED SSD1306 128x64 I2C;
- Cabos jumper;
- Protoboard ou montagem definitiva;
- Fonte USB.

## Ligações

### YL-69

| YL-69 | ESP32 |
|---|---|
| AOUT | GPIO 4 |
| VCC | GPIO 23 |
| GND | GND |

O GPIO23 é utilizado como alimentação controlada do sensor. Dessa forma, o sensor permanece desligado durante a maior parte do tempo.

### OLED SSD1306

| OLED | ESP32 |
|---|---|
| VCC | 3V3 |
| GND | GND |
| SDA | GPIO 21 |
| SCL | GPIO 22 |

Endereço I2C padrão utilizado no projeto: `0x3C`.

Se o display não for detectado, alguns módulos utilizam `0x3D`.

## Atenção ao ADC2

O projeto utiliza o GPIO4, que pertence ao ADC2 do ESP32 clássico.

No ESP32, o ADC2 possui conflito com o controlador Wi-Fi. Por isso o programa segue esta sequência:

```text
Wi-Fi OFF
   ↓
Liga sensor
   ↓
Realiza leitura ADC
   ↓
Desliga sensor
   ↓
Wi-Fi ON
   ↓
Envia dados ao ThingSpeak
   ↓
Wi-Fi OFF
   ↓
Aguarda próximo ciclo
```

Uma melhoria futura seria mover o sensor para um canal ADC1, permitindo simplificar essa lógica.

## Software

O projeto utiliza [MicroPython](https://micropython.org/) no ESP32.

Também é necessário possuir o driver `ssd1306.py` no dispositivo.

## Instalação

### 1. Instale o MicroPython

Grave uma versão compatível do MicroPython no ESP32.

### 2. Envie os arquivos

O ESP32 deve conter:

```text
main.py
config.py
ssd1306.py
```

### 3. Configure as credenciais

Não edite o `config.example.py` diretamente.

Faça uma cópia:

```text
config.example.py → config.py
```

E preencha:

```python
WIFI_SSID = "SEU_WIFI"
WIFI_PASSWORD = "SUA_SENHA"
THINGSPEAK_WRITE_API_KEY = "SUA_CHAVE"
```

O arquivo `config.py` está no `.gitignore` e não deve ser enviado ao GitHub.

## ThingSpeak

Crie um canal no ThingSpeak e configure pelo menos dois campos:

- **Field 1:** Umidade (%)
- **Field 2:** Leitura bruta do ADC

O programa utiliza a API de atualização:

```text
api.thingspeak.com/update
```

A chave de escrita deve ser colocada apenas no `config.py`.

## Calibração

Os valores:

```python
ADC_DRY = 45000
ADC_WET = 15000
```

são exemplos.

A calibração deve ser realizada com o próprio sensor.

### Sensor seco

1. Deixe o sensor fora da água e do solo.
2. Execute o programa.
3. Observe o valor `raw` no terminal.
4. Use esse valor como `ADC_DRY`.

### Sensor molhado

1. Coloque o sensor em uma condição de solo muito úmido ou água.
2. Observe novamente o valor `raw`.
3. Use esse valor como `ADC_WET`.

Depois ajuste:

```python
ADC_DRY = valor_seco
ADC_WET = valor_molhado
```

### Importante

O YL-69 é um sensor resistivo e pode apresentar variações significativas conforme:

- composição do solo;
- temperatura;
- salinidade;
- posição das hastes;
- profundidade;
- estado de oxidação das hastes.

Portanto, a porcentagem representa uma **estimativa relativa de umidade**, e não uma medição laboratorial de teor de água.

## Estrutura do projeto

```text
esp32-soil-monitor/
│
├── main.py
├── ssd1306.py
├── config.example.py
├── .gitignore
├── LICENSE
└── README.md
```

O arquivo `config.py` existe apenas localmente:

```text
config.py
```

e não deve ser versionado.

## Fluxo do sistema

```text
                 ┌──────────────────┐
                 │      ESP32       │
                 └────────┬─────────┘
                          │
                    GPIO 23 / VCC
                          │
                          ▼
                  ┌───────────────┐
                  │    YL-69      │
                  └───────┬───────┘
                          │
                       AOUT
                          │
                          ▼
                    GPIO 4 / ADC
                          │
                          ▼
                 Cálculo da umidade
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
       Display OLED             Wi-Fi + ThingSpeak
         SSD1306                     ☁️
```

## Solução de problemas

### OLED não aparece

Verifique:

- SDA no GPIO21;
- SCL no GPIO22;
- alimentação em 3V3;
- GND;
- endereço I2C.

Tente:

```python
OLED_I2C_ADDR = 0x3D
```

se `0x3C` não funcionar.

### Umidade fica invertida

Se o sensor apresentar aproximadamente:

```text
100% = seco
0% = molhado
```

e isso não corresponder à calibração desejada, revise `ADC_DRY` e `ADC_WET`.

### Wi-Fi não conecta

Verifique:

- SSID;
- senha;
- alcance do roteador;
- se a rede está disponível para o ESP32.

### ThingSpeak não recebe dados

Verifique:

- API Key;
- conexão Wi-Fi;
- configuração dos Fields;
- resposta exibida no terminal serial.

## Melhorias futuras

Possíveis evoluções:

- migrar o sensor para ADC1;
- utilizar sensor capacitivo de umidade;
- adicionar DHT11/DHT22;
- monitorar temperatura e umidade do ar;
- implementar Deep Sleep;
- adicionar bateria;
- criar alarmes no ThingSpeak;
- adicionar LEDs de status;
- utilizar display LCD 16x2;
- criar uma caixa para montagem definitiva;
- armazenar leituras localmente quando o Wi-Fi estiver indisponível;
- adicionar média móvel e filtragem das leituras;
- criar dashboard para acompanhamento histórico.

## Licença

Este projeto está disponível sob a licença MIT.
