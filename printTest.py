import os
import win32api

# Path to the directory where logs are stored
LOG_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "CiscoLogs")

def find_log_and_print_file(serial_number):
    """Finds the log file by serial number in the log directory."""
    file_path = os.path.join(LOG_DIR, f"{serial_number}.txt")
    if os.path.exists(file_path):
        print("Print Complete")
        print_file(file_path)
    else:
        print(f"Log file for serial number {serial_number} not found.")
        return None

def print_file(file_path):
    """Sends the file to the default printer."""
    try:
        # Use win32api to print the file
        win32api.ShellExecute(0, "print", file_path, None, ".", 0)
        print(f"Sent {file_path} to printer.")
    except Exception as e:
        print(f"An error occurred while printing: {e}")

"""if you want to run the script on its own and do it mannually """
if __name__ == "__main__":
    serial_number = input("Enter the serial number to print log: ")
    find_log_and_print_file(serial_number)
