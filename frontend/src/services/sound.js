let audioContext = null;
let audioEnabled = false;

function ensureContext() {
  if (!audioContext) audioContext = new (window.AudioContext || window.webkitAudioContext)();
  return audioContext;
}

export async function enableAudio() {
  try {
    const ctx = ensureContext();
    if (ctx.state === 'suspended') await ctx.resume();
    audioEnabled = ctx.state === 'running';
    // small test sound to confirm
    if (audioEnabled) playFlute(0.12, 220);
    return audioEnabled;
  } catch (e) {
    audioEnabled = false;
    return false;
  }
}

export function isAudioEnabled() {
  return !!(audioEnabled && audioContext && audioContext.state === 'running');
}

export function playFlute(duration = 0.14, frequency = 261.63) {
  try {
    if (!audioContext) return false;
    if (audioContext.state !== 'running') return false;
    const now = audioContext.currentTime;

    const o1 = audioContext.createOscillator();
    const o2 = audioContext.createOscillator();
    const lfo = audioContext.createOscillator();
    const lfoGain = audioContext.createGain();
    const filter = audioContext.createBiquadFilter();
    const env = audioContext.createGain();

    o1.type = 'sine';
    o2.type = 'sine';
    o1.frequency.setValueAtTime(frequency, now);
    o2.frequency.setValueAtTime(frequency * 1.01, now);

    lfo.type = 'sine';
    lfo.frequency.setValueAtTime(5.5, now);
    lfoGain.gain.setValueAtTime(frequency * 0.0025, now);
    lfo.connect(lfoGain);
    lfoGain.connect(o1.frequency);
    lfoGain.connect(o2.frequency);

    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(Math.max(1200, frequency * 6), now);
    filter.Q.setValueAtTime(0.7, now);

    env.gain.setValueAtTime(0.0001, now);
    env.gain.linearRampToValueAtTime(0.28, now + 0.02);
    env.gain.exponentialRampToValueAtTime(0.0001, now + duration);

    o1.connect(filter);
    o2.connect(filter);
    filter.connect(env);
    env.connect(audioContext.destination);

    lfo.start(now);
    o1.start(now);
    o2.start(now);

    try {
      o1.frequency.exponentialRampToValueAtTime(Math.max(40, frequency * 0.94), now + duration);
      o2.frequency.exponentialRampToValueAtTime(Math.max(40, frequency * 0.96), now + duration);
    } catch (e) {}

    o1.stop(now + duration + 0.03);
    o2.stop(now + duration + 0.03);
    lfo.stop(now + duration + 0.03);
    return true;
  } catch (e) {
    return false;
  }
}

// Optional: try to resume if context exists (no creation). Returns boolean.
export async function tryResumeIfExists() {
  if (!audioContext) return false;
  try {
    if (audioContext.state === 'suspended') await audioContext.resume();
    audioEnabled = audioContext.state === 'running';
    return audioEnabled;
  } catch (e) {
    return false;
  }
}

// Expose for debug if needed
export function _getContext() {
  return audioContext;
}
