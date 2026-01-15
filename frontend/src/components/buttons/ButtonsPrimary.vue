<script setup>
import { defineProps } from 'vue';

const prop = defineProps({
  title: { type: String, required: true },
  icon: { type: Object, required: false },
  url: { type: String, required: true },
});
</script>

<template>
  <router-link class="c-button" :to="prop.url"
    ><span v-if="prop.icon" class="c-button__icon"><component :is="prop.icon" /></span>
    <h3>{{ prop.title }}</h3></router-link
  >
</template>

<style scoped>
.c-button {
  display: flex;
  height: 3.1875rem;
  padding: 0.8125rem 5.0625rem;
  justify-content: center;
  align-items: center;
  gap: 0.625rem;
  border-radius: 6.25rem;
  background: var(--blue-100);
  color: var(--color-white);
  text-decoration: none;

  .c-button__icon {
    display: flex;
    align-items: center;
    width: 1.5rem;
    height: 1.5rem;
  }
}
</style>
