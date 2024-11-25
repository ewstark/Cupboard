# eep.circuitpy.py
# 28C256 (and others) EEPROM programmer for Adafruit M4 Grand Central
# Copy to root of M4 Grand Central "CIRCUITPY" drive with filename code.py

import board
import digitalio
import time
import supervisor

# global data
dump_prev_addr     = 0x0000  # track previously dumped address...
dump_prev_count    = 16      # ...and width
write_prev_address = 0x0000  # track previously written address
output_width       = 16      # number of bytes to display per line of dumped memory
force_hex          = True    # only expect hexadecimal numbers in fields; otherwise assume decimal and use 'x', 'o', or '%' prefix or hex, octal, or binary

# on-board red LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# assigned GPIO pins for CPU interface
# IMPORTANT: All pins are connected the EEPROM via a 3v3-5v level translator
pins_addr = [digitalio.DigitalInOut(i) for i in [board.D30, board.D31, board.D32, board.D33, board.D34, board.D35, board.D36, board.D37, board.D38, board.D39, board.D40, board.D41, board.D42, board.D43, board.D44]]
pins_data = [digitalio.DigitalInOut(i) for i in [board.D22, board.D23, board.D24, board.D25, board.D26, board.D27, board.D28, board.D29]]
pin_we    = digitalio.DigitalInOut(board.D45)
pin_oe    = digitalio.DigitalInOut(board.D46)
pin_ce    = digitalio.DigitalInOut(board.D47)

# setup all pins to their default state (ready to read)
def reset_all_pins ():
    for p in pins_data:
        p.switch_to_input(None)     # initially output from EEPROM = input to Grand Central, no pull; will switch when need to write data to the EEPROM
    for p in pins_addr:
        p.switch_to_output(False)   # output from Grand Central = input to EEPROM
    pin_we.switch_to_output(True)   # output from Grand Central = input to EEPROM
    pin_oe.switch_to_output(True)   # output from Grand Central = input to EEPROM
    pin_ce.switch_to_output(False)  # output from Grand Central = input to EEPROM

# set address pins
def set_eeprom_address_pins (address):
    global pins_addr    
    for p in pins_addr:
        p.value = address & 0x01
        address >>= 1

# set data pins
def set_eeprom_data_pins (data):
    global pins_data
    for p in pins_data:
        p.switch_to_output(data & 0x01)
        data >>= 1

# after a write to the data bus, reset the pins to inputs
def reset_data_pin_dir ():
    global pins_data
    for p in pins_data:
        p.switch_to_input()

# set all pins to outputs and write values
def set_all_pins (address, data, oe, we):
    global pin_oe, pin_we
    set_eeprom_address_pins(address)
    set_eeprom_data_pins (data)
    pin_oe.value = oe
    pin_we.value = we

# read the data bus pins and return the byte value
def read_eeprom_data_bus ():
    global pins_data
    data = 0
    val = 0x01
    for p in pins_data:
        if (p.value):
            data += val
        val <<= 1
    return data

# read a byte from the EEPROM
def read_eeprom_byte (address):
    global pin_oe
    set_eeprom_address_pins(address)
    pin_oe.value = False
    data = read_eeprom_data_bus()
    pin_oe.value = True
    return data

# write a byte to EEPROM - returns True if write confirmed or False if write failed
def write_eeprom_byte (address, data):
    global pin_we
    set_eeprom_address_pins(address)
    pin_we.value = False
    set_eeprom_data_pins(data)
    pin_we.value = True
    reset_data_pin_dir()
    # poll data until matches write or timeout (e.g., when SDP is enabled)
    # experiments show ~6.4ms, datasheet claims under 10ms, timeout at 11ms
    matched = False
    start_ns = time.monotonic_ns()
    while not matched and (time.monotonic_ns() - start_ns) < 11000000:
        pin_oe.value = False
        check = read_eeprom_data_bus()
        pin_oe.value = True
        matched = (check == data)
    return matched

# fast write an SDP byte, NOT A NORMAL WRITE CYCLE, expects port direction already set
def write_eeprom_sdp (address, data):
    global pin_we
    set_eeprom_address_pins(address)
    set_eeprom_data_pins(data)
    pin_we.value = False
    pin_we.value = True

# send SDP lock sequence
def lock_eeprom ():
    global pin_ce, pins_data
    for p in pins_data:
        p.switch_to_output(0)
    write_eeprom_sdp(0x5555, 0xaa)
    write_eeprom_sdp(0x2aaa, 0x55)
    write_eeprom_sdp(0x5555, 0xa0)
    pin_ce.value = True
    reset_data_pin_dir()
    time.sleep(0.001)
    pin_ce.value = False

# send SDP unlock sequence
def unlock_eeprom ():
    global pin_ce, pins_data
    for p in pins_data:
        p.switch_to_output(0)
    write_eeprom_sdp(0x5555, 0xaa)
    write_eeprom_sdp(0x2aaa, 0x55)
    write_eeprom_sdp(0x5555, 0x80)
    write_eeprom_sdp(0x5555, 0xaa)
    write_eeprom_sdp(0x2aaa, 0x55)
    write_eeprom_sdp(0x5555, 0x20)
    pin_ce.value = True
    reset_data_pin_dir()
    time.sleep(0.001)
    pin_ce.value = False

# dump a range of addresses from EEPROM
def dump_memory (start_address, num_bytes):
    global output_width
    num_cols = 0
    for a in range(start_address, start_address + num_bytes):
        if num_cols == 0:
            print("%04x: " % a, end='')
        print("%02x " % read_eeprom_byte(a), end='')
        num_cols += 1
        if num_cols >= output_width:
            num_cols = 0
            print()
        elif num_cols % 8 == 0:
            print(" ", end='')
    if num_cols > 0:
        print()

# fill a memory range with a fixed byte
def fill_memory (start_address, num_bytes, data):
    for a in range(start_address, start_address + num_bytes):
        write_eeprom_byte(a, data)

# interpret a number from the fields of user input
def convert_user_number (field_text):
    global force_hex
    v = 0
    try:
        if len(field_text) > 0:
            if force_hex:
                v = int(field_text, 16)
            elif field_text[0] == 'X':
                v = int(field_text[1:], 16)
            elif field_text[0] == '%':
                v = int(field_text[1:], 2)
            elif field_text[0] == 'O':
                v = int(field_text[1:], 8)
            else:
                try:
                    v = int(field_text)
                except:
                    v = int(field_text, 16)
        return v
    except:
        print("FIELD ERROR")
        return 0

def print_version ():
    print("EEP Grand Central v0.1")

def show_help ():
    print_version()
    print("  ?            - Help, show this information")
    print("  .            - Echo request, expects '.' and return to 'EEP:' prompt")
    print("  D addr? len? - Dump EEPROM contents, repeats last parameters if none given")
    print("  DN           - Dump Next contents, increments previous addr by previous count")
    print("  F addr len n - Fill EEPROM with a fixed byte")
    print("  H ON|OFF     - Hex-only mode on or off, report state if no parameter")
    print("  L I MEAN IT  - Lock EEPROM via SDP-enable, passphrase 'I MEAN IT' required")
    print("  OW count     - Output Width, number of bytes per dumped line")
    print("  U            - Unlock EEPROM via SDP-disable")
    print("  V            - Version, report software version")
    print("  W addr data+ - Write one+ bytes to EEPROM")
    print("  WN data+     - Write one+ bytes to EEPROM at next address")
    print("  PT a d oe we - Pin Test (testing function, not normally used)")

def handle_command (cmd, args):
    global dump_prev_addr, dump_prev_count, write_prev_address, output_width, pin_oe, force_hex
    num_args = len(args)

    if cmd == 'D': # Dump memory [addr]? [count]?
        if num_args == 1:  # use new address and previous count
            dump_prev_addr = convert_user_number(args[0])
        elif num_args == 2:  # use new address and count
            dump_prev_addr = convert_user_number(args[0])
            dump_prev_count = convert_user_number(args[1])
        dump_memory(dump_prev_addr, dump_prev_count)

    elif cmd == 'DN': # Dump Next memory block
        dump_prev_addr += dump_prev_count
        dump_memory(dump_prev_addr, dump_prev_count)

    elif cmd == 'F': # Fill [start] [count] [data]
        if num_args == 3:
            address = convert_user_number(args[0])
            count = convert_user_number(args[1])
            data = convert_user_number(args[2])
            fill_memory(address, count, data)
        else:
            print("Fill requires three arguments")

    elif cmd == 'H': # Hex-only mode on or off, report state if no parameter
        if num_args == 0:
            print("Hex-only input:", "Enabled" if force_hex else "Disabled")
        elif num_args == 1:
            if args[0] == 'ON':
                force_hex = True
            elif args[0] == 'OFF':
                force_hex = False
            else:
                print("Hex-only recognizes ON or OFF")
        else:
            print("Hex-only takes up to one field")

    elif cmd == 'L': # Lock EEPROM; send SDP-enable commands
        if num_args == 3:
            if ["I","MEAN","IT"] == [args[0], args[1], args[2]]:
                print("Locking EEPROM via SDP-enable")
                lock_eeprom()
            else:
                print("I don't think you mean it")
        else:
            print("Lock requires passphrase")

    elif cmd == 'OW': # Output Width [count]
        if num_args == 1:
            print("Output Width")
            output_width = convert_user_number(args[0])
        else:
            print("OW requires 1 argument")

    elif cmd == 'PR': # Pin Reset
        print("Pin Reset")
        reset_all_pins()

    elif cmd == 'PT': # Pin Test [addr] [data] [oe] [we]
        if num_args == 4:
            print("Pin Test")
            address = convert_user_number(args[0])
            data = convert_user_number(args[1])
            oe = convert_user_number(args[2])
            we = convert_user_number(args[3])
            set_all_pins(address, data, oe, we)
        else:
            print("PT requires four arguments")

    elif cmd == 'U': # Unlock
        print("Unlocking EEPROM via SDP-disable")
        unlock_eeprom()

    elif cmd == 'W': # Write memory [addr] [data]+
        if num_args < 2:
            print("W requires at least two arguments")
        else:
            write_prev_address = convert_user_number(args[0])
            for v in args[1:]:
                write_eeprom_byte(write_prev_address, convert_user_number(v))
                write_prev_address += 1
            write_prev_address -= 1

    elif cmd == 'WN': # Write Next memory
        if num_args < 1:
            print("WN requires one argument")
        else:
            for v in args:
                write_prev_address += 1
                write_eeprom_byte(write_prev_address, convert_user_number(v))
    
    elif cmd == 'V': # Version
        print_version()

    elif cmd == '?': # Help
        show_help()

    elif cmd == '.': # Echo
        print(".")

    else:
        print("Unknown command '%s'" % cmd)
        show_help()

# -----------------------------------------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------------------------------------
def main ():
    reset_all_pins()
    led.value = True
    print("\nEEP:")
    while True:
        while supervisor.runtime.serial_bytes_available:
            input_fields = input().strip().upper().split(' ')
            if len(input_fields) > 0:
                cmd = input_fields[0]
                args = []
                for a in input_fields[1:]:
                    if len(a) > 0:
                        args.append(a)
                handle_command(cmd, args)
            print("EEP:")
        time.sleep(0.005)
        led.value = not led.value

if __name__ == "__main__":
    main()

