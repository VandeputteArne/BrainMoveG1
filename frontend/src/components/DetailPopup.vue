<script setup>
import { defineProps, defineEmits } from 'vue';
import { TriangleAlert } from 'lucide-vue-next';

const props = defineProps({
  show: { type: Boolean, default: false },
  title: { type: String, default: '' },
  message: { type: String, default: '' },
});

const emit = defineEmits(['close']);

function handleClose() {
  emit('close');
}
</script>

<template>
  <Transition name="fade">
    <div v-if="props.show" class="c-popup-overlay" @click="handleClose">
      <div class="c-popup" @click.stop>
        <div class="c-popup__header">
          <div class="c-popup__icon"><TriangleAlert /></div>
          <h2>{{ props.title || 'Fout' }}</h2>
        </div>

        <div class="c-popup__content">
          <p class="c-popup__message">{{ props.title }}</p>
          <p class="c-popup__submessage">{{ props.message }}</p>
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
  border-radius: 1.25rem;
  max-width: 26rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.c-popup__header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.25rem 1.25rem 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.c-popup__icon {
  font-size: 2rem;
  line-height: 1;
}
.c-popup__content {
  padding: 1.5rem;
  text-align: center;
}
.c-popup__message {
  font-weight: 600;
  margin: 0 0 0.5rem 0;
}
.c-popup__submessage {
  color: #6b7280;
  margin: 0;
}
.c-popup__button {
  width: calc(100% - 3rem);
  margin: 0 1.5rem 1.5rem;
  padding: 0.9rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.75rem;
  font-weight: 600;
  cursor: pointer;
}
</style>
