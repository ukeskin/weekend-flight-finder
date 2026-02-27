import axios from 'axios'

const API_KEY = import.meta.env.VITE_API_KEY || ''

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '',
  headers: {
    'X-API-Key': API_KEY,
  },
})

export function buildParams(filters) {
  const params = {}
  if (filters.weekendStart) params.weekend_start = filters.weekendStart
  if (filters.weekendEnd) params.weekend_end = filters.weekendEnd
  if (filters.destinations && filters.destinations.length) params.destinations = filters.destinations.join(',')
  if (filters.maxPrice) params.max_price = filters.maxPrice
  if (filters.directOnly) params.direct_only = true
  return params
}

export async function fetchStats(filters) {
  const { data } = await api.get('/api/stats', { params: buildParams(filters) })
  return data
}

export async function fetchTopTrips(filters, n = 20) {
  const params = { ...buildParams(filters), n }
  const { data } = await api.get('/api/trips/top', { params })
  return data
}

export async function fetchTrips(filters, page = 1, perPage = 20, sortBy = 'skor', sortOrder = 'desc') {
  const params = { ...buildParams(filters), page, per_page: perPage, sort_by: sortBy, sort_order: sortOrder }
  const { data } = await api.get('/api/trips', { params })
  return data
}

export async function fetchDestinations() {
  const { data } = await api.get('/api/destinations')
  return data
}

export async function fetchWeekends() {
  const { data } = await api.get('/api/weekends')
  return data
}

export async function fetchHeatmap(filters) {
  const { data } = await api.get('/api/heatmap', { params: buildParams(filters) })
  return data
}

export async function fetchCityCompare(filters) {
  const { data } = await api.get('/api/city-compare', { params: buildParams(filters) })
  return data
}
