<template>
  <form @submit.prevent>
    <div v-for="mf in module.fields" :key="mf.field_id" class="dyn-field">
      <label class="form-label d-flex align-items-center gap-1 mb-1">
        <span>
          {{ mf.field.name }}
          <span v-if="mf.is_required" class="text-danger">*</span>
        </span>
        <Info
          v-if="mf.field.description"
          class="text-muted"
          v-tip="mf.field.description"
          style="cursor: help"
        />
      </label>
      <FieldRenderer
        :field="mf.field"
        :model-value="modelValue[mf.field.code]"
        :disabled="loading"
        @update:model-value="(v: any) => updateField(mf.field.code, v)"
      />
    </div>
  </form>
</template>

<script setup lang="ts">
import { Info } from 'lucide-vue-next'
import FieldRenderer from './FieldRenderer.vue'
import { vTip } from '@/components/ui/tooltip'
import type { ModuleOut } from '@/api'

const props = defineProps<{
  module: ModuleOut
  modelValue: Record<string, any>
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: Record<string, any>): void
}>()

function updateField(code: string, value: any) {
  emit('update:modelValue', { ...props.modelValue, [code]: value })
}
</script>

<style scoped>
.dyn-field + .dyn-field {
  margin-top: 16px;
}

.dyn-field .form-label .lucide {
  width: 14px;
  height: 14px;
}
</style>
