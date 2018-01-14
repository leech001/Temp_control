# Комнатный термостат или терморегулятор на Orange PI
Проект комнатного термостата или терморегулятора (контроль температуры) с управлением насосами на Oprange PI с использованием управления через Telegram.

## Цели
1. Автоматизация работы газового котла взагородном доме;
2. Удаленный котроль за состоянием отопления;
3. Удаленное управление режимом отопления.
4. Управление насосами отопления.


# Room thermostat or the thermostat on the Orange PI
Project room thermostat or the thermostat (temperature control) with pump control at Oprange with the use of PI control via Telegram.

## Goals
1. Automation of gas boiler zagorodnom house;
2. Remote monitor the state of heating;
3. Remote control of heating.
4. Pump control heating.

## Решения (Solution)
1. Аппаратные (Hardware)
   1. Orange PI (https://ru.aliexpress.com/item/Orange-Pi-PC-Plus-SET2-Orange-Pi-PC-Plus-Transparent-ABS-Case-Supported-Android-Ubuntu-Debian/32668333407.html)
   2. DALLAS DS18B20 (https://ru.aliexpress.com/item/5pcs-DALLAS-DS18B20-18B20-18S20-TO-92-IC-CHIP-Thermometer-Temperature-Sensor/32236763433.html)
   3. Four Channel Relay Module interface Board Shield 5V (https://ru.aliexpress.com/item/1pcs-lot-4-channel-relay-module-4-channel-relay-control-board-with-optocoupler-Relay-Output-4/32340914033.html?spm=a2g0s.9042311.0.0.8Ihmg6)
2. Программные решения (Software)
   1. Python 3.5
   2. Telepot
   3. gpio_pyH3
   
## Активация 1-Wire интерфейса в Orange PI
```
root@orangepipcplus:/etc# cat modules

8189fs
w1-sunxi
w1-gpio
w1-therm
#gc2035
#vfe_v4l2
#sunxi-cir
```
**Шина 1-Wire в Orange PI работает только на 37 порту! (GPIO.26 or PA.20)**

![GPIO](https://github.com/leech001/Temp_control/blob/master/pic/DS1820B.png?raw=true)

![GPIO](http://yonec.pl/data/uploads/orange-pi-plus-5.png)

![GPIO](https://cdn-images-1.medium.com/max/800/1*pcfeGQr_mUJrXDFDrdKMww.png)

## Установка Python library on controlling GPIO pins, I2C and SPI buses

https://github.com/duxingkei33/orangepi_PC_gpio_pyH3

## Установка Python framework for Telegram Bot API

https://github.com/nickoala/telepot

## Аналогичные проекты

http://home-smart-home.ru/telegram-bot-raspberry-pi-signalizaciiya-control/

