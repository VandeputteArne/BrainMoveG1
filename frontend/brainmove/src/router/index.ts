import { createRouter, createWebHistory } from 'vue-router';
import OnboardingView from '../views/onboarding/OnboardingView.vue';

const routes = [
  {
    path: '/',
    name: 'onboarding',
    component: OnboardingView,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
