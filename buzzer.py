import requests
import RPi.GPIO as GPIO  # type: ignore
import time
import logging
import api_secrets
import socket
from tenacity import retry, wait_fixed, stop_after_attempt, RetryError
from requests.auth import HTTPBasicAuth

logging.basicConfig(level=logging.INFO)

# GPIO Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
buzzer_pins = [8, 10, 12, 16]
for pin in buzzer_pins:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

last_pressed_buzzer_id = None

def is_connected() -> bool:
    """Check if the Raspberry Pi is connected to the internet."""
    try:
        # Try connecting to a known server (e.g., Google's DNS)
        socket.create_connection(("8.8.8.8", 53), 2)
        return True
    except OSError:
        return False

@retry(wait=wait_fixed(5), stop=stop_after_attempt(5))
def make_request(route: str, method="GET", data=None) -> requests.Response:
    """Wrapper function to make an API request with retry logic."""
    headers = {"X-API-KEY": api_secrets.SECRET_API_KEY}
    auth = HTTPBasicAuth(api_secrets.username, api_secrets.password)
    if method == "POST":
        response = requests.post(f"{api_secrets.jeopardy_server}/{route}", headers=headers, auth=auth, data=data)
    else:
        response = requests.get(f"{api_secrets.jeopardy_server}/{route}", headers=headers, auth=auth)
    response.raise_for_status()
    return response

def buzzer_loop() -> None:
    try:
        # Wait until internet is connected before starting
        while not is_connected():
            logging.warning("No internet connection. Retrying in 15 seconds...")
            time.sleep(15)

        while True:
            try:
                response = make_request("is_buzzer_active")
                is_active = response.json().get("buzzer_active_semaphore")
            except RetryError:
                logging.error("Max retries exceeded. Could not check buzzer status.")
                time.sleep(10)
                continue

            if is_active:
                logging.info("Buzzers are active.")
                last_pressed_buzzer_id = None
                while True:
                    for buzzer_id, pin in enumerate(buzzer_pins, start=1):
                        if GPIO.input(pin) == GPIO.HIGH:
                            last_pressed_buzzer_id = buzzer_id
                            logging.info(f"Buzzer {buzzer_id} pressed.")
                            break
                    if last_pressed_buzzer_id:
                        break
                    time.sleep(0.005)

                # Send buzzer press to server
                try:
                    make_request(f"push_buzzer?buzzer_id={last_pressed_buzzer_id}", method="POST")
                    logging.info(f"Successfully sent buzzer {last_pressed_buzzer_id} signal.")
                except RetryError:
                    logging.error(f"Failed to send buzzer {last_pressed_buzzer_id} signal after retries.")
                    continue  # Skip this loop iteration if unable to send the signal

            time.sleep(0.25)

    except KeyboardInterrupt:
        logging.info("Shutting down buzzer loop.")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    buzzer_loop()
