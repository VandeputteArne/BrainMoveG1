import { onMounted, onUnmounted, watch, nextTick } from 'vue';

export function useScrollReveal(containerRef, watchSource) {
  let observer = null;

  function cleanup() {
    if (observer) {
      observer.disconnect();
      observer = null;
    }
  }

  function setup() {
    cleanup();
    if (!containerRef?.value) return;
    const items = containerRef.value.querySelectorAll('[data-reveal]');
    if (!items.length) return;

    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-visible');
          observer?.unobserve(entry.target);
        });
      },
      { threshold: 0, rootMargin: '0px 0px -5% 0px' },
    );

    items.forEach((el, index) => {
      const delay = Math.min(index * 70, 420);
      el.style.setProperty('--reveal-delay', `${delay}ms`);
      observer.observe(el);
    });
  }

  onMounted(async () => {
    await nextTick();
    setup();
  });

  if (watchSource) {
    watch(
      watchSource,
      async () => {
        await nextTick();
        setup();
      },
      { deep: true },
    );
  }

  onUnmounted(() => {
    cleanup();
  });

  return { refresh: setup };
}
