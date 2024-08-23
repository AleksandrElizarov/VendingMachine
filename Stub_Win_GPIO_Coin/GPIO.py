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
    def cleanup():
        print(f'cleanup GPIO работает заглушка ')
    