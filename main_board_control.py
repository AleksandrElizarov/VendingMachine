import threading
from eSSP.constants import Status
from eSSP import eSSP  # Import the library
from time import sleep
import logging
from st7920 import ST7920

#log_file_path = '//home/pi/Desktop/VendingMachine/log_file.log'
#logging.basicConfig(filename=log_file_path,level=logging.DEBUG)

# Initialize the LCD
lcd = ST7920()
lcd.clear()
# Display "Hello, world!" on the LCD
lcd.put_text("Hello, world!", 0, 0)
lcd.redraw()

#  Create a new object ( Validator Object ) and initialize it ( In debug mode, so it will print debug infos )
validator = eSSP(com_port="/dev/ttyUSB0", ssp_address="0", nv11=False, debug=True)

#event == Status.SSP_POLL_CREDIT
#event == Status.SSP_POLL_READ
val = 1

try:  # Command Interpreter
    while True:
        sleep(0.1)
        val = val + 1
        #if validator.response_data:
        (note, currency,event) = validator.get_last_event()
        print(f'Input_cash:{note}')
        #logging.info(f"Data:{val}")
        
except KeyboardInterrupt:  # If user do CTRL+C
    validator.close()  # Close the connection with the validator
    print("Exiting")
    exit(0)
