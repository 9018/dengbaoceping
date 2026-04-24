export const projectStatusOptions = ['draft', 'active', 'archived']
export const assetStatusOptions = ['pending', 'processed', 'failed']
export const fieldStatusOptions = ['missing', 'extracted', 'reviewed', 'corrected', 'rejected']
export const recordStatusOptions = ['generated', 'reviewed', 'approved', 'exported']
export const reviewStatusOptions = ['reviewed', 'corrected', 'rejected']
export const recordReviewStatusOptions = ['reviewed', 'approved', 'exported']
export const exportStatusOptions = ['pending', 'completed', 'failed']
export const ocrStatusOptions = ['pending', 'completed', 'failed']

export const ocrSampleOptions = [
  'firewall_basic',
  'windows_host',
  'windows_host_partial',
  'security_policy',
  'security_policy_missing_action',
  'network_config',
  'noisy_mixed',
]

export const templateCodeOptions = [
  'security_device_basic',
  'security_policy_basic',
  'host_basic_info',
  'network_config_basic',
]

export const workflowSteps = ['项目建档', '证据采集', 'OCR 识别', '字段复核', '记录复核', '项目导出']
