import { createRouter, createWebHistory } from 'vue-router';
import OnboardingStart from '../views/onboarding/OnboardingStart.vue';
import OnboardingSetup from '../views/onboarding/OnboardingSetup.vue';
import OnboardingWarning from '../views/onboarding/OnboardingWarning.vue';
import AppGames from '../views/games/AppGames.vue';
import AppDetail from '../views/games/AppDetail.vue';
import AppGame from '../views/games/AppGame.vue';

const routes = [
  {
    path: '/',
    name: 'onboarding',
    component: OnboardingStart,
    meta: { showTopbar: false, showNav: false, showBack: false, fullScreen: true, paddingbottom: false },
  },
  {
    path: '/setup',
    name: 'setup',
    component: OnboardingSetup,
    meta: { showTopbar: false, showNav: false, showBack: false, fullScreen: true, paddingbottom: false },
  },
  {
    path: '/warning',
    name: 'warning',
    component: OnboardingWarning,
    meta: { showTopbar: false, showNav: false, showBack: false, fullScreen: true, paddingbottom: false },
  },
  {
    path: '/games',
    name: 'games',
    component: AppGames,
    meta: { showTopbar: true, showNav: true, showBack: true, fullScreen: false, paddingbottom: true },
  },
  {
    path: '/games/:id',
    name: 'game-detail',
    component: AppDetail,
    meta: { showTopbar: true, showNav: false, showBack: true, fullScreen: false, paddingbottom: false },
  },
  {
    path: '/games/:id/play',
    name: 'game-play',
    component: AppGame,
    meta: { showTopbar: false, showNav: false, showBack: true, fullScreen: true, paddingbottom: false },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
