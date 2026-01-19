<script setup>
import { Star } from 'lucide-vue-next';
import { computed } from 'vue';

const props = defineProps({
  id: { type: String, required: true },
  snelheid: { type: Number, required: false },
  stars: { type: Number, default: 1 },
  modelValue: { type: String, default: null },
  name: { type: String, default: 'difficulty' },
});

const emit = defineEmits(['update:modelValue']);

const isChecked = computed(() => props.modelValue === props.id);

function select() {
  emit('update:modelValue', props.id);
}

const starCount = computed(() => {
  return props.stars > 0 ? props.stars : 1;
});
</script>

<template>
  <label class="c-filter-difficulty" :data-id="props.id" :data-snelheid="props.snelheid">
    <input class="c-filter-difficulty__input" type="radio" :name="props.name" :value="props.id" :checked="isChecked" @change="select" />
    <span class="c-filter-difficulty__visual" role="none">
      <span class="c-filter-difficulty__stars">
        <Star v-for="i in starCount" :key="i" class="c-filter-difficulty__star" size="18" />
      </span>
    </span>
  </label>
</template>

<style scoped>
.c-filter-difficulty {
  display: inline-block;
  cursor: pointer;
  margin-top: 0.3125rem;
  flex: 1;
}

.c-filter-difficulty__input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
  width: 0;
  height: 0;
}

.c-filter-difficulty__visual {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-40);
  border: 1px solid var(--blue-50);
  background: transparent;
  width: 100%;
}

.c-filter-difficulty__stars {
  display: inline-flex;
  gap: 0.5rem;
  align-items: center;
}

.c-filter-difficulty__star {
  color: var(--blue-50);
  stroke: currentColor;
  fill: currentColor;
}

.c-filter-difficulty__input:checked + .c-filter-difficulty__visual {
  background: var(--blue-100);
  border-color: var(--blue-100);
}

.c-filter-difficulty__input:checked + .c-filter-difficulty__visual .c-filter-difficulty__star {
  color: var(--color-white);
  fill: currentColor;
  stroke: currentColor;
}
</style>
