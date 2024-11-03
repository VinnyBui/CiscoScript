import serial
import time
import os

# Configuration for serial connection
serial_port = 'COM5'  # Replace with your COM port
baud_rate = 9600       # Standard baud rate for Cisco devices

# Establish the serial connection
ser = serial.Serial(
    port=serial_port,
    baudrate=baud_rate,
    timeout=1,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
)

def send_break_signal():
    """Send a break signal to enter ROMMON mode."""
    time.sleep(5)  # Initial wait to allow the router to start booting
    for _ in range(3):  # Send the break signal three times
        ser.send_break()
        time.sleep(1)  # Allow time for the device to process the break
    ser.write(b'\n')  # Send Enter key to proceed

def wait_for_prompt(prompt, timeout=90):
    """Wait for a specific prompt to appear with dynamic timeout handling."""
    start_time = time.time()
    output = ""
    current_timeout = 1  # Start with a 1-second timeout

    while True:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting).decode(errors="ignore")
            output += data
            print(data, end="")  # Print received data immediately
            
            if prompt in output:
                print(f"\nFound prompt: {prompt}")
                return True, output
        
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            print(f"\nTimeout reached while waiting for: {prompt}")
            return False, output

        time.sleep(current_timeout)  # Sleep for the current timeout
        current_timeout = min(current_timeout + 1, 5)  # Increase timeout up to 5 seconds

def write_and_wait(command, expected_prompt, timeout=90):
    """Send a command and wait for the expected prompt."""
    ser.write(command)
    return wait_for_prompt(expected_prompt, timeout)

def get_snmp_chassis_serial():
    """Retrieve and parse the SNMP chassis serial number."""
    ser.reset_input_buffer()  # Clear any previous data in the input buffer
    ser.write(b"\n show snmp chassis\n")
    time.sleep(2)  
    found, output = wait_for_prompt("Router#", timeout=10)  # Wait for the Router prompt

    if found:
        # Search for the serial number in the output
        lines = output.splitlines()
        for line in lines:
            serialNum = line.strip()
            if serialNum and serialNum.isalnum() and len(serialNum) > 5:  # Check for alphanumeric and reasonable length
                print(f"SNMP Chassis Serial Number: {serialNum}")
                return serialNum

    print("Failed to retrieve SNMP chassis information.")
    return None

def create_log_file(serial_number):
    """Create a log file named after the serial number on the desktop in a CiscoLogs folder."""
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "CiscoLogs")
    if not os.path.exists(desktop_path):
        os.makedirs(desktop_path)  # Create the directory if it doesn't exist
    log_file_path = os.path.join(desktop_path, f"{serial_number}.txt")
    return open(log_file_path, "w")


def capture_cisco_commands(log_file):
    """Execute Cisco commands and write output to the log file."""
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
        print(output)  # Display in console as well

try:
    # Step 1: Enter ROMMON mode by sending a break signal
    send_break_signal()
    # Wait for the first rommon prompt
    if write_and_wait(b'', "rommon 1 >")[0]:
        print("Received rommon 1 prompt.")
        # Step 2: Set configuration register to ignore startup config
        if write_and_wait(b"confreg 0x2142\n", "rommon 2 >")[0]:
            print("Configuration register set to 0x2142.")
            # Step 3: Reset the router to apply the new config register setting
            if write_and_wait(b"reset\n", "Would you like to enter the initial configuration dialog? [yes/no]:")[0]:
                print("Router is resetting...")
                ser.write(b'no\n')  # Send no to stop resseting
                time.sleep(0.5)   # Short wait to allow processing
                ser.write(b'\r')  # First Enter
                ser.flush()       # Make sure command is fully sent
                ser.write(b'\r')  
                ser.flush()
                print("Attempting to reach Router> prompt...")
                if write_and_wait(b"", "Router>")[0]:
                    print("Skipped initial configuration dialog.")
                    # Wait for user mode prompt and enter enable mode
                    if write_and_wait(b"enable\n", "Router#")[0]:
                        print("Reached user mode prompt.")
                        # Now proceed with the next commands
                        if write_and_wait(b"\nwrite erase\n", "Erasing the nvram filesystem will remove all configuration files! Continue? [confirm]")[0]:
                            print("Erasing startup configuration...")
                            if write_and_wait(b"\n", "Router#")[0]:
                                if write_and_wait(b"configure terminal\n", "Router(config)#")[0]:
                                    print("Entered config terminal")
                                    if write_and_wait(b"config-register 0x2102\n", "Router(config)#")[0]:
                                        print("STEP 2 OF Router(config)#")
                                        write_and_wait(b"no logging monitor\n", "Router(config)#")[0]
                                        print("STEP 3 OF Router(config)#")
                                        write_and_wait(b"no terminal monitor\n", "Router(config)#")[0]
                                        print("STEP 4 OF Router(config)#")
                                        write_and_wait(b"snmp-server community public RO\n", "Router(config)#")[0]
                                        print("STEP 5 OF Router(config)#")
                                        write_and_wait(bytes([26]), "#")  # Exit configuration mode
                                        ser.write(bytes([26]))
                                        time.sleep(1)
                                        serial_number = get_snmp_chassis_serial()
                                        if serial_number:
                                            print(f"Stored Serial Number: {serial_number}")
                                            # Capture output in a log file
                                            with create_log_file(serial_number) as log_file:
                                                capture_cisco_commands(log_file)
                                            write_and_wait(b"\nreload\n", "System configuration has been modified. Save? [yes/no]:")[0]
                                            ser.write(b"no\n")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Close the serial connection
    ser.close()
    print("Connection closed.")
