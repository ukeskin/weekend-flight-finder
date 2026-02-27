<template>
  <div v-if="loading" class="loading">
    <div class="loading-spinner"></div>
    <div>Yukleniyor...</div>
  </div>
  <div v-else class="chart-container">
    <v-chart :option="chartOption" autoresize style="height: 500px;" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { use } from 'echarts/core'
import { HeatmapChart } from 'echarts/charts'
import { GridComponent, VisualMapComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import { fetchHeatmap } from '../api.js'

use([HeatmapChart, GridComponent, VisualMapComponent, TooltipComponent, CanvasRenderer])

const props = defineProps({ filters: Object })
const loading = ref(true)
const heatmapData = ref([])

const chartOption = computed(() => {
  const cities = [...new Set(heatmapData.value.map(d => d.city))].sort()
  const weekends = [...new Set(heatmapData.value.map(d => d.weekend))].sort()

  const data = heatmapData.value.map(d => [
    weekends.indexOf(d.weekend),
    cities.indexOf(d.city),
    d.min_price,
  ])

  const prices = heatmapData.value.map(d => d.min_price)
  const minP = Math.min(...prices, 0)
  const maxP = Math.max(...prices, 1)

  return {
    tooltip: {
      formatter(params) {
        const [wi, ci, price] = params.data
        return `${cities[ci]}<br>${weekends[wi]}<br>₺${Math.round(price).toLocaleString('tr-TR')}`
      },
    },
    grid: { left: 120, right: 60, top: 10, bottom: 60 },
    xAxis: {
      type: 'category',
      data: weekends,
      axisLabel: { color: '#94a3b8', rotate: 45, fontSize: 11 },
      splitArea: { show: true, areaStyle: { color: ['rgba(30,41,59,0.3)', 'rgba(30,41,59,0.6)'] } },
    },
    yAxis: {
      type: 'category',
      data: cities,
      axisLabel: { color: '#94a3b8', fontSize: 11 },
      splitArea: { show: true, areaStyle: { color: ['rgba(30,41,59,0.3)', 'rgba(30,41,59,0.6)'] } },
    },
    visualMap: {
      min: minP,
      max: maxP,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      inRange: { color: ['#4ade80', '#fbbf24', '#ef4444'] },
      textStyle: { color: '#94a3b8' },
      formatter: (val) => '₺' + Math.round(val).toLocaleString('tr-TR'),
    },
    series: [{
      type: 'heatmap',
      data,
      label: { show: false },
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' },
      },
    }],
  }
})

onMounted(async () => {
  try {
    heatmapData.value = await fetchHeatmap(props.filters)
  } finally {
    loading.value = false
  }
})
</script>
