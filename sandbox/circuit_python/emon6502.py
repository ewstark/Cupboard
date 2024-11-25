# This Circuit Python code is designed to run on an Adafruit M4 Grand Central board. It assumes lots of memory and quick execution speed.

import board
import digitalio
import time
import supervisor

# global data
dump_prev_addr       = 0x0000  # track previously dumped address...
dump_prev_count      = 16      # ...and width
write_prev_address   = 0x0000  # track previously written address
output_width         = 16      # number of bytes to display per line of dumped memory
force_hex            = True    # assume arguments are hexadecimal; otherwise assume decimal and use 'x', 'o', or '%' prefixes for hex, octal, or binary
force_data_bus_reset = False   # global flag to indicate that the data bus needs reset at start of next clock cycle
address_bus_value    = 0x0000  # current state of the address bus
data_bus_value       = 0x00    # current state of the data bus
free_run_enable      = False   # free mode
free_run_delay       = 0       # when in free-run, the delay

# on-board red LED
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Dictionary of all possible 256 opcode bytes mapped to the instruction length/cycles/mnemonic tuple - used to disassemble
# opcode : (length, cycles, mnemonic)
opcodes = {0x00 : (1, 1, "BRK a"),   0x01 : (1, 1, "ORA (zp,x)"),  0x02 : (1, 1, "ILLEGAL"),     0x03 : (1, 1, "ILLEGAL"),  0x04 : (1, 1, "TSB zp •"),     0x05 : (1, 1, "ORA zp"),    0x06 : (1, 1, "ASL zp"),     0x07 : (1, 1, "RMB0 zp •"),    
           0x08 : (1, 1, "PHP s"),   0x09 : (1, 1, "ORA #"),       0x0A : (1, 1, "ASL A"),       0x0B : (1, 1, "ILLEGAL"),  0x0C : (1, 1, "TSB a •"),      0x0D : (1, 1, "ORA a"),     0x0E : (1, 1, "ASL a"),      0x0F : (1, 1, "BBR0 r •"),     
           0x10 : (1, 1, "BPL r"),   0x11 : (1, 1, "ORA (zp),y"),  0x12 : (1, 1, "ORA (zp) ∗"),  0x13 : (1, 1, "ILLEGAL"),  0x14 : (1, 1, "TRB zp •"),     0x15 : (1, 1, "ORA zp,x"),  0x16 : (1, 1, "ASL zp,x"),   0x17 : (1, 1, "RMB1 zp •"),    
           0x18 : (1, 1, "CLC i"),   0x19 : (1, 1, "ORA a,y"),     0x1A : (1, 1, "INC A ∗"),     0x1B : (1, 1, "ILLEGAL"),  0x1C : (1, 1, "TRB a •"),      0x1D : (1, 1, "ORA a,x"),   0x1E : (1, 1, "ASL a,x"),    0x1F : (1, 1, "BBR1 r •"),     
           0x20 : (1, 1, "JSR a"),   0x21 : (1, 1, "AND (zp,x)"),  0x22 : (1, 1, "ILLEGAL"),     0x23 : (1, 1, "ILLEGAL"),  0x24 : (1, 1, "BIT zp"),       0x25 : (1, 1, "AND zp"),    0x26 : (1, 1, "ROL zp"),     0x27 : (1, 1, "RMB2 zp •"),    
           0x28 : (1, 1, "PLP s"),   0x29 : (1, 1, "AND #"),       0x2A : (1, 1, "ROL A"),       0x2B : (1, 1, "ILLEGAL"),  0x2C : (1, 1, "BIT a"),        0x2D : (1, 1, "AND a"),     0x2E : (1, 1, "ROL a"),      0x2F : (1, 1, "BBR2 r •"),     
           0x30 : (1, 1, "BMI r"),   0x31 : (1, 1, "AND (zp),y"),  0x32 : (1, 1, "AND (zp) ∗"),  0x33 : (1, 1, "ILLEGAL"),  0x34 : (1, 1, "BIT zp,x •"),   0x35 : (1, 1, "AND zp,x"),  0x36 : (1, 1, "ROL zp,x"),   0x37 : (1, 1, "RMB3 zp •"),    
           0x38 : (1, 1, "SEC I"),   0x39 : (1, 1, "AND a,y"),     0x3A : (1, 1, "DEC A"),       0x3B : (1, 1, "ILLEGAL"),  0x3C : (1, 1, "BIT a,x ∗"),    0x3D : (1, 1, "AND a,x"),   0x3E : (1, 1, "ROL a,x"),    0x3F : (1, 1, "BBR3 r •"),     
           0x40 : (1, 1, "RTI s"),   0x41 : (1, 1, "EOR (zp,x)"),  0x42 : (1, 1, "ILLEGAL"),     0x43 : (1, 1, "ILLEGAL"),  0x44 : (1, 1, "ILLEGAL"),      0x45 : (1, 1, "EOR zp"),    0x46 : (1, 1, "LSR zp"),     0x47 : (1, 1, "RMB4 zp •"),    
           0x48 : (1, 1, "PHA s"),   0x49 : (1, 1, "EOR #"),       0x4A : (1, 1, "LSR A ∗"),     0x4B : (1, 1, "ILLEGAL"),  0x4C : (1, 1, "JMP a"),        0x4D : (1, 1, "EOR a"),     0x4E : (1, 1, "LSR a"),      0x4F : (1, 1, "BBR4 r •"),     
           0x50 : (1, 1, "BVC r"),   0x51 : (1, 1, "EOR (zp),y"),  0x52 : (1, 1, "EOR (zp) ∗"),  0x53 : (1, 1, "ILLEGAL"),  0x54 : (1, 1, "ILLEGAL"),      0x55 : (1, 1, "EOR zp,x"),  0x56 : (1, 1, "LSR zp,x"),   0x57 : (1, 1, "RMB5 zp •"),    
           0x58 : (1, 1, "CLI i"),   0x59 : (1, 1, "EOR a,y"),     0x5A : (1, 1, "PHY s •"),     0x5B : (1, 1, "ILLEGAL"),  0x5C : (1, 1, "ILLEGAL"),      0x5D : (1, 1, "EOR a,x"),   0x5E : (1, 1, "LSR a,x"),    0x5F : (1, 1, "BBR5 r •"),     
           0x60 : (1, 1, "RTS s"),   0x61 : (1, 1, "ADC (zp,x)"),  0x62 : (1, 1, "ILLEGAL"),     0x63 : (1, 1, "ILLEGAL"),  0x64 : (1, 1, "STZ zp •"),     0x65 : (1, 1, "ADC zp"),    0x66 : (1, 1, "ROR zp"),     0x67 : (1, 1, "RMB6 zp •"),    
           0x68 : (1, 1, "PLA s"),   0x69 : (1, 1, "ADC #"),       0x6A : (1, 1, "ROR A"),       0x6B : (1, 1, "ILLEGAL"),  0x6C : (1, 1, "JMP (a)"),      0x6D : (1, 1, "ADC a"),     0x6E : (1, 1, "ROR a"),      0x6F : (1, 1, "BBR6 r •"),     
           0x70 : (1, 1, "BVS r"),   0x71 : (1, 1, "ADC (zp),y"),  0x72 : (1, 1, "ADC (zp) ∗"),  0x73 : (1, 1, "ILLEGAL"),  0x74 : (1, 1, "STZ zp,x •"),   0x75 : (1, 1, "ADC zp,x"),  0x76 : (1, 1, "ROR zp,x"),   0x77 : (1, 1, "RMB7 zp •"),    
           0x78 : (1, 1, "SEI i"),   0x79 : (1, 1, "ADC a,y"),     0x7A : (1, 1, "PLY s •"),     0x7B : (1, 1, "ILLEGAL"),  0x7C : (1, 1, "JMP (a.x) ∗"),  0x7D : (1, 1, "ADC a,x"),   0x7E : (1, 1, "ROR a,x"),    0x7F : (1, 1, "BBR7 r •"),     
           0x80 : (1, 1, "BRA r •"), 0x81 : (1, 1, "STA (zp,x)"),  0x82 : (1, 1, "ILLEGAL"),     0x83 : (1, 1, "ILLEGAL"),  0x84 : (1, 1, "STY zp"),       0x85 : (1, 1, "STA zp"),    0x86 : (1, 1, "STZ zp"),     0x87 : (1, 1, "SMB0 zp •"),    
           0x88 : (1, 1, "DEY i"),   0x89 : (1, 1, "BIT #"),       0x8A : (1, 1, "TXA i"),       0x8B : (1, 1, "ILLEGAL"),  0x8C : (1, 1, "STY a •"),      0x8D : (1, 1, "STA a"),     0x8E : (1, 1, "STX a"),      0x8F : (1, 1, "BBS0 r •"),     
           0x90 : (1, 1, "BCC r"),   0x91 : (1, 1, "STA (zp),y"),  0x92 : (1, 1, "STA (zp) ∗"),  0x93 : (1, 1, "ILLEGAL"),  0x94 : (1, 1, "STY zp,x"),     0x95 : (1, 1, "STA zp,x"),  0x96 : (1, 1, "STZ zp,y"),   0x97 : (1, 1, "SMB1 zp •"),    
           0x98 : (1, 1, "TYA i"),   0x99 : (1, 1, "STA a,y"),     0x9A : (1, 1, "TSX i"),       0x9B : (1, 1, "ILLEGAL"),  0x9C : (1, 1, "STZ a"),        0x9D : (1, 1, "STA a,x"),   0x9E : (1, 1, "STZ a,x •"),  0x9F : (1, 1, "BBS1 r •"),     
           0xA0 : (1, 1, "LDY #"),   0xA1 : (1, 1, "LDA (zp,x)"),  0xA2 : (1, 1, "LDX # ∗"),     0xA3 : (1, 1, "ILLEGAL"),  0xA4 : (1, 1, "LDY zp"),       0xA5 : (1, 1, "LDA zp"),    0xA6 : (1, 1, "LDX zp"),     0xA7 : (1, 1, "SMB2 zp •"),    
           0xA8 : (1, 1, "TAY i"),   0xA9 : (1, 1, "LDA #"),       0xAA : (1, 1, "TAX i"),       0xAB : (1, 1, "ILLEGAL"),  0xAC : (1, 1, "LDY a"),        0xAD : (1, 1, "LDA a"),     0xAE : (1, 1, "LDX a"),      0xAF : (1, 1, "BBS2 r •"),     
           0xB0 : (1, 1, "BCS r"),   0xB1 : (1, 1, "LDA (zp),y"),  0xB2 : (1, 1, "LDA (zp) ∗"),  0xB3 : (1, 1, "ILLEGAL"),  0xB4 : (1, 1, "LDY zp,x"),     0xB5 : (1, 1, "LDA zp,x"),  0xB6 : (1, 1, "LDX zp,y"),   0xB7 : (1, 1, "SMB3 zp •"),    
           0xB8 : (1, 1, "CLV i"),   0xB9 : (1, 1, "LDA A,y"),     0xBA : (1, 1, "TSX i"),       0xBB : (1, 1, "ILLEGAL"),  0xBC : (1, 1, "LDY a,x"),      0xBD : (1, 1, "LDA a,x"),   0xBE : (1, 1, "LDX a,x"),    0xBF : (1, 1, "BBS3 r •"),     
           0xC0 : (1, 1, "CPY #"),   0xC1 : (1, 1, "CMP (zp,x)"),  0xC2 : (1, 1, "ILLEGAL"),     0xC3 : (1, 1, "ILLEGAL"),  0xC4 : (1, 1, "CPY zp"),       0xC5 : (1, 1, "CMP zp"),    0xC6 : (1, 1, "DEC zp"),     0xC7 : (1, 1, "SMB4 zp •"),    
           0xC8 : (1, 1, "INY i"),   0xC9 : (1, 1, "CMP #"),       0xCA : (1, 1, "DEX i"),       0xCB : (1, 1, "WAI I •"),  0xCC : (1, 1, "CPY a"),        0xCD : (1, 1, "CMP a"),     0xCE : (1, 1, "DEC a"),      0xCF : (1, 1, "BBS4 r •"),     
           0xD0 : (1, 1, "BNE r"),   0xD1 : (1, 1, "CMP (zp),y"),  0xD2 : (1, 1, "CMP (zp) ∗"),  0xD3 : (1, 1, "ILLEGAL"),  0xD4 : (1, 1, "ILLEGAL"),      0xD5 : (1, 1, "CMP zp,x"),  0xD6 : (1, 1, "DEC zp,x"),   0xD7 : (1, 1, "SMB5 zp •"),    
           0xD8 : (1, 1, "CLD i"),   0xD9 : (1, 1, "CMP a,y"),     0xDA : (1, 1, "PHX s •"),     0xDB : (1, 1, "STP I •"),  0xDC : (1, 1, "ILLEGAL"),      0xDD : (1, 1, "CMP a,x"),   0xDE : (1, 1, "DEC a,x"),    0xDF : (1, 1, "BBS5 r •"),     
           0xE0 : (1, 1, "CPX #"),   0xE1 : (1, 1, "SBC (zp,x)"),  0xE2 : (1, 1, "ILLEGAL"),     0xE3 : (1, 1, "ILLEGAL"),  0xE4 : (1, 1, "CPX zp"),       0xE5 : (1, 1, "SBC zp"),    0xE6 : (1, 1, "INC zp"),     0xE7 : (1, 1, "SMB6 zp •"),    
           0xE8 : (1, 1, "INX i"),   0xE9 : (1, 1, "SBC #"),       0xEA : (1, 1, "NOP i"),       0xEB : (1, 1, "ILLEGAL"),  0xEC : (1, 1, "CPX a"),        0xED : (1, 1, "SBC a"),     0xEE : (1, 1, "INC a"),      0xEF : (1, 1, "BBS6 r •"),     
           0xF0 : (1, 1, "BEQ r"),   0xF1 : (1, 1, "SBC (zp),y"),  0xF2 : (1, 1, "SBC (zp) ∗"),  0xF3 : (1, 1, "ILLEGAL"),  0xF4 : (1, 1, "ILLEGAL"),      0xF5 : (1, 1, "SBC zp,x"),  0xF6 : (1, 1, "INC zp,x"),   0xF7 : (1, 1, "SMB7 zp •"),    
           0xF8 : (1, 1, "SED i"),   0xF9 : (1, 1, "SBC a,y"),     0xFA : (1, 1, "PLX s •"),     0xFB : (1, 1, "ILLEGAL"),  0xFC : (1, 1, "ILLEGAL"),      0xFD : (1, 1, "SBC a,x"),   0xFE : (1, 1, "INC a,x"),    0xFF : (1, 1, "BBS7 r •")}     

# pre-compiled demo programs
# blinky
pgm_blinky = ["8000 a2 ff 9a a9 ff 8d 02 60 a9 f0 8d 03 60 a9 00 8d",
              "8010 00 60 8d 01 60 a9 10 8d 01 60 a9 00 8d 01 60 4c",
              "8020 15 80",
              "fffa 00 80 00 80 00 80"]

pgm_hello = ["8000 a2 ff 9a a9 ff 8d 02 60",
             "8008 a9 e0 8d 03 60 a9 38 20",
             "8010 63 80 a9 0e 20 63 80 a9",
             "8018 06 20 63 80 a9 01 20 63",
             "8020 80 a2 00 bd 32 80 f0 07",
             "8028 20 79 80 e8 4c 23 80 4c",
             "8030 2f 80 48 65 6c 6c 6f 2c",
             "8038 20 77 6f 72 6c 64 21 00",
             "8040 48 a9 00 8d 02 60 a9 40",
             "8048 8d 01 60 a9 c0 8d 01 60",
             "8050 ad 00 60 29 80 d0 ef a9",
             "8058 40 8d 01 60 a9 ff 8d 02",
             "8060 60 68 60 20 40 80 8d 00",
             "8068 60 a9 00 8d 01 60 a9 80",
             "8070 8d 01 60 a9 00 8d 01 60",
             "8078 60 20 40 80 8d 00 60 a9",
             "8080 20 8d 01 60 a9 a0 8d 01",
             "8088 60 a9 20 8d 01 60 60",
             "fffa 00 80 00 80 00 80"]

# Full 64K address space
emulated_memory = bytearray(65536)

# take a hex-dump output line and store the data in emulated memory
def store_emulated_memory (asm_out_string):
    global emulated_memory
    fields = asm_out_string.strip().split(' ')
    if len(fields) > 1:
        addr = int(fields[0], 16)
        for d in fields[1:]:
            emulated_memory[addr] = int(d, 16)
            addr += 1

# load a pre-compiled program into emulated ROM
def load_emulated_program (pgm):
    for l in pgm:
        store_emulated_memory(l)

# reset emulated memory to default state
def reset_memory ():
    global emulated_memory
    # fill with NOPs
    for i in range(65536): 
        emulated_memory[i] = 0xea
    # load emulated program
    load_emulated_program(pgm_hello)

# dump the contents of emulated memory
def dump_memory (start_address, num_bytes):
    global emulated_memory
    num_cols = 0
    for a in range(start_address, start_address + num_bytes):
        if num_cols == 0:
            print("%04x: " % a, end='')
        if is_emulated_memory(a):
            print("%02x " % emulated_memory[a], end='')
        else:
            print("?? ", end='')
        num_cols += 1
        if num_cols == 8:
            print(" ", end='')
        elif num_cols >= 16:
            num_cols = 0
            print()
    if num_cols > 0:
        print()

# returns True if the address is part of the emulated memory
def is_emulated_memory (address):
    return False # address >= 0x8000

# assigned GPIO pins for CPU interface
pins_addr = [digitalio.DigitalInOut(i) for i in [board.D38, board.D39, board.D40, board.D41, board.D42, board.D43, board.D44, board.D45, board.D30, board.D31, board.D32, board.D33, board.D34, board.D35, board.D36, board.D37]]  # CPU outputs
pins_data = [digitalio.DigitalInOut(i) for i in [board.D22, board.D23, board.D24, board.D25, board.D26, board.D27, board.D28, board.D29]] # CPU bidirectional
pin_clk   = digitalio.DigitalInOut(board.D14)  # CPU input
pin_rst   = digitalio.DigitalInOut(board.D15)  # CPU input
pin_irq   = digitalio.DigitalInOut(board.D16)  # CPU input
pin_nmi   = digitalio.DigitalInOut(board.D17)  # CPU input
pin_sync  = digitalio.DigitalInOut(board.D18)  # CPU output
pin_vpb   = digitalio.DigitalInOut(board.D19)  # CPU output
pin_rw    = digitalio.DigitalInOut(board.D20)  # CPU output
pin_mlb   = digitalio.DigitalInOut(board.D21)  # CPU output
# pin_rdy   = digitalio.DigitalInOut(board.D)  # CPU input mainly (bidirectional, protected with 10K resistor)
# pin_so    = digitalio.DigitalInOut(board.D)  # CPU input
# pin_be    = digitalio.DigitalInOut(board.D)  # CPU input

# reset all pins to their default state
def reset_all_pins ():
    global pins_addr, pins_data, pin_clk, pin_rst, pin_irq, pin_nmi, pin_sync, pin_vpb, pin_rw, pin_mlb
    for p in pins_addr:
        p.switch_to_input(None) # output from CPU = input to Cupboard, no pull
    for p in pins_data:
        p.switch_to_input(None) # initially assume output from CPU = input to Cupboard, no pull; will switch when need to "write" data to the CPU (on a CPU read instruction)
    pin_clk.switch_to_output(True)   # CPU input = output from Cupboard
    pin_rst.switch_to_output(False)  # CPU input = output from Cupboard
    pin_irq.switch_to_input(None)    # CPU input = output from VIA = input to Cupboard
    pin_nmi.switch_to_output(True)   # CPU input = output from Cupboard (pulled high by 1K)
    pin_sync.switch_to_input(None)   # CPU output = input to Cupboard
    pin_vpb.switch_to_input(None)    # CPU output = input to Cupboard
    pin_rw.switch_to_input(None)     # CPU output = input to Cupboard
    pin_mlb.switch_to_input(None)    # CPU output = input to Cupboard
    # pin_rdy.switch_to_output(True)   # CPU input = output from Cupboard
    # pin_so.switch_to_output(True)    # CPU input = output from Cupboard
    # pin_be.switch_to_output(True)    # CPU input = output from Cupboard

# read the 16-bit address from the address bus
def read_addr_bus ():
    global pins_addr
    addr = 0
    val = 0x0001
    for p in pins_addr:
        if (p.value):
            addr += val
        val <<= 1
    return addr

# switch data bus to output mode and write value bit-by-bit
def write_data_bus (value):
    global pins_data
    for p in pins_data:
        p.switch_to_output(value & 0x01)
        value >>= 1

# reset data bus to input mode after a write
def reset_data_bus ():
    global pins_data
    for p in pins_data:
        p.switch_to_input(None)

# read the data bus (assumed to be in input mode)
def read_data_bus ():
    global pins_data
    data = 0
    val = 0x01
    for p in pins_data:
        if (p.value):
            data += val
        val <<= 1
    return data

# clock falling edge = set clock to low phase
def clock_low ():
    global pin_clk
    pin_clk.value = 0
    time.sleep(0)   # wait a minimum of 40ns for tADS - sleep(0) takes ~16us on M4 in Circuit Python

# clock rising edge = set clock to high phase
def clock_high ():
    global pin_clk  
    pin_clk.value = 1
    time.sleep(0)   # wait a minimum of 40ns for tMDS - sleep(0) takes ~16us on M4 in Circuit Python

# cycle the clock without inspection, used during power-up to reset chip
def dummy_cycle (count):  
    for _ in range(count):
        clock_low()
        time.sleep(0.001)
        clock_high()
        time.sleep(0.001)

# perform one or more complete clock cycles
def cycle_clock (cycles=1, inter_cycle_delay=0):
    global force_data_bus_reset, address_bus_value, data_bus_value, emulated_memory
    global pins_addr, pins_data, pin_clk, pin_rst, pin_irq, pin_nmi, pin_sync, pin_vpb, pin_rw, pin_mlb
    for _ in range(cycles):
        # bring the clock (PHI2) low to start the cycle
        # --\__
        clock_low()
        # if the previous cycle was a read from the CPU, free bus after falling edge
        if (force_data_bus_reset):
            reset_data_bus()
            force_data_bus_reset = False
        # capture the address bus
        address_bus_value = read_addr_bus()
        # capture output status pins
        rw_signal = pin_rw.value      # Read-Write: high = CPU reads from memory, low = CPU writes to memory
        sync_signal = pin_sync.value  # SYNC: high indicates that we're reading an opcode & begin command disassembly
        mlb_signal = pin_mlb.value    # Memory Lock: low indicates memory hold (for delaying RAM access in multi-processor systems)
        vpb_signal = pin_vpb.value    # Vector Pull: low indicates that vector is being fetched during interrupt sequence
        status = "smv%d%d%d" % (1 if sync_signal else 0, 1 if mlb_signal else 0, 1 if vpb_signal else 0)
        # __/--
        clock_high()
        print("%04x %s " % (address_bus_value, status), end='')
        if (rw_signal):
            # READ operation
            if is_emulated_memory(address_bus_value):
                # part of emulated memory - "write" data back to the CPU
                data_bus_value = emulated_memory[address_bus_value]
                write_data_bus(data_bus_value)
                force_data_bus_reset = True # need to reset the written data on the data bus AFTER next falling edge of clock
                print("R %02x" % data_bus_value)
            else:
                # not part of emulated memory - read data from bus and report
                data_bus_value = read_data_bus()
                print("r %02x" % data_bus_value)
        else:
            # WRITE operation
            data_bus_value = read_data_bus()
            if is_emulated_memory(address_bus_value):
                # part of emulated memory - save data and report change
                print("W %02x -> %02x" % (emulated_memory[address_bus_value], data_bus_value))
                emulated_memory[address_bus_value] = data_bus_value
            else:
                # not part of emulated memory - report data
                print("w %02x" % data_bus_value)
        time.sleep(inter_cycle_delay)

# reset state of the CPU
def reset_cpu ():
    global pins_addr, pins_data, pin_clk, pin_rst, pin_irq, pin_nmi, pin_sync, pin_vpb, pin_rw, pin_mlb
    pin_rst.value = False # put CPU into reset
    time.sleep(0.01)      # allow time to settle (not necessary in Circuit Python, more of a note)
    pin_nmi.value = True  # reset value
    pin_clk.value = True  # reset value
    dummy_cycle(3)        # send "wake-up" clocks - see datasheet
    pin_rst.value = True  # bring CPU out of reset
    # dummy_cycle(8)        # post-reset dummy cycles - see datasheet

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
    print("EMon-6502 v0.1")

def show_help ():
    print_version()
    print("  C count?  - Cycle CPU clock, optional number of cycles")
    print("  FR delay? - Free Run clock, optional delay in milliseconds")
    print("  RC        - Reset CPU")
    print("  ?         - Help, show this information")
    print("  .         - Echo request, expects '*' and return to prompt")
    print("  H ON|OFF  - Hex-only mode on or off, report state if no parameter")
    print("  V         - Version, report software version")

def handle_command (cmd, args):
    global dump_prev_addr, dump_prev_count, write_prev_address, output_width, pin_oe, force_hex, free_run_delay, free_run_enable
    num_args = len(args)

    if cmd == 'C': # Cycle clock [count]
        num_steps = 1 if num_args == 0 else convert_user_number(args[0])
        cycle_clock(num_steps)

    elif cmd == 'FR': # Free Run
        free_run_delay = 0 if num_args == 0 else (convert_user_number(args[0]) / 1000.0)
        free_run_enable = True

    elif cmd == 'RC': # Reset Cpu
        print("Reset CPU")
        reset_cpu()

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

    elif cmd == 'V': # Version
        print_version()

    elif cmd == '?': # Help
        show_help()

    elif cmd == '.': # Echo
        print("*")

    else:
        print("Unknown command '%s'" % cmd, args)
        show_help()

# -----------------------------------------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------------------------------------
def main ():
    global free_run_enable, free_run_delay
    reset_all_pins()
    reset_cpu()
    reset_memory()
    led.value = True
    print("\nEMon:")
    while True:
        while supervisor.runtime.serial_bytes_available:
            input_fields = input().strip().upper().split(' ')
            free_run_enable = False  # any keyboard input breaks free-run
            if len(input_fields) > 0:
                cmd = input_fields[0]
                args = []
                for a in input_fields[1:]:
                    if len(a) > 0:
                        args.append(a)
                handle_command(cmd, args)
            print("EMon:")
        if free_run_enable:
            time.sleep(free_run_delay)
            cycle_clock()
        else:
            time.sleep(0.05)
            led.value = not led.value

if __name__ == "__main__":
    main()

