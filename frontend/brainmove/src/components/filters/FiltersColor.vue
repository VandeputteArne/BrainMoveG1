<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import { Check } from 'lucide-vue-next';

const props = defineProps({
  id: { type: [String, Number], required: true },
  name: { type: String, required: true },
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, default: () => [] },
});

const emit = defineEmits(['update:modelValue']);

const isChecked = computed(() => props.modelValue.includes(String(props.id)));

const colorMap = {
  blauw: '#2979ff', // blauw
  rood: '#f91818', // rood
  geel: '#ffc400', // geel
  groen: '#00b709', // groen
};

const inputId = computed(() => {
  const nameSafe = String(props.name || '')
    .replace(/\s+/g, '-')
    .toLowerCase();
  return `filter-color-${nameSafe}-${String(props.id)}`;
});

function onChange(event) {
  const value = String(props.id);
  const newValue = [...props.modelValue];
  if (event.target.checked) {
    if (!newValue.includes(value)) newValue.push(value);
  } else {
    const idx = newValue.indexOf(value);
    if (idx > -1) newValue.splice(idx, 1);
  }
  emit('update:modelValue', newValue);
}
</script>

<template>
  <label :for="inputId" :data-id="props.id" class="c-filter-color__label" :class="{ 'is-checked': isChecked, 'is-unchecked': !isChecked }" :style="{ backgroundColor: colorMap[props.id] }">
    <input :id="inputId" class="c-filter-color__input" type="checkbox" :checked="isChecked" @change="onChange" />
    <Check v-if="isChecked" class="c-filter-color__check" size="16" color="white" />
  </label>
</template>

<style scoped>
.c-filter-color__label {
  display: inline-flex;
  width: 2rem;
  height: 2rem;
  border-radius: 100%;
  cursor: pointer;
  position: relative;
  align-items: center;
  justify-content: center;
  margin-top: 0.3125rem;
}

.c-filter-color__input {
  position: absolute;
  inset: 0;
  margin: 0;
  opacity: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
  border: none;
  background: transparent;
}

.c-filter-color__label.is-unchecked {
  opacity: 0.5;
}
</style>
