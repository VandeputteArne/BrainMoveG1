import { ref, onMounted, onUnmounted } from 'vue';
import { connectSocket, disconnectSocket } from '../services/socket.js';
import { getApiUrl } from '../config/api.js';

// Shared state across all components
const allDevicesConnected = ref(false);
const connectedDevices = ref([]);
const disconnectedDevices = ref([]);
let socket = null;
let listenerCount = 0;

// Load initial state from sessionStorage
function loadFromSessionStorage() {
  try {
    const stored = sessionStorage.getItem('device_status');
    if (stored) {
      const data = JSON.parse(stored);
      allDevicesConnected.value = data.allDevicesConnected || false;
      connectedDevices.value = data.connectedDevices || [];
      disconnectedDevices.value = data.disconnectedDevices || [];
    }
  } catch (error) {
    console.error('[useDeviceStatus] Failed to load from sessionStorage:', error);
  }
}

// Save current state to sessionStorage
function saveToSessionStorage() {
  try {
    const data = {
      allDevicesConnected: allDevicesConnected.value,
      connectedDevices: connectedDevices.value,
      disconnectedDevices: disconnectedDevices.value,
    };
    sessionStorage.setItem('device_status', JSON.stringify(data));
  } catch (error) {
    console.error('[useDeviceStatus] Failed to save to sessionStorage:', error);
  }
}

export function useDeviceStatus() {
  const isActive = ref(false);

  async function fetchDeviceStatus() {
    try {
      const res = await fetch(getApiUrl('devices/status'));
      if (!res.ok) throw new Error(`Request failed: ${res.status}`);
      const data = await res.json();

      console.log('[useDeviceStatus] fetchDeviceStatus:', data);

      // Update connected and disconnected devices
      if (data?.apparaten && Array.isArray(data.apparaten)) {
        const online = [];
        const offline = [];

        data.apparaten.forEach((device) => {
          if (device.status === 'online') {
            online.push(device);
          } else {
            offline.push(device);
          }
        });

        connectedDevices.value = online;
        disconnectedDevices.value = offline;
        allDevicesConnected.value = online.length === 4 && offline.length === 0;

        saveToSessionStorage();
      }
    } catch (error) {
      console.error('[useDeviceStatus] Failed to fetch device status:', error);
    }
  }

  function setupListeners() {
    if (!socket) {
      socket = connectSocket();
      loadFromSessionStorage();
    }

    // Listen for all devices connected
    socket.on('all_devices_connected', (data) => {
      console.log('[useDeviceStatus] all_devices_connected:', data);
      allDevicesConnected.value = true;
      if (data?.apparaten) {
        connectedDevices.value = data.apparaten;
        disconnectedDevices.value = [];
      }
      saveToSessionStorage();
    });

    // Listen for device connected
    socket.on('device_connected', (data) => {
      console.log('[useDeviceStatus] device_connected:', data);

      // Find if device already exists by kleur
      const existingIndex = connectedDevices.value.findIndex((d) => d.kleur === data.kleur);

      if (existingIndex >= 0) {
        // Update existing device
        connectedDevices.value[existingIndex] = { ...connectedDevices.value[existingIndex], ...data };
      } else {
        // Add new device
        connectedDevices.value = [...connectedDevices.value, data];
      }

      // Remove from disconnected by kleur
      disconnectedDevices.value = disconnectedDevices.value.filter((d) => d.kleur !== data.kleur);

      saveToSessionStorage();
    });

    // Listen for device disconnected
    socket.on('device_disconnected', (data) => {
      console.log('[useDeviceStatus] device_disconnected:', data);
      allDevicesConnected.value = false;

      // Remove from connected by kleur
      connectedDevices.value = connectedDevices.value.filter((d) => d.kleur !== data.kleur);

      // Add to disconnected if not already there by kleur
      const existingIndex = disconnectedDevices.value.findIndex((d) => d.kleur === data.kleur);

      if (existingIndex >= 0) {
        disconnectedDevices.value[existingIndex] = { ...disconnectedDevices.value[existingIndex], ...data };
      } else {
        disconnectedDevices.value = [...disconnectedDevices.value, data];
      }

      saveToSessionStorage();
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
    fetchDeviceStatus,
  };
}
