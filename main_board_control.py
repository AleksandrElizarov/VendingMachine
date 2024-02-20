import threading
from eSSP.constants import Status
from eSSP import eSSP  # Import the library
from time import sleep
import logging

log_file_path = '//home/pi/Desktop/VendingMachine/log_file.log'
logging.basicConfig(filename=log_file_path,level=logging.DEBUG)

import spidev

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
        '''
        choice = input("")
        if choice == "p":  # Payout "choice" value bill ( 10, 20, 50, 100, etc. )
            choice = input("")
            validator.payout(int(choice))
        elif choice == "s":  # Route to cashbox ( In NV11, it is any amount <= than "choice" )
            choice = input("")
            validator.set_route_storage(int(choice))
        elif choice == "c":  # Route to cashbox ( In NV11, it is any amount <= than "choice" )
            choice = input("")
            validator.set_route_cashbox(int(choice))
        elif choice == "e":  # Enable ( Automaticaly disabled after a payout )
            validator.enable_validator()
        elif choice == "r":  # Reset ( It's like a "reboot" of the validator )
            validator.reset()
        elif choice == "y":  # NV11 Payout last entered ( next available )
            print("Payout next 1")
            validator.nv11_payout_next_note()
        elif choice == "d":  # Disable
            validator.disable_validator()
        elif choice == "D":  # Disable the payout device
            validator.disable_payout()
        elif choice == "E":  # Empty the storage to the cashbox
            validator.empty_storage()
        elif choice == "g":  # Get the number of bills denominated with their values
            choice = input("")
            validator.get_note_amount(int(choice))
            sleep(1)
            print("Number of bills of %s : %s"%(choice, validator.response_data['getnoteamount_response']))
            '''
except KeyboardInterrupt:  # If user do CTRL+C
    validator.close()  # Close the connection with the validator
    print("Exiting")
    exit(0)
