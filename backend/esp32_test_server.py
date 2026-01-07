#!/usr/bin/env python3
"""
ESP32 Test Server - Receives and displays test button messages from ESP32 devices
"""

import socket
import struct
import time
from datetime import datetime

# Message types (matching ESP32 firmware)
MSG_STATUS = 0x01
MSG_DETECTION = 0x02
MSG_BATTERY = 0x03
MSG_KEEPALIVE = 0x04
MSG_TEST = 0x05

# Command types (to send to ESP32)
CMD_START = 0x01
CMD_STOP = 0x02
CMD_SLEEP = 0x03
CMD_PING = 0x04

# Status events
STATUS_CONNECTED = 0x01
STATUS_RECONNECTED = 0x02
STATUS_SLEEPING = 0x03
STATUS_PONG = 0x04

# Device names by ID
DEVICE_NAMES = {
    0: "esp-blue",
    1: "esp-red",
    2: "esp-yellow",
    3: "esp-green"
}

# Server configuration
SERVER_IP = "0.0.0.0"  # Listen on all interfaces
SERVER_PORT = 5000


class MessageParser:
    """Parse binary messages from ESP32 devices"""
    
    @staticmethod
    def parse_header(data):
        """Parse the common message header (8 bytes)"""
        if len(data) < 8:
            return None
        
        message_type, device_id, reserved, timestamp = struct.unpack('<BBHI', data[:8])
        return {
            'message_type': message_type,
            'device_id': device_id,
            'device_name': DEVICE_NAMES.get(device_id, f"unknown-{device_id}"),
            'reserved': reserved,
            'timestamp': timestamp
        }
    
    @staticmethod
    def parse_status_message(data):
        """Parse status message (12 bytes total)"""
        if len(data) < 12:
            return None
        
        header = MessageParser.parse_header(data)
        if not header:
            return None
        
        status_event = struct.unpack('<B', data[8:9])[0]
        
        status_names = {
            STATUS_CONNECTED: "CONNECTED",
            STATUS_RECONNECTED: "RECONNECTED",
            STATUS_SLEEPING: "SLEEPING",
            STATUS_PONG: "PONG"
        }
        
        header['status_event'] = status_names.get(status_event, f"UNKNOWN({status_event})")
        return header
    
    @staticmethod
    def parse_detection_message(data):
        """Parse detection message (12 bytes total)"""
        if len(data) < 12:
            return None
        
        header = MessageParser.parse_header(data)
        if not header:
            return None
        
        distance = struct.unpack('<H', data[8:10])[0]
        header['distance_mm'] = distance
        return header
    
    @staticmethod
    def parse_battery_message(data):
        """Parse battery message (12 bytes total)"""
        if len(data) < 12:
            return None
        
        header = MessageParser.parse_header(data)
        if not header:
            return None
        
        battery_percent = struct.unpack('<B', data[8:9])[0]
        header['battery_percent'] = battery_percent
        return header
    
    @staticmethod
    def parse_keepalive_message(data):
        """Parse keepalive message (8 bytes total)"""
        return MessageParser.parse_header(data)
    
    @staticmethod
    def parse_test_message(data):
        """Parse test message (12 bytes total)"""
        if len(data) < 12:
            return None
        
        header = MessageParser.parse_header(data)
        if not header:
            return None
        
        test_id = struct.unpack('<B', data[8:9])[0]
        header['test_id'] = test_id
        return header


def format_timestamp():
    """Get formatted timestamp for logging"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def handle_message(data):
    """Parse and handle incoming message"""
    if len(data) < 8:
        print(f"[{format_timestamp()}] ERROR: Message too short ({len(data)} bytes)")
        return
    
    # Parse header to get message type
    header = MessageParser.parse_header(data)
    if not header:
        print(f"[{format_timestamp()}] ERROR: Failed to parse message header")
        return
    
    msg_type = header['message_type']
    device_name = header['device_name']
    timestamp_ms = header['timestamp']
    
    # Handle different message types
    if msg_type == MSG_STATUS:
        msg = MessageParser.parse_status_message(data)
        if msg:
            print(f"[{format_timestamp()}] 📊 STATUS from {device_name}: {msg['status_event']} (timestamp: {timestamp_ms}ms)")
    
    elif msg_type == MSG_DETECTION:
        msg = MessageParser.parse_detection_message(data)
        if msg:
            print(f"[{format_timestamp()}] 🎯 DETECTION from {device_name}: {msg['distance_mm']} mm (timestamp: {timestamp_ms}ms)")
    
    elif msg_type == MSG_BATTERY:
        msg = MessageParser.parse_battery_message(data)
        if msg:
            print(f"[{format_timestamp()}] 🔋 BATTERY from {device_name}: {msg['battery_percent']}% (timestamp: {timestamp_ms}ms)")
    
    elif msg_type == MSG_KEEPALIVE:
        # Keepalive messages are not printed to reduce spam
        pass
    
    elif msg_type == MSG_TEST:
        msg = MessageParser.parse_test_message(data)
        if msg:
            print(f"\n{'='*70}")
            print(f"[{format_timestamp()}] 🧪 TEST BUTTON PRESSED!")
            print(f"  Device: {device_name} (ID: {header['device_id']})")
            print(f"  Test ID: {msg['test_id']}")
            print(f"  Device timestamp: {timestamp_ms} ms")
            print(f"{'='*70}\n")
    
    else:
        print(f"[{format_timestamp()}] ⚠️  Unknown message type: 0x{msg_type:02X} from {device_name}")


def send_command(client_socket, command_type):
    """Send a command to the ESP32"""
    # Command message is 4 bytes: command_type + 3 reserved bytes
    cmd_data = struct.pack('<BBBB', command_type, 0, 0, 0)
    try:
        client_socket.send(cmd_data)
        return True
    except Exception as e:
        print(f"[{format_timestamp()}] ERROR: Failed to send command: {e}")
        return False


def handle_client(client_socket, client_address):
    """Handle a connected ESP32 client"""
    print(f"\n[{format_timestamp()}] ✅ New connection from {client_address[0]}:{client_address[1]}")
    
    try:
        while True:
            # Receive data (ESP32 messages are 8 or 12 bytes)
            data = client_socket.recv(1024)
            
            if not data:
                print(f"[{format_timestamp()}] 🔌 Connection closed by {client_address[0]}")
                break
            
            # Process messages (there might be multiple in the buffer)
            offset = 0
            while offset < len(data):
                # Peek at message type to determine message length
                if offset + 8 <= len(data):
                    msg_type = data[offset]
                    
                    # Determine message length based on type
                    if msg_type == MSG_KEEPALIVE:
                        msg_length = 8
                    elif msg_type in [MSG_STATUS, MSG_DETECTION, MSG_BATTERY, MSG_TEST]:
                        msg_length = 12
                    else:
                        # Unknown message type, try 12 bytes
                        msg_length = 12
                    
                    # Extract and handle this message
                    if offset + msg_length <= len(data):
                        message_data = data[offset:offset + msg_length]
                        handle_message(message_data)
                        offset += msg_length
                    else:
                        # Not enough data for complete message
                        break
                else:
                    # Not enough data for header
                    break
    
    except Exception as e:
        print(f"[{format_timestamp()}] ❌ Error handling client {client_address[0]}: {e}")
    
    finally:
        client_socket.close()
        print(f"[{format_timestamp()}] 👋 Disconnected from {client_address[0]}")


def main():
    """Main server loop"""
    print("=" * 70)
    print("ESP32 Test Server")
    print("=" * 70)
    print(f"Listening on {SERVER_IP}:{SERVER_PORT}")
    print("Waiting for ESP32 devices to connect...")
    print("Press Ctrl+C to stop\n")
    
    # Create TCP server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((SERVER_IP, SERVER_PORT))
        server_socket.listen(5)
        
        while True:
            # Accept incoming connections
            client_socket, client_address = server_socket.accept()
            
            # Handle the client (blocking - for simplicity)
            # For production, you'd want to use threading or async
            handle_client(client_socket, client_address)
    
    except KeyboardInterrupt:
        print(f"\n[{format_timestamp()}] 🛑 Server stopped by user")
    
    except Exception as e:
        print(f"\n[{format_timestamp()}] ❌ Server error: {e}")
    
    finally:
        server_socket.close()
        print(f"[{format_timestamp()}] 🔒 Server socket closed")


if __name__ == "__main__":
    main()
