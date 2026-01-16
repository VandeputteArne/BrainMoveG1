<script setup>
import { History, ChevronRight } from 'lucide-vue-next';

const props = defineProps({
  gebruiker: {
    type: String,
    required: true,
  },
  datumtijd: {
    type: String,
    required: true,
  },
  gemtijd: {
    type: String,
    required: true,
  },
  score: {
    type: String,
    required: true,
  },
  url: {
    type: String,
    required: true,
  },
});
</script>

<template>
  <router-link class="c-card-historie" :to="props.url">
    <History class="c-card-historie__icon" />
    <div class="c-card-historie__info">
      <p>{{ props.gebruiker }}</p>
      <p class="small">{{ props.datumtijd }}</p>
    </div>
    <div class="c-card-historie__score">
      <p class="small">Gem Tijd</p>
      <h3>{{ props.gemtijd }}</h3>
    </div>
    <ChevronRight class="c-card-historie__icon" />
  </router-link>
</template>

<style scoped></style>
