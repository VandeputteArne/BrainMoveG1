import { io } from 'socket.io-client';
import { API_BASE_URL } from '../config/api.js';

let socket = null;

export function getSocket() {
  if (!socket) {
    socket = io(API_BASE_URL, {
      transports: ['websocket'],
      upgrade: false,
      autoConnect: false,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 500,
      timeout: 5000,
    });
  }
  return socket;
}

export function connectSocket() {
  const s = getSocket();
  if (!s.connected) s.connect();
  return s;
}

export function disconnectSocket() {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}
