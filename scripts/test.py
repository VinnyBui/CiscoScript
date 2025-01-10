import sys
import os
import time
# Import the function from utils.cisco_utils
from utils.cisco_utils import test_log, wait_for_prompt

# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

IP_ADDR = "192.168.1.130/255.255.255.0"
DEFAULT_ROUTER = "192.168.1.1"
TFTP_ADDR = "192.168.1.107"
test_commands = [
    "show diagn result swi 1",
    "show version",
    "show env all",
    "show inventory",
    "show license",
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
#NEED TO CLEAN THIS UP
def boot_ios(connection):
    output = connection.send_command_timing("conf t")
    print(output)
    output = connection.send_command_timing("boot system flash:/c2960x-universalk9-mz.152-4.E.bin", delay_factor=2)
    print(output)
    if "Switch(config)" in output:
        output = connection.send_command_timing("int fa0")
        print(output)
        output = connection.send_command_timing("ip add dhcp")
        print(output)
        output = connection.send_command_timing("no shut")
        print(output)
        output = connection.send_command_timing("end")
        print(output)
        # Start TFTP transfer
        output = connection.send_command_timing("copy tftp://192.168.1.107/c2960x-universalk9-mz.152-4.E.bin flash:/c2960x-universalk9-mz.152-4.E.bin",  delay_factor=5)
        print("Initial Copy Command Output:", output)
        start_time = time.time()
        while time.time() - start_time < 20:
            # Fetch updated output
            output += connection.send_command_timing("\n", delay_factor=2)
            print("Progress Output:", output)
            if "Destination filename" in output or "Loading" in output:
                print("TFTP process initiated successfully.")
                break
        while True:
            # Check to see errors
            if "Do you want to overwrite?" in output:
                output = connection.send_command_timing("y", delay_factor=3)
                print("Overwrite confirmation output:", output)
            if "(Socket error)" in output:
                raise Exception("TFTP transfer failed due to socket error.")
                break
            elif "(Connection timed out)" in output:
                raise Exception("TFTP transfer failed due to timeout.")
                break
            elif "Error opening" in output:
                raise Exception("TFTP transfer failed")
                break
            elif "bytes copied" in output:
                print("Copy process completed.")
                break
            # Continuously check output
            output = connection.send_command_timing("\n")
            print("Checking progress output:", output)
        # Proceed with reload
        output = connection.send_command_timing("reload")
        print("Reload command output:", output)
        if "System configuration has been modified. Save? [yes/no]:" in output:
            output = connection.send_command_timing("no")
            print("Configuration save prompt handled.")
            rommon_reset(connection, output)
        else:
            raise Exception("Failed to initiate TFTP transfer!")
    else:
        raise Exception(f"Failed to boot system.")
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
        boot_ios(connection)
        run_diagnostic(connection)
        output = connection.send_command("terminal length 0", expect_string="Switch#")
        print(output)
        test_log(connection, test_commands, default_filename=line_to_use)
    except Exception as e:
        print(f"Error running test command: {e}")