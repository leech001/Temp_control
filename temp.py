# -*- coding: utf-8 -*-

import datetime
import os
import sqlite3
import sys
import time

import telepot
from apscheduler.schedulers.blocking import BlockingScheduler
from pyA20.gpio import gpio
from pyA20.gpio import port
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, \
    ForceReply, InlineKeyboardButton, InlineQueryResultArticle, InlineQueryResultPhoto, InputTextMessageContent

conn = sqlite3.connect('/usr/local/src/tempcontrol/temp.sqlite', check_same_thread=False)
db = conn.cursor()

rele = port.PA1
pomp_1 = port.PA0
pomp_2 = port.PA3

a_pomp_1 = 1
a_pomp_2 = 1

gpio.init()
gpio.setcfg(rele, gpio.OUTPUT)
gpio.setcfg(pomp_1, gpio.OUTPUT)
gpio.setcfg(pomp_2, gpio.OUTPUT)

token = 'TOKEN'  # TempBot #Токен к Telegram боту
bot = telepot.Bot(token)

hysteresis = 0.5  # Гистерезис температуры комнатного термостата
temp = 24.0  # Начальная температура комнатного термостата
heater = True  # Режим нагрева
t_notify = 180  # Интервал уведомлений (мин)

message_with_inline_keyboard = None
s_temp = False
s_notify = False


def get_temperature(idW1):
    filepath = '/sys/devices/w1_bus_master1/' + idW1 + '/w1_slave'
    f = open(filepath, 'r')
    data = f.read()
    f.close()
    return float(data[data.find('t=') + 2:]) / 1000


def on_chat_message(msg):
    global s_temp, temp, s_notify, t_notify, pomp_1, pomp_2, a_pomp_1, a_pomp_2

    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type == 'text':
        command = msg['text']
        if command == '/start' or command == '/start@LeechDacha_bot':
            markup = ReplyKeyboardMarkup(keyboard=[
                [dict(text='Инфо'), dict(text='Управление'), dict(text='Сигнализация')]
            ], resize_keyboard=True)
            bot.sendMessage(chat_id, 'Привет! Я дачный бот. Выбери раздел', reply_markup=markup)

        elif command == 'Главное меню':
            markup = ReplyKeyboardMarkup(keyboard=[
                [dict(text='Инфо'), dict(text='Управление'), dict(text='Сигнализация')]
            ], resize_keyboard=True)
            bot.sendMessage(chat_id, 'Выбери раздел', reply_markup=markup)

        elif command == u'Инфо':
            markup = ReplyKeyboardMarkup(keyboard=[
                [dict(text='Температура'), dict(text='Уст. температура')],
                [dict(text='Режим нагрева'), dict(text='Главное меню')],
            ], resize_keyboard=True)
            bot.sendMessage(chat_id, 'Выбери объект', reply_markup=markup)

        elif command == u'Температура':
            bot_temp(chat_id)

        elif command == u'Уст. температура':
            bot.sendMessage(chat_id, 'Установленная температура %s C' % temp)

        elif command == u'Режим нагрева':
            bot.sendMessage(chat_id, 'Идет нагрев %s' % heater)

        elif command == u'Управление':
            markup = InlineKeyboardMarkup(inline_keyboard=[[dict(text='Задать температуру', callback_data='temp_set')]])
            bot.sendMessage(chat_id, 'Выбери объект', reply_markup=markup)

            markup = ReplyKeyboardMarkup(keyboard=[
                [dict(text='Насос №2 АВТО'), dict(text='Насос №2 ВКЛ'), dict(text='Насос №2 ВЫКЛ')],
                [dict(text='Насос №1 АВТО'), dict(text='Насос №1 ВКЛ'), dict(text='Насос №1 ВЫКЛ')],
                [dict(text='Главное меню')],
            ], resize_keyboard=True)
            bot.sendMessage(chat_id, 'Выбери объект', reply_markup=markup)

        elif command == u'Насос №1 АВТО':
            a_pomp_1 = 1
            bot.sendMessage(chat_id, 'Включен авто режим для насоса №1 ')

        elif command == u'Насос №2 АВТО':
            a_pomp_2 = 1
            bot.sendMessage(chat_id, 'Включен авто режим для насоса №2 ')

        elif command == u'Насос №1 ВКЛ':
            a_pomp_1 = 0
            gpio.output(pomp_1, 0)
            bot.sendMessage(chat_id, 'Включен насос №1 ')

        elif command == u'Насос №2 ВКЛ':
            a_pomp_2 = 0
            gpio.output(pomp_2, 0)
            bot.sendMessage(chat_id, 'Включен насос №2 ')

        elif command == u'Насос №1 ВЫКЛ':
            a_pomp_1 = 0
            gpio.output(pomp_1, 1)
            bot.sendMessage(chat_id, 'Выключен насос №1 ')

        elif command == u'Насос №2 ВЫКЛ':
            a_pomp_2 = 0
            gpio.output(pomp_2, 1)
            bot.sendMessage(chat_id, 'Выключен насос №2 ')

        elif command == u'Сигнализация':
            markup = InlineKeyboardMarkup(
                inline_keyboard=[[dict(text='Задать период оповещения', callback_data='notify_set')]])
            bot.sendMessage(chat_id, 'Выбери объект', reply_markup=markup)

        if s_temp:
            # если происходит установка температуры
            if command.isdigit():
                temp = int(command)
                markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Главное меню')]], resize_keyboard=True)
                bot.sendMessage(chat_id, str("Температура установлена в %s градусов.") % command, reply_markup=markup)
                s_temp = False
            else:
                markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Главное меню')]], resize_keyboard=True)
                bot.sendMessage(chat_id, str(
                    "%s - это не целое число. При необходимости пройдите настройку заново. Значение не установлено!") % command,
                                reply_markup=markup)
                s_temp = False

        if s_notify:
            # если происходит установка периода оповещения
            if command.isdigit():
                job_notify.reschedule('interval', minutes=int(command))
                markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Главное меню')]], resize_keyboard=True)
                bot.sendMessage(chat_id, str("Период оповещения каждые %s минут.") % command, reply_markup=markup)
                s_notify = False
            else:
                markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Главное меню')]], resize_keyboard=True)
                bot.sendMessage(chat_id, str(
                    "%s - это не целое число. При необходимости пройдите настройку заново. Значение не установлено!") % command,
                                reply_markup=markup)
                s_notify = False


def on_callback_query(msg):
    global s_temp, s_notify
    query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
    if data == 'temp_set':
        s_temp = True
        bot.answerCallbackQuery(query_id, text='Установите температуру. Введите целое число в градусах.',
                                show_alert=True)
    elif data == 'notify_set':
        s_notify = True
        bot.answerCallbackQuery(query_id, text='Установите период оповещения. Введите целое число в минутах.',
                                show_alert=True)


def timed_send():
    bot_temp(111111111)  # DachaGroup # You ID or ID group


def bot_temp(chat_id):
    bot.sendMessage(chat_id, "Температура выхода котла: %s\n" \
                             "Температура входа котла: %s\n" \
                             "Температура в помещении: %s\n" % (
                        get_temperature('28-0316b2ec9aff'),
                        get_temperature('28-0316b306ffff'),
                        get_temperature('28-0516a16bcbff')))


def add_temp():
    db.execute("INSERT INTO temp_control (date,temp, temp_s, heater) VALUES ('%s','%s','%s','%s')" % (
        datetime.datetime.now(), get_temperature('28-0516a16bcbff'), temp, heater))
    conn.commit()


def temp_control():
    global heater
    r_temp = get_temperature('28-0516a16bcbff')
    if 0.0 <= r_temp <= 75:
        if r_temp <= (temp - hysteresis):
            gpio.output(rele, 0)
            if a_pomp_1 == 1:
                gpio.output(pomp_1, 0)
            if a_pomp_2 == 1:
                gpio.output(pomp_2, 0)
            heater = True
        elif r_temp >= (temp + hysteresis):
            gpio.output(rele, 1)
            if a_pomp_1 == 1:
                gpio.output(pomp_1, 1)
            if a_pomp_2 == 1:
                gpio.output(pomp_2, 1)
            heater = False
        add_temp()


bot.message_loop({'chat': on_chat_message,
                  'callback_query': on_callback_query})
print('Listening ...')

scheduler = BlockingScheduler()
job_notify = scheduler.add_job(timed_send, 'interval', minutes=t_notify)
job_temp = scheduler.add_job(temp_control, 'interval', seconds=5)
scheduler.start()

while 1:
    time.sleep(10)
