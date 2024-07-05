import threading
from time import sleep
import logging
import sys
import time
import RPi.GPIO as GPIO



class CoinPulseVN5(object):
    '''Pulse protocol to connected with coin acceptor'''
    def __init__(self, GPIO_board_port):
        self.GPIO_board_port = GPIO_board_port
        self.credit_coin_list = [] #Список поступивших монет
        
        self.coin_running = False
        self.count_pulse = 0
        self.duration_pulses = 2.7 # Максимальная длительность в течение, которой поступают импульсы(секунд)
        self.start_time_from_pulse = 0
        self.last_time_pulse = 0
        
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
                    #1 импульс = монете номинал 1
                    if(self.count_pulse == 1):
                        self.credit_coin_list.append(1)
                        print(f"Поступила монета номиналом: 1")
                    #5 импульсов = монете номинал 3
                    if(self.count_pulse == 5):
                        self.credit_coin_list.append(3)
                        print(f"Поступила монета номиналом: 3")
                    #10 импульсов = монете номинал 5
                    if(self.count_pulse == 10):
                        self.credit_coin_list.append(5)
                        print(f"Поступила монета номиналом: 5")
                    #20 импульсов = монете номинал 10
                    if(self.count_pulse == 20):
                        self.credit_coin_list.append(10)
                        print(f"Поступила монета номиналом: 10")    
                        
                    self.start_time_from_pulse = 0
                    self.count_pulse = 0
                    self.coin_running = False

    def get_last_credit_coin(self):
        """Get the last credit coin and delete from the credit list"""
        credit_coin = 0
        if(len(self.credit_coin_list) >= 1):
            credit_coin = self.credit_coin_list[len(self.credit_coin_list) - 1]
            self.credit_coin_list.pop(len(self.credit_coin_list) - 1)
        return credit_coin
        

                    



                    
            

        
