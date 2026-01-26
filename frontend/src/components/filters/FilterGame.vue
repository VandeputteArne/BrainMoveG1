<script setup>
import { Gamepad2, ChevronDown } from 'lucide-vue-next';
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { getApiUrl } from '../../config/api.js';

const gameoptions = ref([]);
const isOpen = ref(false);
const dropdownRef = ref(null);

const modelValue = defineModel();
const emit = defineEmits(['update:gameName']);

const selectedLabel = computed(() => {
  const match = gameoptions.value.find((opt) => String(opt.id) === String(modelValue.value));
  return match ? match.gametype : 'Kies gametype';
});

onMounted(async () => {
  const cachedGames = sessionStorage.getItem('gameFilters');
  if (cachedGames) {
    gameoptions.value = JSON.parse(cachedGames);
    // Set default to first game
    if (gameoptions.value.length > 0) {
      modelValue.value = gameoptions.value[0].id;
      emit('update:gameName', gameoptions.value[0].gametype);
    }
    return;
  }

  try {
    const res = await fetch(getApiUrl('games/filters'));
    const data = await res.json();

    gameoptions.value = data.map((game) => ({
      id: String(game.game_id),
      gametype: game.game_naam,
    }));

    sessionStorage.setItem('gameFilters', JSON.stringify(gameoptions.value));

    // Set default to first game
    if (gameoptions.value.length > 0) {
      modelValue.value = gameoptions.value[0].id;
      emit('update:gameName', gameoptions.value[0].gametype);
    }
  } catch (error) {
    console.error('Failed to fetch game filters:', error);
  }
});

function toggleDropdown() {
  isOpen.value = !isOpen.value;
}

function closeDropdown() {
  isOpen.value = false;
}

function selectOption(option) {
  modelValue.value = option.id;
  emit('update:gameName', option.gametype);
  closeDropdown();
}

function handleOutsideClick(event) {
  if (!dropdownRef.value) return;
  if (!dropdownRef.value.contains(event.target)) closeDropdown();
}

onMounted(() => {
  document.addEventListener('click', handleOutsideClick);
});

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick);
});
</script>

<template>
  <div class="c-filter-game">
    <p>Gametype</p>
    <div ref="dropdownRef" class="c-filter-game__filter">
      <Gamepad2 class="c-filter-game__icon" />
      <button type="button" class="c-filter-game__trigger" :aria-expanded="isOpen" aria-haspopup="listbox" @click="toggleDropdown" @keydown.escape="closeDropdown">
        <span class="c-filter-game__label">{{ selectedLabel }}</span>
        <ChevronDown class="c-filter-game__chevron" :class="{ 'is-open': isOpen }" />
      </button>
      <div v-if="isOpen" class="c-filter-game__menu" role="listbox" aria-label="Gametype">
        <button v-for="option in gameoptions" :key="option.id" type="button" class="c-filter-game__option" role="option" :aria-selected="String(option.id) === String(modelValue)" @click="selectOption(option)">
          {{ option.gametype }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.c-filter-game {
  display: flex;
  flex-direction: column;
  gap: 0.3125rem;
  font-size: 0.875rem;

  .c-filter-game__filter {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    border-radius: var(--radius-40);
    border: solid 1px var(--gray-40);
    padding: 0.5rem 0.625rem;
    cursor: pointer;
    position: relative;
  }

  .c-filter-game__icon {
    width: 1.25rem;
    height: 1.25rem;
    color: var(--blue-100);
  }

  .c-filter-game__trigger {
    all: unset;
    flex-grow: 1;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    width: 100%;
  }

  .c-filter-game__label {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .c-filter-game__chevron {
    width: 1rem;
    height: 1rem;
    color: var(--blue-100);
    transition: transform 0.2s ease;
  }

  .c-filter-game__chevron.is-open {
    transform: rotate(180deg);
  }

  .c-filter-game__menu {
    position: absolute;
    left: 0;
    right: 0;
    top: calc(100% + 0.375rem);
    background: var(--color-white);
    border: 1px solid var(--gray-40);
    border-radius: 0.75rem;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
    padding: 0.375rem;
    display: grid;
    gap: 0.25rem;
    z-index: 10;
  }

  .c-filter-game__option {
    all: unset;
    padding: 0.5rem 0.75rem;
    border-radius: 0.625rem;
    cursor: pointer;
    color: var(--gray-120);
  }

  .c-filter-game__option[aria-selected='true'] {
    background: var(--blue-10);
    color: var(--blue-120);
    font-weight: 600;
  }

  .c-filter-game__option:hover {
    background: var(--gray-10);
  }
}
</style>
