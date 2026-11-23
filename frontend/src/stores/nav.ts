import { defineStore } from 'pinia'
import { ref } from 'vue'
import { categoryApi, moduleApi, type CategoryOut, type ModuleListItem } from '@/api'

export const useNavStore = defineStore('nav', () => {
  const categories = ref<CategoryOut[]>([])
  const modules = ref<ModuleListItem[]>([])

  async function refresh() {
    const [c, m] = await Promise.all([categoryApi.list(), moduleApi.list({ enabled_only: true })])
    categories.value = c.data
    modules.value = m.data
  }

  return { categories, modules, refresh }
})
