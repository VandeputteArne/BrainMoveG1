<script setup>
import { computed } from 'vue';

const props = defineProps({
  id: { type: String, required: true },
  rondes: { type: Number, required: true },
  modelValue: { type: String, default: null },
  name: { type: String, default: 'rounds' },
});

const emit = defineEmits(['update:modelValue']);
const isChecked = computed(() => props.modelValue === props.id);

function select() {
  emit('update:modelValue', props.id);
}
</script>

<template>
  <label class="c-filter-rounds">
    <input class="c-filter-rounds__input" type="radio" :name="props.name" :value="props.id" :checked="isChecked" @change="select" />
    <span class="c-filter-rounds__visual">
      <span class="c-filter-rounds__count">{{ props.rondes }}</span>
    </span>
  </label>
</template>

<style scoped>
.c-filter-rounds {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-40);
  flex: 1;
  cursor: pointer;
  margin-top: 0.3125rem;

  .c-filter-rounds__input {
    position: absolute;
    opacity: 0;
    pointer-events: none;
    width: 0;
    height: 0;
  }

  .c-filter-rounds__visual {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 0.25rem 1rem;
    border: solid 0.0625rem var(--blue-50) !important;
    border-radius: var(--radius-40);
    background: transparent;
    text-align: center;
    flex: 1;
    color: var(--blue-50);
  }

  .c-filter-rounds__input:checked + .c-filter-rounds__visual {
    background: var(--blue-100);
    border-color: var(--blue-100);
    color: #fff;
  }
}
</style>
