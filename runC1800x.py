import serial
import time
import os

# Configuration for serial connection
SERIAL_PORT = 'COM1'    # Replace with your COM port
BAUD_RATE = 9600         # Standard baud rate for Cisco devices
TIMEOUT = 1              # Serial read timeout in seconds

# Initialize serial connection
ser = serial.Serial(
    port=SERIAL_PORT,
    baudrate=BAUD_RATE,
    timeout=TIMEOUT,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
)

def send_breaks_until_rommon(prompt, timeout=10):
    """Send break signals until the specified ROMMON prompt is detected or timeout reached."""
    end_time = time.time() + timeout
    time.sleep(5)
    while True:
        ser.send_break()
        time.sleep(0.5)
        output = read_all_output()
        if output:
            print(output, end="")
            if prompt in output:
                print(f"Detected '{prompt}' prompt.")
                return True
        if time.time() > end_time:
            raise Exception(f"Timeout: Unable to detect '{prompt}' prompt.")

def read_all_output():
    """Read all available output from the serial buffer."""
    time.sleep(0.5)
    out = ""
    while ser.in_waiting > 0:
        out += ser.read(ser.in_waiting).decode(errors='ignore')
    return out

def wait_for_prompt(prompt, timeout=90):
    """Wait for a specific prompt within the given timeout."""
    print(f"Waiting for prompt: {prompt}")
    end_time = time.time() + timeout
    buffer = ""
    while time.time() < end_time:
        data = read_all_output()
        if data:
            buffer += data
            print(data, end="")
            if prompt in buffer:
                print(f"\nFound prompt: {prompt}")
                return True
        time.sleep(1)
    raise Exception(f"Timeout reached while waiting for prompt: {prompt}")

def send_command(cmd, expect=None, timeout=30):
    """Send a command and optionally wait for an expected prompt."""
    if not cmd.endswith("\n"):
        cmd += "\n"
    ser.write(cmd.encode())
    if expect:
        return wait_for_prompt(expect, timeout=timeout)
    else:
        time.sleep(2)  # Just send and wait a bit
        return True

def answer_initial_dialog(prompt):
    """
    After reset, the device prompts:
    'Would you like to enter the initial configuration dialog? [yes/no]:'
    Respond with 'no' and then wait for the Router prompt.
    """
    print("Waiting for initial configuration dialog prompt...")
    dialog_prompt = "Would you like to enter the initial configuration dialog? [yes/no]:"
    if wait_for_prompt(dialog_prompt, timeout=10):
        ser.write(("n\n\n").encode())
        time.sleep(1)
        # After responding 'no', we expect a Router> prompt
        wait_for_prompt(prompt, timeout=60)

def enter_enable_mode():
    """From Router> to Router# by sending 'enable'."""
    print("Entering enable mode...")
    send_command("enable")
    wait_for_prompt("Router#")

def get_snmp_chassis_serial():
    """Retrieve the SNMP chassis serial number using 'show snmp chassis'."""
    print("Getting SNMP chassis serial number...")
    ser.write(b"show snmp chassis\n")
    time.sleep(2)
    output = read_all_output()
    print(output)
    # Try to extract a likely serial number
    # For simplicity, assume the serial number line is directly visible
    # Adjust parsing logic as needed
    lines = output.splitlines()
    for line in lines:
        line = line.strip()
        # Heuristic: Serial numbers often alphanumeric and >5 chars
        if line and len(line) > 5 and line.isalnum():
            print(f"SNMP Chassis Serial Number: {line}")
            return line
    print("Failed to retrieve SNMP chassis information.")
    return None

def capture_cisco_commands(log_file):
    """Capture output from a list of Cisco commands and log them."""
    commands = [
        "term length 0",
        "show inventory",
        "show hardware",
        "show env all",
        "show license feature",
        "show license status"
    ]
    for cmd in commands:
        log_file.write(f"\nCommand: {cmd}\n")
        ser.write((cmd + "\n").encode())
        time.sleep(2)
        output = read_all_output()
        log_file.write(output + "\n")
        print(output)

def main():
    try:
        if not ser.is_open:
            raise Exception("Failed to open serial port.")
        print(f"Connected to {SERIAL_PORT}.")

        send_breaks_until_rommon("rommon 1 >")

        print("Sending 'confreg 0x2142' command...")
        send_command("confreg 0x2142")

        print("Sending 'reset' command to reboot the device...")
        send_command("reset")

        print("Waiting for the device to reboot (60s)...")
        time.sleep(60)

        answer_initial_dialog("Router>")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        ser.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()
