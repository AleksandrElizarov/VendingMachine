import threading
from time import sleep
import logging
import sys
import time
from pygame.locals import *
import pygame

#from eSSP.constants import Status
#from eSSP import eSSP  


COM_PORT = "/dev/ttyUSB0" # Название последовательного порта

FONT_SIZE = 120  # Размер шрифта

BACKGROUND_COLOR = (255, 255, 200)  # Цвет фона синий (0, 0, 128)
BACKGROUND_COLOR_ALARM = (255, 255, 0)  # Цвет фона желтый

TEXT_COLOR = (255, 255, 255)  # Цвет шрифта белый (255, 255, 255)


MILLILITRE_PULSE = 0.17 #параметры датчика потока воды 1000мл=5880пульов или 0,17мл=1пульс
available_volume = 0 #оплаченный обьем для выдачи


total_sum = 0
validator = None

# Установка времени работы программы
start_time = time.time()
duration = 1  # время работы программы в секундах


    # Инициализация Pygame
pygame.init()
# Фиксированный размер шрифта
font = pygame.font.SysFont(None, FONT_SIZE)

# Установка полноэкранного режима
screen = pygame.display.set_mode((0, 0), FULLSCREEN)
pygame.display.set_caption('Vending Machine Display')

# Создание текста
text_line1 = "Добро пожаловать,"
text_line2 = "внесите оплату!"
text_surface1 = font.render(text_line1, True, TEXT_COLOR)  # Белый текст для первой строки
text_surface2 = font.render(text_line2, True, TEXT_COLOR)  # Белый текст для второй строки

# Определение координат для текста
text_rect1 = text_surface1.get_rect(topleft=(320, 200))  # Пример: координаты (100, 100)
text_rect2 = text_surface2.get_rect(topleft=(320, 350))  # Пример: координаты (100, 200)

# Заполнение экрана
screen.fill(BACKGROUND_COLOR) 
      
# Рисование текста на экране
screen.blit(text_surface1, text_rect1)
screen.blit(text_surface2, text_rect2)




# Основной цикл программы
while True:
    # Проверка времени работы программы
    if time.time() - start_time >= duration:
        break
    
    try:
        #Экемпляр купюроприемника
        if(validator == None):
            validator = eSSP(com_port=COM_PORT, ssp_address="0", nv11=False, debug=True)
        
            
            #validator.get_last_credit_cash()
        

            # Обновление экрана
            pygame.display.flip()

        validator.close()  # Close the connection with the validator
        pygame.quit()
        sys.exit()

    except Exception as e:
        # Создание текста
        text_alarm_line_1 = "Временные"
        text_alarm_line_1_surface = font.render(text_alarm_line_1, True, TEXT_COLOR) 
        text_alarm_line_2 = "технические"
        text_alarm_line_2_surface = font.render(text_alarm_line_2, True, TEXT_COLOR)
        text_alarm_line_3 = "неполадки"
        text_alarm_line_3_surface = font.render(text_alarm_line_3, True, TEXT_COLOR)

        # Определение координат для текста
        text_alarm_line_1_rect = text_alarm_line_1_surface.get_rect(topleft=(330, 200))  
        text_alarm_line_2_rect = text_alarm_line_2_surface.get_rect(topleft=(330, 300)) 
        text_alarm_line_3_rect = text_alarm_line_3_surface.get_rect(topleft=(330, 400))   
    
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


