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
    <div class="c-card-historie__start">
      <History />
      <div class="c-card-historie__info">
        <p>{{ props.gebruiker }}</p>
        <p class="small c-card-historie__gray">{{ props.datumtijd }}</p>
      </div>
    </div>
    <div class="c-card-historie__end">
      <div class="c-card-historie__score">
        <p class="small c-card-historie__gray">Gem Tijd</p>
        <h3>{{ props.gemtijd }}</h3>
      </div>
      <ChevronRight class="c-card-historie__icon" />
    </div>
  </router-link>
</template>

<style scoped>
.c-card-historie {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.625rem;
  border-radius: var(--radius-40);
  border: 1px solid var(--gray-30);
  text-decoration: none;
  color: inherit;
  transition: background-color 0.2s ease-in-out;

  .c-card-historie__start {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding-left: 0.375rem;
  }

  .c-card-historie__end {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .c-card-historie__score {
    text-align: right;
  }

  .c-card-historie__gray {
    color: var(--gray-50);
  }

  .c-card-historie__icon {
    color: var(--blue-100);
  }
}
</style>
