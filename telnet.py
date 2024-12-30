from netmiko import ConnectHandler
import logging
import os

session_log_path = os.path.join("logs", "telnet_log.txt")

# Enable debugging to capture session output
logging.basicConfig(level=logging.DEBUG)

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
    output = connection.send_command_timing("telnet l0")
    print("Telnet to L0 initiated:")
    print(output)

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Close connection if established
    if connection:
        connection.disconnect()
        print("Connection to TermG closed.")