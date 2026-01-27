<script setup>
import { Lock } from 'lucide-vue-next';

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
            <div class="c-input-gebruiker">
              <label for="confirmPassword" class="c-input-gebruiker__label"><Lock class="c-input-gebruiker__icon" /></label>
              <input id="confirmPassword" class="c-input-gebruiker__input" type="password" name="confirmPassword" autocomplete="current-password" :placeholder="placeholder" :value="confirmValue" @input="onInput" :disabled="loading" />
            </div>
            <p class="c-popup__error" v-if="error">{{ error }}</p>
            <div class="c-popup__confirm-actions">
              <button type="button" class="c-button c-popup__cancel" @click="handleClose" :disabled="loading">{{ cancelLabel }}</button>
              <button type="submit" class="c-button c-popup__confirm" :disabled="loading">{{ loading ? 'Bezig...' : confirmLabel }}</button>
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

.fade-enter-active,
.fade-leave-active {
  transition: opacity 220ms ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.fade-enter-active .c-popup,
.fade-leave-active .c-popup {
  transition: transform 220ms cubic-bezier(0.2, 0.8, 0.2, 1), opacity 220ms ease;
}

.fade-enter-from .c-popup {
  transform: translateY(12px) scale(0.98);
  opacity: 0;
}

.fade-leave-to .c-popup {
  transform: translateY(8px) scale(0.98);
  opacity: 0;
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
.c-popup__confirm-actions .c-button {
  width: auto;
  flex: 1;
  padding: 0.8125rem 2rem;
  height: 3.1875rem;
}

.c-popup__cancel.c-button {
  background: var(--gray-20);
  color: var(--gray-80);
}

.c-input-gebruiker {
  display: flex;
  border-radius: var(--radius-40);
  border: solid 1px var(--gray-40);
  padding: 0.5rem 0.625rem;
  margin-top: 0.3125rem;
}

.c-input-gebruiker__label {
  display: flex;
  align-items: center;
  color: var(--gray-40);
  margin-right: 0.5rem;
}

.c-input-gebruiker__input {
  width: 100%;
  border: none;
  outline: none;
  color: var(--gray-80);
  font-size: 0.875rem;
  background-color: transparent;
}

.c-input-gebruiker__icon {
  width: 1.25rem;
  height: 1.25rem;
  color: var(--blue-100);
}
</style>
