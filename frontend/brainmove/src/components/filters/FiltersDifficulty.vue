<script setup>
import { Star } from 'lucide-vue-next';
import { computed } from 'vue';

const props = defineProps({
  id: { type: String, required: true },
  snelheid: { type: Number, required: false },
  modelValue: { type: String, default: null },
  name: { type: String, default: 'difficulty' },
});

const emit = defineEmits(['update:modelValue']);

const isChecked = computed(() => props.modelValue === props.id);

function select() {
  emit('update:modelValue', props.id);
}

const MAX_STARS = 3;
const filled = computed(() => {
  if (Number.isFinite(props.snelheid)) return Math.min(MAX_STARS, props.snelheid);
  const parsed = parseInt(props.id, 10);
  return Number.isFinite(parsed) ? Math.min(MAX_STARS, parsed) : 1;
});
const stars = Array.from({ length: MAX_STARS }, (_, i) => i + 1);
</script>

<template>
  <label class="c-filter-difficulty" :data-id="props.id" :data-snelheid="props.snelheid">
    <input class="c-filter-difficulty__input" type="radio" :name="props.name" :value="props.id" :checked="isChecked" @change="select" />
    <span class="c-filter-difficulty__visual" role="none">
      <span class="c-filter-difficulty__stars">
        <template v-for="i in stars" :key="i">
          <Star
            class="c-filter-difficulty__star"
            :class="{
              'is-filled': i <= filled,
              'is-selected': isChecked && i <= filled,
            }"
            size="18"
          />
        </template>
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
    fill: none;
  }

  .c-filter-difficulty__star.is-filled {
    fill: currentColor;
    stroke: currentColor;
    color: var(--blue-50);
  }

  .c-filter-difficulty__input:checked + .c-filter-difficulty__visual {
    background: var(--blue-100);
    border-color: var(--blue-100);
  }

  .c-filter-difficulty__input:checked + .c-filter-difficulty__visual .c-filter-difficulty__star:not(.is-filled) {
    color: var(--blue-100);
    fill: none;
    stroke: var(--color-white);
  }

  .c-filter-difficulty__input:checked + .c-filter-difficulty__visual .c-filter-difficulty__star.is-filled {
    color: #ffffff;
    fill: currentColor;
  }
}
</style>
