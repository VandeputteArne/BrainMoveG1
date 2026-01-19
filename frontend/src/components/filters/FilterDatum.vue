<script setup>
import { Calendar } from 'lucide-vue-next';
import { ref } from 'vue';

const dateRef = ref(null);
const selectedDate = ref('');

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
      <input ref="dateRef" type="date" v-model="selectedDate" class="c-filter-datum__input" @click.stop />
    </div>
  </div>
</template>

<style scoped>
.c-filter-datum {
  display: flex;
  flex-direction: column;
  gap: 0.3125rem;
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

.c-filter-datum__input::-webkit-calendar-picker-indicator {
  display: none;
}
</style>
