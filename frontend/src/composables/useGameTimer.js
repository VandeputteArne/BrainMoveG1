import { ref, computed } from 'vue';

export function useGameTimer() {
  const elapsedSeconds = ref(0);
  let timerInterval = null;

  const formattedTime = computed(() => {
    const total = elapsedSeconds.value;
    const hours = Math.floor(total / 3600);
    const minutes = Math.floor((total % 3600) / 60);
    const seconds = total % 60;
    if (hours > 0) {
      return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  });

  function startTimer() {
    if (timerInterval) return;
    elapsedSeconds.value = 0;
    timerInterval = setInterval(() => {
      elapsedSeconds.value += 1;
    }, 1000);
  }

  function stopTimer() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  }

  return {
    elapsedSeconds,
    formattedTime,
    startTimer,
    stopTimer,
  };
}
