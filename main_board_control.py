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


PRICE_WATER = 30 #Цена за 1литр
COM_PORT = "/dev/ttyUSB0" # Название последовательного порта
PIN_SENSOR_FLOW = 40 # Пин датчика жидкости
PIN_OUTPUT_VALVE = 36 # Пин клапана для выдачи воды

MILLILITRE_PULSE = 0.00222 #параметры датчика потока воды 1000мл=450пульов или 0,0022мл=1пульс

available_liquid = 0 #оплаченный обьем для выдачи




FONT_SIZE = 120  # Размер шрифта

BACKGROUND_COLOR = (0, 0, 128)  # Цвет фона синий (0, 0, 128)
BACKGROUND_COLOR_ALARM = (128, 128, 128)  # Цвет фона серый

TEXT_COLOR = (255, 255, 255)  # Цвет шрифта белый (255, 255, 255)
TEXT_COLOR_ALARM = (255, 255, 0)  # Цвет шрифта желтый



total_sum = 0
validator = None

# Установка времени работы программы
start_time = time.time()
duration = 50  # время работы программы в секундах


# Инициализация GPIO
GPIO.setmode(GPIO.BOARD)

# Настройка пина как вход
GPIO.setup(PIN_SENSOR_FLOW, GPIO.IN) # Пин датчика жидкости

# Настройка пина как выход
GPIO.setup(PIN_OUTPUT_VALVE, GPIO.OUT) # Пин клапана для выдачи воды


# Функция, которая будет вызываться по прерыванию RAISING
def count_liquid(channel):
    global available_liquid
    if(available_liquid > 0):
        available_liquid = available_liquid - MILLILITRE_PULSE
    if(available_liquid <= 0):
        available_liquid = 0

# Настройка прерывания
GPIO.add_event_detect(PIN_SENSOR_FLOW, GPIO.RISING, callback=count_liquid, bouncetime=5)


# Инициализация Pygame
pygame.init()
# Фиксированный размер шрифта
font = pygame.font.SysFont(None, FONT_SIZE)

# Установка размера экрана
screen_width = 1000
screen_height = 320
#screen = pygame.display.set_mode((screen_width, screen_height))

screen = pygame.display.set_mode((0, 0), FULLSCREEN)
pygame.display.set_caption('Vending Machine Display')




# Основной цикл программы
while True:
    
    
    try:
        #Экемпляр купюроприемника
        if(validator == None):
            validator = eSSP(com_port=COM_PORT, ssp_address="0", nv11=False, debug=True)
            print(f'Objact-{validator}')
            
        #Если внесена оплата, то вывести на диспле сумму и увеличить доступный обьем
        credit_cash = validator.get_last_credit_cash()
        if(credit_cash > 0):
            available_liquid = available_liquid + credit_cash/PRICE_WATER
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
        if(available_liquid > 0):
            GPIO.output(PIN_OUTPUT_VALVE, GPIO.HIGH)
            
            # Создание текста
            text_credit_cash1 = f"ДОСТУПНО:  {round(available_liquid, 2)} л."
            text_surface_credit_cash1 = font.render(text_credit_cash1, True, TEXT_COLOR) 
            # Определение координат для текста
            text_credit_cash_rect1 = text_surface_credit_cash1.get_rect(topleft=(130, 300))  # координаты 
            # Заполнение экрана
            screen.fill(BACKGROUND_COLOR)
            # Рисование текста на экране
            screen.blit(text_surface_credit_cash1, text_credit_cash_rect1)
            # Обновление экрана
            pygame.display.flip()
            
        else:        
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
        sleep(duration)
        
        print(f'Exception-{e}')
        
    # Проверка времени работы программы
    if time.time() - start_time >= duration:
        break
    

pygame.quit()
sys.exit()
#validator.close()  # Close the connection with the validator
    


