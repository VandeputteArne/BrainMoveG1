<script setup>
import { computed } from 'vue';

const props = defineProps({
  show: { type: Boolean, default: false },
  confirmValue: { type: String, default: '' },
  placeholder: { type: String, default: 'Wachtwoord' },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  title: { type: String, default: 'Bevestig uitschakelen' },
  message: { type: String, default: 'Voer uw wachtwoord in om alle apparaten uit te schakelen.' },
  cancelLabel: { type: String, default: 'Annuleren' },
  confirmLabel: { type: String, default: 'Bevestigen' },
});

const emit = defineEmits(['close', 'confirm', 'update:confirmValue']);

function handleClose() {
  emit('close');
}

function handleConfirm() {
  emit('confirm');
}

function onInput(e) {
  emit('update:confirmValue', e.target.value);
}
</script>

<template>
  <Transition name="fade">
    <div v-if="show" class="c-popup-overlay" @click="handleClose">
      <div class="c-popup" @click.stop>
        <div class="c-popup__header">
          <h2>{{ title }}</h2>
        </div>

        <div class="c-popup__content">
          <form class="c-password-form" @submit.prevent="handleConfirm">
            <p class="c-popup__submessage">{{ message }}</p>
            <!-- Hidden username field to satisfy browser accessibility/autofill heuristics -->
            <input type="text" name="username" autocomplete="username" tabindex="-1" aria-hidden="true" style="position: absolute; left: -9999px; width: 1px; height: 1px; opacity: 0; border: 0; padding: 0; margin: 0" />
            <input class="c-popup__input" type="password" name="confirmPassword" autocomplete="current-password" :placeholder="placeholder" :value="confirmValue" @input="onInput" :disabled="loading" />
            <p class="c-popup__error" v-if="error">{{ error }}</p>
            <div class="c-popup__confirm-actions">
              <button type="button" class="c-popup__cancel" @click="handleClose" :disabled="loading">{{ cancelLabel }}</button>
              <button type="submit" class="c-popup__confirm" :disabled="loading">{{ loading ? 'Bezig...' : confirmLabel }}</button>
            </div>
          </form>
        </div>
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
  border-radius: 1rem;
  max-width: 28rem;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}
.c-popup__header {
  padding: 1.25rem 1.25rem 0.5rem;
  border-bottom: 1px solid #eee;
}
.c-popup__content {
  padding: 1.25rem;
  text-align: center;
}
.c-popup__submessage {
  color: #4b5563;
  margin-bottom: 0.5rem;
}
.c-popup__input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  box-sizing: border-box;
}
.c-popup__error {
  color: #b91c1c;
  margin-top: 0.5rem;
}
.c-popup__confirm-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 0.75rem;
}
.c-popup__cancel {
  cursor: pointer;
  background: transparent;
  border: 1px solid #e5e7eb;
  padding: 0.5rem 1rem;
  border-radius: 8px;
}
.c-popup__confirm {
  cursor: pointer;
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
}
</style>
