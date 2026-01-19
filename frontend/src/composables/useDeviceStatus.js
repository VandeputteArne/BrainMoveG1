import { ref, onMounted, onUnmounted } from 'vue';
import { connectSocket, disconnectSocket } from '../services/socket.js';

// Shared state across all components
const allDevicesConnected = ref(false);
const connectedDevices = ref([]);
const disconnectedDevices = ref([]);
let socket = null;
let listenerCount = 0;

export function useDeviceStatus() {
  const isActive = ref(false);

  function setupListeners() {
    if (!socket) {
      socket = connectSocket();
    }

    // Listen for all devices connected
    socket.on('all_devices_connected', (data) => {
      console.log('[useDeviceStatus] all_devices_connected:', data);
      allDevicesConnected.value = true;
      if (data?.devices) {
        connectedDevices.value = data.devices;
      }
    });

    // Listen for device connected
    socket.on('device_connected', (data) => {
      console.log('[useDeviceStatus] device_connected:', data);
      if (data?.device) {
        const deviceId = data.device.id || data.device;
        if (!connectedDevices.value.includes(deviceId)) {
          connectedDevices.value.push(deviceId);
        }
        disconnectedDevices.value = disconnectedDevices.value.filter((id) => id !== deviceId);
      }
    });

    // Listen for device disconnected
    socket.on('device_disconnected', (data) => {
      console.log('[useDeviceStatus] device_disconnected:', data);
      allDevicesConnected.value = false;
      if (data?.device) {
        const deviceId = data.device.id || data.device;
        connectedDevices.value = connectedDevices.value.filter((id) => id !== deviceId);
        if (!disconnectedDevices.value.includes(deviceId)) {
          disconnectedDevices.value.push(deviceId);
        }
      }
    });

    isActive.value = true;
    listenerCount++;
  }

  function removeListeners() {
    if (!socket || listenerCount <= 0) return;

    listenerCount--;

    // Only remove listeners and disconnect when no components are using it
    if (listenerCount === 0) {
      socket.off('all_devices_connected');
      socket.off('device_connected');
      socket.off('device_disconnected');
      disconnectSocket();
      socket = null;
      isActive.value = false;
    }
  }

  onMounted(() => {
    setupListeners();
  });

  onUnmounted(() => {
    removeListeners();
  });

  return {
    allDevicesConnected,
    connectedDevices,
    disconnectedDevices,
    isActive,
  };
}
