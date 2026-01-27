<script setup>
import { computed } from 'vue';
import { ChevronRight } from 'lucide-vue-next';

const props = defineProps({
  /** progress in percent (0-100) shown as the arc */
  progress: { type: Number, default: 25 },
  /** diameter in pixels for the circular button */
  size: { type: Number, default: 60 },
  /** background color of the inner circle */
  color: { type: String, default: '#2979ff' },
  /** whether the button is disabled */
  disabled: { type: Boolean, default: false },
  /** optional router destination (string or location object) */
  to: { type: [String, Object], default: null },
});

const emits = defineEmits(['click']);

const stroke = 3;

const radius = computed(() => (props.size - stroke) / 2);
const circumference = computed(() => 2 * Math.PI * radius.value);
const normalizedProgress = computed(() => Math.max(0, Math.min(100, Number(props.progress || 0))));
const dashoffset = computed(() => circumference.value * (1 - normalizedProgress.value / 100));

// Switch between button and router-link based on disabled state
const componentType = computed(() => (props.disabled ? 'button' : 'router-link'));

function handleClick(e) {
  if (props.disabled) {
    e && e.preventDefault && e.preventDefault();
    e && e.stopPropagation && e.stopPropagation();
    return;
  }
  emits('click', e);
}
</script>

<template>
  <component :is="componentType" :to="props.to" class="c-btn-next" :style="{ width: size + 'px', height: size + 'px' }" :aria-disabled="disabled" @click="handleClick">
    <svg class="c-btn-next__ring" :width="size" :height="size" :viewBox="`0 0 ${size} ${size}`" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <circle class="c-btn-next__track" :cx="size / 2" :cy="size / 2" :r="radius" :stroke-width="stroke" fill="none" />
      <circle class="c-btn-next__progress" :cx="size / 2" :cy="size / 2" :r="radius" :stroke-width="stroke" fill="none" stroke-linecap="round" :style="{ strokeDasharray: circumference + ' ' + circumference, strokeDashoffset: dashoffset + 'px' }" />
    </svg>

    <span class="c-btn-next__inner" :style="{ backgroundColor: color }">
      <component :is="ChevronRight" size="20" color="white" />
    </span>
  </component>
</template>

<style scoped>
.c-btn-next {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
}

.c-btn-next[aria-disabled='true'] {
  cursor: default;
  opacity: 0.6;
}

.c-btn-next__ring {
  position: absolute;
  inset: 0;
  transform: rotate(90deg);
}

.c-btn-next__track {
  stroke: rgba(0, 0, 0, 0.12);
}

.c-btn-next__progress {
  stroke: #000;
  transition: stroke-dashoffset 300ms linear;
}

.c-btn-next__inner {
  width: calc(100% - 0.75rem);
  height: calc(100% - 0.75rem);
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>
