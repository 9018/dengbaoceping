<template>
  <el-dialog v-model="visible" title="上传证据" width="640px">
    <el-form label-width="110px">
      <el-form-item label="证据文件">
        <input type="file" @change="onFileChange" />
      </el-form-item>
      <el-form-item label="证据标题">
        <el-input v-model="form.title" />
      </el-form-item>
      <el-form-item label="证据类型">
        <el-input v-model="form.evidence_type" />
      </el-form-item>
      <el-form-item label="证据摘要">
        <el-input v-model="form.summary" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item label="关联设备">
        <el-input v-model="form.device" />
      </el-form-item>
      <el-form-item label="标签(JSON)">
        <el-input v-model="form.tags_json" placeholder='例如 ["demo","export"]' />
      </el-form-item>
      <el-form-item label="端口(JSON)">
        <el-input v-model="form.ports_json" placeholder='例如 [80,443]' />
      </el-form-item>
      <el-form-item label="证据时间">
        <el-input v-model="form.evidence_time" placeholder="ISO 时间字符串，可留空" />
      </el-form-item>
      <el-form-item label="来源标识">
        <el-input v-model="form.source_ref" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" @click="submit">上传</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'

const props = defineProps<{ modelValue: boolean }>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'submit', value: Record<string, unknown>): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const form = reactive({
  file: null as File | null,
  title: '防火墙配置截图',
  evidence_type: 'screenshot',
  summary: '边界防护设备联调样例',
  device: '服务器A',
  tags_json: '["demo","export"]',
  ports_json: '',
  evidence_time: '',
  source_ref: 'manual-demo',
})

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  form.file = input.files?.[0] || null
}

function safeParse(value: string) {
  if (!value.trim()) return undefined
  try {
    return JSON.parse(value)
  } catch {
    return value
  }
}

function submit() {
  emit('submit', {
    file: form.file,
    title: form.title,
    evidence_type: form.evidence_type,
    summary: form.summary,
    device: form.device,
    tags_json: safeParse(form.tags_json),
    ports_json: safeParse(form.ports_json),
    evidence_time: form.evidence_time || undefined,
    source_ref: form.source_ref,
  })
}
</script>
