import sys
import os
import time
# Add the parent directory of telnet_scripts to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)
# Import the function from utils.cisco_utils
from utils.cisco_utils import test_log, wait_for_prompt
test_commands = [
  "show diagnostic result swi all",
  "show post",
  "show version",
  "show env all",
  "show inventory",
]

def rommon_reset(connection, prompt, wait_time=600):
    import time
    # Check initial prompt
    start_time = time.time()
    while "RETURN" not in prompt:
        if time.time() - start_time > wait_time:
            raise Exception("Timeout waiting for 'RETURN' prompt.")
        
        # Send an empty command to get updated output
        prompt = connection.send_command_timing("\r\n")
        print(prompt)
        time.sleep(5)  # Wait for a short interval before retrying

    # Handle 'initial configuration dialog' if detected
    if "initial configuration dialog?" in prompt:
        output = connection.send_command("n", expect_string="Switch>")
        print(output)
        output = connection.send_command("enable", expect_string="Switch#")
        print(output)
    else:
        raise Exception("Unexpected prompt after waiting for 'RETURN'.")
def rommon_mode(connection):
    output = connection.send_command_timing("flash", delay_factor=5)
    print(output)
    while "switch:" not in output:
        output += connection.send_command_timing("\n", delay_factor=1)
        print(output)
    
    connection.send_command_timing("\n", delay_factor=1)
    output = connection.send_command_timing("set SWITCH_NUMBER 1", delay_factor=5)
    print(output)
    connection.send_command_timing("\n", delay_factor=1)
    output = connection.send_command_timing("set SWITCH_PRIORITY 1", delay_factor=5)
    print(output)
    output = connection.send_command_timing("delete flash:config.text")
    print(output)
    if "Are you sure" in output:
        output = connection.send_command_timing("y")
        print(output)
        output = connection.send_command_timing("reset")
        print(output)
        output = connection.send_command_timing("y")
        rommon_reset(connection, output)
    else:
        raise Exception(f"Failed to delete")
def run_diagnostic(connection):
    output = connection.send_command_timing("diagnostic start switch 1 test all")
    print(output)
    if "Do you want to continue?" in output:
        output = connection.send_command_timing("yes")
        print(output)
        rommon_reset(connection, output)
def run(connection, line_to_use):
    try:
        rommon_mode(connection)
        run_diagnostic(connection)
        output = connection.send_command("terminal length 0", expect_string="Switch#")
        print(output)
        test_log(connection, test_commands, default_filename=line_to_use)
    except Exception as e:
        print(f"Error running test command: {e}")