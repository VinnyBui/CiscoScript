import serial
import time
import os

# Configuration for serial connection
SERIAL_PORT = 'COM5'  # Replace with your COM port
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
    found, output = wait_for_prompt('Press RETURN to get started!', timeout=240)
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

    found = wait_for_prompt("Switch(config)#")
    if not found:
        print("##Failed to switch to config terminal")
        return

    ser.write(b"no logging console\n")
    ser.write(b"snmp-server community public RO\n")
    ser.write(bytes([26]))


def main():
    """Main function to execute all steps."""
    try:
        if write_and_wait(b'', "switch:", timeout=250)[0]:
            delete_configuration_password()


        

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        ser.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()
