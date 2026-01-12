import { createRouter, createWebHistory } from 'vue-router';
import OnboardingStart from '../views/onboarding/OnboardingStart.vue';
import OnboardingSetup from '../views/onboarding/OnboardingSetup.vue';
import OnboardingWarning from '../views/onboarding/OnboardingWarning.vue';
import AppGames from '../views/AppGames.vue';

const routes = [
  {
    path: '/',
    name: 'onboarding',
    component: OnboardingStart,
  },
  {
    path: '/setup',
    name: 'setup',
    component: OnboardingSetup,
  },
  {
    path: '/warning',
    name: 'warning',
    component: OnboardingWarning,
  },
  {
    path: '/games',
    name: 'games',
    component: AppGames,
    meta: { showTopbar: true, showNav: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
