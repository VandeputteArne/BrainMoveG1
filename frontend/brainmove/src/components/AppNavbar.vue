<script setup>
import { Gamepad, Trophy, History, Cpu } from 'lucide-vue-next';
import { useRoute } from 'vue-router';
import { computed } from 'vue';

const route = useRoute();
const currentPath = computed(() => route.path);

function isActive(targetPath) {
  return currentPath.value === targetPath || currentPath.value.startsWith(targetPath + '/');
}
</script>

<template>
  <nav class="c-navbar">
    <ul class="c-navbar__list">
      <li :class="['c-navbar__item', { 'c-nav__item--active': isActive('/games') }]">
        <router-link to="/games">
          <Gamepad />
          Games
        </router-link>
      </li>
      <li :class="['c-navbar__item', { 'c-nav__item--active': isActive('/leaderboard') }]">
        <router-link to="/leaderboard">
          <Trophy />
          Leaderboard
        </router-link>
      </li>
      <li :class="['c-navbar__item', { 'c-nav__item--active': isActive('/historie') }]">
        <router-link to="/historie">
          <History />
          Historie
        </router-link>
      </li>
      <li :class="['c-navbar__item', { 'c-nav__item--active': isActive('/apparaten') }]">
        <router-link to="/apparaten">
          <Cpu />
          Apparaten
        </router-link>
      </li>
    </ul>
  </nav>
</template>

<style scoped>
.c-navbar {
  position: fixed;
  bottom: 0rem;
  left: 50%;
  transform: translateX(-50%);
  width: 100vw;

  .c-navbar__list {
    display: flex;
    justify-content: space-around;
    gap: 1rem;
    padding: 0.5rem 1rem;
    list-style: none;
    margin: 0;
  }

  .c-navbar__item a {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: var(--gray-80);
    text-decoration: none;
    font-size: 0.875rem;
    gap: 0.25rem;
  }

  .c-nav__item--active a {
    color: var(--blue-100);
  }
}
</style>
