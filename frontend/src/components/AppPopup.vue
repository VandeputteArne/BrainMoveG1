<script setup>
import { computed } from 'vue';
import { TriangleAlert } from 'lucide-vue-next';

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  devices: {
    type: Array,
    default: () => [],
  },
  type: {
    type: String,
    default: 'low',
    validator: (v) => ['low', 'offline'].includes(v),
  },
  // Optional custom title/message for generic popups
  customTitle: {
    type: String,
    default: '',
  },
  customMessage: {
    type: String,
    default: '',
  },
});

const emit = defineEmits(['close']);

function getColorName(kleur) {
  const colors = {
    rood: 'Rood',
    blauw: 'Blauw',
    geel: 'Geel',
    groen: 'Groen',
  };
  return colors[kleur] || kleur || '';
}

const deviceList = computed(() => {
  return props.devices.map((d) => ({
    ...d,
    colorName: getColorName(d.kleur),
    image: d.kleur ? `/images/potjes/${d.kleur}.png` : '',
  }));
});

const title = computed(() => {
  if (props.customTitle) return props.customTitle;
  const count = props.devices.length;
  if (count > 1) {
    return props.type === 'offline' ? 'Potjes offline' : 'Potjes bijna leeg';
  }
  return props.type === 'offline' ? 'Potje offline' : 'Potje bijna leeg';
});

const message = computed(() => {
  if (props.customMessage) return props.customMessage;
  const count = props.devices.length;
  if (count === 0) return '';

  if (count === 1) {
    const colorName = getColorName(props.devices[0].kleur);
    if (props.type === 'offline') {
      return `Het ${colorName} potje is offline!`;
    }
    return `Het ${colorName} potje is bijna leeg!`;
  }

  if (props.type === 'offline') {
    return `${count} potjes zijn offline!`;
  }
  return `${count} potjes zijn bijna leeg!`;
});

const submessage = computed(() => {
  if (props.type === 'offline') {
    return 'Zet de potjes aan om de training te kunnen starten.';
  }
  return 'Laad de batterijen op om de training goed te laten werken.';
});

const hasCustom = computed(() => !!(props.customTitle || props.customMessage));

function handleClose() {
  emit('close');
}
</script>

<template>
  <Transition name="fade">
    <div v-if="show" class="c-popup-overlay" @click="handleClose">
      <div class="c-popup" @click.stop>
        <div class="c-popup__header">
          <div class="c-popup__icon"><TriangleAlert /></div>
          <h2>{{ title }}</h2>
        </div>

        <div class="c-popup__content">
          <!-- If a custom message is provided, show it plainly -->
          <template v-if="hasCustom">
            <p class="c-popup__message">{{ title }}</p>
            <p class="c-popup__submessage">{{ message }}</p>
          </template>

          <!-- Otherwise show device(s) view -->
          <template v-else>
            <div v-if="deviceList.length === 1" class="c-popup__single-device">
              <img :src="deviceList[0].image" :alt="`${deviceList[0].colorName} potje`" class="c-popup__image" />
            </div>
            <div v-else-if="deviceList.length > 1" class="c-popup__devices-grid">
              <div v-for="device in deviceList" :key="device.kleur" class="c-popup__device-item">
                <img :src="device.image" :alt="`${device.colorName} potje`" class="c-popup__image-small" />
                <span class="c-popup__device-label">{{ device.colorName }}</span>
              </div>
            </div>

            <p class="c-popup__submessage">{{ submessage }}</p>
          </template>
        </div>

        <button class="c-popup__button" @click="handleClose">Begrepen</button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.c-popup-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
}

.c-popup {
  background: white;
  border-radius: 1.5rem;
  max-width: 25rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.c-popup__header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.5rem 1.5rem 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.c-popup__icon {
  font-size: 2rem;
  line-height: 1;
}

.c-popup__title {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  color: #1f2937;
}

.c-popup__content {
  padding: 2rem 1.5rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.c-popup__single-device {
  width: 100%;
  display: flex;
  justify-content: center;
}

.c-popup__devices-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  width: 100%;
  margin-bottom: 0.5rem;
}

.c-popup__device-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.c-popup__device-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #4b5563;
  text-transform: capitalize;
}

.c-popup__image {
  width: 4rem;
  height: auto;
  object-fit: contain;
  margin-bottom: 0.5rem;
}

.c-popup__image-small {
  width: 4rem;
  height: auto;
  object-fit: contain;
}

.c-popup__message {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.c-popup__submessage {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
  line-height: 1.5;
}

.c-popup__button {
  width: calc(100% - 3rem);
  margin: 0 1.5rem 1.5rem;
  padding: 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.75rem;
  font-size: 1.125rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.c-popup__button:hover {
  background: #2563eb;
}

.c-popup__button:active {
  background: #1d4ed8;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.fade-enter-active .c-popup,
.fade-leave-active .c-popup {
  transition:
    transform 0.3s ease,
    opacity 0.3s ease;
}

.fade-enter-from .c-popup,
.fade-leave-to .c-popup {
  transform: scale(0.9);
  opacity: 0;
}
</style>
