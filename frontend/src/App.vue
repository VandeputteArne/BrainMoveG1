<script setup>
import { computed, watch, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import AppTopbar from './components/AppTopbar.vue';
import AppNav from './components/AppNavbar.vue';
import { useDeviceStatus } from './composables/useDeviceStatus';

const { pauseMonitoring, resumeMonitoring, fetchDeviceStatus } = useDeviceStatus();

const route = useRoute();
const showTopbar = computed(() => !!route.meta.showTopbar);
const showNav = computed(() => !!route.meta.showNav);
const showBack = computed(() => !!route.meta.showBack);
const fullScreen = computed(() => !!route.meta.fullScreen);
const paddingbottom = computed(() => !!route.meta.paddingbottom);
const paddingtop = computed(() => !!route.meta.paddingtop);

function isInGameRoute(r) {
  const name = r?.name;
  return name === 'game-play' || name === 'game-memory-play';
}

onMounted(() => {
  if (isInGameRoute(route)) {
    pauseMonitoring();
  } else {
    resumeMonitoring();
    fetchDeviceStatus();
  }
});

watch(
  () => route.name,
  (newName) => {
    if (newName === 'game-play' || newName === 'game-memory-play') pauseMonitoring();
    else {
      resumeMonitoring();
      fetchDeviceStatus();
    }
  },
);
</script>

<template>
  <AppTopbar v-if="showTopbar" :showBack="showBack" />
  <div :class="{ 'c-body': !fullScreen, 'c-body--no-padding-bottom': !paddingbottom, 'c-body--no-padding-top': !paddingtop }">
    <router-view v-slot="{ Component, route }">
      <transition :name="route.meta.transition || 'fade'" mode="out-in">
        <component :is="Component" :key="route.path" />
      </transition>
    </router-view>
  </div>
  <AppNav v-if="showNav" />
</template>

<style scoped>
.c-body {
  padding: 1.25rem 1.25rem;
  margin-bottom: 4.375rem;
  margin-top: 3.5625rem;

  @media (width >= 768px) {
    margin-top: 5.0625rem;
  }
}

.c-body--no-padding-bottom {
  margin-bottom: 0;
}

.c-body--no-padding-top {
  margin-top: 0;
}

.fade-enter-active {
  transition: opacity 0.25s ease-in;
}

.fade-leave-active {
  transition: opacity 0.2s ease-out;
}

.fade-enter-from {
  opacity: 0;
}

.fade-leave-to {
  opacity: 0;
}

.slide-left-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-left-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.6, 1);
}

.slide-left-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.slide-left-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.slide-right-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-right-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.6, 1);
}

.slide-right-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.slide-right-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.c-body > div {
  min-height: 100%;
}
</style>
