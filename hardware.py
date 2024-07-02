import platform
from threading import Thread
import time

# Check if we are on WSL or Raspberry Pi
if platform.system() == 'Linux' and 'microsoft' in platform.uname().release:
    from dummy_gpio import GPIO # type: ignore
else:
    import RPi.GPIO as GPIO # type: ignore

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(8, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

class Buzzer:
    def __init__(self) -> None:
        self.last_pressed_buzzer_id = None
        self.buzzer_loop_running = False
        self.buzzer_loop_stopped = True

    def buzzer_loop(self) -> None:
        self.last_pressed_buzzer_id = None
        while self.buzzer_loop_running:
            if GPIO.input(8) == GPIO.HIGH:
                self.last_pressed_buzzer_id = 1
                break

            if GPIO.input(10) == GPIO.HIGH:
                self.last_pressed_buzzer_id = 2
                break

            if GPIO.input(12) == GPIO.HIGH:
                self.last_pressed_buzzer_id = 3
                break

            if GPIO.input(16) == GPIO.HIGH:
                self.last_pressed_buzzer_id = 4
                break
            time.sleep(0.1)
        self.buzzer_loop_stopped = True

    def start_buzzer_loop(self) -> None:
        print("Starting Buzzer Loop")
        if not self.buzzer_loop_stopped:
            self.stop_buzzer_loop()

        self.buzzer_loop_running = True
        self.buzzer_loop_stopped = False

        t = Thread(target=self.buzzer_loop)
        t.start()

    def stop_buzzer_loop(self) -> None:
        print("Stopping Buzzer Loop")
        while not self.buzzer_loop_stopped:
            self.buzzer_loop_running = False

    def get_last_pressed_buzzer_id(self):
        print("Last Buzzer ID =", self.last_pressed_buzzer_id)
        return self.last_pressed_buzzer_id
