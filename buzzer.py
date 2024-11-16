import RPi.GPIO as GPIO  # type: ignore
import time
import logging
from tenacity import RetryError
import requests
from requests.auth import HTTPBasicAuth
import api_secrets

logging.basicConfig(level=logging.INFO)

# GPIO Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
buzzer_pins = [8, 10, 12, 16]
for pin in buzzer_pins:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

last_pressed_buzzer_id = None

def send_buzzer_push(buzzer_id) -> requests.Response:
    """Wrapper function to make an API request with retry logic."""
    auth = HTTPBasicAuth(api_secrets.username, api_secrets.password)
    response = requests.post(f"{api_secrets.jeopardy_server}/push_buzzer?buzzer_id={buzzer_id}", auth=auth)
    response.raise_for_status()
    return response

def buzzer_loop() -> None:
    try:
        while True:
            last_pressed_buzzer_id = None
            while True:
                for buzzer_id, pin in enumerate(buzzer_pins, start=1):
                    if GPIO.input(pin) == GPIO.HIGH:
                        last_pressed_buzzer_id = buzzer_id
                        logging.info(f"Buzzer {buzzer_id} pressed.")
                        break
                if last_pressed_buzzer_id:
                    break
                time.sleep(0.0025)

            # Send buzzer press to server
            try:
                send_buzzer_push(last_pressed_buzzer_id)
                logging.info(f"Successfully sent buzzer {last_pressed_buzzer_id} signal.")
            except RetryError:
                logging.error(f"Failed to send buzzer {last_pressed_buzzer_id} signal after retries.")
                continue  # Skip this loop iteration if unable to send the signal

            time.sleep(0.5)

    except KeyboardInterrupt:
        logging.info("Shutting down buzzer loop.")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    buzzer_loop()
