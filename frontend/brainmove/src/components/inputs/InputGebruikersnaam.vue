<script setup>
import { User } from 'lucide-vue-next';

import { defineProps, defineEmits, ref, defineExpose } from 'vue';

const props = defineProps({
  modelValue: { type: String, default: '' },
});

const emit = defineEmits(['update:modelValue']);

const inputRef = ref(null);

function onInput(e) {
  emit('update:modelValue', e.target.value);
}

function focus() {
  inputRef.value?.focus();
}

defineExpose({ focus });
</script>

<template>
  <div>
    <h3>Gebruikersnaam</h3>
    <div class="c-input-gebruiker">
      <label for="gebruikersnaam" class="c-input-gebruiker__label"><User /></label>
      <input ref="inputRef" id="gebruikersnaam" type="text" :value="props.modelValue" @input="onInput" placeholder="Gebruikersnaam" class="c-input-gebruiker__input" />
    </div>
  </div>
</template>

<style scoped>
.c-input-gebruiker {
  display: flex;
  border-radius: var(--radius-40);
  border: solid 1px var(--gray-40);
  padding: 0.5rem 0.625rem;
  margin-top: 0.3125rem;

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
}
</style>
