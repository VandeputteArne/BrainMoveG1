<template>
  <div class="sport-card mb-8">
    <div class="h-64">
      <apexchart width="100%" height="100%" type="line" :options="options" :series="series" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import VueApexCharts from 'vue3-apexcharts';

defineOptions({ components: { apexchart: VueApexCharts } });

type ResultA = { round?: number; time?: number };
type ResultB = { status: 'correct' | 'early' | 'missed'; reactionTime?: number };

const props = defineProps<{
  results: (ResultA | ResultB)[];
  averageTime: number;
}>();

// normalize incoming data to { round, time } where time is a number in seconds or null
const chartData = computed(() =>
  props.results.map((r, i) => {
    // shape A: { round, time }
    if ((r as ResultA).time !== undefined) {
      return { round: (r as ResultA).round ?? i + 1, time: (r as ResultA).time ?? null };
    }
    // shape B: { status, reactionTime }
    const rb = r as ResultB;
    return { round: i + 1, time: rb.status === 'correct' ? rb.reactionTime ?? null : null };
  })
);

// Apex verwacht series als array van {x, y}
const series = computed(() => [
  {
    name: 'Reactietijd',
    data: chartData.value.map((p) => ({ x: p.round, y: p.time })),
  },
]);

const options = computed(() => ({
  chart: {
    toolbar: { show: false },
    zoom: { enabled: false },
  },
  stroke: {
    width: 3,
    curve: 'smooth',
  },
  markers: {
    size: 5,
    hover: { size: 8 },
  },
  grid: {
    strokeDashArray: 3,
  },
  xaxis: {
    title: { text: '' },
    labels: { style: { fontSize: '12px' } },
  },
  yaxis: {
    labels: { style: { fontSize: '12px' } },
  },
  tooltip: {
    y: {
      formatter: (val: number) => (val == null ? '-' : `${val.toFixed(2)} s`),
    },
    x: { formatter: (val: number) => `Ronde ${val}` },
  },
  // dit is jouw ReferenceLine (gemiddelde)
  annotations: {
    yaxis: [
      {
        y: props.averageTime,
        borderColor: 'hsl(var(--primary))',
        strokeDashArray: 5,
        label: {
          text: `Gem: ${props.averageTime.toFixed(2)} s`,
          style: {
            background: 'transparent',
            color: 'hsl(var(--muted-foreground))',
            fontSize: '11px',
          },
        },
      },
    ],
  },
}));
</script>
