<script setup>
import { onMounted, onUnmounted, computed, ref } from 'vue';
import CardPotjes from '../../components/cards/CardPotjes.vue';
import ButtonsPrimary from '../../components/buttons/ButtonsPrimary.vue';
import AppPopup from '../../components/AppPopup.vue';
import { Power } from 'lucide-vue-next';
import { getApiUrl } from '../../config/api.js';

const connectedDevices = ref([]);
const disconnectedDevices = ref([]);
const colorOrder = ['rood', 'blauw', 'geel', 'groen'];

function labelForColor(kleur) {
  const idx = colorOrder.indexOf(kleur);
  if (idx >= 0) return `Potje ${idx + 1}`;
  return kleur ? `Potje ${kleur}` : 'Potje';
}

function normalizeDevice(d) {
  if (!d || typeof d !== 'object') return d;
  const copy = { ...d };
  const nested = copy.status && (copy.status.batterij ?? copy.status.battery);
  const rawBattery = copy.batterij ?? copy.battery ?? nested;
  const batteryUnknown = rawBattery === null || rawBattery === undefined;
  copy._batterijUnknown = batteryUnknown;
  copy.batterij = batteryUnknown ? 100 : rawBattery;
  return copy;
}

onMounted(() => {
  try {
    const raw = sessionStorage.getItem('device_status');
    if (raw) {
      const parsed = JSON.parse(raw);
      const connected = Array.isArray(parsed.connectedDevices) ? parsed.connectedDevices : [];
      const disconnected = Array.isArray(parsed.disconnectedDevices) ? parsed.disconnectedDevices : [];
      connectedDevices.value = connected.map(normalizeDevice);
      disconnectedDevices.value = disconnected.map(normalizeDevice);
    }
  } catch (e) {
    console.error('Failed to read device_status from sessionStorage', e);
    connectedDevices.value = [];
    disconnectedDevices.value = [];
  }
});

function updateFromParsed(parsed) {
  const connected = Array.isArray(parsed.connectedDevices) ? parsed.connectedDevices : [];
  const disconnected = Array.isArray(parsed.disconnectedDevices) ? parsed.disconnectedDevices : [];
  connectedDevices.value = connected.map(normalizeDevice);
  disconnectedDevices.value = disconnected.map(normalizeDevice);
}

function readFromSessionStorage() {
  try {
    const raw = sessionStorage.getItem('device_status');
    if (raw) {
      const parsed = JSON.parse(raw);
      updateFromParsed(parsed);
    } else {
      connectedDevices.value = [];
      disconnectedDevices.value = [];
    }
  } catch (e) {
    console.error('Failed to read device_status from sessionStorage', e);
    connectedDevices.value = [];
    disconnectedDevices.value = [];
  }
}

function onDeviceStatusChangedEvent(e) {
  if (!e) return;
  if (e.detail) updateFromParsed(e.detail);
  else readFromSessionStorage();
}

function onStorageEvent(e) {
  if (e?.key === 'device_status') readFromSessionStorage();
}

onMounted(() => {
  // ensure initial read (already done above) and listen for updates
  window.addEventListener('device_status_changed', onDeviceStatusChangedEvent);
  window.addEventListener('storage', onStorageEvent);
});

onUnmounted(() => {
  window.removeEventListener('device_status_changed', onDeviceStatusChangedEvent);
  window.removeEventListener('storage', onStorageEvent);
});

const devices = computed(() => {
  const online = (connectedDevices.value || []).map((d) => ({ ...d }));
  const offline = (disconnectedDevices.value || []).map((d) => ({ ...d }));
  const all = [...online, ...offline];
  const colorOrder = ['rood', 'blauw', 'geel', 'groen'];
  all.sort((a, b) => {
    const ia = colorOrder.indexOf(a.kleur);
    const ib = colorOrder.indexOf(b.kleur);
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
  });
  return all;
});

function formatBattery(b) {
  if (b === null || b === undefined) return 100;
  return b;
}

const showConfirmModal = ref(false);
const confirmPassword = ref('');
const confirmError = ref('');
const confirmLoading = ref(false);

function turnOff() {
  confirmPassword.value = '';
  confirmError.value = '';
  showConfirmModal.value = true;
}

async function performTurnOff(password) {
  confirmError.value = '';
  confirmLoading.value = true;
  try {
    const res = await fetch(getApiUrl(`devices/uitschakelen`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ inputGebruiker: password }),
    });

    if (!res.ok) {
      let msg = res.statusText || 'Fout bij uitschakelen';
      try {
        const j = await res.json();
        if (j && j.message) msg = j.message;
      } catch (e) {}
      confirmError.value = msg;
      console.error('Failed to turn off devices:', msg);
      return false;
    }

    showConfirmModal.value = false;
    return true;
  } catch (err) {
    confirmError.value = 'Netwerkfout — probeer opnieuw';
    console.error('Error turning off devices:', err);
    return false;
  } finally {
    confirmLoading.value = false;
  }
}

function cancelTurnOff() {
  showConfirmModal.value = false;
  confirmPassword.value = '';
  confirmError.value = '';
}

async function confirmAndTurnOff() {
  if (!confirmPassword.value) {
    confirmError.value = 'Vul je wachtwoord in';
    return;
  }
  await performTurnOff(confirmPassword.value);
}
</script>

<template>
  <div class="c-apparaten">
    <h1>Apparaten</h1>
    <div class="c-apparaten__grid">
      <template v-if="devices.length">
        <CardPotjes v-for="d in devices" :key="d.kleur" :kleur="d.kleur" :status="d.status === 'online'" :label="labelForColor(d.kleur)" :batterij="formatBattery(d.batterij)" />
      </template>
      <template v-else>
        <p>Geen apparaten gevonden.</p>
      </template>
    </div>

    <button @click="turnOff" class="c-button c-apparaten__button">
      <span class="c-button__icon"><Power /></span>
      <h3>Alles uitschakelen</h3>
    </button>

    <AppPopup :show="showConfirmModal" confirmMode v-model:confirmValue="confirmPassword" :confirmPlaceholder="'Wachtwoord'" :confirmError="confirmError" :confirmLoading="confirmLoading" :customTitle="'Bevestig uitschakelen'" :customMessage="'Voer uw wachtwoord in om alle apparaten uit te schakelen.'" :confirmCancelLabel="'Annuleren'" :confirmConfirmLabel="'Bevestigen'" @close="cancelTurnOff" @confirm="() => performTurnOff(confirmPassword)" />
  </div>
</template>

<style scoped>
.c-apparaten {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-title);
  max-width: 75rem;
  margin: 0 auto;
}

.c-apparaten__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(auto, 1fr));
  gap: 1.25rem;
  width: 100%;
  box-sizing: border-box;
  justify-items: center;

  @media (width >= 768px) {
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
  }

  @media (width >= 1024px) {
    grid-template-columns: repeat(4, 1fr);
    gap: 2rem;
  }
}

.c-apparaten__button {
  margin-top: 1rem;
  max-width: 400px;
  align-self: center;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-box {
  background: var(--surface, #fff);
  padding: 1.25rem;
  border-radius: 8px;
  width: 100%;
  max-width: 28rem;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}
.modal-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  margin-top: 0.75rem;
  margin-bottom: 0.5rem;
  border: 1px solid var(--muted, #ddd);
  border-radius: 4px;
  box-sizing: border-box;
}
.modal-error {
  color: var(--danger, #b71c1c);
  margin: 0.25rem 0 0.75rem 0;
}
.modal-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 0.5rem;
}
</style>
