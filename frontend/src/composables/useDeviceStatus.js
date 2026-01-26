import { ref, onMounted, onUnmounted } from 'vue';
import { connectSocket, disconnectSocket } from '../services/socket.js';
import { getApiUrl } from '../config/api.js';

const allDevicesConnected = ref(false);
const connectedDevices = ref([]);
const disconnectedDevices = ref([]);
let socket = null;
let listenerCount = 0;
const monitoringPaused = ref(false);

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

function saveToSessionStorage() {
  try {
    const data = {
      allDevicesConnected: allDevicesConnected.value,
      connectedDevices: connectedDevices.value,
      disconnectedDevices: disconnectedDevices.value,
    };
    sessionStorage.setItem('device_status', JSON.stringify(data));
    try {
      window.dispatchEvent(new CustomEvent('device_status_changed', { detail: data }));
    } catch (e) {
      // ignore
    }
  } catch (error) {
    console.error('[useDeviceStatus] Failed to save to sessionStorage:', error);
  }
}

export function useDeviceStatus() {
  const isActive = ref(false);

  function normalizeDevice(d) {
    if (!d || typeof d !== 'object') return d;
    const copy = { ...d };
    if (copy.kleur || copy.color) {
      copy.kleur = String(copy.kleur ?? copy.color).toLowerCase();
    }
    if (typeof copy.status === 'string' && copy.status.toLowerCase() === 'sleeping') {
      copy.status = 'offline';
    }
    const nested = copy.status && (copy.status.batterij ?? copy.status.battery);
    const rawBattery = copy.batterij ?? copy.battery ?? nested;
    const batteryValue = typeof rawBattery === 'string' ? Number.parseFloat(rawBattery) : Number(rawBattery);
    const batteryUnknown = rawBattery === null || rawBattery === undefined || Number.isNaN(batteryValue);
    copy._batterijUnknown = batteryUnknown;
    copy.batterij = batteryUnknown ? 100 : batteryValue;
    return copy;
  }

  function pauseMonitoring() {
    monitoringPaused.value = true;
  }

  function resumeMonitoring() {
    monitoringPaused.value = false;
  }

  async function fetchDeviceStatus() {
    try {
      const res = await fetch(getApiUrl('devices/status'));
      if (!res.ok) throw new Error(`Request failed: ${res.status}`);
      const data = await res.json();

      console.log('[useDeviceStatus] fetchDeviceStatus:', data);

      if (data?.apparaten && Array.isArray(data.apparaten)) {
        const online = [];
        const offline = [];

        data.apparaten.forEach((device) => {
          const dev = normalizeDevice(device);
          if (dev.status === 'online') online.push(dev);
          else offline.push(dev);
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

  function applyBatteryUpdate(payload) {
    if (!payload) return false;
    const items = Array.isArray(payload)
      ? payload
      : Array.isArray(payload.apparaten)
        ? payload.apparaten
        : [payload];
    let didUpdate = false;

    items.forEach((item) => {
      const update = normalizeDevice(item);
      if (!update?.kleur) return;

      const updateList = (list) => {
        const idx = list.value.findIndex((d) => d.kleur === update.kleur);
        if (idx < 0) return false;
        list.value = list.value.map((d, i) => (i === idx ? { ...d, ...update } : d));
        return true;
      };

      if (updateList(connectedDevices) || updateList(disconnectedDevices)) {
        didUpdate = true;
      }
    });

    return didUpdate;
  }

  function setupListeners() {
    if (!socket) {
      socket = connectSocket();
      loadFromSessionStorage();
    }

    socket.on('all_devices_connected', (data) => {
      if (monitoringPaused.value) return;
      console.log('[useDeviceStatus] all_devices_connected:', data);
      allDevicesConnected.value = true;
      if (data?.apparaten) {
        connectedDevices.value = data.apparaten.map(normalizeDevice);
        disconnectedDevices.value = [];
      }
      saveToSessionStorage();
    });

    socket.on('device_connected', (data) => {
      if (monitoringPaused.value) return;
      console.log('[useDeviceStatus] device_connected:', data);
      const dev = normalizeDevice(data);
      const existingIndex = connectedDevices.value.findIndex((d) => d.kleur === dev.kleur);
      if (existingIndex >= 0) {
        connectedDevices.value[existingIndex] = { ...connectedDevices.value[existingIndex], ...dev };
      } else {
        connectedDevices.value = [...connectedDevices.value, dev];
      }
      disconnectedDevices.value = disconnectedDevices.value.filter((d) => d.kleur !== dev.kleur);
      saveToSessionStorage();
    });

    socket.on('device_disconnected', (data) => {
      if (monitoringPaused.value) return;
      console.log('[useDeviceStatus] device_disconnected:', data);
      allDevicesConnected.value = false;
      const dev = normalizeDevice(data);
      connectedDevices.value = connectedDevices.value.filter((d) => d.kleur !== dev.kleur);
      const existingIndex = disconnectedDevices.value.findIndex((d) => d.kleur === dev.kleur);
      if (existingIndex >= 0) {
        disconnectedDevices.value[existingIndex] = { ...disconnectedDevices.value[existingIndex], ...dev };
      } else {
        disconnectedDevices.value = [...disconnectedDevices.value, dev];
      }
      saveToSessionStorage();
    });

    socket.on('device_battery_update', (data) => {
      if (monitoringPaused.value) return;
      console.log('[useDeviceStatus] device_battery_update:', data);
      const updated = applyBatteryUpdate(data);
      if (updated) saveToSessionStorage();
    });

    isActive.value = true;
    listenerCount++;
  }

  function removeListeners() {
    if (!socket || listenerCount <= 0) return;

    listenerCount--;

    if (listenerCount === 0) {
      socket.off('all_devices_connected');
      socket.off('device_connected');
      socket.off('device_disconnected');
      socket.off('device_battery_update');
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
    pauseMonitoring,
    resumeMonitoring,
  };
}
