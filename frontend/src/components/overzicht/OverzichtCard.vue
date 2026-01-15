<script setup>
import { defineProps } from 'vue';
import { Download, Clock, Zap, Trophy, Disc2, ChartNoAxesCombined } from 'lucide-vue-next';

const props = defineProps({
  waarde: {
    type: [Object, Number, String],
  },
  label: {
    type: String,
  },
});
</script>

<template>
  <div class="c-overzicht__stat">
    <div class="c-overzicht__stat-header">
      <p class="label">{{ props.label }}</p>
      <span class="c-overzicht__stat-icon">
        <Clock class="c-overzicht__stat-svg" v-if="props.label == 'Gemiddelde'" />
        <Trophy class="c-overzicht__stat-svg" v-else-if="props.label == 'Beste'" />
        <Zap class="c-overzicht__stat-svg" v-else-if="props.label == 'Ranking'" />
        <Disc2 class="c-overzicht__stat-svg" v-else-if="props.label == 'Exactheid'" />
      </span>
    </div>
    <h2>
      <template v-if="props.label === 'Gemiddelde' || props.label === 'Beste'">{{ props.waarde }}s</template>
      <template v-else-if="props.label === 'Ranking'">#{{ props.waarde }}</template>
      <template v-else-if="props.label === 'Exactheid'">{{ props.waarde }}%</template>
      <template v-else>{{ props.waarde }}</template>
    </h2>
  </div>
</template>

<style scoped>
.c-overzicht__stat {
  padding: 0.8125rem;
  border-radius: var(--radius-20);
  border: 1px solid var(--gray-30);

  .c-overzicht__stat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.375rem;
  }

  .c-overzicht__stat-icon {
    display: flex;
    align-items: center;
    width: 1.25rem;
    height: 1.25rem;
    color: var(--blue-100);
  }

  .c-overzicht__stat-svg {
    width: 100%;
    height: 100%;
    stroke-width: 0.175rem;
  }
}
</style>
