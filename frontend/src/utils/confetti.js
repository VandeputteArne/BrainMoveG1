export const loadConfettiScript = () => {
  return new Promise((resolve) => {
    if (window.confetti) {
      resolve();
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.2/dist/confetti.browser.min.js';
    script.onload = resolve;
    document.head.appendChild(script);
  });
};

export const fireConfetti = () => {
  const count = 200;
  const defaults = {
    origin: { y: 0.7 },
    zIndex: 9999,
  };

  function fire(particleRatio, opts) {
    const confetti = window.confetti;
    if (!confetti) return;

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

  // Probeer af te spelen, ook bij refresh
  const playPromise = audio.play();

  if (playPromise !== undefined) {
    playPromise.catch(() => {
      // Als autoplay geblokkeerd is, speel dan af bij eerste interactie
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
