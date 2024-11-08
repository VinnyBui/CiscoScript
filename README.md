# Cisco Device Automation Script

This script connects to a Cisco device, retrieves specific information (like the SNMP chassis serial number), logs Cisco command outputs to a file, and optionally prints the log file.

## Prerequisites

### 1. Install Python and Required Libraries

1. **Python 3.x**: Ensure Python is installed on your machine. You can download Python from [python.org](https://www.python.org/downloads/).
2. **Python Package**: Install the necessary Python package using the following command:
    ```bash
    pip install pywin32
    ```

### 2. Configuration

- **Serial Port**: The script defaults to `COM5`. If your serial port is different, update the `SERIAL_PORT` variable in `script.py`:
    ```python
    SERIAL_PORT = 'COM5'  # Change this to your COM port
    ```
- **Log Directory**: Log files are saved to `~/Desktop/CiscoLogs` by default. You can modify this path if needed:
    ```python
    LOG_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "CiscoLogs")
    ```

### 3. Printer Setup

- Ensure a default printer is set up and connected on your machine.
- Verify that the **Print Spooler** service is running. This service manages print jobs in Windows.

### 4. Running the Scripts

- **script.py**: Run this script to connect to a Cisco router, retrieve data, and save the output to a log file.
    ```bash
    python script.py
    ```
- **printTest.py**: Run this script if you want to manually print a log file by entering the serial number:
    ```bash
    python printTest.py
    ```
    - When prompted, input the serial number of the log you want to print:
        ```
        Enter the serial number to print log: [Your Serial Number]
        ```

### 5. Log File Location

- Log files are saved to your Desktop in the following directory:
    ```
    ~/Desktop/CiscoLogs
    ```
- Each log file is named after the serial number of the device.

### 6. Troubleshooting

- **Serial Connection Issues**:
    - Ensure the correct COM port is specified in the script.
    - Close any other applications that may be using the serial port (e.g., other terminal emulators).
- **Printer Not Working**:
    - Verify that the printer is set as the default printer in your system settings.
    - Restart the **Print Spooler** service if print jobs are not being processed:
        ```bash
        net stop spooler
        net start spooler
        ```
- **Permission Errors**:
    - Run the script as an administrator if you encounter access issues.

### 7. Notes

- This script currently supports **Windows OS** due to the use of `pywin32` for printing.
- For multi-device testing, consider using a tool like SecureCRT for running scripts across multiple terminals simultaneously.

### 8. Future Enhancements

- Integration with Cisco’s API for automated part number and coverage lookup.
- Support for logging and printing on non-Windows systems (e.g., using the `lp` command on Linux).

