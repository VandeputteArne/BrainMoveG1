<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

import { Timer, OctagonX } from 'lucide-vue-next';

const countdown = ref(3);
const showCountdown = ref(true);

onMounted(async () => {
  for (let i = 3; i >= 1; i--) {
    countdown.value = i;
    if (i === 1) {
      try {
        await fetch('http://10.42.0.1:8000/games/1/play', { method: 'GET' });
      } catch (e) {
        // ignore network/CORS errors for this signal
      }
    }
    await new Promise((r) => setTimeout(r, 700));
  }
  showCountdown.value = false;
});

const router = useRouter();

function goBack() {
  if (window.history.length > 1) router.back();
  else router.push('/games');
}
</script>

<template>
  <div v-if="showCountdown" class="c-countdown" aria-hidden="true">
    <div class="c-countdown__number">{{ countdown }}</div>
    <p class="c-countdown__text">Maak je klaar...</p>
  </div>

  <div v-else class="c-game">
    <div class="c-game__top">
      <button class="c-game__close" type="button" @click="goBack" aria-label="Sluit het spel">
        <span class="c-game__span"><OctagonX class="c-game__close-icon" /></span> stop
      </button>
      <p class="c-game__timer">
        <span class="c-game__span"><Timer class="c-game__timer-icon" /></span>10:22:00
      </p>
    </div>

    <div class="c-game__bot">
      <div class="c-game__color" style="background-color: red"></div>

      <div class="c-game__round">
        <h3>Ronde 1 / 5</h3>
        <div class="c-game__progressbar">
          <div class="c-game__progressbar-fill" style="width: 20%"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.c-countdown {
  position: fixed;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  inset: 0;
  background: var(--gray-90);
  z-index: 1200;

  .c-countdown__number {
    color: white;
    font-weight: 700;
    font-size: 4rem;
    padding: 0rem 1rem;
    border-radius: 0.5rem;
    animation: pop 0.45s ease forwards;
    user-select: none;
  }

  .c-countdown__text {
    margin-top: 1rem;
    color: var(--color-white);
    font-size: 1.5rem;
    user-select: none;
  }
}

.c-game {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;

  .c-game__top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem 0.75rem;
  }

  .c-game__close {
    display: flex;
    align-items: center;
    gap: 0.3125rem;
    text-decoration: none;
    color: var(--gray-80);
    background-color: transparent;
    border: none;
    cursor: pointer;

    .c-game__close-icon {
      width: 1.5rem;
      height: 1.5rem;
    }
  }

  .c-game__span {
    display: flex;
    align-items: end;
    width: 1.5rem;
    height: 1.5rem;
  }

  .c-game__timer {
    display: flex;
    align-items: end;
    gap: 0.3125rem;
    color: var(--gray-80);

    .c-game__timer-icon {
      width: 1.5rem;
      height: 1.5rem;
    }
  }

  .c-game__bot {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .c-game__color {
    width: 100%;
    height: 100%;
  }

  .c-game__round {
    position: absolute;
    bottom: 2rem;
    max-width: 12.5rem;
    left: 50%;
    transform: translateX(-50%);
    width: 90%;
    color: var(--color-white);
    text-align: center;

    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .c-game__progressbar {
    width: 100%;
    height: 1.5625rem;
    background: var(--color-white);
    border-radius: var(--radius-40);
    margin-top: 0.5rem;
    overflow: hidden;
    padding: 0.1875rem;
  }

  .c-game__progressbar-fill {
    height: 100%;
    background: var(--blue-100);
    border-radius: var(--radius-40);
    transition: width 0.3s ease;
  }
}

@keyframes pop {
  from {
    transform: scale(0.35);
    opacity: 0;
    filter: blur(2px);
  }
  60% {
    transform: scale(1.08);
    opacity: 1;
    filter: blur(0);
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
