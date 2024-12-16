BAUD_RATE = 9600

DEFAULT_TIMEOUT = 300
LONG_TIMEOUT = 1200
DELETE_TIMEOUT = 10

DEFAULT_IP_ADDR = "192.168.1.150/255.255.255.0"
DEFAULT_ROUTER = "192.168.1.1"
TFTP_SERVER = "192.168.1.110"

LOG_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "CiscoLogs")
DEFAULT_LOG_FILE = "session_log.txt"
SESSION_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../logs")
SESSION_LOG_FILE = os.path.join(SESSION_LOG_DIR, "session_log.txt")