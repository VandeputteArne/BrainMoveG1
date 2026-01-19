<script setup>
import { computed } from 'vue';
import { Trophy } from 'lucide-vue-next';

const props = defineProps({
  name: { type: String, required: true },
  time: { type: Number, required: true },
  count: { type: Number, required: true },
  full: { type: Boolean, default: false },
  borderDark: { type: Boolean, default: false },
  total: { type: Number, default: 0 },
});

const medalClass = computed(() => {
  if (props.count === 1) return 'is-gold';
  if (props.count === 2) return 'is-silver';
  if (props.count === 3) return 'is-bronze';
  return '';
});

const borderClass = computed(() => {
  if (props.total > 0 && props.count === props.total) return 'last-of-type';
  if (props.total === 0 && props.count === 3) return 'last-of-type';
  return '';
});

const showTrophy = computed(() => props.count <= 3);
</script>

<template>
  <div class="c-leaderboard">
    <div class="c-leaderboard__item" :class="[borderClass, props.borderDark ? 'border-dark' : '']">
      <div class="c-leaderboard__left">
        <p :class="['c-leaderboard__rank', medalClass, !showTrophy ? 'c-leaderboard__rank--under-3' : '', full ? 'c-leaderboard__rank--full' : '']">{{ props.count }}</p>

        <div v-if="showTrophy" :class="['c-leaderboard__icon-block', medalClass]">
          <Trophy class="c-leaderboard__icon" />
        </div>

        <p class="c-leaderboard__name">{{ props.name }}</p>
      </div>
      <div class="c-leaderboard__right">
        <p class="c-leaderboard__small">Gem tijd</p>
        <div class="c-leaderboard__time">
          <h3>{{ props.time }}</h3>
          <span class="small">s</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.c-leaderboard {
  display: flex;
  flex-direction: column;

  .c-leaderboard__item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: solid 1px var(--gray-20);
  }

  .c-leaderboard__item.border-dark {
    border-bottom: solid 1px var(--gray-30);
  }

  .c-leaderboard__item.last-of-type {
    border-bottom: none;
  }

  .c-leaderboard__right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.25rem;
  }

  .c-leaderboard__left {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .c-leaderboard__icon-block {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 50%;
    background-color: var(--color-yellow);
  }

  .c-leaderboard__icon {
    width: 1.5rem;
    height: 1.5rem;
    color: var(--color-white);
  }

  .c-leaderboard__name {
    font-weight: 500;
  }

  .c-leaderboard__icon-block.is-gold {
    background: #d4af37;
  }
  .c-leaderboard__icon-block.is-silver {
    background: #c0c0c0;
  }
  .c-leaderboard__icon-block.is-bronze {
    background: #cd7f32;
  }

  .c-leaderboard__rank {
    font-weight: 700;
  }

  .c-leaderboard__rank.is-gold {
    color: #d4af37;
  }
  .c-leaderboard__rank.is-silver {
    color: #6f6f6f;
  }
  .c-leaderboard__rank.is-bronze {
    color: #cd7f32;
  }

  .c-leaderboard__time {
    display: flex;
    align-items: baseline;
    gap: 0.1rem;
  }
  .c-leaderboard__small {
    font-size: 0.75rem;
    color: var(--gray-60);
  }
  .c-leaderboard__rank--under-3 {
  }

  .c-leaderboard__rank--full {
    background-color: var(--color-white);
    width: 1.5rem;
    height: 1.5rem;

    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 100%;
  }
}
</style>
