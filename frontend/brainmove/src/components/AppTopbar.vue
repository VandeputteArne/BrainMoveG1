<script setup>
import { Wifi, BatteryFull } from 'lucide-vue-next';
</script>

<template>
  <div class="c-topbar">
    <div class="c-topbar__inhoud">
      <h3>BrainMove</h3>
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

  .c-topbar__inhoud {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .c-topbar__icons {
    display: flex;
    gap: 0.5rem;
  }
}
</style>
