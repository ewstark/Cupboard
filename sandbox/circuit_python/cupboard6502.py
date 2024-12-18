# This Circuit Python code is designed to run on an Adafruit M4 Grand Central board. It assumes lots of memory and quick execution speed.

import board
import digitalio
import time
import supervisor

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
    time.sleep(0)   # wait a minimum of 40ns for tADS (not necessary in Circuit Python, more of a note) - sleep(0) takes ~16us on M4

def clock_high ():  # clock rising edge = set clock to high phase
    pin_clk.value = 1
    time.sleep(0)   # wait a minimum of 40ns for tMDS (not necessary in Circuit Python, more of a note)

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
 