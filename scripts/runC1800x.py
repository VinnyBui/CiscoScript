import serial
import time
import os
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

def wait_for_prompt(prompt, timeout=90):
    start_time = time.time()
    output = ""
    current_timeout = 1

    while True:
        data = read_all_output()
        if data:
            output += data
            print(data, end="")
            if prompt in output:
                print(f"\nFound prompt: {prompt}")
                return True, output

        if time.time() - start_time > timeout:
            print(f"\nTimeout reached while waiting for: {prompt}")
            return False, output

        time.sleep(current_timeout)
        current_timeout = min(current_timeout + 1, 5)

def write_and_wait(command, expected_prompt, timeout=90):
    ser.write(command)
    return wait_for_prompt(expected_prompt, timeout)

def send_break_signal():
    """Send a break signal to enter ROMMON mode."""
    print("Sending break signals...")
    time.sleep(3)
    for _ in range(6):
        ser.send_break()
        time.sleep(1)
    ser.write(b'\n')

def configure_terminal():
    """Enter terminal configuration mode and set up basic configurations."""
    if write_and_wait(b"\nwrite erase\n", "Continue? [confirm]")[0]:
        if write_and_wait(b"\n", "Router#")[0]:
            if write_and_wait(b"configure terminal\n", "Router(config)#")[0]:
                write_and_wait(b"config-register 0x2102\n", "Router(config)#")
                write_and_wait(b"no logging monitor\n", "Router(config)#")
                write_and_wait(b"snmp-server community public RO\n", "Router(config)#")
                write_and_wait(bytes([26]), "#")
    # After configuration is done, we are at Router# or similar prompt.

def configure_router():
    """Run initial configuration commands on the router."""
    if write_and_wait(b"confreg 0x2142\n", "rommon 2 >")[0]:
        print("Configuration register set to 0x2142.")
        if write_and_wait(b"reset\n", "Would you like to enter the initial configuration dialog? [yes/no]:")[0]:
            print("Router is resetting...")
            ser.write(b'no\n')
            ser.write(b'\r')
            ser.flush()
            if write_and_wait(b"", "Router>")[0]:
                if write_and_wait(b"enable\n", "Router#")[0]:
                    print("Reached user mode prompt.")
                    configure_terminal()
                    # Now we are fully in IOS mode at Router#.

def close_pyserial():
    """Close the pyserial connection."""
    if ser.is_open:
        ser.close()
    print("Closed pyserial connection.")

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
        "fast_cli": False,  # Add this line
        "session_log": "session_log.txt",  # Optional logging
    }
    print("Connecting via Netmiko over serial...")
    net_connect = ConnectHandler(**device)
    net_connect.enable()
    print("Netmiko connection established. At Router# prompt.")
    return net_connect

def get_snmp_chassis_serial_netmiko(net_connect):
    """Retrieve the SNMP chassis serial number using Netmiko."""
    # Can also just return output since it holds the serial as well
    output = net_connect.send_command("show snmp chassis")
    print(output)
    # Attempt to extract a likely serial number
    lines = output.splitlines()
    for line in lines:
        line = line.strip()
        if line and len(line) > 5 and line.isalnum():
            print(f"SNMP Chassis Serial Number: {line}")
            return line
    print("Failed to retrieve SNMP chassis information.")
    return "UnknownSerial"

def capture_cisco_commands_netmiko(net_connect, serial_number):
    """Capture output from a list of Cisco commands using Netmiko and log them."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    log_path = os.path.join(LOG_DIR, f"{serial_number}.txt")
    with open(log_path, "w") as log_file:
        commands = [
            "term length 0",
            "!",
            "show inventory",
            "show hardware",
            "show env all",
        ]
        for cmd in commands:
            log_file.write(f"\n{cmd}\n")
            output = net_connect.send_command(cmd)
            log_file.write(output + "\n")
            print(output)
    print(f"Logs saved to {log_path}")

def reload_router_netmiko(net_connect):
    """Send the reload command and respond 'no' to the save configuration prompt via Netmiko."""
    # Send reload and handle prompts
    output = net_connect.send_command_timing("reload")
    if "System configuration has been modified. Save? [yes/no]:" in output:
        net_connect.send_command_timing("no")
        output = net_connect.send_command_timing("")
    if "Proceed with reload? [confirm]" in output:
        # Just send an empty line to confirm
        net_connect.send_command_timing("\n")
    print("Device is reloading...")

def main():
    try:
        send_break_signal()
        # Wait for rommon 1 >
        if write_and_wait(b'', "rommon 1 >", timeout=30)[0]:
            configure_router()
            # Now at Router#, close pyserial and switch to Netmiko
            close_pyserial()
            net_connect = connect_netmiko()

            serial_number = get_snmp_chassis_serial_netmiko(net_connect)
            capture_cisco_commands_netmiko(net_connect, serial_number)

            reload_router_netmiko(net_connect)
            net_connect.disconnect()

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if ser.is_open:
            ser.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()
