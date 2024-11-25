import serial
import argparse

# show extra runtime information
verbose = False

def echo_check (ser):
    ser.write(b'.\r\n')
    ser.readline() # ignore echo
    echo_done = False
    attempts = 1
    while not echo_done and attempts < 5:
        data = ser.readline()
        if len(data) > 0:
            data = data.decode('utf-8').strip()
            echo_done = (data == "EEP:")
        else:                
            ser.write(b'.\r\n')
            ser.readline() # ignore echo
        attempts += 1
    return attempts < 5
    
def version_check (ser):
    ser.write(b'V\r\n')
    ser.readline() # ignore echo
    ver = ser.readline().decode('utf-8').strip()
    print(ver)
    data = ser.readline().decode('utf-8').strip()
    return (data == "EEP:")

def read_eeprom (port, output_filename, relocate):
    with open(output_filename, "wt") as f:
        with serial.Serial(port, 115200, timeout=1) as ser:
            if not echo_check(ser):
                return
            if not version_check(ser):
                return
            addr = 0
            ser.write(b'D 0 10\r\n')
            ser.readline() # ignore echo
            while addr < 0x8000:
                f.write("%04x " % (addr + relocate))
                data = ser.readline().decode('utf-8').strip().split(' ')[1:]
                ser.readline() # ignore "EEP:"
                for d in data:
                    if len(d) > 0:
                        f.write("%02x " % int(d, 16))
                        addr += 1
                f.write("\n")
                if addr < 0x8000:
                    ser.write(b'DN\r\n')
                    ser.readline() # ignore echo

def write_eeprom (port, input_filename, relocate):
    with open(input_filename, "rt") as f:
        with serial.Serial(port, 115200, timeout=2) as ser:
            if not echo_check(ser):
                return
            if not version_check(ser):
                return
            for l in f.readlines():
                t = l.strip().split(' ', 1)
                if len(t) > 1:
                    addr = int(t[0], 16) - relocate
                    cmd = "W %04x %s" % (addr, t[1])
                    print(cmd)
                    ser.write(bytes(cmd, 'utf-8'))
                    ser.readline() # ignore echo
                    ser.readline() # ignore "EEP:"

def main ():
    global verbose
    parser = argparse.ArgumentParser(description='EEP EEPROM Programmer Client')
    parser.add_argument('command', type=str, help='EEP command: READ|WRITE|COMPARE')
    parser.add_argument('filename', type=str, help='file to read, write, or compare')
    parser.add_argument('-p', '--port', type=str, default="COM15", help='serial port of programmer')
    parser.add_argument('-r', '--relocate', type=int, default=0x8000, help='address offset to apply')
    parser.add_argument('-v', '--verbose', action="store_true", help='display extra runtime info')
    args = parser.parse_args()
    verbose = args.verbose
    relocate = args.relocate
    filename = args.filename
    port = args.port

    if verbose:
        print("Connecting to EEPROM programmer on port %s" % port)
        print("Relocation offset = 0x%04x" % relocate)

    cmd = args.command.upper()
    if cmd in ["R", "READ"]:  # read contents of EEPROM and store in hex file
        print(f"Read EEPROM into {filename}")
        read_eeprom(port, filename, relocate)

    elif cmd in ["W", "WRITE"]:  # write EEPROM with contents of hex file
        print(f"Write {filename} to EEPROM")
        write_eeprom(port, filename, relocate)

    elif cmd in ["C", "COMPARE"]:  # compare EEPROM contents with that of a hex file
        print(f"Compare {filename} to EEPROM")

    else:
        print(f"Unrecognized command {cmd}")
    print("Exiting")

if __name__ == "__main__":
    main()
