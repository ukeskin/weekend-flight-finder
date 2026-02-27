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

    <DataTable :filters="filters" :key="'table-' + filterKey" />
  </main>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { fetchDestinations, fetchWeekends } from './api.js'
import Sidebar from './components/Sidebar.vue'
import DataTable from './components/DataTable.vue'

const destinations = ref([])
const weekends = ref([])
const filters = ref({
  weekendStart: '',
  weekendEnd: '',
  destinations: [],
  maxPrice: null,
  directOnly: false,
})

const filterKey = computed(() => JSON.stringify(filters.value))

function onFiltersChange(newFilters) {
  filters.value = { ...newFilters }
}

onMounted(async () => {
  const [dests, wkends] = await Promise.all([fetchDestinations(), fetchWeekends()])
  destinations.value = dests
  weekends.value = wkends
  if (wkends.length >= 1) {
    filters.value.weekendStart = wkends[0]
    filters.value.weekendEnd = wkends[0]
  }
  if (dests.length >= 1) {
    filters.value.destinations = dests.slice(0, 3).map(d => d.code)
  }
})
</script>
