<script setup>
import { Gamepad2, Trophy, History, Cpu } from 'lucide-vue-next';
import { useRoute } from 'vue-router';
import { computed } from 'vue';

const route = useRoute();
const currentPath = computed(() => route.path);

function isActive(targetPath) {
  return currentPath.value === targetPath || currentPath.value.startsWith(targetPath + '/');
}

const items = [
  { path: '/games', label: 'Games', icon: Gamepad2 },
  { path: '/leaderboard', label: 'Leaderboard', icon: Trophy },
  { path: '/historie', label: 'Historie', icon: History },
  { path: '/apparaten', label: 'Apparaten', icon: Cpu },
];
</script>

<template>
  <nav class="c-navbar" aria-label="Bottom navigation">
    <ul class="c-navbar__list">
      <li v-for="item in items" :key="item.path" :class="['c-navbar__item', { 'c-nav__item--active': isActive(item.path) }]">
        <router-link :to="item.path" class="c-navbar__link">
          <div class="c-navbar__bol" aria-hidden="true">
            <component :is="item.icon" />
          </div>

          <component :is="item.icon" class="c-navbar__icon" aria-hidden="true" />

          <span class="c-navbar__label">{{ item.label }}</span>
        </router-link>
      </li>
    </ul>
  </nav>
</template>

<style scoped>
.c-navbar {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100vw;
  background-color: var(--color-white);
  z-index: 100;
  box-shadow: var(--shadow);
}

.c-navbar__list {
  display: flex;
  justify-content: space-around;
  gap: 1rem;
  padding: 0.5rem 1rem;
  list-style: none;
  margin: 0;
}

.c-navbar__item {
  position: relative;
}

/* link layout */
.c-navbar__link {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 0.25rem;
  color: var(--gray-80);
  text-decoration: none;
  font-size: 0.875rem;
  position: relative;
}

.c-navbar__icon {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease;
}

.c-navbar__label {
  line-height: 1;
}

.c-navbar__bol {
  display: flex;
  justify-content: center;
  align-items: center;

  width: 3.4rem;
  height: 3.4rem;
  border-radius: 50%;
  background-color: var(--blue-100);
  color: var(--color-white);

  position: absolute;
  top: -2rem;
  left: 50%;
  transform: translateX(-50%) translateY(10px) scale(0.6);
  opacity: 0;

  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.2);

  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
}

.c-nav__item--active .c-navbar__link {
  color: var(--blue-100);
}

.c-nav__item--active .c-navbar__bol {
  opacity: 1;
  transform: translateX(-50%) translateY(0) scale(1);
}

.c-nav__item--active .c-navbar__icon {
  opacity: 0;
  transform: scale(0.85);
}
</style>
