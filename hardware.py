from threading import Thread
import RPi.GPIO as GPIO # type: ignore
import time

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

    def buzzer_loop(self, assigned_buzzer_ids: list) -> None:
        self.last_pressed_buzzer_id = None
        while self.buzzer_loop_running:
            for buzzer_id, pin in [(1, 8), (2, 10), (3, 12), (4, 16)]:
                if GPIO.input(pin) == GPIO.HIGH and buzzer_id in assigned_buzzer_ids:
                    self.last_pressed_buzzer_id = buzzer_id
                    self.buzzer_loop_running = False
                    break
            time.sleep(0.001)
        self.buzzer_loop_stopped = True

    def start_buzzer_loop(self, assigned_buzzer_ids) -> None:
        if not self.buzzer_loop_stopped:
            self.stop_buzzer_loop()

        self.buzzer_loop_running = True
        self.buzzer_loop_stopped = False

        t = Thread(target=self.buzzer_loop, args=(assigned_buzzer_ids,))
        t.start()

    def stop_buzzer_loop(self) -> None:
        while not self.buzzer_loop_stopped:
            self.buzzer_loop_running = False

    def get_last_pressed_buzzer_id(self):
        return self.last_pressed_buzzer_id
