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
    :value="filters.destinations"
    @change="onCitiesChange"
  >
    <option v-for="d in destinations" :key="d.code" :value="d.code">{{ d.label }}</option>
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

</template>

<script setup>
const props = defineProps({
  destinations: Array,
  weekends: Array,
  filters: Object,
})

const emit = defineEmits(['update:filters'])

function onCitiesChange(e) {
  const selected = Array.from(e.target.selectedOptions, o => o.value)
  emit('update:filters', { ...props.filters, destinations: selected })
}
</script>
