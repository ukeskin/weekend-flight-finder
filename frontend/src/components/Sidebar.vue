<template>
  <h2>Filtreler</h2>

  <label>Hafta Sonu Baslangic</label>
  <select :value="filters.weekendStart" @change="emit('update:filters', { ...filters, weekendStart: $event.target.value })">
    <option v-for="w in weekends" :key="w" :value="w">{{ w }}</option>
  </select>

  <label>Hafta Sonu Bitis</label>
  <select :value="filters.weekendEnd" @change="emit('update:filters', { ...filters, weekendEnd: $event.target.value })">
    <option v-for="w in weekends" :key="w" :value="w">{{ w }}</option>
  </select>

  <label>Destinasyon</label>
  <select
    multiple
    :value="filters.cities"
    @change="onCitiesChange"
  >
    <option v-for="d in destinations" :key="d" :value="d">{{ d }}</option>
  </select>

  <label>Maks. Toplam Fiyat (TRY)</label>
  <input
    type="number"
    :value="filters.maxPrice"
    @change="emit('update:filters', { ...filters, maxPrice: $event.target.value ? Number($event.target.value) : null })"
    placeholder="Sinirsiz"
    step="500"
    min="1000"
  />

  <div class="checkbox-row">
    <input
      type="checkbox"
      id="directOnly"
      :checked="filters.directOnly"
      @change="emit('update:filters', { ...filters, directOnly: $event.target.checked })"
    />
    <label for="directOnly" style="margin:0">Sadece direkt ucus</label>
  </div>

  <label>Kalkis Havalimani</label>
  <div class="radio-group">
    <label v-for="opt in origins" :key="opt.value" :class="{ active: filters.origin === opt.value }">
      <input
        type="radio"
        :value="opt.value"
        :checked="filters.origin === opt.value"
        @change="emit('update:filters', { ...filters, origin: opt.value })"
      />
      {{ opt.label }}
    </label>
  </div>
</template>

<script setup>
const props = defineProps({
  destinations: Array,
  weekends: Array,
  filters: Object,
})

const emit = defineEmits(['update:filters'])

const origins = [
  { value: 'all', label: 'Hepsi' },
  { value: 'IST', label: 'IST' },
  { value: 'SAW', label: 'SAW' },
]

function onCitiesChange(e) {
  const selected = Array.from(e.target.selectedOptions, o => o.value)
  emit('update:filters', { ...props.filters, cities: selected })
}
</script>
