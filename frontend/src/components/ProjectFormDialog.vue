<template>
  <el-dialog v-model="visible" :title="mode === 'create' ? '新建项目' : '编辑项目'" width="520px">
    <el-form label-width="96px">
      <el-form-item label="项目编码">
        <el-input v-model="form.code" placeholder="可选，建议唯一" />
      </el-form-item>
      <el-form-item label="项目名称">
        <el-input v-model="form.name" placeholder="请输入项目名称" />
      </el-form-item>
      <el-form-item label="项目类型">
        <el-input v-model="form.project_type" />
      </el-form-item>
      <el-form-item label="项目状态">
        <el-select v-model="form.status" class="w-full">
          <el-option v-for="status in projectStatusOptions" :key="status" :label="status" :value="status" />
        </el-select>
      </el-form-item>
      <el-form-item label="项目说明">
        <el-input v-model="form.description" type="textarea" :rows="3" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" @click="submit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { projectStatusOptions } from '@/utils/constants'
import type { Project } from '@/types/domain'

const props = defineProps<{
  modelValue: boolean
  project?: Project | null
  mode?: 'create' | 'edit'
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'submit', value: { code: string | null; name: string; project_type: string; status: string; description: string | null }): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const form = reactive({
  code: '' as string | null,
  name: '',
  project_type: '等级保护测评',
  status: 'draft',
  description: '' as string | null,
})

watch(
  () => props.project,
  (project) => {
    form.code = project?.code ?? ''
    form.name = project?.name ?? ''
    form.project_type = project?.project_type ?? '等级保护测评'
    form.status = project?.status ?? 'draft'
    form.description = project?.description ?? ''
  },
  { immediate: true },
)

const mode = computed(() => props.mode || 'create')

function submit() {
  emit('submit', {
    code: form.code || null,
    name: form.name.trim(),
    project_type: form.project_type.trim() || '等级保护测评',
    status: form.status,
    description: form.description?.trim() || null,
  })
}
</script>

<style scoped>
.w-full {
  width: 100%;
}
</style>
