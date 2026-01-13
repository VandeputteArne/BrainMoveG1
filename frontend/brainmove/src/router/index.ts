import { createRouter, createWebHistory } from 'vue-router';
import OnboardingStart from '../views/onboarding/OnboardingStart.vue';
import OnboardingSetup from '../views/onboarding/OnboardingSetup.vue';
import OnboardingWarning from '../views/onboarding/OnboardingWarning.vue';
import AppGames from '../views/games/AppGames.vue';
import AppDetail from '../views/games/AppDetail.vue';

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
  {
    path: '/games/:id',
    name: 'game-detail',
    component: AppDetail,
    meta: { showTopbar: true, showNav: false, showBack: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
