import time
import serial
import os
import re
import logging
from config.config import BAUD_RATE, LOG_DIR, DEFAULT_TIMEOUT, LONG_TIMEOUT, DELETE_TIMEOUT, SESSION_LOG_FILE

def list_com_ports():
    """Lists available COM ports and allows user selection."""
    import serial.tools.list_ports
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

def configure_serial(port, baud_rate=9600):
  """Configures and returns a serial connection."""
  try:
    return serial.Serial(
      port=port,
      baudrate=baud_rate,
      timeout=1,
      bytesize=serial.EIGHTBITS,
      parity=serial.PARITY_NONE,
      stopbits=serial.STOPBITS_ONE,
    )
  except serial.SerialException as e:
    print(f"Failed to configure serial connection on {port}: {e}")
    raise

def read_all_output(ser):
  """Reads all available output from the serial connection."""
  time.sleep(0.5)
  out = ""
  while ser.in_waiting > 0:
    out += ser.read(ser.in_waiting).decode(errors='ignore')
  return out

def send_command(ser, command, delay=1):
  """Send a command over a serial connection."""
  ser.write(command)
  ser.flush()
  time.sleep(delay)

def wait_for_prompt(prompt, timeout=DEFAULT_TIMEOUT):
  """
  Waits for a specific prompt within a given timeout.

  Args:
    prompt (str): The expected prompt string to wait for.
    timeout (int): Time (in seconds) to wait before timing out.

  Returns:
    tuple: (bool, str) where the boolean indicates success, 
    and the string contains the captured output.
  """
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

def write_and_wait(ser, command, expected_prompt, timeout=DEFAULT_TIMEOUT):
  send_command(ser, command)
  return wait_for_prompt(expected_prompt, timeout)

def rommon_reset(ser):
  """Resets the device in ROMMON mode and waits for initialization prompts."""
  ser.reset_input_buffer()  # Clear buffer before waiting
  found, output = wait_for_prompt('Press RETURN to get started!', timeout=LONG_TIMEOUT)
  if found:
    print("\r##Detected 'Press RETURN to get started!'. Sending Enter key.")
    ser.reset_input_buffer()  # Clear the input buffer before sending Enter
    send_command(ser, b"\r") 
    send_command(ser, b"\r\r")

    found, output = wait_for_prompt("Would you like to enter the initial configuration dialog? [yes/no]:")
    if not found:
      print("\rFailed to detect initial configuration dialog. Output was:\r", output)
      return

    time.sleep(1) 
    send_command(ser, b"n\r")
    #Entering > mode
    found, output = wait_for_prompt("Switch>\r")
    if found:
      send_command(ser, b"en\r")
  else:
    raise Exception(f"Failed to find RETURN.")

def delete_file(ser, filename, prompt='Are you sure you want to delete', timeout=DELETE_TIMEOUT):
  """
  Deletes a file from flash memory and confirms deletion.

  Args:
    ser (serial.Serial): Serial connection object.
    filename (str): Name of the file to delete.
    prompt (str): Confirmation prompt string.
    timeout (int): Timeout for waiting for the prompt.

  Returns:
    bool: True if deletion was successful, False otherwise.
  """
  try:
    cmd = f"delete flash:{filename}\r".encode()
    send_command(ser, cmd)
    time.sleep(1)
    found, output = wait_for_prompt(prompt, timeout)
    if found:
      print(output)
      send_command(ser, b"y\r")
      print(f"Deleted {filename}")
    else:
      print(f"#Failed to find or delete {filename} (no prompt or file not found).")
  except Exception as e:
    print(f"Error during file deletion for {filename}: {e}")

def close_pyserial(ser):
  """Ensure the PySerial connection is fully closed."""
  if ser.is_open:
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    ser.close()
    print("PySerial connection closed.")
  time.sleep(2)  # Allow time for the OS to release the port

def connect_netmiko(serial_port, baud_rate=9600):
  """Connect to a Cisco device using Netmiko over serial."""
  from netmiko import ConnectHandler

  device = {
    "device_type": "cisco_ios_serial",
    "serial_settings": {
      "port": serial_port,
      "baudrate": baud_rate,
      "bytesize": 8,
      "parity": "N",
      "stopbits": 1,
    },
    "global_delay_factor": 2,
    "fast_cli": False,
    "session_log": SESSION_LOG_FILE,
    "read_timeout_override": 30,
  }

  print(f"Connecting to {serial_port} via Netmiko...")
  net_connect = ConnectHandler(**device)
  print("Netmiko connection established.")
  return net_connect

def parse_version_data(log_contents):
  """Parses device log contents for model, serial number, and software version."""
  try:
    model = re.search(r"Model number\s+:\s+(\S+)", log_contents).group(1)
    serial = re.search(r"System serial number\s+:\s+(\S+)", log_contents).group(1)
    sw_version = re.search(r"Version\s+([\d\.()a-zA-Z]+)", log_contents).group(1)
    return {"model": model, "serial_number": serial, "sw_version": sw_version}
  except AttributeError:
    logging.warning("Failed to parse version data.")
    return {"model": "UNKNOWN_MODEL", "serial_number": "UNKNOWN_SERIAL", "sw_version": "UNKNOWN_VERSION"}

def test_log(net_connect, commands, log_dir=LOG_DIR, default_filename="device_log.txt"):
  """Runs commands via Netmiko and logs the output."""
  #If directory doesnt exit, make new one
  if not os.path.exists(log_dir):
      os.makedirs(log_dir)
  log_path = os.path.join(log_dir, default_filename)
  try:
    #Run command and store in file
    with open(log_path, "w") as log_file:
      for cmd in commands:
        log_file.write(f"\n{cmd}\n")
        output = net_connect.send_command_timing(cmd, delay_factor=5)
        log_file.write(output + "\n")
        print(output)
  except Exception as e:
    print(f"Error while running commands: {e}")
    return

  try:
    # Parse and rename log file based on device information
    with open(log_path, "r") as file:
      log_contents = file.read()
    version_data = parse_version_data(log_contents)
    new_file_name = f"{version_data['model']}_{version_data['serial_number']}_{version_data['sw_version']}.txt"
    new_log_path = os.path.join(log_dir, new_file_name)
    # Handle existing file before renaming
    if os.path.exists(new_log_path):
      print(f"File {new_file_name} already exists. Overwriting...")
      os.remove(new_log_path)
    os.rename(log_path, new_log_path)
    print(f"Logs saved to {new_log_path}")
  except Exception as e:
      print(f"Error during log parsing or renaming: {e}")

