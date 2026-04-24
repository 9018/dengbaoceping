import type { TagProps } from 'element-plus'

export type StatusKind = 'project' | 'asset' | 'ocr' | 'field' | 'record' | 'export'

type StatusTagType = TagProps['type']

type StatusMeta = {
  label: string
  type: StatusTagType
}

const statusRegistry: Record<StatusKind, Record<string, StatusMeta>> = {
  project: {
    draft: { label: '草稿中', type: 'warning' },
    active: { label: '执行中', type: 'success' },
    archived: { label: '已归档', type: 'info' },
  },
  asset: {
    pending: { label: '待处理', type: 'warning' },
    processed: { label: '已入库', type: 'success' },
    failed: { label: '入库失败', type: 'danger' },
  },
  ocr: {
    pending: { label: '识别中', type: 'warning' },
    completed: { label: '已完成', type: 'success' },
    failed: { label: '识别失败', type: 'danger' },
  },
  field: {
    missing: { label: '字段缺失', type: 'info' },
    extracted: { label: '已抽取', type: 'primary' },
    reviewed: { label: '已复核', type: 'success' },
    corrected: { label: '已修正', type: 'warning' },
    rejected: { label: '已驳回', type: 'danger' },
  },
  record: {
    generated: { label: '待复核', type: 'warning' },
    generated_low_confidence: { label: '低置信度', type: 'danger' },
    reviewed: { label: '已复核', type: 'primary' },
    approved: { label: '已审批', type: 'success' },
    exported: { label: '已导出', type: 'info' },
  },
  export: {
    pending: { label: '导出中', type: 'warning' },
    completed: { label: '已完成', type: 'success' },
    failed: { label: '导出失败', type: 'danger' },
  },
}

const emptyLabelRegistry: Record<StatusKind, string> = {
  project: '未设置',
  asset: '未设置',
  ocr: '未执行',
  field: '待处理',
  record: '未生成',
  export: '未导出',
}

export function getStatusLabel(kind: StatusKind, status?: string | null) {
  if (!status) return emptyLabelRegistry[kind]
  return statusRegistry[kind][status]?.label || status
}

export function getStatusTagType(kind: StatusKind, status?: string | null): StatusTagType {
  if (!status) return 'info'
  return statusRegistry[kind][status]?.type || 'info'
}
