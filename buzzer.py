import RPi.GPIO as GPIO
from threading import Thread

GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(8, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)


class Buzzer:
    def __init__(self) -> None:
        self.last_pressed_buzzer_id = None
        self.buzzer_loop_running = False
        self.buzzer_loop_stopped = True

    def buzzer_loop(self) -> None:
        while self.buzzer_loop_running:
            if GPIO.input(8) == GPIO.HIGH:
                self.last_pressed_buzzer_id = 1

            if GPIO.input(10) == GPIO.HIGH:
                self.last_pressed_buzzer_id = 2

            if GPIO.input(12) == GPIO.HIGH:
                self.last_pressed_buzzer_id = 3

            if GPIO.input(16) == GPIO.HIGH:
                self.last_pressed_buzzer_id = 4
        self.buzzer_loop_stopped = True

    def start_buzzer_loop(self) -> None:
        if not self.buzzer_loop_stopped:
            self.stop_buzzer_loop()

        self.buzzer_loop_running = True
        self.buzzer_loop_stopped = False

        t = Thread(target=self.buzzer_loop)
        t.start()

    def stop_buzzer_loop(self) -> None:
        while not self.buzzer_loop_stopped:
            self.buzzer_loop_running = False

    def get_last_pressed_buzzer_id(self):
        return self.last_pressed_buzzer_id
