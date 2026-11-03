import axiosInstance from './axios'

export async function fetchAllPages(url) {
  const items = []
  let next = url
  while (next) {
    const { data } = await axiosInstance.get(next)
    if (Array.isArray(data)) return items.concat(data)
    items.push(...(data.results || []))
    next = data.next
  }
  return items
}
