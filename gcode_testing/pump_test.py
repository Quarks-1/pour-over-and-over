from gpiozero import LED
from time import sleep

led = LED(16)

while True:
    led.on()
    sleep(10)
    led.off()
    sleep(1)