<template>
  <div v-if="loading" class="loading">
    <div class="loading-spinner"></div>
    <div>Yukleniyor...</div>
  </div>
  <div v-else>
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th v-for="col in columns" :key="col.key" @click="toggleSort(col.key)">
              {{ col.label }}
              <template v-if="sortBy === col.key">{{ sortOrder === 'asc' ? ' ▲' : ' ▼' }}</template>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="trip in trips" :key="trip.id">
            <td>{{ trip.origin }}</td>
            <td>{{ trip.destination_city }}</td>
            <td>{{ trip.destination_country }}</td>
            <td>{{ trip.weekend }}</td>
            <td>{{ trip.outbound?.airline }}</td>
            <td>{{ trip.outbound?.departure_time }}</td>
            <td>{{ transferText(trip.outbound?.stops) }}</td>
            <td>{{ formatPrice(trip.outbound?.price) }}</td>
            <td>{{ trip.return_leg?.airline }}</td>
            <td>{{ trip.return_leg?.departure_time }}</td>
            <td>{{ transferText(trip.return_leg?.stops) }}</td>
            <td>{{ formatPrice(trip.return_leg?.price) }}</td>
            <td style="color: var(--green); font-weight: 600;">{{ formatPrice(trip.total_price) }}</td>
            <td><span class="deal-score">{{ trip.score }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="table-footer">
      <span>Toplam {{ totalResults.toLocaleString('tr-TR') }} sonuc</span>
      <div class="pagination">
        <button :disabled="page <= 1" @click="goPage(page - 1)">Onceki</button>
        <span>{{ page }} / {{ totalPages }}</span>
        <button :disabled="page >= totalPages" @click="goPage(page + 1)">Sonraki</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchTrips } from '../api.js'

const props = defineProps({ filters: Object })

const trips = ref([])
const loading = ref(true)
const page = ref(1)
const totalResults = ref(0)
const totalPages = ref(1)
const sortBy = ref('score')
const sortOrder = ref('desc')

const columns = [
  { key: 'origin', label: 'Kalkis' },
  { key: 'destination_city', label: 'Sehir' },
  { key: 'destination_country', label: 'Ulke' },
  { key: 'weekend', label: 'Hafta Sonu' },
  { key: 'outbound_airline', label: 'Gidis Havayolu' },
  { key: 'outbound_departure', label: 'Gidis Kalkis' },
  { key: 'outbound_stops', label: 'Gidis Aktarma' },
  { key: 'outbound_price', label: 'Gidis Fiyat' },
  { key: 'return_airline', label: 'Donus Havayolu' },
  { key: 'return_departure', label: 'Donus Kalkis' },
  { key: 'return_stops', label: 'Donus Aktarma' },
  { key: 'return_price', label: 'Donus Fiyat' },
  { key: 'total_price', label: 'Toplam Fiyat' },
  { key: 'score', label: 'Skor' },
]

function transferText(n) {
  if (n === 0) return 'Direkt'
  if (n === undefined || n === null) return ''
  return `${n} aktarma`
}

function formatPrice(val) {
  if (!val && val !== 0) return ''
  return '₺' + Math.round(val).toLocaleString('tr-TR')
}

async function loadData() {
  loading.value = true
  try {
    const result = await fetchTrips(props.filters, page.value, 50, sortBy.value, sortOrder.value)
    trips.value = result.data
    totalResults.value = result.total
    totalPages.value = result.total_pages
  } finally {
    loading.value = false
  }
}

function toggleSort(key) {
  const sortableKeys = ['score', 'total_price', 'total_duration_minutes', 'weekend']
  const map = {
    score: 'score',
    total_price: 'total_price',
    total_duration_minutes: 'total_duration_minutes',
    weekend: 'weekend',
  }
  const backendKey = map[key]
  if (!sortableKeys.includes(backendKey)) return
  if (sortBy.value === backendKey) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = backendKey
    sortOrder.value = backendKey === 'total_price' || backendKey === 'weekend' ? 'asc' : 'desc'
  }
  page.value = 1
  loadData()
}

function goPage(p) {
  page.value = p
  loadData()
}

onMounted(loadData)
</script>
