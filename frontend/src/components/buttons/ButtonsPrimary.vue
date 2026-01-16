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
