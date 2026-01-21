import { ref, onMounted, onUnmounted } from 'vue';

/**
 * Composable for responsive breakpoint detection
 * @param {number} breakpoint - Breakpoint in pixels (default: 768)
 * @returns {Object} - { isMobile: Ref<boolean> }
 */
export function useMediaQuery(breakpoint = 768) {
  const isMobile = ref(window.innerWidth < breakpoint);

  const updateIsMobile = () => {
    isMobile.value = window.innerWidth < breakpoint;
  };

  onMounted(() => {
    window.addEventListener('resize', updateIsMobile);
  });

  onUnmounted(() => {
    window.removeEventListener('resize', updateIsMobile);
  });

  return { isMobile };
}
