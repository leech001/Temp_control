# -*- coding: utf-8 -*-

import sys
import os
import time
import datetime
import telepot
from pyA20.gpio import gpio
from pyA20.gpio import port
from apscheduler.schedulers.blocking import BlockingScheduler

import sqlite3
conn = sqlite3.connect('temp.sqlite', check_same_thread=False)
db = conn.cursor()


"""
start - Начало работы
heater - Режим отопления
temp_s - Заданная температура
temp_set - Задать температуру (/temp_set Температура)
temp - Вывести температуру
notify - Уведомления
notify_change - Задать период уведомлений (/notify_change Период в минутах)
"""

rele = port.PA1 #Порт реле комнатного термостата
gpio.init()
gpio.setcfg(rele, gpio.OUTPUT)

token = '...'  #Токен к Telegram боту
bot = telepot.Bot(token)

hysteresis = 0.5 #Гистерезис температуры комнатного термостата
temp = 24.0 #Начальная температура комнатного термостата
heater = True #Режим нагрева
t_notify = 60 #Интервал уведомлений (мин)

def getTemperature(idW1):
    filepath = '/sys/devices/w1_bus_master1/' + idW1 + '/w1_slave'
    f = open(filepath, 'r')
    data = f.read()
    f.close()
    return float(data[data.find('t=') + 2:]) / 1000


def on_chat_message(msg):
    global temp
    global t_notify

    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type == 'text':
        command = msg['text']
        if command == '/start' or command == '/start@LeechDacha_bot':
            keyboard = {'keyboard': [['@Температура','@Заданная температура'], ['@Режим отопления', '@Уведомления']]}
            bot.sendMessage(chat_id, str('Привет! Я дачный бот. Чем могу быть полезен?'), reply_markup=keyboard)

        elif command == '/heater' or command == '/heater@LeechDacha_bot' or command == '@Режим отопления':
            bot.sendMessage(chat_id, str(heater))

        elif command == '/temp_s' or command == '/temp_s@LeechDacha_bot' or command == '@Заданная температура':
            bot.sendMessage(chat_id, 'Заданная температура ' + str(temp) + ' C')

        elif command.startswith('/temp_set') or command.startswith('/temp_set@LeechDacha_bot'):
            temp = command.replace('/temp_set@LeechDacha_bot', '')
            temp = float(temp.replace('/temp_set', ''))
            bot.sendMessage(chat_id, 'Температура установлена на '+ str(temp) + ' C')

        elif command == '/temp' or command == '/temp@LeechDacha_bot' or command == '@Температура':
            bot_temp(chat_id)

        elif command == '/notify' or command == '/notify@LeechDacha_bot' or command == '@Уведомления':
            bot.sendMessage(chat_id, 'Уведомления каждые ' + str(t_notify) + ' минут')

        elif command.startswith('/notify_change') or command.startswith('/notify_change@LeechDacha_bot'):
            t_notify = command.replace('/notify_change@LeechDacha_bot', '')
            t_notify = int(t_notify.replace('/notify_change', ''))
            job_notify.reschedule('interval', minutes=t_notify)
            bot.sendMessage(chat_id, 'Заданные уведомления каждые ' + str(t_notify) + ' минут')

def timed_send():
    bot_temp(...)  # You ID or ID group

def bot_temp(chat_id):
    bot.sendMessage(chat_id, 'Температура выхода котла: ' + str(getTemperature('28-0316b2ec9aff')) + ' C\n'
                             'Температура входа котла: ' + str(getTemperature('28-0316b306ffff')) + ' C\n'
                             'Температура в помещении: ' + str(getTemperature('28-0516a16bcbff')) + ' C')

def add_temp():
    db.execute("INSERT INTO temp_control (date,temp, temp_s, heater) VALUES ('%s','%s','%s','%s')" % (datetime.datetime.now(), getTemperature('28-0516a16bcbff'), temp, heater))
    conn.commit()

def temp_control():
    global heater
    r_temp = getTemperature('28-0516a16bcbff')
    if 0 <= r_temp <=100:
        if r_temp <= (temp-hysteresis):
            gpio.output(rele, 0)
            heater = True
        elif r_temp >= (temp+hysteresis):
            gpio.output(rele, 1)
            heater = False
        add_temp()

bot.message_loop({'chat': on_chat_message})
print ('Listening ...')

scheduler = BlockingScheduler()
job_notify = scheduler.add_job(timed_send, 'interval', minutes=t_notify)
job_temp  = scheduler.add_job(temp_control, 'interval', seconds=5)
scheduler.start()

while 1:
    time.sleep(10)
