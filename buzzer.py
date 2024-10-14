import requests
import RPi.GPIO as GPIO # type: ignore
import time
import logging
import api_secrets

logging.basicConfig(level=logging.INFO)

# GPIO Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
buzzer_pins = [8, 10, 12, 16]
for pin in buzzer_pins:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

headers = {"X-API-KEY": api_secrets.SECRET_API_KEY}
last_pressed_buzzer_id = None

def buzzer_loop() -> None:
    try:
        while True:
            response = requests.get(f"{api_secrets.jeopardy_server}:{api_secrets.jeopardy_server_port}/is_buzzer_active", headers=headers)
            response.raise_for_status()
            is_active = response.json().get("buzzer_active_semaphore")

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
                    time.sleep(0.01)  # Shorter delay for responsiveness

                try:
                    response = requests.post(f"{api_secrets.jeopardy_server}:{api_secrets.jeopardy_server_port}/push_buzzer?buzzer_id={last_pressed_buzzer_id}", headers=headers)
                    response.raise_for_status()
                    logging.info(f"Successfully sent buzzer {last_pressed_buzzer_id} signal.")
                except requests.RequestException as e:
                    logging.error(f"Failed to send buzzer signal: {e}")

            time.sleep(0.5)

    except KeyboardInterrupt:
        logging.info("Shutting down buzzer loop.")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    buzzer_loop()
