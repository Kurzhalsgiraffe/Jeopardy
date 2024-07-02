class GPIO:
    BOARD = 'BOARD'
    BCM = 'BCM'
    IN = 'IN'
    OUT = 'OUT'
    LOW = False
    HIGH = True
    PUD_DOWN = 'PUD_DOWN'

    def __init__(self):
        pass

    @staticmethod
    def setmode(mode):
        print(f"GPIO setmode({mode})")

    @staticmethod
    def setup(channel, mode, pull_up_down=None, initial=None):
        print(f"GPIO setup(channel={channel}, mode={mode}, pull_up_down={pull_up_down}, initial={initial})")

    @staticmethod
    def input(channel):
        if channel == 8:
            return GPIO.HIGH
        return GPIO.LOW

    @staticmethod
    def setwarnings(flag):
        print(f"GPIO setwarnings({flag})")

    @staticmethod
    def cleanup():
        print("GPIO cleanup()")
