import threading
from time import sleep
from typing import Callable, Tuple
import json
import sys
import os
import time
from datetime import datetime
import io
from pygame.locals import *
import pygame
import requests
from PIL import Image
import psutil
from loguru import logger
logger.add('logs/logs.log', rotation='10MB')

import platform
##### Проверяем на какой операционной системе запущен скрипт, и соответственно импортируем модули #####
# Получаем имя операционной системы
os_name = platform.system()

if os_name == "Linux":
    logger.info("Скрипт запущен на Linux")
    import RPi.GPIO as GPIO
    from CoinInterface.CoinPulseHX916 import CoinPulseHX916
    coin_pulse = CoinPulseHX916(GPIO_board_port=31) 
  
elif os_name == "Windows":
    logger.info("Скрипт запущен на Windows")
    from Stub_Win_GPIO_Coin.GPIO import GPIO
    from Stub_Win_GPIO_Coin.CoinPulseHX916 import CoinPulseHX916

    coin_pulse = CoinPulseHX916 

else:
    logger.info("Скрипт запущен на другой операционной системе")    


##################### VERIABLES GLOBAL #####################
SERIAL_NUMBER_MACHINE = '1111111'
DOMAIN = 'https://monitorvending.pythonanywhere.com/'

#URL get QR-code by GET-method query str 'serial_number_machine'
url_get_qr_code = f'{DOMAIN}get_qr_code/'
#URL refresh states alarm and get info about amount mwallet GET-method query str 'serial_number_machine','main_power',open_door',low_water'
url_refresh_states_alarm_get_mwallet_amount = f'{DOMAIN}refresh_states_alarm_machine/'
#URL create coin transaction in DataBase POST method {"serial_number_machine": "64-number", "coin_amount": coin_amount}
url_create_coin_transaction = f'{DOMAIN}create_transaction/'

COM_PORT = "/dev/ttyUSB0" # Название последовательного порта
PIN_INPUT_SENSOR_FLOW = 32 # Пин датчика жидкости

PIN_INPUT_OZON = 40 # Пин кнопки Озонатора
PIN_INPUT_START = 38 # Пин кнопки старт
PIN_INPUT_STOP = 36 # Пин кнопики стоп

PIN_INPUT_MAIN_POWER = 33 # Пин входа оценки электропитания
PIN_INPUT_OPEN_DOOR = 28 # Пин открытия двери
PIN_INPUT_LOW_WATER = 29 # Пин оценки уровня воды

PIN_OUTPUT_VALVE = 37 # Пин клапана для выдачи воды
PIN_OUTPUT_OZON = 35 # Пин включения озонатора

MILLILITRE_PULSE = 0.00222 #параметры датчика потока воды 1000мл=450пульов или 0,0022мл=1пульс

TOTAL_AMOUNT_AVAILABLE = 0 # общая сумма, внесенная через монетоприемник/Мобильный кошелек

LIQUID_AVAILABLE = 0 # оплаченный обьем для выдачи

AMOUNT_MWALLET = 0 # сумма оплаченная через Мобильный кошелек

LIST_TRANSACTION_COIN = [] # список сумм транзакций внесенных через монетоприемник


### VERIABLES ALARMS ###
MAIN_POWER = 'true'
OPEN_DOOR = 'false'
LOW_WATER = 'false'

PRICE_WATER = 3 #Цена за 1литр
DATE_FILTER_UPDATE = '2024-06-01' # дата обновления фильтра
QR_LOADED = False # Флаг успешной загрузки QR-кода


ozon_running = False # Флаг включения Озонатора
duration_ozon_running = 10 #Время в секундах работы озонатора


# Режим для мониторинга количества импульсов датчика жидкости
debug_flow_sensor_vision = True
number_pulse_sensor = 0


# Создание объекта блокировки
file_lock = threading.Lock()



##################### FUNCTION FUNCTION FUNCTION #####################
def init_GPIO():
    '''Инициализация всех GPIO портов'''

    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    # Настройка пина как вход
    GPIO.setup(PIN_INPUT_SENSOR_FLOW, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Пин датчика жидкости
    GPIO.setup(PIN_INPUT_OZON, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Пин кнопки Озонатора
    GPIO.setup(PIN_INPUT_START, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Пин кнопки СТАРТ
    GPIO.setup(PIN_INPUT_STOP, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Пин кнопки СТОП
    GPIO.setup(PIN_INPUT_MAIN_POWER, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Пин электропитания
    GPIO.setup(PIN_INPUT_OPEN_DOOR, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Пин двери
    GPIO.setup(PIN_INPUT_LOW_WATER, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Пин уровня воды

    # Настройка пина как выход
    GPIO.setup(PIN_OUTPUT_VALVE, GPIO.OUT) # Пин клапана для выдачи воды
    GPIO.output(PIN_OUTPUT_VALVE, GPIO.LOW)

    GPIO.setup(PIN_OUTPUT_OZON, GPIO.OUT) # Пин озонатора
    GPIO.output(PIN_OUTPUT_OZON, GPIO.LOW)

   
def set_output_GPIO(pin_input_board: int, gpio_state: str):
    '''Функция установки PIN'а в высокое или низкое состояние: LOW/HIGH'''
    if(gpio_state == "HIGH"):
        GPIO.output(pin_input_board, GPIO.HIGH)
    else:
        GPIO.output(pin_input_board, GPIO.LOW)


def count_liquid(channel):
    '''
    Функция, которая будет вызываться по прерыванию RAISING/FALLING от датчика потока жижкости
    '''
    global LIQUID_AVAILABLE
    global number_pulse_sensor
    if(LIQUID_AVAILABLE > 0):
        LIQUID_AVAILABLE = LIQUID_AVAILABLE - MILLILITRE_PULSE
        number_pulse_sensor = number_pulse_sensor + 1
    if(LIQUID_AVAILABLE <= 0):
        LIQUID_AVAILABLE = 0
        number_pulse_sensor = 0
        #Выключаем нагрузки
        set_output_GPIO(PIN_OUTPUT_VALVE, 'LOW')
        set_output_GPIO(PIN_OUTPUT_OZON, 'LOW')
        

def stop_flow(channel):
    '''Функция для обработки кнопки СТОП'''
    set_output_GPIO(PIN_OUTPUT_VALVE, 'LOW')
    

def start_flow(channel):
    '''Функция для обработки кнопки СТАРТ'''
    if(LIQUID_AVAILABLE > 0):
        set_output_GPIO(PIN_OUTPUT_VALVE, 'HIGH')
 
                         
def add_event_detect_GPIO(pin_input_board: int, edge: str, callback: Callable[[int], None], bouncetime: int) -> None:
    '''Настройка прерывания на портах GPIO''' 
    if(edge == 'RISING'):
        GPIO.add_event_detect(pin_input_board, GPIO.RISING, callback, bouncetime)
    else:
         GPIO.add_event_detect(pin_input_board, GPIO.FALLING, callback, bouncetime)  


def render_text_pygame(text: str, font, text_color: Tuple[int, int, int], topleft_point_position: Tuple[int, int]):
    # Создание текста
    text_surface = font.render(text, True, text_color) 
    # Определение координат для текста
    text_rect = text_surface.get_rect(topleft=topleft_point_position)  # координаты 
    # Рисование текста на экране
    screen.blit(text_surface, text_rect)


def loop_get_mwallet_push_alarm():
        '''Функция получения суммы оплаты через Мобильный кошелек и отправка состояния аварий'''
        global SERIAL_NUMBER_MACHINE
        global AMOUNT_MWALLET
        global url_refresh_states_alarm_get_mwallet_amount
        global MAIN_POWER
        global OPEN_DOOR 
        global LOW_WATER
        cpu_percent = 0.0
        cpu_temperature = 0.0
        virtual_memory = 0.0
        while True:
            ### Получение температуры и загрузки CPU и использование оперативной памяти
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                virtual_memory = psutil.virtual_memory()
                virtual_memory = virtual_memory.percent
                if os_name == "Linux":
                    # Температура процессора из системного файла
                    with open("/sys/class/thermal/thermal_zone0/temp") as f:
                        temp = f.read()
                    cpu_temperature = float(temp) / 1000.0  
                else:
                    cpu_temperature = 0.0
            except Exception as e:
                logger.exception(f'get_CPUparametrs_exception: {e}')

            ### Передача состояние аварий с сухих контактов и информации по CPU на сервер
            logger.info(f'cpu_percent: {cpu_percent}, cpu_temperature: {cpu_temperature}, virtual_memory: {virtual_memory}')
            try:
                params = {
                'serial_number_machine': SERIAL_NUMBER_MACHINE,
                    'main_power': MAIN_POWER,
                    'open_door': OPEN_DOOR,
                    'low_water': LOW_WATER,
                    'cpu_percent': cpu_percent,
                    'cpu_temperature': cpu_temperature,
                    'virtual_memory': virtual_memory
                }
                response = requests.get(url_refresh_states_alarm_get_mwallet_amount, params=params, timeout=5)
                data = response.json()
                AMOUNT_MWALLET = float(data['m_transactions_amount'])
                logger.info(data)
        
            except Exception as e:
                AMOUNT_MWALLET = 0
                logger.exception(f'refresh_states_alarm_get_mwallet_amount_exception: {e}')
            sleep(2)    
            


def loop_get_qr_code():
            '''Функция получения qr кода для оплаты, дату обновления фильтра и цену за литр'''
            global SERIAL_NUMBER_MACHINE
            global QR_LOADED
            global DATE_FILTER_UPDATE
            global PRICE_WATER
            global url_get_qr_code
            while True:
                try:
                    # Получение URL для QR кода
                    params = {'serial_number_machine': SERIAL_NUMBER_MACHINE}
                    response = requests.get(url_get_qr_code, params=params, timeout=5)

                    data = response.json()
                    logger.info(data)

                    # Загрузка изображения QR-кода по URL
                    if data['success']:
                        #Получаем qr_code
                        qr_url = data['qr_code']
                        #Получаем дату обновления фильтра
                        DATE_FILTER_UPDATE = data['date_filter_update']
                        PRICE_WATER = float(data['price'])
                        #Проверка наличия QR кода у аппарата
                        if qr_url == "":
                            QR_LOADED = False
                        else:
                            response = requests.get(qr_url, timeout=5)

                            if response.status_code == 200:
                                qr_image = Image.open(io.BytesIO(response.content))
                            else:
                                logger.error(f"Failed to retrieve QR code, status code: {response.status_code}")
                                QR_LOADED = False

                            # Изменение размера изображения до 40x40 пикселей
                            qr_image = qr_image.resize((250,250), Image.Resampling.BICUBIC)
                            
                            with file_lock:
                                qr_image.save("resized_qrcode.png")
                                logger.info("QR_image_SAVE")
                                QR_LOADED = True
                                
                except Exception as e:
                    QR_LOADED = False
                    logger.exception(f'get_qr_code_exception: {e}') 
                sleep(10)  


def loop_send_transaction_coin():
    '''Функция записи транзакции на сервер в базу данных о сумме внесенной через монетоприемник'''
    global SERIAL_NUMBER_MACHINE
    global url_create_coin_transaction
    global LIST_TRANSACTION_COIN    
    while True:
        if LIST_TRANSACTION_COIN:
            try:
                data = {"serial_number_machine": SERIAL_NUMBER_MACHINE, "coin_amount": LIST_TRANSACTION_COIN[len(LIST_TRANSACTION_COIN)-1]}   
                response = requests.post(url_create_coin_transaction, json=data)
                logger.info(f'send_transaction_coin: data:{data}, response:{response.json()}')
                LIST_TRANSACTION_COIN.pop()
            except Exception as e:
                    logger.exception(f'send_transaction_coin_exception: {e}') 
        sleep(1)  





##################### FONT SIZE #####################
FONT_SIZE = 80  # Размер шрифта
FONT_small_SIZE = 56  # Размер шрифта

BACKGROUND_COLOR = (0, 0, 128)  # Цвет фона синий (0, 0, 128) серый 242, 242, 240) 
BACKGROUND_COLOR_ALARM = (128, 128, 128)  # Цвет фона серый

TEXT_COLOR = (255, 255, 255)  # Цвет шрифта белый (255, 255, 255)
TEXT_COLOR_ALARM = (255, 255, 0)  # Цвет шрифта желтый


##################### INITIALIZATION PYGAME #####################
pygame.init()
# Фиксированный размер шрифта
font = pygame.font.SysFont(None, FONT_SIZE)
small_font = pygame.font.SysFont(None, FONT_small_SIZE)

# Установка размера экрана
screen_width = 200
screen_height = 200

if os_name == "Linux":
                screen = pygame.display.set_mode((0, 0), FULLSCREEN) 
else:
    screen = pygame.display.set_mode((screen_width, screen_height))


# Получение размеров экрана
screen_width, screen_height = screen.get_size()
# Вывод размеров экрана
logger.info(f'Ширина экрана: {screen_width}, Высота экрана: {screen_height}')

pygame.display.set_caption('Vending Machine Display')

# Скрытие курсора мыши
pygame.mouse.set_visible(False)

 
init_GPIO()
add_event_detect_GPIO(pin_input_board=PIN_INPUT_SENSOR_FLOW, edge='FALLING', callback=count_liquid, bouncetime=5)
add_event_detect_GPIO(pin_input_board=PIN_INPUT_START, edge='FALLING', callback=start_flow, bouncetime=300)
add_event_detect_GPIO(pin_input_board=PIN_INPUT_STOP, edge='FALLING', callback=stop_flow, bouncetime=300)

####### LOOP THREADS #######
system_loop_get_mwallet_push_alarm = threading.Thread(target=loop_get_mwallet_push_alarm)
system_loop_get_mwallet_push_alarm.daemon = True
system_loop_get_mwallet_push_alarm.start()

system_loop_get_qr_code = threading.Thread(target=loop_get_qr_code)
system_loop_get_qr_code.daemon = True
system_loop_get_qr_code.start()

system_loop_send_transaction_coin = threading.Thread(target=loop_send_transaction_coin)
system_loop_send_transaction_coin.daemon = True
system_loop_send_transaction_coin.start()


# Основной цикл программы
main_loop_running = True
while main_loop_running:
    sleep(0.1)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # Обработка события закрытия окна
            main_loop_running = False
        elif event.type == pygame.KEYDOWN:
            # Обработка события нажатия клавиши (например, ESC)
            if event.key == pygame.K_ESCAPE:
                main_loop_running = False    
    
    try:
        #Электропитание - обработка состояния input_state_bt_ozon = GPIO.input(PIN_INPUT_OZON)
        input_state_main_power = GPIO.input(PIN_INPUT_MAIN_POWER)
        if(input_state_main_power == False):
            
        
        


        #Если внесена оплата монетой, то вывести на дисплей сумму и увеличить доступный обьем
        credit_coin = coin_pulse.get_last_credit_coin()
        if(credit_coin > 0):
            TOTAL_AMOUNT_AVAILABLE = TOTAL_AMOUNT_AVAILABLE + credit_coin
            LIQUID_AVAILABLE = LIQUID_AVAILABLE + credit_coin/PRICE_WATER
            LIST_TRANSACTION_COIN.append(credit_coin)
            screen.fill(BACKGROUND_COLOR)
            render_text_pygame(f"ВНЕСЕНО:  {credit_coin} сом", font, TEXT_COLOR, (100, 200))
            # Обновление экрана
            pygame.display.flip()
            sleep(2)
            
        #Если внесена оплата Q-код, то вывести на дисплей сумму и увеличить доступный обьем   
        if(AMOUNT_MWALLET > 0):
            TOTAL_AMOUNT_AVAILABLE = TOTAL_AMOUNT_AVAILABLE + AMOUNT_MWALLET
            LIQUID_AVAILABLE = LIQUID_AVAILABLE + AMOUNT_MWALLET/PRICE_WATER
            screen.fill(BACKGROUND_COLOR)
            render_text_pygame(f"ВНЕСЕНО:  {AMOUNT_MWALLET} сом", font, TEXT_COLOR, (100, 250))
            AMOUNT_MWALLET = 0
            # Обновление экрана
            pygame.display.flip()
            sleep(2)
            
        
        #Если произведена оплата и предоставлен доступный обьем воды для выдачи
        if(LIQUID_AVAILABLE > 0):
            input_state_bt_ozon = GPIO.input(PIN_INPUT_OZON)
            screen.fill(BACKGROUND_COLOR)
            
            #Нажата кнопка ОЗОНАТОР
            if(input_state_bt_ozon == False):
                ozon_running = True
                set_output_GPIO(PIN_OUTPUT_OZON, 'HIGH') #Включаем Озонатор
                time_ozon = duration_ozon_running
                sleep(0.1) #Дребезг контактов
                
            if(ozon_running):
                render_text_pygame(f"Озонатор работает, {time_ozon} сек.", font, TEXT_COLOR, (80, 30))
                time_ozon = time_ozon - 1
                if(time_ozon < 0):
                    ozon_running = False
                    set_output_GPIO(PIN_OUTPUT_OZON, 'LOW') #Выключаем Озонатор
                sleep(1)    
            else:
                render_text_pygame("Используйте озонатор", font, TEXT_COLOR, (100, 30))
            
            render_text_pygame(f"СУММА:  {TOTAL_AMOUNT_AVAILABLE} сом", font, TEXT_COLOR, (100, 150))
            render_text_pygame(f"ДОСТУПНО:  {round(LIQUID_AVAILABLE, 2)} л.", font, TEXT_COLOR, (100, 250))
            #Если используется debug_flow_sensor_vision, то можно видеть количество импульсов с датчика жидкости 
            if(debug_flow_sensor_vision):
                render_text_pygame(f"Импульсы: {number_pulse_sensor}", font, TEXT_COLOR, (100, 400))
            
            # Обновление экрана
            pygame.display.flip()
            
        else:
            #Выключаем нагрузки
            if os_name == "Linux":
                logger.info("Скрипт запущен на Linux")
                set_output_GPIO(PIN_OUTPUT_VALVE, 'LOW') 
                set_output_GPIO(PIN_OUTPUT_OZON, 'LOW')

      
            TOTAL_AMOUNT_AVAILABLE = 0  
            screen.fill(BACKGROUND_COLOR) 
            render_text_pygame("Добро пожаловать!", font, TEXT_COLOR, (125, 25))
            render_text_pygame(f"Стоимость: 1 литра = {PRICE_WATER} сом", font, TEXT_COLOR, (15, 95))
            # Преобразование строки в объект datetime
            date_obj = datetime.strptime(DATE_FILTER_UPDATE, "%Y-%m-%d")
            # Преобразование объекта datetime в строку нужного формата
            formatted_date = date_obj.strftime("%d.%m.%Y")
            render_text_pygame(f"Последняя замена фильтров: {formatted_date}", small_font, TEXT_COLOR, (10, 170))
            render_text_pygame("QR-код для оплаты", small_font, TEXT_COLOR, (10, 320))
            logger.info(DATE_FILTER_UPDATE)
            if QR_LOADED:
                # Загрузка изображения QR-кода в Pygame
                with file_lock:
                    qr_surface = pygame.image.load("resized_qrcode.png")
                    # Отображение изображения QR-кода 
                    screen.blit(qr_surface, (500, 225))
                

            # Обновление экрана
            pygame.display.flip()
            
        
    except Exception as e:
        #Выключаем нагрузки
        set_output_GPIO(PIN_OUTPUT_VALVE, 'LOW')
        set_output_GPIO(PIN_OUTPUT_OZON, 'LOW')

        #GPIO.cleanup();  
        # Заполнение экрана
        screen.fill(BACKGROUND_COLOR_ALARM)
        render_text_pygame("Аппарат", font, TEXT_COLOR, (380, 200))
        render_text_pygame("временно", font, TEXT_COLOR, (380, 300))
        render_text_pygame("не работает", font, TEXT_COLOR, (380, 400))
        
        # Обновление экрана
        pygame.display.flip()
        logger.exception(f'Exception-{e}')
   
#Выключаем нагрузки   
set_output_GPIO(PIN_OUTPUT_VALVE, 'LOW')
set_output_GPIO(PIN_OUTPUT_OZON, 'LOW')

GPIO.cleanup()
pygame.quit()
sys.exit()
    



