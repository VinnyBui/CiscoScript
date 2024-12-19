import serial
import time
import os
import platform

# Determine the correct serial port based on the operating system
if platform.system() == "Windows":
    SERIAL_PORT = 'COM1'  # Default port for Windows
else:
    SERIAL_PORT = '/dev/ttyS0'  # Default port for Linux

# Configuration for serial connection
BAUD_RATE = 9600       # Standard baud rate for Cisco devices
LOG_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "CiscoLogs")  # Log directory on Desktop

# Establish the serial connection
ser = serial.Serial(
    port=SERIAL_PORT,
    baudrate=BAUD_RATE,
    timeout=1,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
)

def send_break_signal():
    """Send a break signal to enter ROMMON mode."""
    time.sleep(5)
    for _ in range(3):
        ser.send_break()
        time.sleep(1)
    ser.write(b'\n')

def wait_for_prompt(prompt, timeout=90):
    """Wait for a specific prompt to appear within the timeout."""
    start_time = time.time()
    output = ""
    current_timeout = 1

    while True:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting).decode(errors="ignore")
            output += data
            print(data, end="")

            if prompt in output:
                print(f"\nFound prompt: {prompt}")
                return True, output

        if time.time() - start_time > timeout:
            print(f"\nTimeout reached while waiting for: {prompt}")
            return False, output

        time.sleep(current_timeout)
        current_timeout = min(current_timeout + 1, 5)

def write_and_wait(command, expected_prompt, timeout=90):
    """Send a command and wait for the expected prompt."""
    ser.write(command)
    return wait_for_prompt(expected_prompt, timeout)

def get_snmp_chassis_serial():
    """Retrieve the SNMP chassis serial number."""
    ser.reset_input_buffer()
    ser.write(b"\n show snmp chassis\n")
    time.sleep(2)
    found, output = wait_for_prompt("Router#", timeout=10)

    if found:
        lines = output.splitlines()
        for line in lines:
            serial_num = line.strip()
            if serial_num and serial_num.isalnum() and len(serial_num) > 5:
                print(f"SNMP Chassis Serial Number: {serial_num}")
                return serial_num

    print("Failed to retrieve SNMP chassis information.")
    return None

def create_log_file(serial_number):
    """Create a log file named after the serial number on the Desktop."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    return open(os.path.join(LOG_DIR, f"{serial_number}.txt"), "w")

def capture_cisco_commands(log_file):
    """Capture output from a list of Cisco commands and log them."""
    commands = [
        "term length 0",
        "!",
        "show inventory",
        "show hardware",
        "show env all",
        "show license feature",
        "show license status"
    ]
    for cmd in commands:
        log_file.write(f"\n{cmd}\n")
        ser.write((cmd + "\r").encode())
        time.sleep(2)
        
        output = ""
        while ser.in_waiting > 0:
            output += ser.read(ser.in_waiting).decode(errors="ignore")
        log_file.write(output + "\n")
        print(output)

def configure_router():
    """Run initial configuration commands on the router."""
    if write_and_wait(b"confreg 0x2142\n", "rommon 2 >")[0]:
        print("Configuration register set to 0x2142.")
        if write_and_wait(b"reset\n", "Would you like to enter the initial configuration dialog? [yes/no]:")[0]:
            print("Router is resetting...")
            ser.write(b'no\n')
            ser.write(b'\r')
            ser.flush()
            if write_and_wait(b"", "Router>")[0]:
                if write_and_wait(b"enable\n", "Router#")[0]:
                    print("Reached user mode prompt.")
                    configure_terminal()

def configure_terminal():
    """Enter terminal configuration mode and set up basic configurations."""
    if write_and_wait(b"\nwrite erase\n", "Continue? [confirm]")[0]:
        if write_and_wait(b"\n", "Router#")[0]:
            if write_and_wait(b"configure terminal\n", "Router(config)#")[0]:
                write_and_wait(b"config-register 0x2102\n", "Router(config)#")
                write_and_wait(b"no logging monitor\n", "Router(config)#")
                write_and_wait(b"no terminal monitor\n", "Router(config)#")
                write_and_wait(b"snmp-server community public RO\n", "Router(config)#")
                write_and_wait(bytes([26]), "#")

def reload_router():
    """Send the reload command and respond 'no' to the save configuration prompt."""
    if write_and_wait(b"\nreload\n", "System configuration has been modified. Save? [yes/no]:")[0]:
        print("Sending 'no' to discard saving the configuration...")
        ser.write(b"no\n")
        ser.flush()  # Ensure 'no' is sent immediately

        # Wait for confirmation of the reload or any final prompt if necessary
        write_and_wait(b"", "Proceed with reload? [confirm]", timeout=10)
        ser.write(b"\n")  # Send confirmation
        ser.flush()

def main():
    """Main function to execute all steps."""
    try:
        send_break_signal()
        if write_and_wait(b'', "rommon 1 >")[0]:
            configure_router()
            serial_number = get_snmp_chassis_serial()
            if serial_number:
                with create_log_file(serial_number) as log_file:
                    capture_cisco_commands(log_file)
                
                reload_router() 
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        ser.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()
