<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const props = defineProps({
  hidden: { type: Boolean, default: false },
  suppressed: { type: Boolean, default: false },
  onlineOnly: { type: Boolean, default: false },
  autoCloseMs: { type: Number, default: 3500 },
});

const show = ref(false);
const message = ref('');
const type = ref('info');
let closeTimer = null;

const colorLabels = {
  rood: 'rood',
  blauw: 'blauw',
  groen: 'groen',
  geel: 'geel',
};

function getColorLabel(kleur) {
  return colorLabels[kleur] || kleur || 'onbekend';
}

function setBanner(nextMessage, nextType = 'info') {
  if (props.hidden || props.suppressed) return;
  message.value = nextMessage;
  type.value = nextType;
  show.value = true;
  if (closeTimer) clearTimeout(closeTimer);
  closeTimer = setTimeout(() => {
    show.value = false;
  }, props.autoCloseMs);
}

function closeBanner() {
  show.value = false;
  if (closeTimer) clearTimeout(closeTimer);
  closeTimer = null;
}

function toColorSet(list) {
  return new Set((list || []).map((d) => d?.kleur).filter(Boolean));
}

function readSnapshot(detail) {
  return {
    connected: Array.isArray(detail?.connectedDevices) ? detail.connectedDevices : [],
    disconnected: Array.isArray(detail?.disconnectedDevices) ? detail.disconnectedDevices : [],
  };
}

function getLowBatterySet(list) {
  const low = new Set();
  (list || []).forEach((d) => {
    const battery = Number(d?.batterij ?? 100);
    if (!d?.kleur) return;
    if (battery <= 10 && battery > 0) low.add(d.kleur);
  });
  return low;
}

function compareAndNotify(prev, next) {
  const prevOnline = toColorSet(prev.connected);
  const prevOffline = toColorSet(prev.disconnected);
  const nextOnline = toColorSet(next.connected);
  const nextOffline = toColorSet(next.disconnected);

  const newlyOffline = [...nextOffline].filter((c) => !prevOffline.has(c));
  if (newlyOffline.length) {
    const label = getColorLabel(newlyOffline[0]);
    if (!props.onlineOnly) {
      setBanner(`Potje ${label} is offline`, 'offline');
      return;
    }
  }

  const newlyOnline = [...nextOnline].filter((c) => !prevOnline.has(c));
  if (newlyOnline.length) {
    const label = getColorLabel(newlyOnline[0]);
    setBanner(`Potje ${label} is online`, 'online');
    return;
  }

  const prevLow = getLowBatterySet([...prev.connected, ...prev.disconnected]);
  const nextLow = getLowBatterySet([...next.connected, ...next.disconnected]);
  const newlyLow = [...nextLow].filter((c) => !prevLow.has(c));
  if (newlyLow.length) {
    const label = getColorLabel(newlyLow[0]);
    if (!props.onlineOnly) {
      setBanner(`Potje ${label} batterij bijna leeg`, 'low');
    }
  }
}

function handleDeviceStatusChanged(e) {
  if (!e?.detail) return;
  const stored = sessionStorage.getItem('device_status_prev');
  let prev = { connected: [], disconnected: [] };
  if (stored) {
    try {
      prev = JSON.parse(stored);
    } catch (err) {}
  }
  const next = readSnapshot(e.detail);
  compareAndNotify(prev, next);
  sessionStorage.setItem('device_status_prev', JSON.stringify(next));
}

onMounted(() => {
  try {
    const raw = sessionStorage.getItem('device_status');
    if (raw) {
      const parsed = JSON.parse(raw);
      const snap = readSnapshot(parsed);
      sessionStorage.setItem('device_status_prev', JSON.stringify(snap));
    }
  } catch (err) {}
  window.addEventListener('device_status_changed', handleDeviceStatusChanged);
});

onUnmounted(() => {
  window.removeEventListener('device_status_changed', handleDeviceStatusChanged);
  if (closeTimer) clearTimeout(closeTimer);
});
</script>

<template>
  <transition name="c-banner">
    <div v-if="show && !props.hidden" class="c-live-banner" :class="`c-live-banner--${type}`" role="status">
      <span class="c-live-banner__text">{{ message }}</span>
      <button class="c-live-banner__close" type="button" aria-label="Sluiten" @click="closeBanner">×</button>
    </div>
  </transition>
</template>

<style scoped>
.c-live-banner {
  position: fixed;
  top: 5.2rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2100;
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 1rem;
  border-radius: 999px;
  color: var(--color-white);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  background: var(--blue-90);
  max-width: calc(100vw - 2rem);
}

.c-live-banner--offline {
  background: var(--color-red);
}

.c-live-banner--online {
  background: var(--color-green);
}

.c-live-banner--low {
  background: var(--color-orange);
}

.c-live-banner__text {
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.c-live-banner__close {
  all: unset;
  cursor: pointer;
  font-size: 1.1rem;
  line-height: 1;
  padding: 0 0.25rem;
  color: inherit;
}

.c-banner-enter-active,
.c-banner-leave-active {
  transition:
    opacity 200ms ease,
    transform 200ms ease;
}

.c-banner-enter-from,
.c-banner-leave-to {
  opacity: 0;
  transform: translate(-50%, -10px);
}
</style>
