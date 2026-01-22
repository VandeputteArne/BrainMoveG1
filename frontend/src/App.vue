<script setup>
import { computed, watch, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import AppTopbar from './components/AppTopbar.vue';
import AppNav from './components/AppNavbar.vue';
import { useDeviceStatus } from './composables/useDeviceStatus';
import AppPopup from './components/AppPopup.vue';

const { pauseMonitoring, resumeMonitoring, fetchDeviceStatus, connectedDevices, disconnectedDevices } = useDeviceStatus();

const showPopup = ref(false);
const popupDevices = ref([]);
const popupType = ref('low');
const LOW_BATTERY_THRESHOLD = 10;

function checkDeviceAlerts() {
  const inGame = isInGameRoute(route);
  if (inGame) return;

  const online = connectedDevices.value || [];
  const offline = disconnectedDevices.value || [];

  const offlineDevices = offline.filter((d) => d?.kleur);
  if (offlineDevices.length > 0) {
    popupDevices.value = offlineDevices;
    popupType.value = 'offline';
    showPopup.value = true;
    return;
  }

  const lowBatteryDevices = online.filter((d) => {
    const battery = Number(d?.batterij ?? 100);
    return battery <= LOW_BATTERY_THRESHOLD && battery > 0;
  });

  if (lowBatteryDevices.length > 0) {
    popupDevices.value = lowBatteryDevices;
    popupType.value = 'low';
    showPopup.value = true;
    return;
  }

  if (showPopup.value && offlineDevices.length === 0 && lowBatteryDevices.length === 0) {
    showPopup.value = false;
  }
}

function handlePopupClose() {
  showPopup.value = false;
}

watch(
  [connectedDevices, disconnectedDevices],
  () => {
    checkDeviceAlerts();
  },
  { deep: true },
);

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
    checkDeviceAlerts();
  }
});

watch(
  () => route.name,
  (newName) => {
    if (newName === 'game-play' || newName === 'game-memory-play') {
      pauseMonitoring();
      showPopup.value = false;
    } else {
      resumeMonitoring();
      fetchDeviceStatus();
      checkDeviceAlerts();
    }
  },
);
</script>

<template>
  <AppPopup :show="showPopup" :devices="popupDevices" :type="popupType" @close="handlePopupClose" />
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
