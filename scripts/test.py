import sys
import os

# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Import the function from utils.cisco_utils
from utils.cisco_utils import test_log

commands = [
    "show diagn result swi 1",
    "show version",
    "show env all",
    "show inventory",
    "show license",
]

def run(connection):
    try:
        output = connection.send_command("enable", expect_string="Switch#")
        print(output)
        output = connection.send_command("terminal length 0", expect_string="Switch#")
        print(output)
        test_log(connection, commands)
    except Exception as e:
        print(f"Error running test command: {e}")