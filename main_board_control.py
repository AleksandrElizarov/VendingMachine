import threading
from time import sleep
import logging
import sys
import time
from pygame.locals import *
import pygame

from eSSP.constants import Status
from eSSP import eSSP
import RPi.GPIO as GPIO


PRICE_WATER = 3 #Цена за 1литр
COM_PORT = "/dev/ttyUSB0" # Название последовательного порта
PIN_INPUT_SENSOR_FLOW = 32 # Пин датчика жидкости
PIN_INPUT_OZON = 40 # Пин датчика жидкости
PIN_INPUT_START = 38 # Пин кнопки старт
PIN_INPUT_STOP = 36 # Пин кнопики стоп

PIN_OUTPUT_VALVE = 37 # Пин клапана для выдачи воды
PIN_OUTPUT_OZON = 35 # Пин включения озонатора

MILLILITRE_PULSE = 0.00222 #параметры датчика потока воды 1000мл=450пульов или 0,0022мл=1пульс

liquid_available = 0 #оплаченный обьем для выдачи

validator = None

ozon_running = False
duration_ozon_running = 10 #Время в секундах работы озонатора

# Установка времени работы программы
start_time = time.time()
duration = 50  # время работы программы в секундах


FONT_SIZE = 120  # Размер шрифта

BACKGROUND_COLOR = (0, 0, 128)  # Цвет фона синий (0, 0, 128) серый 242, 242, 240) 
BACKGROUND_COLOR_ALARM = (128, 128, 128)  # Цвет фона серый

TEXT_COLOR = (255, 255, 255)  # Цвет шрифта белый (255, 255, 255)
TEXT_COLOR_ALARM = (255, 255, 0)  # Цвет шрифта желтый


# Инициализация GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Настройка пина как вход
GPIO.setup(PIN_INPUT_SENSOR_FLOW, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Пин датчика жидкости
GPIO.setup(PIN_INPUT_OZON, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Пин кнопки Озонатора
GPIO.setup(PIN_INPUT_START, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Пин кнопки СТАРТ
GPIO.setup(PIN_INPUT_STOP, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Пин кнопки СТОП


# Настройка пина как выход
GPIO.setup(PIN_OUTPUT_VALVE, GPIO.OUT) # Пин клапана для выдачи воды
GPIO.output(PIN_OUTPUT_VALVE, GPIO.LOW)

GPIO.setup(PIN_OUTPUT_OZON, GPIO.OUT) # Пин озонатора
GPIO.output(PIN_OUTPUT_OZON, GPIO.LOW)

# Функция, которая будет вызываться по прерыванию RAISING от датчика потока жижкости
def count_liquid(channel):
    global liquid_available
    if(liquid_available > 0):
        liquid_available = liquid_available - MILLILITRE_PULSE
    if(liquid_available <= 0):
        liquid_available = 0
        #Выключаем нагрузки
        GPIO.output(PIN_OUTPUT_VALVE, GPIO.LOW)
        GPIO.output(PIN_OUTPUT_OZON, GPIO.LOW)
        
#Функция для обработки кнопки СТОП
def stop_flow(channel):
    print('STOP_valve')
    GPIO.output(PIN_OUTPUT_VALVE, GPIO.LOW)
    
#Функция для обработки кнопки СТАРТ
def start_flow(channel):
    if(liquid_available > 0):
        print('START_valve')
        GPIO.output(PIN_OUTPUT_VALVE, GPIO.HIGH)
        
                               
    
# Настройка прерывания
GPIO.add_event_detect(PIN_INPUT_SENSOR_FLOW, GPIO.FALLING, callback=count_liquid, bouncetime=5)

GPIO.add_event_detect(PIN_INPUT_START, GPIO.FALLING, callback=start_flow, bouncetime=300)
GPIO.add_event_detect(PIN_INPUT_STOP, GPIO.FALLING, callback=stop_flow, bouncetime=300)

# Инициализация Pygame
pygame.init()
# Фиксированный размер шрифта
font = pygame.font.SysFont(None, FONT_SIZE)

# Установка размера экрана
screen_width = 1300
screen_height = 350
#screen = pygame.display.set_mode((screen_width, screen_height))

screen = pygame.display.set_mode((0, 0), FULLSCREEN)
pygame.display.set_caption('Vending Machine Display')



 
# Основной цикл программы
main_loop_running = True
while main_loop_running:
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # Обработка события закрытия окна
            main_loop_running = False
        elif event.type == pygame.KEYDOWN:
            # Обработка события нажатия клавиши (например, ESC)
            if event.key == pygame.K_ESCAPE:
                main_loop_running = False    
    
    try:
        #Экемпляр купюроприемника
        if(validator == None):
            validator = eSSP(com_port=COM_PORT, ssp_address="0", nv11=False, debug=True)
        else:
            if(validator.running == False):
                raise Exception("Validator disconnected")
                
            
            
        #Если внесена оплата, то вывести на диспле сумму и увеличить доступный обьем
        credit_cash = validator.get_last_credit_cash()
        if(credit_cash > 0):
            liquid_available = liquid_available + credit_cash/PRICE_WATER
            # Создание текста
            text_credit_cash1 = f"ВНЕСЕНО:  {credit_cash} сом"
            text_surface_credit_cash1 = font.render(text_credit_cash1, True, TEXT_COLOR) 
            # Определение координат для текста
            text_credit_cash_rect1 = text_surface_credit_cash1.get_rect(topleft=(130, 300))  # координаты 
            # Заполнение экрана
            screen.fill(BACKGROUND_COLOR)
            # Рисование текста на экране
            screen.blit(text_surface_credit_cash1, text_credit_cash_rect1)
            # Обновление экрана
            pygame.display.flip()
            sleep(3)
        
        #Если произведена оплата и предоставлен доступный обьем воды для выдачи
        if(liquid_available > 0):
            input_state_bt_ozon = GPIO.input(PIN_INPUT_OZON)
            
            #Нажата кнопка ОЗОНАТОР
            if(input_state_bt_ozon == False):
                ozon_running = True
                GPIO.output(PIN_OUTPUT_OZON, GPIO.HIGH) #Включаем Озонатор
                time_ozon = duration_ozon_running
                sleep(0.1) #Дребезг контактов
                
            if(ozon_running):
                # Создание текста
                text_ozonator = f"Озонатор работает, {time_ozon} сек."
                text_surface_ozonator = font.render(text_ozonator, True, TEXT_COLOR) 
                # Определение координат для текста
                text_ozonator_rect = text_surface_ozonator.get_rect(topleft=(130, 150))  # координаты
                time_ozon = time_ozon - 1
                if(time_ozon < 0):
                    ozon_running = False
                    GPIO.output(PIN_OUTPUT_OZON, GPIO.LOW) #Выключаем Озонатор
                sleep(1)    
            else:
                # Создание текста
                text_ozonator = "Используйте озонатор"
                text_surface_ozonator = font.render(text_ozonator, True, TEXT_COLOR) 
                # Определение координат для текста
                text_ozonator_rect = text_surface_ozonator.get_rect(topleft=(130, 150))  # координаты 

            # Создание текста
            text_credit_cash1 = f"ДОСТУПНО:  {round(liquid_available, 2)} л."
            text_surface_credit_cash1 = font.render(text_credit_cash1, True, TEXT_COLOR) 
            # Определение координат для текста
            text_credit_cash_rect1 = text_surface_credit_cash1.get_rect(topleft=(130, 300))  # координаты 
            # Заполнение экрана
            screen.fill(BACKGROUND_COLOR)
            # Рисование текста на экране
            screen.blit(text_surface_ozonator, text_ozonator_rect)
            screen.blit(text_surface_credit_cash1, text_credit_cash_rect1)
            # Обновление экрана
            pygame.display.flip()
            
        else:
            #Выключаем нагрузки
            GPIO.output(PIN_OUTPUT_VALVE, GPIO.LOW)
            GPIO.output(PIN_OUTPUT_OZON, GPIO.LOW)
            # Создание текста
            text_line1 = "Добро пожаловать!"
            text_line2 = f"Стоимость: 1 литра = {PRICE_WATER} сома"
            text_line3 = "Пожалуста, внесите оплату."
            text_surface1 = font.render(text_line1, True, TEXT_COLOR)  
            text_surface2 = font.render(text_line2, True, TEXT_COLOR)
            text_surface3 = font.render(text_line3, True, TEXT_COLOR)

            # Определение координат для текста
            text_rect1 = text_surface1.get_rect(topleft=(250, 100))  # координаты 
            text_rect2 = text_surface2.get_rect(topleft=(70, 300))  # координаты
            text_rect3 = text_surface3.get_rect(topleft=(70, 500))  # координаты 

            # Заполнение экрана
            screen.fill(BACKGROUND_COLOR) 
                      
            # Рисование текста на экране
            screen.blit(text_surface1, text_rect1)
            screen.blit(text_surface2, text_rect2)
            screen.blit(text_surface3, text_rect3)

            # Обновление экрана
            pygame.display.flip()
            
        
    except Exception as e:
        #Выключаем нагрузки
        GPIO.output(PIN_OUTPUT_VALVE, GPIO.LOW)
        GPIO.output(PIN_OUTPUT_OZON, GPIO.LOW)
        # Создание текста
        text_alarm_line_1 = "Временные"
        text_alarm_line_1_surface = font.render(text_alarm_line_1, True, TEXT_COLOR_ALARM) 
        text_alarm_line_2 = "технические"
        text_alarm_line_2_surface = font.render(text_alarm_line_2, True, TEXT_COLOR_ALARM)
        text_alarm_line_3 = "неполадки"
        text_alarm_line_3_surface = font.render(text_alarm_line_3, True, TEXT_COLOR_ALARM)

        # Определение координат для текста
        text_alarm_line_1_rect = text_alarm_line_1_surface.get_rect(topleft=(380, 200))  
        text_alarm_line_2_rect = text_alarm_line_2_surface.get_rect(topleft=(380, 300)) 
        text_alarm_line_3_rect = text_alarm_line_3_surface.get_rect(topleft=(380, 400))   

        # Заполнение экрана
        screen.fill(BACKGROUND_COLOR_ALARM)
        
        # Рисование текста на экране
        screen.blit(text_alarm_line_1_surface, text_alarm_line_1_rect)
        screen.blit(text_alarm_line_2_surface, text_alarm_line_2_rect)
        screen.blit(text_alarm_line_3_surface, text_alarm_line_3_rect)
        
        # Обновление экрана
        pygame.display.flip()
        print(f'Exception-{e}')
        
    # Проверка времени работы программы
    if time.time() - start_time >= duration:
        break
#Выключаем нагрузки    
GPIO.output(PIN_OUTPUT_VALVE, GPIO.LOW)
GPIO.output(PIN_OUTPUT_OZON, GPIO.LOW)
pygame.quit()
sys.exit()
validator.close()  # Close the connection with the validator
    



