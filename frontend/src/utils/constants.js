// 质量标签与缺陷等级（与后端 algorithms/feature_engineering.py 保持一致）
export const LABEL_NAMES = { 0: '合格', 1: '欠拧', 2: '过拧', 3: '滑牙', 4: '虚拧' }

export const LABEL_COLORS = {
  合格: '#67c23a',
  欠拧: '#e6a23c',
  过拧: '#f56c6c',
  滑牙: '#f56c6c',
  虚拧: '#909399',
}

export const DEFECT_LEVELS = { 0: '无', 1: '轻微', 2: '一般', 3: '严重' }

export const SPECS = ['M12', 'M16', 'M20', 'M24']

export const GRADES = ['8.8', '10.9', '12.9']

export const WEAR_NAMES = { 0: '新工具', 1: '中度磨损', 2: '重度磨损' }

// 标签类型颜色映射（Element Plus tag type）
export const LABEL_TAG_TYPE = {
  0: 'success',
  1: 'warning',
  2: 'danger',
  3: 'danger',
  4: 'info',
}
