from netmiko import ConnectHandler
import logging
import os
import importlib.util

session_log_path = os.path.abspath(os.path.join("..", "logs", "telnet_log.txt"))
# Enable debugging to capture session output
logging.basicConfig(level=logging.INFO)
# Device connection details
device = {
    "device_type": "cisco_ios_telnet",
    "ip": "192.168.1.250",
    "timeout": 60,
}
try:
    line_to_use = input("Enter the line you want to use (L0, L1, L2, L3, L4, L5, L6, L7, L8, L9, L10, L11, L12, L13, L14): ").strip()
    # Validate input
    valid_lines = [f"L{i}" for i in range(15)]
    if line_to_use not in valid_lines:
        print(f"Invalid line selection. Please choose from: {', '.join(valid_lines)}")
        exit()
    connection = ConnectHandler(**device, session_log=session_log_path)
    print("Connection established to TermG.")
    # Send telnet command with the selected line
    command = f"telnet {line_to_use}"
    output = connection.send_command_timing(command)
    print(f"Telnet to {line_to_use} initiated:")
    print(output)
    # Check for specific error message
    if "% Connection refused by remote host" in output:
        print("Failed to connect to L: Connection refused by remote host. Exiting program.")
        connection.disconnect()
        exit(1)
    # Capture the current prompt
    current_prompt = connection.find_prompt()
    print(f"Current prompt: {current_prompt}")
    while True:
        current_prompt = connection.find_prompt()
        user_input = input(current_prompt).strip()
        if user_input.lower() == "exit":
            print("Program is ending..")
            break
        elif user_input.startswith("runP "):
            script_name = user_input[5:].strip()
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(script_dir, ".."))
            script_path = os.path.join(project_root, "telnet_scripts", script_name)

            if os.path.exists(script_path):
                try:
                    # Dynamically load the script
                    spec = importlib.util.spec_from_file_location(script_name, script_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    # Run the script's `run` function
                    if hasattr(module, "run"):
                        module.run(connection, line_to_use)
                        # Update prompt after script execution
                        current_prompt = connection.find_prompt()
                    else:
                        print(f"Script '{script_name}' does not have a 'run' function.")
                except Exception as e:
                    print(f"Failed to run script: {e}")
            else:
                print(f"Script '{script_name}' not found in the 'telnet_scripts' folder.")
        else:
            try:
                # Send command and update prompt dynamically
                output = connection.send_command_timing(user_input, delay_factor=1)
                print(output)
                current_prompt = connection.find_prompt()
            except Exception as e:
                print(f"Error executing command: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # Close connection if established
    if 'connection' in locals():
        connection.disconnect()
        print(f"Line {line_to_use} disconnected.")
        print("Connection to TermG closed.")
