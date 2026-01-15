<script setup>
import { Zap, Crown } from 'lucide-vue-next';
import { computed } from 'vue';

const props = defineProps({
  id: { type: String, required: true },
  title: { type: String, default: 'Color Sprint' },
  tag: { type: String, default: 'Reactiesnelheid' },
  bestTime: { type: Number, default: 0 },
  unit: { type: String, default: 's' },
  image: { type: String, default: 'images/cards/color-sprint.png' },
});
</script>

<template>
  <router-link :to="`/games/${props.id}`" class="c-game-card" :style="{ backgroundImage: `url(${props.image})` }">
    <div class="c-game-card__tag">
      <Zap class="c-game-card__icon" />
      <p>{{ props.tag }}</p>
    </div>
    <div class="c-game-card__info">
      <p class="c-game-card__title">{{ props.title }}</p>
      <div class="c-game-card__best">
        <Crown class="c-game-card__icon c-game-card__icon--yellow" />
        <p class="small">{{ props.bestTime }}{{ props.unit }}</p>
      </div>
    </div>
  </router-link>
</template>

<style scoped>
.c-game-card {
  display: flex;
  justify-content: space-between;
  flex-direction: column;
  height: 12.875rem;
  width: 100%;
  background-image: url('/images/cards/color-sprint.png');
  background-repeat: no-repeat;
  background-size: cover;
  background-position: center;
  border-radius: var(--radius-20);
  text-decoration: none;
  color: var(--color-white);
  padding: 0.75rem;

  .c-game-card__tag {
    display: flex;
    align-items: center;
    gap: 0.625rem;
    background-color: var(--blue-100);
    width: fit-content;
    padding: 0.125rem 0.3125rem;
    border-radius: var(--radius-40);
  }

  .c-game-card__icon {
    width: 1rem;
    height: 1rem;
  }

  .c-game-card__info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: var(--color-black);
    background-color: var(--color-white);
    padding: 0.75rem;
    border-radius: var(--radius-15);
  }

  .c-game-card__best {
    display: flex;
    align-items: center;
    gap: 0.3125rem;
  }

  .c-game-card__icon--yellow {
    color: var(--color-yellow);
  }

  .c-game-card__title {
    font-weight: 600;
    margin: 0;
  }
}
</style>
