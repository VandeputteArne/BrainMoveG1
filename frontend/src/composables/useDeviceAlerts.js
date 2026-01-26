import { ref, watch } from 'vue';

const LOW_BATTERY_THRESHOLD = 10;

export function useDeviceAlerts(connectedDevices, disconnectedDevices, isInGameRoute) {
  const showPopup = ref(false);
  const popupDevices = ref([]);
  const popupType = ref('low');
  let previousOfflineColors = new Set();

  function generatePopupKey(devices, type) {
    const deviceIds = devices
      .map((d) => d.kleur)
      .sort()
      .join(',');
    return `${type}:${deviceIds}`;
  }

  function wasPopupDismissed(devices, type) {
    const key = generatePopupKey(devices, type);
    const dismissed = sessionStorage.getItem('dismissedPopup');
    return dismissed === key;
  }

  function markPopupDismissed(devices, type) {
    const key = generatePopupKey(devices, type);
    sessionStorage.setItem('dismissedPopup', key);
  }

  function checkDeviceAlerts() {
    const online = connectedDevices.value || [];
    const offline = disconnectedDevices.value || [];

    const offlineDevices = offline.filter((d) => d?.kleur);
    const offlineColors = new Set(offlineDevices.map((d) => d.kleur));
    const hasNewOffline = offlineDevices.some((d) => !previousOfflineColors.has(d.kleur));

    if (isInGameRoute()) {
      previousOfflineColors = offlineColors;
      return;
    }
    if (offlineDevices.length > 0) {
      if (hasNewOffline && !wasPopupDismissed(offlineDevices, 'offline')) {
        popupDevices.value = offlineDevices;
        popupType.value = 'offline';
        showPopup.value = true;
        previousOfflineColors = offlineColors;
        return;
      }
    }

    const allDevices = [...online, ...offline];
    const seen = new Set();
    const lowBatteryDevices = allDevices.filter((d) => {
      if (!d?.kleur || seen.has(d.kleur)) return false;
      seen.add(d.kleur);
      const battery = Number(d?.batterij ?? 100);
      return battery <= LOW_BATTERY_THRESHOLD && battery > 0;
    });

    if (lowBatteryDevices.length > 0) {
      if (!wasPopupDismissed(lowBatteryDevices, 'low')) {
        popupDevices.value = lowBatteryDevices;
        popupType.value = 'low';
        showPopup.value = true;
      }
      return;
    }

    if (showPopup.value && offlineDevices.length === 0 && lowBatteryDevices.length === 0) {
      showPopup.value = false;
    }
    previousOfflineColors = offlineColors;
  }

  function handlePopupClose() {
    markPopupDismissed(popupDevices.value, popupType.value);
    showPopup.value = false;
  }

  watch(
    [connectedDevices, disconnectedDevices],
    () => {
      checkDeviceAlerts();
    },
    { deep: true },
  );

  return {
    showPopup,
    popupDevices,
    popupType,
    checkDeviceAlerts,
    handlePopupClose,
  };
}
