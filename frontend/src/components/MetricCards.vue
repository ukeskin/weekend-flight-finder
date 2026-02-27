<template>
  <div class="metrics">
    <div class="metric-box">
      <div class="value">{{ stats ? stats.total.toLocaleString('tr-TR') : '—' }}</div>
      <div class="label">Toplam Firsat</div>
    </div>
    <div class="metric-box">
      <div class="value">{{ stats && stats.cheapest ? formatPrice(stats.cheapest) : '—' }}</div>
      <div class="label">En Ucuz</div>
    </div>
    <div class="metric-box">
      <div class="value">{{ stats && stats.average ? formatPrice(stats.average) : '—' }}</div>
      <div class="label">Ort. Fiyat</div>
    </div>
    <div class="metric-box">
      <div class="value">{{ stats ? stats.destinations : '0' }}</div>
      <div class="label">Destinasyon</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchStats } from '../api.js'

const props = defineProps({ filters: Object })
const stats = ref(null)

function formatPrice(val) {
  return '₺' + Math.round(val).toLocaleString('tr-TR')
}

onMounted(async () => {
  stats.value = await fetchStats(props.filters)
})
</script>
