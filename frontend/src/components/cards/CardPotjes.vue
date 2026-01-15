<script setup>
const props = defineProps({
  kleur: String,
  status: Boolean,
});
</script>

<template>
  <div class="c-potje">
    <img :src="`/images/potjes/${props.kleur}.png`" :alt="`Potje ${props.kleur}`" class="c-potje__image" />
    <div class="c-potje__status-balk">
      <div :class="`c-potje__status ${props.status ? 'c-potje__status--online' : 'c-potje__status--offline'}`"></div>
      <h3 v-if="props.status">Online</h3>
      <h3 v-else>Offline</h3>
    </div>
  </div>
</template>

<style scoped>
.c-potje {
  width: 100%;
  padding: 0.875rem 1.875rem;

  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-20);
  border: solid 1px var(--blue-50);

  .c-potje__status-balk {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
  }

  .c-potje__status {
    width: 0.875rem;
    height: 0.875rem;
    border-radius: 100%;
  }

  .c-potje__status--online {
    background-color: var(--color-green);
  }

  .c-potje__status--offline {
    background-color: var(--color-red);
  }

  .c-potje__image {
    width: 80%;
    max-width: 10rem;
    height: auto;
  }
}
</style>
