import { createApp } from 'vue';
import './style.css';
import App from './App.vue';
import router from './router';

function setAppHeight() {
  const height = window.innerHeight;
  document.documentElement.style.setProperty('--app-height', `${height}px`);
}

setAppHeight();
window.addEventListener('resize', setAppHeight);
window.addEventListener('orientationchange', setAppHeight);
if (window.visualViewport) {
  window.visualViewport.addEventListener('resize', setAppHeight);
  window.visualViewport.addEventListener('scroll', setAppHeight);
}

function preloadImages(sources: string[]) {
  sources.forEach((src: string) => {
    const img = new Image();
    img.decoding = 'async';
    img.src = src;
  });
}

preloadImages(['/images/training-afgerond.png']);

createApp(App).use(router).mount('#app');
