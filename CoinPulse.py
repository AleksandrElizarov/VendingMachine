import threading
from time import sleep
import logging
import sys
import time
import RPi.GPIO as GPIO



class CoinPulse(object):
    '''Pulse protocol to connected with coin acceptor'''
    def __init__(self, GPIO_board_port):
        self.GPIO_board_port = GPIO_board_port
        self.credit_coin_list = [] #Список поступивших монет
        
        self.coin_running = False
        self.duration_pulse = 0
        self.last_time_pulse = 0
        
        # Инициализация GPIO
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        # Настройка пина как вход
        GPIO.setup(GPIO_board_port, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Пин монетоприемника
        
        # Настройка прерывания
        GPIO.add_event_detect(GPIO_board_port, GPIO.FALLING, callback=count_coin, bouncetime=100)
                        
    #Функция которая вызывается по прерыванию от монетоприемника
    def count_coin(channel):
       
        print(f'PULSE: {time.time() - last_time_pulse}')
        last_time_pulse = time.time()
        coin_counter += 1
        print(f"Количество импульсов: {coin_counter}")        
            

        
