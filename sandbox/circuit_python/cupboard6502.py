# This Circuit Python code is designed to run on an Adafruit M4 Grand Central board. It assumes lots of memory and quick execution speed.

import board
import digitalio
import time
import supervisor

# Full 64K address space
emulated_memory = bytearray(65536)

# The following is the assembler output - be sure to load at correct address!
hello_world_program = ['a2', 'ff', '9a', 'a2', '00', 'bd', '11', 'ff', 'f0', 'f6', '20', '21', 'ff', 'e8', '4c', '05',
                       'ff', '48', '65', '6c', '6c', '6f', '2c', '20', '57', '6f', '72', '6c', '64', '21', '0d', '0a',
                       '00', '8d', 'f0', 'ff', '60', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea',
                       'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea',
                       'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea',
                       'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea',
                       'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea',
                       'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea',
                       'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea',
                       'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea',
                       'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea',
                       'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea',
                       'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea',
                       'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea',
                       'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea',
                       '00', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', 'ea', '00', 'ff', '00', 'ff', '00', 'ff']

def load_program (load_address, program_data):
    global emulated_memory
    for d in program_data:
        emulated_memory[load_address] = int(d, 16)
        load_address += 1

def reset_memory ():
    global emulated_memory
    # fill RAM with NOPs
    for i in range(65536): 
        emulated_memory[i] = 0xea
    # load program
    load_program(0xff00, hello_world_program)

def dump_memory (start_address, num_bytes):
    global emulated_memory
    num_cols = 0
    for a in range(start_address, start_address + num_bytes):
        if num_cols == 0:
            print("%04x: " % a, end='')
        print("%02x " % emulated_memory[a], end='')
        num_cols += 1
        if num_cols >= 8:
            num_cols = 0
            print()
    if num_cols > 0:
        print()

# on-board red LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# assigned GPIO pins for CPU interface
pins_addr = [digitalio.DigitalInOut(i) for i in [board.D30, board.D31, board.D32, board.D33, board.D34, board.D35, board.D36, board.D37, board.D38, board.D39, board.D40, board.D41, board.D42, board.D43, board.D44, board.D45]]  # CPU outputs
pins_data = [digitalio.DigitalInOut(i) for i in [board.D46, board.D47, board.D48, board.D49, board.D50, board.D51, board.D52, board.D53]] # CPU bidirectional
pin_sync  = digitalio.DigitalInOut(board.D19)  # CPU output
pin_nmi   = digitalio.DigitalInOut(board.D20)  # CPU input
pin_mlb   = digitalio.DigitalInOut(board.D21)  # CPU output
pin_irq   = digitalio.DigitalInOut(board.D22)  # CPU input
pin_rdy   = digitalio.DigitalInOut(board.D23)  # CPU input mainly (bidirectional, protected with 10K resistor)
pin_vpb   = digitalio.DigitalInOut(board.D24)  # CPU output
pin_rst   = digitalio.DigitalInOut(board.D25)  # CPU input
pin_so    = digitalio.DigitalInOut(board.D26)  # CPU input
pin_clk   = digitalio.DigitalInOut(board.D27)  # CPU input
pin_be    = digitalio.DigitalInOut(board.D28)  # CPU input
pin_rw    = digitalio.DigitalInOut(board.D29)  # CPU output

# setup pins
for p in pins_addr:
    p.switch_to_input(None) # output from CPU = input to Cupboard, no pull
for p in pins_data:
    p.switch_to_input(None) # initially assume output from CPU = input to Cupboard, no pull; will switch when need to "write" data to the CPU (on a CPU read instruction)
pin_sync.switch_to_input(None)   # CPU output = input to Cupboard
pin_nmi.switch_to_output(True)   # CPU input = output from Cupboard
pin_mlb.switch_to_input(None)    # CPU output = input to Cupboard
pin_irq.switch_to_output(True)   # CPU input = output from Cupboard
pin_rdy.switch_to_output(True)   # CPU input = output from Cupboard
pin_vpb.switch_to_input(None)    # CPU output = input to Cupboard
pin_rst.switch_to_output(False)  # CPU input = output from Cupboard
pin_so.switch_to_output(True)    # CPU input = output from Cupboard
pin_clk.switch_to_output(True)   # CPU input = output from Cupboard
pin_be.switch_to_output(True)    # CPU input = output from Cupboard
pin_rw.switch_to_input(None)     # CPU output = input to Cupboard

def read_addr_bus ():
    # read the 16-bit address from the address bus
    addr = 0
    val = 0x0001
    for p in pins_addr:
        if (p.value):
            addr += val
        val <<= 1
    return addr

def write_data_bus (value):
    # switch data bus to output mode and write value bit-by-bit
    for p in pins_data:
        p.switch_to_output(value & 0x01)
        value >>= 1

def reset_data_bus ():
    # reset data bus to input mode after a write
    for p in pins_data:
        p.switch_to_input(None)

def read_data_bus ():
    data = 0
    val = 0x01
    for p in pins_data:
        if (p.value):
            data += val
        val <<= 1
    return data

def clock_low ():  # clock falling edge = set clock to low phase
    pin_clk.value = 0
    time.sleep(0.0001)   # wait a minimum of 40ns for tADS (not necessary in Circuit Python, more of a note)

def clock_high ():  # clock rising edge = set clock to high phase
    pin_clk.value = 1
    time.sleep(0.0001)   # wait a minimum of 40ns for tMDS (not necessary in Circuit Python, more of a note)

def dummy_cycle (count):  # cycle the clock without inspection, used during power-up
    for _ in range(count):
        clock_low()
        clock_high()

def set_memory_byte (addr, val):
    global emulated_memory
    lsb = val & 0x00ff
    emulated_memory[addr] = lsb

def set_memory_word (addr, val):
    global emulated_memory
    lsb = val & 0x0ff
    msb = (val >> 8) & 0x0ff
    emulated_memory[addr] = lsb
    emulated_memory[addr+1] = msb

need_to_reset_data_bus = False  # global flag to indicate that the data bus needs reset at start of next clock cycle

address_bus_value = 0x0000
data_bus = 0x00

def cycle_clock (cycles=1, inter_cycle_delay=0):
    global need_to_reset_data_bus, address_bus_value, data_bus, emulated_memory
    for _ in range(cycles):
        # bring the clock (PHI2) low to start the cycle
        # --\__
        clock_low()
        # if the previous cycle was a read from the CPU, free bus after falling edge
        if (need_to_reset_data_bus):
            reset_data_bus()
            need_to_reset_data_bus = False
        # capture the address bus
        address_bus_value = read_addr_bus()
        # capture output status pins
        rw_signal = pin_rw.value      # Read-Write: high = CPU reads from memory, low = CPU writes to memory
        sync_signal = pin_sync.value  # SYNC: high indicates that we're reading an opcode & begin command disassembly
        mlb_signal = pin_mlb.value    # Memory Lock: low indicates memory hold (for delaying RAM access in multi-processor systems)
        vpb_signal = pin_vpb.value    # Vector Pull: low indicates that vector is being fetched during interrupt sequence
        status = "s%d m%d v%d" % (1 if sync_signal else 0, 1 if mlb_signal else 0, 1 if vpb_signal else 0)
        # __/--
        clock_high()
        print("%04x %s " % (address_bus_value, status), end='')
        if (rw_signal):
            # read from memory into CPU
            data_bus = emulated_memory[address_bus_value]
            write_data_bus(data_bus)
            need_to_reset_data_bus = True # need to reset the written data on the data bus AFTER next falling edge of clock
            print("R %02x" % data_bus)
        else:
            # write from CPU out to memory
            data_bus = read_data_bus()
            print("W %02x -> %02x" % (emulated_memory[address_bus_value], data_bus))
            emulated_memory[address_bus_value] = data_bus
        time.sleep(inter_cycle_delay)

def reset_cpu ():
    pin_rst.value = False # put CPU into reset
    time.sleep(0.01)      # allow time to settle (not necessary in Circuit Python, more of a note)
    pin_nmi.value = True  # reset value
    pin_irq.value = True  # reset value
    pin_rdy.value = True  # reset value
    pin_so.value = True   # reset value
    pin_clk.value = True  # reset value
    pin_be.value = True   # reset value
    dummy_cycle(3)        # send "wake-up" clocks - see datasheet
    pin_rst.value = True  # bring CPU out of reset
    # dummy_cycle(7)        # post-reset dummy cycles - see datasheet

def field_number (field_text):
    if len(field_text) > 0:
        if field_text[0] == 'X':
            return int(field_text[1:], 16)
        elif field_text[0] in ['%','B']:
            return int(field_text[1:], 2)
        elif field_text[0] == 'O':
            return int(field_text[1:], 8)
        else:
            return int(field_text)
    return 0

def write_memory (write_address, write_data):
    global emulated_memory
    print("Stored 0x%02x at 0x%04x" % (write_data, write_address))
    emulated_memory[write_address] = write_data

def show_help ():
    print("")
    print("Cupboard v0.1")
    print("C [count=1]      - Cycle CPU clock, number of cycles")
    print("D [addr] [count] - Dump memory; repeats last parameters if none given")
    print("DN               - Dump next memory; increments previous addr by previous count")
    print("RC               - Reset CPU")
    print("RM               - Reset memory")
    print("W [addr] [data]  - Write a byte to memory")
    print("WN [data]        - Write a byte to memory at next address")
    print("")

dump_prev_addr = 0xff00
dump_prev_count = 64
write_prev_address = 0x0000

def handle_command (cmdline):
    global dump_prev_addr, dump_prev_count, write_prev_address
    fields = cmdline.split(' ')
    num_fields = len(fields) - 1
    if num_fields == -1:
        return
    cmd = fields[0]
    if cmd == 'C': # Cycle clock [count]
        num_steps = 1 if num_fields == 0 else field_number(fields[1])
        cycle_clock(num_steps)
    elif cmd == 'D': # Dump memory
        if num_fields == 1:  # use new addr and prev count
            dump_prev_addr = field_number(fields[1])
        elif num_fields == 2:  # use new addr and count
            dump_prev_addr = field_number(fields[1])
            dump_prev_count = field_number(fields[2])
        dump_memory(dump_prev_addr, dump_prev_count)
    elif cmd == 'DN': # Dump Next memory block
        dump_prev_addr += dump_prev_count
        dump_memory(dump_prev_addr, dump_prev_count)
    elif cmd == 'RC': # Reset Cpu
        print("Reset CPU")
        reset_cpu()
    elif cmd == 'RM': # Reset Memory
        print("Reset memory")
        reset_memory()
    elif cmd == 'W': # Write memory
        if num_fields == 2:
            print("Write memory")
            write_prev_address = field_number(fields[1])
            write_memory(write_prev_address, field_number(fields[2]))
        else:
            print("Write requires two arguments: address data")
    elif cmd == 'WN': # Write Next memory
        if num_fields == 1:
            print("Write memory")
            write_prev_address += 1
            write_memory(write_prev_address, field_number(fields[1]))
        else:
            print("Write Next requires one argument: data")
    elif cmd in ['?','H']: # help
        show_help()
    else:
        print("Unknown command '%s'" % cmd)
        show_help()

# -----------------------------------------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------------------------------------
def main ():
    reset_memory()
    reset_cpu()
    while True:
        led.value = True
        if supervisor.runtime.serial_bytes_available:
            cmdline = input().strip().upper()
            # ignore empty input
            if len(cmdline) > 0:
                handle_command(cmdline)
        time.sleep(0.01)
        led.value = False
        time.sleep(0.05)

if __name__ == "__main__":
    main()
