import board
import digitalio
import time
import supervisor

# on-board red LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

def handle_command (cmd):
    print("RX: {}".format(cmd))

while True:
    if supervisor.runtime.serial_bytes_available:
        cmd = input().strip().upper()
        # ignore empty input
        if len(cmd) > 0:
            handle_command(cmd)
    led.value = True
    time.sleep(0.001)
    led.value = False
    time.sleep(0.1)