<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import AppTopbar from './components/AppTopbar.vue';
import AppNav from './components/AppNavbar.vue';

const route = useRoute();
const showTopbar = computed(() => !!route.meta.showTopbar);
const showNav = computed(() => !!route.meta.showNav);
const showBack = computed(() => !!route.meta.showBack);
</script>

<template>
  <AppTopbar v-if="showTopbar" :showBack="showBack" />
  <div class="c-body">
    <router-view />
  </div>
  <AppNav v-if="showNav" />
</template>

<style scoped>
.c-body {
  padding: 1.25rem 1.25rem;
  margin-bottom: 4.375rem;
  margin-top: 3.5625rem;
}
</style>
