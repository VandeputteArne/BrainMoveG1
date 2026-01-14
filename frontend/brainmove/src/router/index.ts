import { createRouter, createWebHistory } from 'vue-router';
import OnboardingStart from '../views/onboarding/OnboardingStart.vue';
import OnboardingSetup from '../views/onboarding/OnboardingSetup.vue';
import OnboardingWarning from '../views/onboarding/OnboardingWarning.vue';
import AppGames from '../views/games/AppGames.vue';
import AppDetail from '../views/games/AppDetail.vue';
import AppGame from '../views/games/AppGame.vue';
import ResultatenProficiat from '../views/resultaten/ResultatenProficiat.vue';
import ResultatenOverzicht from '../views/resultaten/ResultatenOverzicht.vue';

const routes = [
  {
    path: '/',
    name: 'onboarding',
    component: OnboardingStart,
    meta: { showTopbar: false, showNav: false, showBack: false, fullScreen: true, paddingbottom: false, paddingtop: false },
  },
  {
    path: '/setup',
    name: 'setup',
    component: OnboardingSetup,
    meta: { showTopbar: false, showNav: false, showBack: false, fullScreen: true, paddingbottom: false, paddingtop: false },
  },
  {
    path: '/warning',
    name: 'warning',
    component: OnboardingWarning,
    meta: { showTopbar: false, showNav: false, showBack: false, fullScreen: true, paddingbottom: false, paddingtop: false },
  },
  {
    path: '/games',
    name: 'games',
    component: AppGames,
    meta: { showTopbar: true, showNav: true, showBack: false, fullScreen: false, paddingbottom: true, paddingtop: true },
  },
  {
    path: '/games/:id',
    name: 'game-detail',
    component: AppDetail,
    meta: { showTopbar: true, showNav: false, showBack: true, fullScreen: false, paddingbottom: false, paddingtop: true },
  },
  {
    path: '/games/:id/play',
    name: 'game-play',
    component: AppGame,
    meta: { showTopbar: false, showNav: false, showBack: true, fullScreen: true, paddingbottom: false, paddingtop: false },
  },
  {
    path: '/resultaten/proficiat',
    name: 'resultaten-proficiat',
    component: ResultatenProficiat,
    meta: { showTopbar: false, showNav: false, showBack: false, fullScreen: true, paddingbottom: false, paddingtop: false },
  },
  {
    path: '/resultaten/overzicht/:id',
    name: 'resultaten-overzicht',
    component: ResultatenOverzicht,
    meta: { showTopbar: false, showNav: false, showBack: false, fullScreen: false, paddingbottom: false, paddingtop: false },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
