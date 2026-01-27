import { onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { getApiUrl } from '../config/api.js';

function readChosenColors() {
  try {
    const raw = sessionStorage.getItem('lastGamePayload');
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed.kleuren)) {
      return parsed.kleuren.map((c) => String(c).toLowerCase());
    }
  } catch (e) {}
  return [];
}

function readOfflineColors(detail) {
  const offline = Array.isArray(detail?.disconnectedDevices) ? detail.disconnectedDevices : [];
  const fromDisconnected = offline.map((d) => d?.kleur).filter(Boolean);

  if (fromDisconnected.length > 0) return new Set(fromDisconnected);

  const apparaten = Array.isArray(detail?.apparaten) ? detail.apparaten : [];
  const fromApparaten = apparaten.filter((d) => d?.status === 'offline').map((d) => d?.kleur).filter(Boolean);
  return new Set(fromApparaten);
}

export function useGameDeviceGuard(gameId) {
  const router = useRouter();
  let previousOffline = new Set();
  let redirected = false;

  function updateBaseline() {
    try {
      const raw = sessionStorage.getItem('device_status');
      if (!raw) return;
      const parsed = JSON.parse(raw);
      previousOffline = readOfflineColors(parsed);
    } catch (e) {}
  }

  async function handleDeviceStatusChanged(e) {
    if (redirected) return;
    if (!e?.detail) return;

    const nextOffline = readOfflineColors(e.detail);
    const newlyOffline = [...nextOffline].filter((c) => !previousOffline.has(c));
    previousOffline = nextOffline;
    if (!newlyOffline.length) return;

    const chosenColors = readChosenColors();
    if (!chosenColors.length) return;

    const hit = newlyOffline.find((c) => chosenColors.includes(String(c).toLowerCase()));
    if (!hit) return;

    redirected = true;
    const title = 'Potje offline';
    const message = `Het ${hit} potje is offline gegaan. Kies andere kleuren en start opnieuw.`;
    try {
      sessionStorage.setItem('last_global_popup', JSON.stringify({ title, message }));
    } catch (err) {}
    try {
      await fetch(getApiUrl('games/stop'), { method: 'GET' });
    } catch (err) {
      console.error('[useGameDeviceGuard] stop game failed', err);
    }
    router.push(`/games/${gameId}`);
  }

  onMounted(() => {
    updateBaseline();
    window.addEventListener('device_status_changed', handleDeviceStatusChanged);
  });

  onUnmounted(() => {
    window.removeEventListener('device_status_changed', handleDeviceStatusChanged);
  });
}
