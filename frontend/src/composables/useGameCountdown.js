import { ref } from 'vue';

/**
 * Composable for game countdown (3, 2, 1, GO!)
 * @param {Object} options - Configuration options
 * @param {number} options.gameId - The game ID to signal backend
 * @param {Function} options.onComplete - Callback when countdown finishes
 * @returns {Object} countdown state and control functions
 */
export function useGameCountdown(options = {}) {
  const { gameId = null, onComplete = null } = options;

  const countdown = ref(3);
  const showCountdown = ref(true);
  const countdownText = ref('');

  async function startCountdown() {
    showCountdown.value = true;

    for (let i = 3; i >= 1; i--) {
      countdown.value = i;
      countdownText.value = 'Maak je klaar...';
      await new Promise((r) => setTimeout(r, 700));
    }

    // Show "GO!" and signal backend
    countdown.value = 'GO!';
    countdownText.value = '';

    // Signal backend when showing GO! (if gameId provided)
    if (gameId) {
      try {
        await fetch(`http://10.42.0.1:8000/games/${gameId}/play`, { method: 'GET' });
      } catch (e) {
        console.warn('Failed to signal game start to backend:', e);
      }
    }

    await new Promise((r) => setTimeout(r, 500));

    // Hide countdown and trigger callback
    showCountdown.value = false;

    if (onComplete && typeof onComplete === 'function') {
      onComplete();
    }
  }

  return {
    countdown,
    showCountdown,
    countdownText,
    startCountdown,
  };
}
