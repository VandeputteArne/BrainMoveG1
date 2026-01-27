<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue';
import { tryResumeIfExists } from '../../services/sound.js';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  durationMs: { type: Number, default: 2000 },
  title: { type: String, default: 'Start' },
  text: { type: String, default: '' },
  autoResume: { type: Boolean, default: true },
  overlayClass: { type: String, default: 'c-game__intro' },
  contentClass: { type: String, default: 'c-game__intro-content' },
  ariaLabel: { type: String, default: 'Start' },
});

const emit = defineEmits(['update:modelValue', 'done', 'exiting']);
const root = ref(null);
const hiding = ref(false);
let timer = null;

function clearTimer() {
  if (timer) {
    clearTimeout(timer);
    timer = null;
  }
}

async function startAutoTimer() {
  clearTimer();
  if (props.autoResume) {
    try {
      await tryResumeIfExists();
    } catch (e) {}
  }
  timer = setTimeout(() => {
    initiateExit();
  }, props.durationMs);
}

function initiateExit() {
  clearTimer();
  if (hiding.value) return;
  emit('exiting');
  hiding.value = true;
  const el = root.value;
  if (!el) {
    finishExit();
    return;
  }

  const onTransitionEnd = (ev) => {
    if (ev.target === el && (ev.propertyName === 'opacity' || ev.propertyName === 'visibility')) {
      el.removeEventListener('transitionend', onTransitionEnd);
      finishExit();
    }
  };
  el.addEventListener('transitionend', onTransitionEnd);
}

function finishExit() {
  hiding.value = false;
  emit('update:modelValue', false);
  emit('done');
}

function onClickStart() {
  initiateExit();
}

watch(
  () => props.modelValue,
  (v) => {
    if (v) {
      hiding.value = false;
      startAutoTimer();
    } else {
      initiateExit();
    }
  },
);

onMounted(() => {
  if (props.modelValue) startAutoTimer();
});

onUnmounted(() => {
  clearTimer();
});
</script>

<template>
  <div ref="root" :class="[overlayClass, { 'is-hidden': hiding, 'is-visible': !hiding }]" @click.self="onClickStart" role="button" :aria-label="ariaLabel">
    <div :class="contentClass">
      <h2 class="c-intro__title">{{ title }}</h2>
      <p v-if="text" class="c-intro__text">{{ text }}</p>
      <slot />
    </div>
  </div>
</template>

<style scoped>
.c-game__intro,
.c-game-memory__intro {
  position: fixed;
  inset: 0;
  height: var(--app-height, 100vh);
  min-height: var(--app-height, 100vh);
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  opacity: 1;
  transition:
    opacity 260ms ease,
    visibility 260ms ease;
}
.c-game__intro.is-hidden,
.c-game-memory__intro.is-hidden {
  opacity: 0;
  pointer-events: none;
}
.c-game__intro-content,
.c-game-memory__intro-content {
  text-align: center;
  color: white;
  padding: 2rem;
}

.c-intro__title {
  margin: 0;
  margin-bottom: 1rem;
  font-size: 2rem;
  opacity: 0;
  transform: translateY(10px);
}

.c-intro__text {
  margin: 0;
  font-size: 1.2rem;
  opacity: 0;
  transform: translateY(12px);
}

.c-game__intro.is-visible .c-intro__title,
.c-game-memory__intro.is-visible .c-intro__title {
  animation: intro-rise 420ms ease-out forwards;
}

.c-game__intro.is-visible .c-intro__text,
.c-game-memory__intro.is-visible .c-intro__text {
  animation: intro-rise 520ms ease-out forwards;
  animation-delay: 80ms;
}

@media (prefers-reduced-motion: reduce) {
  .c-intro__title,
  .c-intro__text {
    animation: none !important;
    opacity: 1;
    transform: none;
  }
}

@keyframes intro-rise {
  0% {
    opacity: 0;
    transform: translateY(12px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
