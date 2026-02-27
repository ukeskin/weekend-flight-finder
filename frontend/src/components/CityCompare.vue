<template>
  <div v-if="loading" class="loading">
    <div class="loading-spinner"></div>
    <div>Yukleniyor...</div>
  </div>
  <div v-else>
    <div class="chart-container">
      <v-chart :option="chartOption" autoresize style="height: 450px;" />
    </div>

    <div class="city-tables">
      <div>
        <h4>En Ucuz 10 Destinasyon</h4>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Sehir</th>
                <th>Min Fiyat</th>
                <th>Ort Fiyat</th>
                <th>Secenek</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in cheapest10" :key="c.city">
                <td>{{ c.city }}</td>
                <td>₺{{ Math.round(c.min_price).toLocaleString('tr-TR') }}</td>
                <td>₺{{ Math.round(c.avg_price).toLocaleString('tr-TR') }}</td>
                <td>{{ c.count }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div>
        <h4>En Cok Secenek</h4>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Sehir</th>
                <th>Min Fiyat</th>
                <th>Ort Fiyat</th>
                <th>Secenek</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in mostOptions10" :key="c.city">
                <td>{{ c.city }}</td>
                <td>₺{{ Math.round(c.min_price).toLocaleString('tr-TR') }}</td>
                <td>₺{{ Math.round(c.avg_price).toLocaleString('tr-TR') }}</td>
                <td>{{ c.count }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import { fetchCityCompare } from '../api.js'

use([BarChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps({ filters: Object })
const loading = ref(true)
const cities = ref([])

const cheapest10 = computed(() => [...cities.value].sort((a, b) => a.min_price - b.min_price).slice(0, 10))
const mostOptions10 = computed(() => [...cities.value].sort((a, b) => b.count - a.count).slice(0, 10))

const chartOption = computed(() => {
  const sorted = [...cities.value].sort((a, b) => a.min_price - b.min_price)
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter(params) {
        const city = params[0].name
        return params.map(p => `${p.seriesName}: ₺${Math.round(p.value).toLocaleString('tr-TR')}`).join('<br>')
      },
    },
    legend: { data: ['En Ucuz', 'Ortalama'], textStyle: { color: '#94a3b8' } },
    grid: { left: 60, right: 20, bottom: 80 },
    xAxis: {
      type: 'category',
      data: sorted.map(c => c.city),
      axisLabel: { color: '#94a3b8', rotate: 45, fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#94a3b8', formatter: val => '₺' + (val / 1000).toFixed(0) + 'k' },
    },
    series: [
      { name: 'En Ucuz', type: 'bar', data: sorted.map(c => c.min_price), itemStyle: { color: '#4ade80' } },
      { name: 'Ortalama', type: 'bar', data: sorted.map(c => c.avg_price), itemStyle: { color: '#38bdf8', opacity: 0.6 } },
    ],
  }
})

onMounted(async () => {
  try {
    cities.value = await fetchCityCompare(props.filters)
  } finally {
    loading.value = false
  }
})
</script>
