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
            <td>{{ trip.kalkis_havalimani }}</td>
            <td>{{ trip.varis_sehir }}</td>
            <td>{{ trip.varis_ulke }}</td>
            <td>{{ trip.hafta_sonu }}</td>
            <td>{{ trip.havayolu_gidis }}</td>
            <td>{{ trip.kalkis_saati_gidis }}</td>
            <td>{{ transferText(trip.aktarma_int_gidis) }}</td>
            <td>{{ trip.fiyat_tl_gidis ? '₺' + Math.round(trip.fiyat_tl_gidis).toLocaleString('tr-TR') : '' }}</td>
            <td>{{ trip.havayolu_donus }}</td>
            <td>{{ trip.kalkis_saati_donus }}</td>
            <td>{{ transferText(trip.aktarma_int_donus) }}</td>
            <td>{{ trip.fiyat_tl_donus ? '₺' + Math.round(trip.fiyat_tl_donus).toLocaleString('tr-TR') : '' }}</td>
            <td style="color: var(--green); font-weight: 600;">₺{{ Math.round(trip.toplam_fiyat).toLocaleString('tr-TR') }}</td>
            <td><span class="deal-score">{{ trip.skor }}</span></td>
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
const sortBy = ref('skor')
const sortOrder = ref('desc')

const columns = [
  { key: 'kalkis_havalimani', label: 'Kalkis' },
  { key: 'varis_sehir', label: 'Sehir' },
  { key: 'varis_ulke', label: 'Ulke' },
  { key: 'hafta_sonu', label: 'Hafta Sonu' },
  { key: 'havayolu_gidis', label: 'Gidis Havayolu' },
  { key: 'kalkis_saati_gidis', label: 'Gidis Kalkis' },
  { key: 'aktarma_int_gidis', label: 'Gidis Aktarma' },
  { key: 'fiyat_tl_gidis', label: 'Gidis Fiyat' },
  { key: 'havayolu_donus', label: 'Donus Havayolu' },
  { key: 'kalkis_saati_donus', label: 'Donus Kalkis' },
  { key: 'aktarma_int_donus', label: 'Donus Aktarma' },
  { key: 'fiyat_tl_donus', label: 'Donus Fiyat' },
  { key: 'toplam_fiyat', label: 'Toplam Fiyat' },
  { key: 'skor', label: 'Skor' },
]

function transferText(n) {
  return n === 0 ? 'Direkt' : `${n} aktarma`
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
  const sortableKeys = ['skor', 'toplam_fiyat', 'toplam_sure', 'hafta_sonu']
  if (!sortableKeys.includes(key)) return
  if (sortBy.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = key
    sortOrder.value = key === 'toplam_fiyat' || key === 'hafta_sonu' ? 'asc' : 'desc'
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
