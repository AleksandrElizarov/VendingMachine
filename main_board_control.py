import threading
from time import sleep
import logging

from eSSP.constants import Status
from eSSP import eSSP  # Import the library
from st7920 import ST7920


MILLILITRE_PULSE = 0.17 #параметры датчика потока воды 1000мл=5880пульов или 0,17мл=1пульс
available_volume = 0 #оплаченный обьем для выдачи

#Экемпляр купюроприемника
#validator = eSSP(com_port="/dev/ttyUSB0", ssp_address="0", nv11=False, debug=True)


total_sum = 0




try:  # MAIN LOOP
    while True:
        sleep(1)
        
        lcd = ST7920()
        lcd.clear()
        # Display "Hello, world!" on the LCD
        lcd.put_text("Hello, world!", 0, 0)
        lcd.redraw()
        
        total_sum = total_sum + 5#validator.get_last_credit_cash()
        print(f'Общая сумма: {total_sum} сом')
        
        
        
except KeyboardInterrupt:  # If user do CTRL+C
    validator.close()  # Close the connection with the validator
    print("Exiting")
    exit(0)
