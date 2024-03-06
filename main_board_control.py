import threading
from time import sleep
import logging
import sys
import time
from pygame.locals import *

from eSSP.constants import Status
from eSSP import eSSP  
import pygame


MILLILITRE_PULSE = 0.17 #параметры датчика потока воды 1000мл=5880пульов или 0,17мл=1пульс
available_volume = 0 #оплаченный обьем для выдачи

#Экемпляр купюроприемника
#validator = eSSP(com_port="/dev/ttyUSB0", ssp_address="0", nv11=False, debug=True)


total_sum = 0

# Инициализация Pygame
pygame.init()

# Установка полноэкранного режима
info = pygame.display.Info()
screen = pygame.display.set_mode((0, 0), FULLSCREEN)
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h
pygame.display.set_caption('Vending Machine Display')

# Фиксированный размер шрифта
font_size = 120
font = pygame.font.SysFont(None, font_size)

# Создание текста
text_line1 = "Добро пожаловать,"
text_line2 = "внесите оплату!"
text_surface1 = font.render(text_line1, True, (255, 255, 255))  # Белый текст для первой строки
text_surface2 = font.render(text_line2, True, (255, 255, 255))  # Белый текст для второй строки
background_color = (0, 0, 128)  # Синий фон

# Установка времени работы программы
start_time = time.time()
duration = 7  # время работы программы в секундах

# Определение координат для текста
text_rect1 = text_surface1.get_rect(topleft=(320, 200))  # Пример: координаты (100, 100)
text_rect2 = text_surface2.get_rect(topleft=(320, 350))  # Пример: координаты (100, 200)

# Основной цикл программы
while True:
    screen.fill(background_color)  # Заполнение экрана синим цветом

    #validator.get_last_credit_cash()
    # Рисование текста на экране
    screen.blit(text_surface1, text_rect1)
    screen.blit(text_surface2, text_rect2)

    # Проверка времени работы программы
    if time.time() - start_time >= duration:
        break

    # Обновление экрана
    pygame.display.flip()

pygame.quit()
sys.exit() 
validator.close()  # Close the connection with the validator

