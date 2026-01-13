<script setup>
import { User } from 'lucide-vue-next';
</script>

<template>
  <div>
    <h3>Gebruikersnaam</h3>
    <div class="c-input-gebruiker">
      <label for="gebruikersnaam" class="c-input-gebruiker__label"><User /></label>
      <input id="gebruikersnaam" type="text" placeholder="Gebruikersnaam" class="c-input-gebruiker__input" />
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
