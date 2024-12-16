import serial
import time
import os

# Configuration for serial connection
SERIAL_PORT = 'COM1'  # Replace with your COM port
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

def wait_for_prompt(prompt, timeout=90):
    """Wait for a specific prompt to appear within the timeout."""
    start_time = time.time()
    output = ""
    while True:
        # Read incoming data
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting).decode(errors="ignore")
            output += data
            print(data, end="")  # Log incoming data for debugging

            # Check if the prompt exists in the accumulated output
            if prompt in output:
                print(f"\n## Prompt found: {prompt}")
                return True, output

        # Timeout check
        if time.time() - start_time > timeout:
            print(f"\nTimeout reached while waiting for: {prompt}")
            print(f"Final received data:\n{output}")  # Log all data received before timeout
            return False, output

        time.sleep(0.5)  # Avoid busy-waiting

def write_and_wait(command, expected_prompt, timeout=60):
    """Send a command and wait for the expected prompt."""
    ser.write(command)
    return wait_for_prompt(expected_prompt, timeout)

def delete_configuration_password():
    ser.write(b"set SWITCH_NUMBER 1\n")
    ser.write(b"set BOOT\n")
    ser.write(b"set SWITCH_PRIORITY 15\n")

    ser.write(b"flash\n")
    ser.flush()

    time.sleep(10)
    write_and_wait(b"", "switch:")
    
    # Delete config.text
    ser.write(b"delete flash:config.text\n")
    found = wait_for_prompt('Are you sure you want to delete "flash:config.text" (y/n)?', timeout=10)[0]
    if found:
        ser.write(b"y\n")  # Send 'y' to confirm deletion
        time.sleep(1)  # Allow time for the deletion to complete
        print("\n##Confirmed deletion of flash:config.text")
    else:
        print("\n##Failed to find confirmation prompt for config.text deletion or file does not exist.")
    
    # Delete vlan.dat
    ser.write(b"delete flash:vlan.dat\n")
    found = wait_for_prompt('Are you sure you want to delete "flash:vlan.dat" (y/n)?', timeout=10)[0]
    if found:
        ser.write(b"y\n")  # Send 'y' to confirm deletion
        time.sleep(1)  # Allow time for the deletion to complete
        print("\n##Confirmed deletion of flash:vlan.dat")
    else:
        print("\n##Failed to find confirmation prompt for vlan.dat deletion or file does not exist.")
    
    # Reset the device
    ser.write(b"reset\n")
    found = wait_for_prompt("Are you sure you want to reset the system (y/n)?")[0]
    if found:
        ser.write(b"y\n")  # Confirm reset
        time.sleep(1)  # Allow time for the deletion to complete
        print("\n##Resetting the device.")
    else:
        print("\n##Failed to find reload confirmation prompt.")

    # Wait for "Press RETURN to get started!"
    ser.reset_input_buffer()  # Clear buffer before waiting
    found, output = wait_for_prompt('Press RETURN to get started!', timeout=220)
    if found:
        print("\n##Detected 'Press RETURN to get started!'. Sending Enter key.")
        ser.reset_input_buffer()  # Clear the input buffer before sending Enter
        ser.write(b"\r")  # Try carriage return
        ser.flush()
        # Or send both
        ser.write(b"\r\n")
        ser.flush()
        configure_router()
    else:
        print("\nFAILED to detect 'Press RETURN to get started!'. Output was:\n", output)

def configure_router():

    # Wait for configuration dialog prompt
    found, output = wait_for_prompt("Would you like to enter the initial configuration dialog? [yes/no]:")
    if not found:
        print("\nFailed to detect initial configuration dialog. Output was:\n", output)
        return

    # Answer "no" to skip the dialog
    ser.write(b"no\n")
    ser.flush()

    # Wait for Switch> prompt
    found, output = wait_for_prompt("Switch>")
    if not found:
        print("\nFailed to detect 'Switch>' prompt. Output was:\n", output)
        return

    # Enter enable mode
    ser.write(b"enable\n")
    ser.flush()
    found, output = wait_for_prompt("Switch#")
    if not found:
        print("\nFailed to detect 'Switch#' prompt. Output was:\n", output)
        return

    # Proceed to configuration terminal
    configure_terminal()

def configure_terminal():
    ser.write(b"config terminal\n")

    # Wait for Switch(config)
    found = wait_for_prompt("Switch(config)#")
    if not found:
        print("##Failed to switch to config terminal")
        return

    # Send command
    ser.write(b"no logging console\n")
    ser.write(b"snmp-server community public RO\n")
    ser.write(bytes([26]))

def get_snmp_chassis_serial():
    """Retrieve the SNMP chassis serial number."""
    ser.reset_input_buffer()  # Clear input buffer to avoid stale data
    
    # Send the command
    ser.write(b"show snmp chassis\n")
    ser.flush()
    time.sleep(2)  # Wait for the output to be generated
    
    # Wait for the completion of the command output
    found, output = wait_for_prompt("Switch#", timeout=10)  # Match "Switch#" as the prompt
    if found:
        print("\nCommand executed successfully. Parsing output...")
        
        # Split lines and find the serial number
        lines = output.splitlines()
        for line in lines:
            serial_num = line.strip()
            if serial_num and serial_num.isalnum() and len(serial_num) > 5:
                print(f"SNMP Chassis Serial Number: {serial_num}")
                return serial_num

        print("No valid serial number found in the output.")
    else:
        print("Failed to retrieve SNMP chassis information. Output was:\n", output)
    
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
        "show version",
        "show env all",
        "show diagnostic result switch 1",
        "show license all switch 1", 
        "show processes",
        "show inventory",
        "show env all"
    ]
    
    # Run all the commands in the list
    for cmd in commands:
        log_file.write(f"\n{cmd}\n")
        ser.write((cmd + "\r").encode())
        time.sleep(2)
        
        output = ""
        while ser.in_waiting > 0:
            output += ser.read(ser.in_waiting).decode(errors="ignore")
        log_file.write(output + "\n")
        print(output)

def close_restart_switch():
    ser.write(b"!\n")
    time.sleep(0.5)
    ser.write(b"\n")

    found = wait_for_prompt("#")[0]
    if not found:
        print("##Can't erase")
        return 
    
    ser.write(b"write erase\n")

    found = wait_for_prompt("Erasing the nvram filesystem will remove all configuration files! Continue? [confirm]")[0]
    if not found:
        print("##Failed to erase")
        return 
    
    ser.write(b"\n")
    ser.write(b"reload\n")

    found = wait_for_prompt("System configuration has been modified. Save? [yes/no]: ")[0]
    if not found:
        print("##Failed to reload")
        return
    
    ser.write(b"no\n")

    found = wait_for_prompt("Proceed with reload? [confirm]")[0]
    if not found:
        print("##Failed to proceed with reload")
        return
    
    ser.write(b"\n")

def main():
    """Main function to execute all steps."""
    try:
        if write_and_wait(b'', "switch:", timeout=250)[0]:
            delete_configuration_password()
            serial_number = get_snmp_chassis_serial()
            if serial_number:
                with create_log_file(serial_number) as log_file:
                    capture_cisco_commands(log_file)

                close_restart_switch()
        print("Script is done")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        ser.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()
