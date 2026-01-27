let confettiLoadPromise = null;

export const loadConfettiScript = () => {
  if (confettiLoadPromise) return confettiLoadPromise;

  confettiLoadPromise = new Promise((resolve) => {
    if (window.confetti) {
      resolve(true);
      return;
    }

    const script = document.createElement('script');
    let settled = false;

    const finish = (ok) => {
      if (settled) return;
      settled = true;
      resolve(!!ok);
    };

    script.src = '/vendor/canvas-confetti.min.js';
    script.onload = () => finish(true);
    script.onerror = () => finish(false);
    document.head.appendChild(script);

    setTimeout(() => finish(!!window.confetti), 1500);
  });

  return confettiLoadPromise;
};

export const fireConfetti = () => {
  const count = 200;
  const defaults = {
    origin: { y: 0.7 },
    zIndex: 9999,
  };

  function fire(particleRatio, opts) {
    const confetti = window.confetti;
    if (!confetti) {
      fireConfettiFallback();
      return;
    }

    confetti({
      ...defaults,
      ...opts,
      particleCount: Math.floor(count * particleRatio),
    });
  }

  // Van links
  fire(0.25, {
    spread: 26,
    startVelocity: 55,
    origin: { x: 0, y: 0.6 },
  });
  fire(0.2, {
    spread: 60,
    origin: { x: 0, y: 0.6 },
  });
  fire(0.35, {
    spread: 100,
    decay: 0.91,
    scalar: 0.8,
    origin: { x: 0, y: 0.6 },
  });
  fire(0.1, {
    spread: 120,
    startVelocity: 25,
    decay: 0.92,
    scalar: 1.2,
    origin: { x: 0, y: 0.6 },
  });
  fire(0.1, {
    spread: 120,
    startVelocity: 45,
    origin: { x: 0, y: 0.6 },
  });

  // Van rechts
  fire(0.25, {
    spread: 26,
    startVelocity: 55,
    origin: { x: 1, y: 0.6 },
  });
  fire(0.2, {
    spread: 60,
    origin: { x: 1, y: 0.6 },
  });
  fire(0.35, {
    spread: 100,
    decay: 0.91,
    scalar: 0.8,
    origin: { x: 1, y: 0.6 },
  });
  fire(0.1, {
    spread: 120,
    startVelocity: 25,
    decay: 0.92,
    scalar: 1.2,
    origin: { x: 1, y: 0.6 },
  });
  fire(0.1, {
    spread: 120,
    startVelocity: 45,
    origin: { x: 1, y: 0.6 },
  });
};

export const playCelebrationSound = () => {
  const audio = new Audio('/images/sounds/1gift-confetti-447240.mp3');
  audio.volume = 0.5;

  const playPromise = audio.play();

  if (playPromise !== undefined) {
    playPromise.catch(() => {
      const playOnInteraction = () => {
        const newAudio = new Audio('/images/sounds/1gift-confetti-447240.mp3');
        newAudio.volume = 0.5;
        newAudio.play().catch((err) => console.log('Audio afspelen mislukt:', err));
        document.removeEventListener('click', playOnInteraction);
        document.removeEventListener('keydown', playOnInteraction);
        document.removeEventListener('touchstart', playOnInteraction);
      };

      document.addEventListener('click', playOnInteraction, { once: true });
      document.addEventListener('keydown', playOnInteraction, { once: true });
      document.addEventListener('touchstart', playOnInteraction, { once: true });
    });
  }
};

function ensureFallbackStyle() {
  if (document.getElementById('bm-confetti-fallback-style')) return;
  const style = document.createElement('style');
  style.id = 'bm-confetti-fallback-style';
  style.textContent = `
    .bm-confetti {
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 9999;
      overflow: hidden;
    }
    .bm-confetti__piece {
      position: absolute;
      top: -10%;
      width: 8px;
      height: 12px;
      opacity: 0.9;
      animation-name: bm-confetti-fall;
      animation-timing-function: linear;
      animation-fill-mode: forwards;
    }
    @keyframes bm-confetti-fall {
      0% {
        transform: translate3d(0, -10%, 0) rotate(0deg);
        opacity: 1;
      }
      100% {
        transform: translate3d(var(--drift), 110%, 0) rotate(540deg);
        opacity: 0;
      }
    }
  `;
  document.head.appendChild(style);
}

function fireConfettiFallback() {
  if (document.getElementById('bm-confetti-fallback')) return;
  ensureFallbackStyle();

  const container = document.createElement('div');
  container.id = 'bm-confetti-fallback';
  container.className = 'bm-confetti';

  const colors = ['#ff3b30', '#ffcc00', '#34c759', '#0a84ff', '#ff2d55', '#bf5af2'];
  const count = 80;

  for (let i = 0; i < count; i += 1) {
    const piece = document.createElement('div');
    piece.className = 'bm-confetti__piece';
    piece.style.left = `${Math.random() * 100}%`;
    piece.style.backgroundColor = colors[i % colors.length];
    piece.style.setProperty('--drift', `${(Math.random() * 2 - 1) * 140}px`);
    piece.style.animationDuration = `${900 + Math.random() * 600}ms`;
    piece.style.animationDelay = `${Math.random() * 200}ms`;
    piece.style.borderRadius = Math.random() > 0.5 ? '2px' : '999px';
    container.appendChild(piece);
  }

  document.body.appendChild(container);
  setTimeout(() => {
    container.remove();
  }, 1800);
}
