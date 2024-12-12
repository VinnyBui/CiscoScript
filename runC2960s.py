import serial
import time
import os
import re
from netmiko import ConnectHandler

# Configuration for serial connection
SERIAL_PORT = 'COM1'  # Replace with your COM port
BAUD_RATE = 9600       # Standard baud rate for Cisco devices
LOG_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "CiscoLogs")

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

def wait_for_prompt(prompt, timeout=60):
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

def write_and_wait(command, expected_prompt, timeout=60):
    send_command(command)
    return wait_for_prompt(expected_prompt, timeout)

def delete_file(filename, prompt='Are you sure you want to delete', timeout=10):
    """Delete a given file from flash and confirm deletion if prompted."""
    cmd = f"delete flash:{filename}\r".encode()
    send_command(cmd)
    time.sleep(1)
    found, output = wait_for_prompt(prompt, timeout)
    if found:
      print(output)
      send_command(b"y\r")
    else:
        print(f"#Failed to find or delete {filename} (no prompt or file not found).")
#Need to clean rommon_reset function later
def rommon_reset():
  ser.reset_input_buffer()  # Clear buffer before waiting
  found, output = wait_for_prompt('Press RETURN to get started!', timeout=350)
  if found:
    print("\r##Detected 'Press RETURN to get started!'. Sending Enter key.")
    ser.reset_input_buffer()  # Clear the input buffer before sending Enter
    send_command(b"\r") 
    send_command(b"\r\r")

    found, output = wait_for_prompt("Would you like to enter the initial configuration dialog? [yes/no]:")
    if not found:
      print("\rFailed to detect initial configuration dialog. Output was:\r", output)
      return

    time.sleep(1) 
    send_command(b"n\r")
    #Entering # mode
    found, output = wait_for_prompt("Switch>\r")
    if found:
      send_command(b"en\r")
  return

def rommon_mode():
  send_command(b"flash\r")
  found, output = wait_for_prompt("switch:")
  if found:
    send_command(b"set SWITCH_NUMBER 1\r")
    send_command(b"set SWITCH_PRIORITY 1\r")
    found, output = wait_for_prompt("switch:")
    if found:
      files_to_delete = [
        "config.text",
        "config.text.backup",
        "private-config.text",
        "private-config.text.backup",
      ]

      for f in files_to_delete:
        delete_file(f)
      found, output = wait_for_prompt("switch:")
      if found:
        send_command(b"reset\r")
        send_command(b"y\r")
        rommon_reset()

def run_diagnostic():
  found, output = wait_for_prompt("Switch#")
  if found:
    send_command(b"diagnostic start swi 1 test all\r")
    send_command(b"y\r")
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
        "read_timeout_override" : 15,
    }
    print("Connecting via Netmiko over serial...")
    net_connect = ConnectHandler(**device)
    print("Netmiko connection established.")
    return net_connect

def parse_version_data(log_contents):
    """
    Parse the log contents to extract Model and Serial Number.
    """
    try:
        # Extract Model
        model_match = re.search(r"Model number\s+:\s+(\S+)", log_contents)
        model = model_match.group(1) if model_match else "UNKNOWN_MODEL"

        # Extract System Serial Number
        serial_match = re.search(r"System serial number\s+:\s+(\S+)", log_contents)
        serial = serial_match.group(1) if serial_match else "UNKNOWN_SERIAL"

        return {"model": model, "serial_number": serial}

    except Exception as e:
        print(f"Unexpected error during parsing: {e}")
        return {"model": "UNKNOWN_MODEL", "serial_number": "UNKNOWN_SERIAL"}

def test_log(net_connect):
  """Run diagnostic and informational commands via Netmiko and log output."""
  file_name = "BLANK"
  if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
  log_path = os.path.join(LOG_DIR, f"{file_name}.txt")
    
  with open(log_path, "w") as log_file:
    commands = [
      "show diagnostic result swi all",
      "show post",
      "show version",
      "show env all",
      "show inventory",
    ]
    for cmd in commands:
      log_file.write(f"\n{cmd}\n")
      output = net_connect.send_command(cmd)
      log_file.write(output + "\n")
      print(output)
  
  # Parse the log file to extract details
  with open(log_path, "r") as file:
    log_contents = file.read()

  version_data = parse_version_data(log_contents)
  new_file_name = f"{version_data['model']}_{version_data['serial_number']}.txt"
  new_log_path = os.path.join(LOG_DIR, new_file_name)
  os.rename(log_path, new_log_path)

  print(f"Test logs saved to {new_log_path}")

def main():
  try:
    # if write_and_wait(b'\r', "switch:", timeout=60)[0]:
    #   rommon_mode()
    #   run_diagnostic()
    #   found, output = wait_for_prompt("Switch#\r")
    #   if found:
    #     close_pyserial()
    #     net_connect = connect_netmiko()
    #     test_log(net_connect)
    close_pyserial()
    net_connect = connect_netmiko()
    test_log(net_connect)


  except Exception as e:
    print(f"An error occurred: {e}")
  finally:
    print("Connection closed.")

if __name__ == "__main__":
  main()