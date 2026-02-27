<template>
  <aside class="sidebar">
    <Sidebar
      :destinations="destinations"
      :weekends="weekends"
      :filters="filters"
      @update:filters="onFiltersChange"
    />
  </aside>
  <main class="main-content">
    <h1>Hafta Sonu Ucus Bulucu</h1>
    <p class="subtitle">Istanbul'dan Avrupa'ya en uygun hafta sonu tatili firsatlari</p>

    <MetricCards :filters="filters" :key="filterKey" />

    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <BestDeals v-if="activeTab === 'deals'" :filters="filters" :key="'deals-' + filterKey" />
    <PriceHeatmap v-if="activeTab === 'heatmap'" :filters="filters" :key="'heatmap-' + filterKey" />
    <CityCompare v-if="activeTab === 'compare'" :filters="filters" :key="'compare-' + filterKey" />
    <DataTable v-if="activeTab === 'table'" :filters="filters" :key="'table-' + filterKey" />
  </main>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { fetchDestinations, fetchWeekends } from './api.js'
import Sidebar from './components/Sidebar.vue'
import MetricCards from './components/MetricCards.vue'
import BestDeals from './components/BestDeals.vue'
import PriceHeatmap from './components/PriceHeatmap.vue'
import CityCompare from './components/CityCompare.vue'
import DataTable from './components/DataTable.vue'

const destinations = ref([])
const weekends = ref([])
const activeTab = ref('deals')
const filters = ref({
  weekendStart: '',
  weekendEnd: '',
  cities: [],
  maxPrice: null,
  directOnly: false,
  origin: 'all',
})

const tabs = [
  { id: 'deals', label: 'En Iyi Firsatlar' },
  { id: 'heatmap', label: 'Fiyat Haritasi' },
  { id: 'compare', label: 'Karsilastirma' },
  { id: 'table', label: 'Detay Tablosu' },
]

const filterKey = computed(() => JSON.stringify(filters.value))

function onFiltersChange(newFilters) {
  filters.value = { ...newFilters }
}

onMounted(async () => {
  const [dests, wkends] = await Promise.all([fetchDestinations(), fetchWeekends()])
  destinations.value = dests
  weekends.value = wkends
  if (wkends.length >= 2) {
    filters.value.weekendStart = wkends[0]
    filters.value.weekendEnd = wkends[wkends.length - 1]
  }
})
</script>
