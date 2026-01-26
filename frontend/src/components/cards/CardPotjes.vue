<script setup>
import { BatteryFull, BatteryMedium, BatteryLow } from 'lucide-vue-next';
import { computed } from 'vue';

const props = defineProps({
  kleur: {
    type: String,
    required: true,
  },
  status: {
    type: Boolean,
    required: true,
  },
  label: {
    type: String,
    required: false,
  },
  batterij: {
    type: Number,
    required: false,
  },
});

const LOW_BATTERY_THRESHOLD = 10;
const isLowBattery = computed(() => {
  if (props.batterij === null || props.batterij === undefined) return false;
  return Number(props.batterij) <= LOW_BATTERY_THRESHOLD;
});

const showBattery = computed(() => props.status && props.batterij !== undefined && props.batterij !== null);
const isOffline = computed(() => !props.status);
</script>

<template>
  <div class="c-potje">
    <img :src="`/images/potjes/${props.kleur}.png`" :alt="`Potje ${props.kleur}`" class="c-potje__image" />
    <div class="c-potje__header">
      <p class="c-potje__label">{{ props.label }}</p>
      <div v-if="showBattery" class="c-potje__batterij">
        <p class="c-potje__label">{{ props.batterij }}%</p>
        <div class="c-potje__batterijen">
          <BatteryFull class="c-potje__batterij-icon" v-if="props.batterij > 66" size="16" />
          <BatteryMedium class="c-potje__batterij-icon c-potje__batterij-icon--medium" v-else-if="props.batterij > 33" size="16" />
          <BatteryLow class="c-potje__batterij-icon c-potje__batterij-icon--low" v-else size="16" />
        </div>
      </div>
    </div>
    <div class="c-potje__status-balk" :class="{ 'c-potje__status-balk--spaced': isOffline }">
      <div :class="['c-potje__status', props.status ? 'c-potje__status--online' : 'c-potje__status--offline', { 'c-potje__status--pulse': props.status, 'c-potje__status--low': props.status && isLowBattery }]"></div>
      <h3 v-if="props.status">Online</h3>
      <h3 v-else>Offline</h3>
    </div>
  </div>
</template>

<style scoped>
.c-potje {
  width: 100%;
  padding: 0.875rem 1.875rem;

  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  border-radius: var(--radius-20);
  border: solid 1px var(--blue-50);

  .c-potje__status-balk {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
  }

  .c-potje__status {
    width: 0.875rem;
    height: 0.875rem;
    border-radius: 100%;
  }

  .c-potje__status--online {
    background-color: var(--color-green);
  }

  .c-potje__status--offline {
    background-color: var(--color-red);
  }

  .c-potje__status--pulse {
    animation: status-pulse 1.8s ease-in-out infinite;
    box-shadow: 0 0 0 rgba(0, 0, 0, 0);
  }

  .c-potje__status--low {
    animation: status-pulse-low 1.4s ease-in-out infinite;
  }

  .c-potje__image {
    width: 60%;
    max-width: 5rem;
    height: auto;
  }

  .c-potje__header {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
    margin-bottom: 0.5rem;
  }

  .c-potje__label {
    font-size: 1rem;
  }

  .c-potje__batterij {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 0.3125rem;
    margin-top: 0.25rem;
  }

  .c-potje__batterij-icon {
    width: 1.5rem;
    height: 1.5rem;
  }

  .c-potje__batterij-icon--medium {
    color: var(--color-yellow);
  }

  .c-potje__batterij-icon--low {
    color: var(--color-red);
  }

  .c-potje__batterijen {
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

@keyframes status-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(38, 197, 120, 0.5);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(38, 197, 120, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(38, 197, 120, 0);
  }
}

@keyframes status-pulse-low {
  0% {
    box-shadow: 0 0 0 0 rgba(230, 62, 62, 0.5);
  }
  70% {
    box-shadow: 0 0 0 12px rgba(230, 62, 62, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(230, 62, 62, 0);
  }
}
</style>
