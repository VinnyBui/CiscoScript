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
  "show inventory",
  "show voice port summary",
  "show voice dsp",
  "show diag",
  "show ver",
]

def run_diagnostic(connection):
  output = connection.send_command_timing("\n")
  if "initial configuration dialog?" in output:
    connection.send_command_timing("n")
    connection.send_command_timing("en")


def run(connection, line_to_use):
  try:
      run_diagnostic(connection)
      output = connection.send_command("terminal length 0", expect_string="Switch#")
      print(output)
      test_log(connection, test_commands, default_filename=line_to_use)
  except Exception as e:
      print(f"Error running test command: {e}")