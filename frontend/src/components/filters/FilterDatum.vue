<script setup>
import { Calendar } from 'lucide-vue-next';
import { ref } from 'vue';

const dateRef = ref(null);
const modelValue = defineModel();

function openDatePicker(event) {
  if (event.target !== dateRef.value && dateRef.value) {
    dateRef.value.showPicker?.() || dateRef.value.focus();
  }
}
</script>

<template>
  <div class="c-filter-datum">
    <p>Datum</p>
    <div class="c-filter-datum__filter" @click="openDatePicker">
      <Calendar class="c-filter-datum__icon" />
      <span v-if="!modelValue" class="c-filter-datum__placeholder">Kies datum</span>
      <input ref="dateRef" type="date" v-model="modelValue" class="c-filter-datum__input" @click.stop />
    </div>
  </div>
</template>

<style scoped>
.c-filter-datum {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.c-filter-datum__filter {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border-radius: var(--radius-40);
  border: solid 1px var(--gray-40);
  padding: 0.5rem 0.625rem;
  cursor: pointer;
  position: relative;
}

.c-filter-datum__icon {
  width: 1.25rem;
  height: 1.25rem;
  color: var(--blue-100);
}

.c-filter-datum__input {
  all: unset;
  flex-grow: 1;
  cursor: pointer;
  height: 100%;
}

.c-filter-datum__placeholder {
  position: absolute;
  left: calc(1.25rem + 1rem);
  right: 0.625rem;
  color: var(--gray-50);
  pointer-events: none;
  line-height: 1;
}

@media (min-width: 768px) {
  .c-filter-datum__placeholder {
    display: none;
  }
}

.c-filter-datum__input::-webkit-calendar-picker-indicator {
  display: none;
}
</style>
