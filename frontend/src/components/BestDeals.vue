<template>
  <div v-if="loading" class="loading">
    <div class="loading-spinner"></div>
    <div>Yukleniyor...</div>
  </div>
  <div v-else-if="!trips.length" class="loading">
    <div>Bu filtrelerle eslesen ucus bulunamadi.</div>
  </div>
  <div v-else>
    <div v-for="trip in trips" :key="trip.id" class="deal-card">
      <div>
        <h3>
          {{ trip.varis_sehir }}, {{ trip.varis_ulke }}
          <span class="airport-code">({{ trip.varis_havalimani }})</span>
        </h3>
        <p>{{ trip.hafta_sonu }}</p>
        <p>Gidis: {{ trip.kalkis_saati_gidis }} → {{ trip.varis_saati_gidis }} ({{ transferText(trip.aktarma_int_gidis) }})</p>
        <p>Donus: {{ trip.kalkis_saati_donus }} → {{ trip.varis_saati_donus }} ({{ transferText(trip.aktarma_int_donus) }})</p>
        <p v-if="trip.sure_gidis || trip.sure_donus">{{ trip.sure_gidis || '' }} + {{ trip.sure_donus || '' }}</p>
      </div>
      <div class="deal-right">
        <div class="deal-price">₺{{ Math.round(trip.toplam_fiyat).toLocaleString('tr-TR') }}</div>
        <div class="deal-score">Skor: {{ trip.skor }}</div>
        <div class="deal-origin">{{ trip.kalkis_havalimani }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchTopTrips } from '../api.js'

const props = defineProps({ filters: Object })
const trips = ref([])
const loading = ref(true)

function transferText(n) {
  return n === 0 ? 'Direkt' : `${n} aktarma`
}

onMounted(async () => {
  try {
    trips.value = await fetchTopTrips(props.filters, 20)
  } finally {
    loading.value = false
  }
})
</script>
