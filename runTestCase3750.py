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

def delete_configuration_password():
    ser.write(b"set SWITCH_NUMBER 1\n")
    ser.write(b"set BOOT\n")
    ser.write(b"set SWITCH_PRIORITY 15\n\n")
    ser.write(b"flash\n")
    ser.flush()
    time.sleep(1)
    if write_and_wait(b"\n", "switch:")[0]:
        ser.write(b"delete flash:config.text\n")
        write_and_wait(b"", "Are you sure you want to delete flash:config.text (y/n)?")
        time.sleep(1)
        ser.write(b"y\n")
        time.sleep(1)
        ser.write(b"delete flash:vlan.dat\n")
        write_and_wait(b"", "Are you sure you want to delete flash:vlan.dat (y/n)?")
        time.sleep(1)
        ser.write(b"y\n")
        ser.write(b"reset\n")
        ser.write(b"y\n")
        
def configure_router():
    time.sleep(3)
    write_and_wait(b"\n", "would you like to enter the initial configuration dialog? [yes/no]: ")
    ser.write(b"no\n")
    write_and_wait(b"\nno\n", "Switch>")
    if write_and_wait(b"enable\n", "Switch#")[0]:
        write_and_wait(b"\nterm length 0\n", "Switch#")
        configure_terminal()

def configure_terminal():
    write_and_wait(b"config terminal\n", "Switch(config)#")
    write_and_wait(b"no logging console\n", "Switch(config)#")
    write_and_wait(b"snmp-server community public RO\n", "Switch(config)#")
    write_and_wait(bytes([26]), "#")

def main():
    """Main function to execute all steps."""
    try:
        send_break_signal()
        if write_and_wait(b'', "switch:")[0]:
            delete_configuration_password()

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        ser.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()
