import { ref } from 'vue';
import { useRouter } from 'vue-router';

/**
 * Composable for game countdown (3, 2, 1, GO!)
 * @param {Object} options - Configuration options
 * @param {number} options.gameId - The game ID to signal backend
 * @param {Function} options.onComplete - Callback when countdown finishes
 * @returns {Object} countdown state and control functions
 */
export function useGameCountdown(options = {}) {
  const { gameId = null, onComplete = null } = options;
  const router = useRouter();

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
        const res = await fetch(`http://10.42.0.1:8000/games/${gameId}/play`, { method: 'GET' });

        if (res.ok) {
          const data = await res.json();
          console.log('Game start response:', data);

          if (data.status === 'already_running') {
            console.warn('Game is already running, redirecting to detail');
            showCountdown.value = false;
            router.push(`/games/${gameId}`);
            return;
          }
          if (data.status === 'missing_settings') {
            console.warn('Game settings are missing, redirecting to detail');
            showCountdown.value = false;
            router.push(`/games/${gameId}`);
            return;
          }
        } else if (res.status === 409) {
          // 409 Conflict - game already running
          const data = await res.json();
          console.warn('Game conflict (409):', data);
          showCountdown.value = false;
          router.push(`/games/${gameId}`);
          return;
        } else {
          console.warn('Game start failed with status:', res.status);
        }
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
