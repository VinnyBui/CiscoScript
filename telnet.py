from netmiko import ConnectHandler
import logging
import os
import importlib.util

session_log_path = os.path.join("logs", "telnet_log.txt")

# Enable debugging to capture session output
logging.basicConfig(level=logging.INFO)

# Device connection details
device = {
    "device_type": "cisco_ios_telnet",
    "ip": "192.168.1.250",
    "timeout": 60,
}

try:
    # Establish connection to TermG
    connection = ConnectHandler(**device, session_log=session_log_path)
    print("Connection established to TermG.")

    # Telnet to L0
    output = connection.send_command_timing("telnet l1")
    print("Telnet to L0 initiated:")
    print(output)

    # Check for specific error message
    if "% Connection refused by remote host" in output:
        print("Failed to connect to L0: Connection refused by remote host. Exiting program.")
        exit(1)

    while True:
        user_input = input("Switch> ").strip() or input("Switch# ").strip() or input("Switch: ").strip()

        if user_input.lower() == "exit":
            print("Program is ending..")
            break
        elif user_input.startswith("runP "):
            script_name = user_input[5:].strip()  
            script_path = os.path.join("scripts", script_name)

            if os.path.exists(script_path):
                try:
                    # Dynamically load the script
                    spec = importlib.util.spec_from_file_location(script_name, script_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Run the script's `run` function
                    if hasattr(module, "run"):
                        module.run(connection)
                    else:
                        print(f"Script '{script_name}' does not have a 'run' function.")

                except Exception as e:
                    print(f"Failed to run script: {e}")
            else:
                print(f"Script '{script_name}' not found in the 'scripts' folder.")
        else:
            try:
                output = connection.send_command_timing(user_input)
                print(output)
            except Exception as e:
                print(f"Error executing command: {e}")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Close connection if established
    if 'connection' in locals():
        connection.disconnect()
        print("Connection to TermG closed.")