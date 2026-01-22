<script setup>
import { Wifi, BatteryFull, ChevronLeft } from 'lucide-vue-next';
import { useRoute } from 'vue-router';
import { computed } from 'vue';

const props = defineProps({
  showBack: { type: Boolean, default: false },
});

const route = useRoute();
const currentPath = computed(() => route.path);

function isActive(targetPath) {
  return currentPath.value === targetPath || currentPath.value.startsWith(targetPath + '/');
}
</script>

<template>
  <div class="c-topbar">
    <div class="c-topbar__inhoud">
      <router-link v-if="props.showBack" to="/games" class="c-topbar__back">
        <ChevronLeft />
        <h3>Terug</h3>
      </router-link>
      <h3 v-else>BrainMove</h3>
      <div class="c-topbar__icons">
        <Wifi />
        <BatteryFull />
      </div>
    </div>
  </div>

  <div class="c-topbar-desktop">
    <div class="c-topbar__inhoud">
      <router-link v-if="props.showBack" to="/games" class="c-topbar__back">
        <ChevronLeft />
        <h3>Terug</h3>
      </router-link>
      <div v-else class="c-topbar-desktop__left">
        <img src="/images/BrainMove-Logo.png" alt="BrainMove Logo" class="c-topbar-desktop__logo" />
        <nav class="c-topbar-desktop__nav">
          <ul class="c-topbar-desktop__list">
            <li class="c-topbar-desktop__item">
              <router-link to="/games" :class="['c-topbar-desktop__link', { 'c-topbar-desktop__link--active': isActive('/games') }]">Games</router-link>
            </li>
            <li class="c-topbar-desktop__item">
              <router-link to="/leaderboard" :class="['c-topbar-desktop__link', { 'c-topbar-desktop__link--active': isActive('/leaderboard') }]">Leaderboard</router-link>
            </li>
            <li class="c-topbar-desktop__item">
              <router-link to="/historie" :class="['c-topbar-desktop__link', { 'c-topbar-desktop__link--active': isActive('/historie') }]">Historie</router-link>
            </li>
            <li class="c-topbar-desktop__item">
              <router-link to="/apparaten" :class="['c-topbar-desktop__link', { 'c-topbar-desktop__link--active': isActive('/apparaten') }]">Apparaten</router-link>
            </li>
          </ul>
        </nav>
      </div>
      <div class="c-topbar__icons">
        <Wifi />
        <BatteryFull />
      </div>
    </div>
  </div>
</template>

<style scoped>
.c-topbar {
  @media (width <= 768px) {
    display: block;
  }

  display: none;
  padding: 1rem 1.25rem;
  color: var(--gray-80);
  border-bottom: solid 1px var(--gray-20);
  position: fixed;
  top: 0;
  width: 100vw;
  background-color: var(--color-white);
  z-index: 100;

  .c-topbar__inhoud {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .c-topbar__icons {
    display: flex;
    gap: 0.5rem;
  }

  .c-topbar__back {
    display: flex;
    align-items: center;
    color: var(--gray-80);
    gap: 0.0625rem;
    text-decoration: none;
  }
}

.c-topbar-desktop {
  @media (width >= 768px) {
    display: block;
  }

  display: none;
  padding: 1rem 1.25rem;
  color: var(--gray-80);
  border-bottom: solid 1px var(--gray-20);
  position: fixed;
  top: 0;
  width: 100vw;
  background-color: var(--color-white);
  z-index: 100;

  .c-topbar__inhoud {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .c-topbar__icons {
    display: flex;
    gap: 0.5rem;
  }

  .c-topbar__back {
    display: flex;
    align-items: center;
    color: var(--gray-80);
    gap: 0.0625rem;
    text-decoration: none;
  }

  .c-topbar-desktop__nav {
    margin-left: 2rem;
    display: flex;
    align-items: center;
  }

  .c-topbar-desktop__list {
    display: flex;
    gap: 2rem;
    list-style: none;
    margin: 0;
    padding: 0;

    @media (width < 992px) {
      gap: 1rem;
    }
  }

  .c-topbar-desktop__left {
    display: flex;
  }

  .c-topbar-desktop__logo {
    height: 3rem;
    width: auto;
  }

  .c-topbar-desktop__link {
    text-decoration: none;
    font-weight: 500;
    font-size: 1rem;
    color: var(--gray-80);
    padding: 0.5rem 1rem;
    border-radius: var(--radius-10);
    transition:
      color 0.3s ease,
      font-weight 0.3s ease;
    position: relative;
  }

  .c-topbar-desktop__link:hover {
    color: var(--blue-100);
  }

  .c-topbar-desktop__link--active {
    color: var(--blue-100);
    font-weight: 600;
  }

  .c-topbar-desktop__link::after {
    content: '';
    position: absolute;
    bottom: 0rem;
    left: 50%;
    transform: translateX(-50%);
    height: 0.1875rem;
    background-color: var(--blue-100);
    border-radius: 2px 2px 0 0;
    width: 0%;
    transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .c-topbar-desktop__link--active::after {
    width: 80%;
  }
}
</style>
