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
        self.count_pulse = 0
        self.duration_pulses = 2 # Максимальная длительность в течение, которой ппоступают импульсы
        self.last_time_pulse = 0

        self.start_time_from_pulse = 0
        
        # Инициализация GPIO
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        # Настройка пина как вход
        GPIO.setup(self.GPIO_board_port, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Пин монетоприемника
        # Настройка прерывания
        GPIO.add_event_detect(self.GPIO_board_port, GPIO.FALLING, callback=self.count_coin, bouncetime=100)

        system_loop_thread = threading.Thread(target=self.system_loop)
        system_loop_thread.setDaemon(True)
        system_loop_thread.start()
                        
    #Функция которая вызывается по прерыванию от монетоприемника
    def count_coin(self, channel):
        if(self.coin_running == False):
            self.coin_running = True
            self.start_time_from_pulse = time.time()
        self.count_pulse += 1
        print(f"Количество импульсов: {self.count_pulse}")    

    def system_loop(self):  
        while True:
            if(self.coin_running):
                if(time.time() - self.start_time_from_pulse >= self.duration_pulses):
                    print(f"Поступила монета номиналом: {self.count_pulse}")
                    self.credit_coin_list.append(self.count_pulse)
                    self.start_time_from_pulse = 0
                    self.count_pulse = 0
                    self.coin_running = False

    def get_last_credit_cash_from_list(self):
        pass

                    



                    
            

        
