import { createRouter, createWebHistory } from 'vue-router';
import OnboardingStart from '../views/onboarding/OnboardingStart.vue';
import OnboardingSetup from '../views/onboarding/OnboardingSetup.vue';
import OnboardingWarning from '../views/onboarding/OnboardingWarning.vue';
import AppGames from '../views/games/AppGames.vue';
import AppDetail from '../views/games/AppDetail.vue';
import AppGame from '../views/games/AppGameColor.vue';
import AppGameMemory from '../views/games/AppGameMemory.vue';
import AppGameNumberMatch from '../views/games/AppGameNumberMatch.vue';
import AppGameFallingColors from '../views/games/AppGameFallingColors.vue';
import AppGameColorBattle from '../views/games/AppGameColorBattle.vue';
import ResultatenProficiat from '../views/resultaten/ResultatenProficiat.vue';
import ResultatenOverzicht from '../views/resultaten/ResultatenOverzicht.vue';
import ApparatenView from '../views/apparaten/AppApparaten.vue';
import AppHistorie from '../views/historie/AppHistorie.vue';
import AppLeaderboard from '../views/leaderboard/AppLeaderboard.vue';

const routes = [
  {
    path: '/',
    name: 'onboarding',
    component: OnboardingStart,
    meta: { showTopbar: false, showNav: false, showBack: false, fullScreen: true, paddingbottom: false, paddingtop: false, transition: 'fade' },
  },
  {
    path: '/setup',
    name: 'setup',
    component: OnboardingSetup,
    meta: { showTopbar: false, showNav: false, showBack: false, fullScreen: false, paddingbottom: false, paddingtop: false, transition: 'slide-left' },
  },
  {
    path: '/warning',
    name: 'warning',
    component: OnboardingWarning,
    meta: { showTopbar: false, showNav: false, showBack: false, fullScreen: false, paddingbottom: false, paddingtop: false, transition: 'slide-left' },
  },
  {
    path: '/games',
    name: 'games',
    component: AppGames,
    meta: { showTopbar: true, showNav: true, showBack: false, fullScreen: false, paddingbottom: true, paddingtop: true, transition: 'fade' },
  },
  {
    path: '/games/:id',
    name: 'game-detail',
    component: AppDetail,
    meta: { showTopbar: true, showNav: false, showBack: true, fullScreen: false, paddingbottom: false, paddingtop: true, transition: 'slide-left' },
  },
  {
    path: '/games/1/play',
    name: 'game-play',
    component: AppGame,
    meta: { showTopbar: false, showNav: false, showBack: true, fullScreen: true, paddingbottom: false, paddingtop: false, transition: 'fade' },
  },
  {
    path: '/games/2/play',
    name: 'game-memory-play',
    component: AppGameMemory,
    meta: { showTopbar: false, showNav: false, showBack: true, fullScreen: true, paddingbottom: false, paddingtop: false, transition: 'fade' },
  },
  {
    path: '/games/3/play',
    name: 'game-number-match-play',
    component: AppGameNumberMatch,
    meta: { showTopbar: false, showNav: false, showBack: true, fullScreen: true, paddingbottom: false, paddingtop: false, transition: 'fade' },
  },
  {
    path: '/games/4/play',
    name: 'game-falling-colors-play',
    component: AppGameFallingColors,
    meta: { showTopbar: false, showNav: false, showBack: true, fullScreen: true, paddingbottom: false, paddingtop: false, transition: 'fade' },
  },
  {
    path: '/games/5/play',
    name: 'game-color-battle-play',
    component: AppGameColorBattle,
    meta: { showTopbar: false, showNav: false, showBack: true, fullScreen: true, paddingbottom: false, paddingtop: false, transition: 'fade' },
  },
  {
    path: '/resultaten/proficiat',
    name: 'resultaten-proficiat',
    component: ResultatenProficiat,
    meta: { showTopbar: false, showNav: false, showBack: false, fullScreen: true, paddingbottom: false, paddingtop: false, transition: 'fade' },
  },
  {
    path: '/resultaten/overzicht',
    name: 'resultaten-overzicht',
    component: ResultatenOverzicht,
    meta: { showTopbar: false, showNav: false, showBack: false, fullScreen: false, paddingbottom: false, paddingtop: false, transition: 'slide-left' },
  },
  {
    path: '/resultaten/overzicht/:id',
    name: 'resultaten-overzicht-detail',
    component: ResultatenOverzicht,
    meta: { showTopbar: false, showNav: false, showBack: false, fullScreen: false, paddingbottom: false, paddingtop: false, transition: 'fade' },
  },
  {
    path: '/apparaten',
    name: 'apparaten',
    component: ApparatenView,
    meta: { showTopbar: true, showNav: true, showBack: false, fullScreen: false, paddingbottom: true, paddingtop: true, transition: 'fade' },
  },
  {
    path: '/historie',
    name: 'historie',
    component: AppHistorie,
    meta: { showTopbar: true, showNav: true, showBack: false, fullScreen: false, paddingbottom: true, paddingtop: true, transition: 'fade' },
  },
  {
    path: '/leaderboard',
    name: 'leaderboard',
    component: AppLeaderboard,
    meta: { showTopbar: true, showNav: true, showBack: false, fullScreen: false, paddingbottom: true, paddingtop: true, transition: 'fade' },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
