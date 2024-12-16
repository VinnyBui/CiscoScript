import serial
import time
import os
import re
import serial.tools.list_ports
from netmiko import ConnectHandler

BAUD_RATE = 9600       # Standard baud rate for Cisco devices
LOG_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "CiscoLogs")

def list_com_ports():
    """
    List all available COM ports and let the user select one.
    Returns the selected COM port name (e.g., 'COM1').
    """
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        raise Exception("No COM ports available. Please check your connection.")

    print("Available COM Ports:")
    for i, port in enumerate(ports):
        print(f"{i + 1}: {port.device} - {port.description}")

    while True:
        try:
            choice = int(input("Select a COM port (by number): "))
            if 1 <= choice <= len(ports):
                return ports[choice - 1].device
            else:
                print("Invalid choice. Please select a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

# Dynamically select the COM port
SERIAL_PORT = list_com_ports()

ser = serial.Serial(
    port=SERIAL_PORT,
    baudrate=BAUD_RATE,
    timeout=1,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
)

def read_all_output():
    time.sleep(0.5)
    out = ""
    while ser.in_waiting > 0:
        out += ser.read(ser.in_waiting).decode(errors='ignore')
    return out

def send_command(command, delay=1):
    """Send a command to the serial connection, flush, and wait."""
    ser.write(command)
    ser.flush()
    time.sleep(delay)

def wait_for_prompt(prompt, timeout=120):
    start_time = time.time()
    output = ""
    current_timeout = 1

    while True:
        data = read_all_output()
        if data:
            output += data
            print(data, end="")
            if prompt in output:
                print(f"\rFound prompt: {prompt}")
                return True, output

        if time.time() - start_time > timeout:
            print(f"\rTimeout reached while waiting for: {prompt}")
            return False, output

        time.sleep(current_timeout)
        current_timeout = min(current_timeout + 1, 5)

def write_and_wait(command, expected_prompt, timeout=120):
    send_command(command)
    return wait_for_prompt(expected_prompt, timeout)

# def log_to_file(data):
#     with open("rommon_reset_log.txt", "a") as log_file:
#         log_file.write(data + "\n")

def rommon_reset():
  found, output = wait_for_prompt('Press RETURN to get started', timeout=350)
  time.sleep(5)
  ser.reset_input_buffer()  
  ser.reset_output_buffer()
  if not found:
    raise Exception("Failed to find Press RETURN prompt")
  print("\r##Detected 'Press RETURN to get started'. Sending Enter key.")
  send_command(b"\r") 

  print("Waiting for 'Switch>' prompt...")
  found, output = wait_for_prompt("Switch>", timeout=60)
  if not found:
    raise Exception("Failed to find 'Switch>' prompt")

  print("Found 'Switch>' prompt. Entering 'enable' mode.")
  send_command(b"en\r")
  time.sleep(2) 
  found, output = wait_for_prompt("Switch#")
  if not found:
    raise Exception("Failed to enter 'enable' mode (Switch#)")
  print("Successfully entered 'enable' mode.")

def rommon_mode():
  send_command(b"flash\r", delay=5)
  found, output = wait_for_prompt("switch:", timeout=500)
  if not found:
    raise Exception("Flash initialization failed.")

  send_command(b"set SWITCH_IGNORE_STARTUP_CFG 1\r")
  send_command(b"set SWITCH_NUMBER 1\r")
  send_command(b"set SWITCH_PRIORITY 1\r")

  found, output = wait_for_prompt("switch:")
  if not found:
    raise Exception("Failed after setting switch configurations.")

  send_command(b"boot flash:packages.conf\r")
  rommon_reset()

def close_pyserial():
    """Ensure the PySerial connection is fully closed."""
    if ser.is_open:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        ser.close()
        print("PySerial connection closed.")
    time.sleep(2)  # Allow time for the OS to release the port

def connect_netmiko():
    """Connect to the device using Netmiko over serial."""
    device = {
        "device_type": "cisco_ios_serial",
        "serial_settings": {
            "port": SERIAL_PORT,
            "baudrate": BAUD_RATE,
            "bytesize": 8,
            "parity": "N",
            "stopbits": 1,
        },
        "global_delay_factor": 2,
        "fast_cli": False, 
        "session_log": "session_log.txt", 
        "read_timeout_override" : 30,
    }
    print("Connecting via Netmiko over serial...")
    net_connect = ConnectHandler(**device)
    print("Netmiko connection established.")
    return net_connect

def start_config(net_connect):
  output = net_connect.send_command(
    "copy run start",
    expect_string=r"Destination filename \[startup-config\]\?",
    read_timeout=60
  )
  print(output)
  output = net_connect.send_command("\r", expect_string="Switch#")
  print(output)
  output = net_connect.send_command("write erase", expect_string=r"\[confirm\]", read_timeout=60)
  print(output)
  output = net_connect.send_command("\r", expect_string="Switch#")
  print("Configuration erased")

def parse_version_data(log_contents):
  try:
    # Extract Model
    model_match = re.search(r"Model Number\s+:\s+(\S+)", log_contents)
    model = model_match.group(1) if model_match else "UNKNOWN_MODEL"

    # Extract System Serial Number
    serial_match = re.search(r"System Serial Number\s+:\s+(\S+)", log_contents)
    serial = serial_match.group(1) if serial_match else "UNKNOWN_SERIAL"

    # Extract SW Version (First Occurrence)
    version_match = re.search(r"Version\s+([\d\.()a-zA-Z]+)", log_contents)
    sw_version = version_match.group(1) if version_match else "UNKNOWN_VERSION"

    return {"model": model, "serial_number": serial, "sw_version": sw_version}

  except Exception as e:
    print(f"Unexpected error during parsing: {e}")
    return {
      "model": "UNKNOWN_MODEL",
      "serial_number": "UNKNOWN_SERIAL",
      "sw_version": "UNKNOWN_VERSION",
    }

def test_log(net_connect):
  """Run diagnostic and informational commands via Netmiko and log output."""
  file_name = "BLANK"
  if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
  log_path = os.path.join(LOG_DIR, f"{file_name}.txt")
    
  with open(log_path, "w") as log_file:
    commands = [
      "diagnostic start switch 1 test non-disruptive",
      "show diagn result swi 1",
      "show post",
      "show version",
      "show env all",
      "show inventory",
    ]
    for cmd in commands:
      log_file.write(f"\n{cmd}\n")
      output = net_connect.send_command(
        cmd, expect_string=r"Switch#|Switch>", read_timeout=60
      )
      log_file.write(output + "\n")
      print(output)
  
  # Parse the log file to extract details
  with open(log_path, "r") as file:
    log_contents = file.read()

  version_data = parse_version_data(log_contents)
  new_file_name = f"{version_data['model']}_{version_data['serial_number']}_{version_data['sw_version']}.txt"
  new_log_path = os.path.join(LOG_DIR, new_file_name)

  # Handle existing file before renaming
  if os.path.exists(new_log_path):
    print(f"File {new_file_name} already exists. Overwriting...")
    os.remove(new_log_path)
  
  os.rename(log_path, new_log_path)
  print(f"Test logs saved to {new_log_path}")

def main():
  try:
    if write_and_wait(b'\r', "switch:", timeout=120)[0]:
      rommon_mode()
      if write_and_wait(b"\r", "Switch#")[0]:
        close_pyserial()
        net_connect = connect_netmiko()
        start_config(net_connect)
        test_log(net_connect)
        net_connect.disconnect()

  except Exception as e:
    print(f"An error occurred: {e}")
  finally:
    print(f"Connection closed on {SERIAL_PORT}")

if __name__ == "__main__":
  main()

