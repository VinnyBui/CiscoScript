import sys
import os
import re
import logging
# Add the parent directory of telnet_scripts to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
# Import the function from utils.cisco_utils
from utils.cisco_utils import test_log
from config.config import LOG_DIR
test_commands = [
  "diagnostic start switch 1 test non-disruptive",
  "show diagn result swi 1",
  "show post",
  "show version",
  "show env all",
  "show inventory",
]

def boot_reset(connection, wait_time=600):
    import time
    start_time = time.time()
    while True:
      prompt = connection.send_command_timing("\n", delay_factor=2, read_timeout=120)
      print(prompt)
      if "initial configuration dialog?" in prompt:
        output = connection.send_command_timing("n", delay_factor=1)
        print(output)
        output = connection.send_command_timing("enable", delay_factor=1)
        print(output)
        return
      if time.time() - start_time > wait_time:
        raise Exception("Timeout waiting for 'RETURN' prompt.")
      time.sleep(2)


def rommon_mode(connection):
    output = connection.send_command_timing("flash", delay_factor=5)
    print(output)
    while "switch:" not in output:
        output += connection.send_command_timing("\n", delay_factor=1)
        print(output)
    
    connection.send_command_timing("\n", delay_factor=1)
    output = connection.send_command_timing("set SWITCH_IGNORE_STARTUP_CFG 1", delay_factor=5)
    print(output)
    connection.send_command_timing("\n", delay_factor=1)
    output = connection.send_command_timing("set SWITCH_NUMBER 1", delay_factor=5)
    print(output)
    connection.send_command_timing("\n", delay_factor=1)
    output = connection.send_command_timing("set SWITCH_PRIORITY 1", delay_factor=5)
    print(output)
    output = connection.send_command_timing("boot flash:packages.conf")
    print(output)
    print("Leaving rommon_mode")
    boot_reset(connection)
def parse_version_data(log_contents):
  """Parses device log contents for model, serial number, and software version."""
  try:
    model = re.search(r"Model Number\s+:\s+(\S+)", log_contents).group(1)
    serial = re.search(r"SerialNo\s+:\s+(\S+)", log_contents).group(1)
    sw_version = re.search(r"\bVersion\b\s+(\d+\.\d+\.\d+[a-zA-Z]*)", log_contents, re.IGNORECASE).group(1)
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
def run_diagnostic(connection):
    output = connection.send_command_timing("copy run start")
    print(output)
    if "Destination filename" in output:
        output = connection.send_command_timing("\r", delay_factor=1)
        print(output)
        output = connection.send_command_timing("\r", delay_factor=1)
        print(output)
        output = connection.send_command_timing("write erase" , delay_factor=5)
        print(output)
        output = connection.send_command_timing("\r")
        print(output)
        print("Configuration erased")
def run(connection, line_to_use):
    try:
        # rommon_mode(connection)
        run_diagnostic(connection)
        output = connection.send_command("terminal length 0", expect_string="Switch#")
        print(output)
        test_log(connection, test_commands, default_filename=line_to_use)
    except Exception as e:
        print(f"Error running test command: {e}")