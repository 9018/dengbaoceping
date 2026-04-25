<template>
  <el-dialog v-model="visible" :title="mode === 'create' ? '新增设备资产' : '编辑设备资产'" width="640px">
    <el-form label-width="110px">
      <el-form-item label="分类标识">
        <el-input v-model="form.category" placeholder="例如 firewall / switch / server" />
      </el-form-item>
      <el-form-item label="分类名称">
        <el-input v-model="form.category_label" placeholder="例如 防火墙 / 交换机 / 服务器" />
      </el-form-item>
      <el-form-item label="资产名称">
        <el-input v-model="form.filename" placeholder="填写测试对象名称" />
      </el-form-item>
      <el-form-item label="主 IP">
        <el-input v-model="form.primary_ip" placeholder="例如 10.0.0.1" />
      </el-form-item>
      <el-form-item label="批次号">
        <el-input v-model="form.batch_no" />
      </el-form-item>
      <el-form-item label="相对路径">
        <el-input v-model="form.relative_path" placeholder="例如 assets/device-manual.txt" />
      </el-form-item>
      <el-form-item label="绝对路径">
        <el-input v-model="form.absolute_path" />
      </el-form-item>
      <el-form-item label="MIME 类型">
        <el-input v-model="form.mime_type" />
      </el-form-item>
      <el-form-item label="大小">
        <el-input-number v-model="form.file_size" :min="0" class="w-full" />
      </el-form-item>
      <el-form-item label="来源">
        <el-input v-model="form.source" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="form.ingest_status" class="w-full">
          <el-option v-for="status in assetStatusOptions" :key="status" :label="status" :value="status" />
        </el-select>
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
import type { Asset } from '@/types/domain'
import { assetStatusOptions } from '@/utils/constants'

const props = defineProps<{
  modelValue: boolean
  asset?: Asset | null
  mode?: 'create' | 'edit'
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'submit', value: Record<string, unknown>): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const form = reactive({
  asset_kind: 'test_object',
  category: 'device',
  category_label: '设备资产',
  batch_no: '',
  filename: '',
  primary_ip: '',
  file_ext: '',
  mime_type: 'text/plain',
  relative_path: 'assets/device.txt',
  absolute_path: '',
  file_size: 0,
  file_sha256: '',
  file_mtime: '',
  source: 'manual',
  ingest_status: 'pending',
})

watch(
  () => props.asset,
  (asset) => {
    form.asset_kind = asset?.asset_kind ?? 'test_object'
    form.category = asset?.category ?? 'device'
    form.category_label = asset?.category_label ?? '设备资产'
    form.batch_no = asset?.batch_no ?? ''
    form.filename = asset?.filename ?? ''
    form.primary_ip = asset?.primary_ip ?? ''
    form.file_ext = asset?.file_ext ?? ''
    form.mime_type = asset?.mime_type ?? 'text/plain'
    form.relative_path = asset?.relative_path ?? 'assets/device.txt'
    form.absolute_path = asset?.absolute_path ?? ''
    form.file_size = asset?.file_size ?? 0
    form.file_sha256 = asset?.file_sha256 ?? ''
    form.file_mtime = asset?.file_mtime ?? ''
    form.source = asset?.source ?? 'manual'
    form.ingest_status = asset?.ingest_status ?? 'pending'
  },
  { immediate: true },
)

const mode = computed(() => props.mode || 'create')

function submit() {
  emit('submit', {
    asset_kind: form.asset_kind,
    category: form.category.trim(),
    category_label: form.category_label.trim(),
    batch_no: form.batch_no.trim() || null,
    filename: form.filename.trim(),
    primary_ip: form.primary_ip.trim() || null,
    file_ext: form.file_ext.trim() || null,
    mime_type: form.mime_type.trim() || null,
    relative_path: form.relative_path.trim(),
    absolute_path: form.absolute_path.trim() || null,
    file_size: form.file_size,
    file_sha256: form.file_sha256.trim() || null,
    file_mtime: form.file_mtime.trim() || null,
    source: form.source.trim() || null,
    ingest_status: form.ingest_status,
  })
}
</script>

<style scoped>
.w-full {
  width: 100%;
}
</style>
