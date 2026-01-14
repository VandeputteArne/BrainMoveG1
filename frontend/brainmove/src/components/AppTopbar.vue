<script setup>
import { Wifi, BatteryFull, ChevronLeft } from 'lucide-vue-next';

const props = defineProps({
  showBack: { type: Boolean, default: false },
});
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
</template>

<style scoped>
.c-topbar {
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
</style>
