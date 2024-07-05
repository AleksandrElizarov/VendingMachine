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
from loguru import logger
logger.add('logs.log', rotation='10MB')

import platform
##### Проверяем на какой операционной системе запущен скрипт, и соответственно импортируем модули #####
# Получаем имя операционной системы
os_name = platform.system()

if os_name == "Linux":
    print("Скрипт запущен на Linux")
    from eSSP.constants import Status
    from eSSP import eSSP
    import RPi.GPIO as GPIO
    from CoinInterface.CoinPulseHX916 import CoinPulseVN5
  
elif os_name == "Windows":
    print("Скрипт запущен на Windows")
    class GPIO():
        '''Класс заглушка для RP.GPIO'''
        HIGH = 1
        LOW = 0
        BOARD = 1
        IN = 1
        OUT = 0
        PUD_UP = 1
        PUD_DOWN = 0
        FALLING = 0
        RISING = 1

        def output(pin, state):
            print(f'output GPIO работает заглушка ')
        def setmode(board):
            print(f'setmode GPIO работает заглушка ')
        def setwarnings(boolean):
            print(f'setwarnings GPIO работает заглушка ')
        def setup(pin, pin_in_out, pull_up_down=PUD_DOWN):
            print(f'setup GPIO работает заглушка ')
        def add_event_detect(pin, edge, callbacb, bouncetime):
            print(f'add_event_detect GPIO работает заглушка ')
        def input(pin_input):
            print(f'input GPIO работает заглушка ')
            return False

else:
    print("Скрипт запущен на другой операционной системе")    



##################### VERIABLES GLOBAL #####################
SERIAL_NUMBER_MACHINE = '1111111'
DOMAIN = 'https://monitorvending.pythonanywhere.com/'

#URL get QR-code by GET-method query str 'serial_number_machine'
url_get_qr_code = f'{DOMAIN}get_qr_code/'
#URL refresh states alarm and get info about amount mwallet GET-method query str 'serial_number_machine','main_power',open_door',low_water'
url_refresh_states_alarm_get_mwallet_amount = f'{DOMAIN}refresh_states_alarm_machine/'
#URL create coin/cash transaction in DataBase POST method {"serial_number_machine": "64-number", "cash_amount": cash_amount}
url_create_coin_cash_transaction = f'{DOMAIN}create_transaction/'

COM_PORT = "/dev/ttyUSB0" # Название последовательного порта
PIN_INPUT_SENSOR_FLOW = 32 # Пин датчика жидкости
PIN_INPUT_COIN_ACCEPTOR = 31 # Пин монетоприемника

PIN_INPUT_OZON = 40 # Пин кнопки Озонатора
PIN_INPUT_START = 38 # Пин кнопки старт
PIN_INPUT_STOP = 36 # Пин кнопики стоп

PIN_OUTPUT_VALVE = 37 # Пин клапана для выдачи воды
PIN_OUTPUT_OZON = 35 # Пин включения озонатора

MILLILITRE_PULSE = 0.00222 #параметры датчика потока воды 1000мл=450пульов или 0,0022мл=1пульс

LIQUID_AVAILABLE = 0 # оплаченный обьем для выдачи

AMOUNT_MWALLET = 0 # сумма оплаченная через Мобильный кошелек

LIST_TRANSACTION_COIN_MWALLET = [] # список сумм транзакций внесенных через монетоприемник и валютоприемник


### VERIABLES ALARMS ###
MAIN_POWER = 'true'
OPEN_DOOR = 'false'
LOW_WATER = 'false'

PRICE_WATER = 3 #Цена за 1литр
DATE_FILTER_UPDATE = '2024-06-01' # дата обновления фильтра
QR_LOADED = False # Флаг успешной загрузки QR-кода


#validator = None
coin_pulse = None

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
        while True:
            try:
                params = {
                'serial_number_machine': SERIAL_NUMBER_MACHINE,
                    'main_power': MAIN_POWER,
                    'open_door': OPEN_DOOR,
                    'low_water': LOW_WATER
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


def loop_send_transaction_coin_cash():
    '''Функция записи транзакции на сервер в базуданных о сумме внесенной через монетоприемник/купюроприемник'''
    global SERIAL_NUMBER_MACHINE
    global url_create_coin_cash_transaction
    global LIST_TRANSACTION_COIN_MWALLET    
    while True:
        if LIST_TRANSACTION_COIN_MWALLET:
            try:
                data = {"serial_number_machine": SERIAL_NUMBER_MACHINE, "cash_amount": LIST_TRANSACTION_COIN_MWALLET.pop()}   
                response = requests.post(url_create_coin_cash_transaction, json=data)
                logger.info(f'send_transaction_coin_cash: {response.json()}')
            except Exception as e:
                    logger.exception(f'send_transaction_coin_cash_exception: {e}') 
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
screen_width = 800
screen_height = 480

#screen = pygame.display.set_mode((screen_width, screen_height))
screen = pygame.display.set_mode((0, 0), FULLSCREEN)

# Получение размеров экрана
screen_width, screen_height = screen.get_size()
# Вывод размеров экрана
print(f'Ширина экрана: {screen_width}, Высота экрана: {screen_height}')

pygame.display.set_caption('Vending Machine Display')

# Скрытие курсора мыши
pygame.mouse.set_visible(False)

 
init_GPIO()
add_event_detect_GPIO(pin_input_board=PIN_INPUT_SENSOR_FLOW, edge='FALLING', callback=count_liquid, bouncetime=5)
add_event_detect_GPIO(pin_input_board=PIN_INPUT_START, edge='FALLING', callback=count_liquid, bouncetime=300)
add_event_detect_GPIO(pin_input_board=PIN_INPUT_STOP, edge='FALLING', callback=count_liquid, bouncetime=300)

####### LOOP THREADS #######
system_loop_get_mwallet_push_alarm = threading.Thread(target=loop_get_mwallet_push_alarm)
system_loop_get_mwallet_push_alarm.daemon = True
system_loop_get_mwallet_push_alarm.start()

system_loop_get_qr_code = threading.Thread(target=loop_get_qr_code)
system_loop_get_qr_code.daemon = True
system_loop_get_qr_code.start()

system_loop_send_transaction_coin_cash = threading.Thread(target=loop_send_transaction_coin_cash)
system_loop_send_transaction_coin_cash.daemon = True
system_loop_send_transaction_coin_cash.start()


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

        '''        
        #Экемпляр купюроприемника
        if(validator == None):
            validator = eSSP(com_port=COM_PORT, ssp_address="0", nv11=False, debug=True)
        else:
            if(validator.running == False):
                raise Exception("Validator disconnected")
            
        #Если внесена оплата купюрой, то вывести на дисплей сумму и увеличить доступный обьем
        credit_cash = validator.get_last_credit_cash()
        if(credit_cash > 0):
            LIQUID_AVAILABLE = LIQUID_AVAILABLE + credit_cash/PRICE_WATER
            screen.fill(BACKGROUND_COLOR)
            render_text_pygame(f"ВНЕСЕНО:  {credit_cash} сом", font, TEXT_COLOR, (130, 300))
            # Обновление экрана
            pygame.display.flip()
            sleep(2)
        '''

        #Экемпляр монетоприемника
        if coin_pulse is None:
            coin_pulse = CoinPulseVN5(GPIO_board_port=31)    
                
        #Если внесена оплата монетой, то вывести на дисплей сумму и увеличить доступный обьем
        credit_coin = coin_pulse.get_last_credit_coin()
        if(credit_coin > 0):
            LIQUID_AVAILABLE = LIQUID_AVAILABLE + credit_coin/PRICE_WATER
            LIST_TRANSACTION_COIN_MWALLET.append(credit_coin)
            screen.fill(BACKGROUND_COLOR)
            render_text_pygame(f"ВНЕСЕНО:  {credit_coin} сом", font, TEXT_COLOR, (100, 200))
            # Обновление экрана
            pygame.display.flip()
            sleep(2)
            
            
        if(AMOUNT_MWALLET > 0):
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
                render_text_pygame(f"Озонатор работает, {time_ozon} сек.", font, TEXT_COLOR, (80, 130))
                time_ozon = time_ozon - 1
                if(time_ozon < 0):
                    ozon_running = False
                    set_output_GPIO(PIN_OUTPUT_OZON, 'LOW') #Выключаем Озонатор
                sleep(1)    
            else:
                render_text_pygame("Используйте озонатор", font, TEXT_COLOR, (100, 130))

            render_text_pygame(f"ДОСТУПНО:  {round(LIQUID_AVAILABLE, 2)} л.", font, TEXT_COLOR, (100, 250))
            #Если используется debug_flow_sensor_vision, то можно видеть количество импульсов с датчика жидкости 
            if(debug_flow_sensor_vision):
                render_text_pygame(f"Импульсы: {number_pulse_sensor}", font, TEXT_COLOR, (100, 400))
            
            # Обновление экрана
            pygame.display.flip()
            
        else:
            #Выключаем нагрузки
            if os_name == "Linux":
                print("Скрипт запущен на Linux")
                set_output_GPIO(PIN_OUTPUT_VALVE, 'LOW') 
                set_output_GPIO(PIN_OUTPUT_OZON, 'LOW')
    

                        
                
            screen.fill(BACKGROUND_COLOR) 
            render_text_pygame("Добро пожаловать!", font, TEXT_COLOR, (125, 25))
            render_text_pygame(f"Стоимость: 1 литра = {PRICE_WATER} сом", font, TEXT_COLOR, (15, 95))
            # Преобразование строки в объект datetime
            date_obj = datetime.strptime(DATE_FILTER_UPDATE, "%Y-%m-%d")
            # Преобразование объекта datetime в строку нужного формата
            formatted_date = date_obj.strftime("%d.%m.%Y")
            render_text_pygame(f"Последняя замена фильтров: {formatted_date}", small_font, TEXT_COLOR, (10, 170))
            render_text_pygame("QR-код для оплаты", small_font, TEXT_COLOR, (10, 320))
            print(DATE_FILTER_UPDATE)
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
        render_text_pygame("Временные", font, TEXT_COLOR, (380, 200))
        render_text_pygame("технические", font, TEXT_COLOR, (380, 300))
        render_text_pygame("неполадки", font, TEXT_COLOR, (380, 400))
        
        # Обновление экрана
        pygame.display.flip()
        logger.exception(f'Exception-{e}')
    '''    
    # Проверка времени работы программы
    if time.time() - start_time >= duration:
        break
    '''
#Выключаем нагрузки   
set_output_GPIO(PIN_OUTPUT_VALVE, 'LOW')
set_output_GPIO(PIN_OUTPUT_OZON, 'LOW')

#GPIO.cleanup();
pygame.quit()
sys.exit()
validator.close()  # Close the connection with the validator
    



